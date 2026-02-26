import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Location as DBLocation,
    Metric as DBMetric,
    OptimizationResult as DBOptimizationResult,
    Route as DBRoute,
)
from src.models.geo_utils import (
    compute_distance_matrix,
    detect_region_info,
    estimate_fuel_cost,
    infer_category,
)
from src.models.llama_client import LlamaClient
from src.models.qwen_client import QwenClient
from src.models.schemas import (
    Location as PydanticLocation,
    Route as PydanticRoute,
)
from src.services.model_selector import (
    MODEL_QWEN,
    get_model_recommendation,
    select_best_model,
)
from src.services.quality_evaluator import evaluate_route_quality

logger = logging.getLogger("optimizer")


class Optimizer:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.qwen_client = QwenClient()
        self.llama_client = LlamaClient()
        self.max_locations_per_prompt = 40

    def _convert_db_to_pydantic(
        self,
        db_loc: DBLocation,
    ) -> PydanticLocation:
        return PydanticLocation(
            ID=db_loc.id,
            name=db_loc.name,
            address=db_loc.name,
            lat=db_loc.lat,
            lon=db_loc.lon,
            time_window_start=db_loc.time_window_start,
            time_window_end=db_loc.time_window_end,
            priority="A",
        )

    def _calculate_real_metrics(
        self,
        locations: List[PydanticLocation],
    ) -> Dict[str, Any]:
        if not locations:
            return {
                "distance_km": 0.0,
                "time_minutes": 0.0,
                "cost_rub": 0.0,
            }

        loc_dicts = [{"lat": loc.lat,
                      "lon": loc.lon} for loc in locations]

        info = detect_region_info(loc_dicts)
        matrix = compute_distance_matrix(loc_dicts)

        total_dist = 0.0
        for i in range(len(locations) - 1):
            total_dist += matrix[i][i + 1]

        speed = 25.0 if info["classification"] == "urban" else 45.0
        time_mins = (total_dist / speed) * 60 + (len(locations) * 15)

        return {
            "distance_km": round(total_dist, 2),
            "time_minutes": round(time_mins, 2),
            "cost_rub": estimate_fuel_cost(total_dist),
        }

    async def optimize(
        self,
        db_locations: List[DBLocation],
        model: str = "auto",
    ) -> PydanticRoute:
        start_time_ms = int(time.time() * 1000)

        pydantic_locations = [
            self._convert_db_to_pydantic(loc)
            for loc in db_locations
        ]

        original_ids = [loc.id for loc in db_locations]
        baseline = self._calculate_real_metrics(pydantic_locations)

        target_model = (
            select_best_model(len(pydantic_locations))
            if model == "auto"
            else model
        )

        optimized_route = await self._generate_with_fallback(
            pydantic_locations[: self.max_locations_per_prompt],
            {"fuel_rate": 7.0},
            target_model,
        )

        real_stats = self._calculate_real_metrics(
            optimized_route.locations,
        )

        optimized_route.total_distance_km = real_stats["distance_km"]
        optimized_route.total_cost_rub = real_stats["cost_rub"]
        optimized_route.total_time_hours = (
            real_stats["time_minutes"] / 60
        )

        q_score = evaluate_route_quality(
            {**baseline, "constraints_satisfied": True},
            {**real_stats, "constraints_satisfied": True},
        )

        improvement_pct = 0.0
        if baseline["distance_km"] > 0:
            improvement_pct = max(
                0.0,
                (
                    (baseline["distance_km"] - real_stats["distance_km"])
                    / baseline["distance_km"]
                )
                * 100,
            )

        object.__setattr__(
            optimized_route,
            "quality_score",
            q_score,
        )

        try:
            route_id = str(uuid.uuid4())
            optimized_ids = [
                loc.ID for loc in optimized_route.locations
            ]

            new_route = DBRoute(
                id=route_id,
                name=optimized_route.name or "Optimized Route",
                locations_order=optimized_ids,
                total_distance=optimized_route.total_distance_km,
                total_time=optimized_route.total_time_hours,
                total_cost=optimized_route.total_cost_rub,
                model_used=optimized_route.model_used or "unknown",
            )
            self.db.add(new_route)

            self.db.add(
                DBMetric(
                    route_id=route_id,
                    model_name=optimized_route.model_used,
                    response_time_ms=(
                        int(time.time() * 1000) - start_time_ms
                    ),
                    quality_score=q_score,
                    cost=0.0,
                ),
            )

            self.db.add(
                DBOptimizationResult(
                    original_route=original_ids,
                    optimized_route=optimized_ids,
                    improvement_percentage=round(
                        improvement_pct,
                        2,
                    ),
                    model_used=optimized_route.model_used,
                    created_at=datetime.now(
                        timezone.utc,
                    ).replace(tzinfo=None),
                ),
            )

            await self.db.commit()
            logger.info(
                "Optimization results for route %s saved successfully.",
                route_id,
            )

        except Exception as exc:
            await self.db.rollback()
            logger.error("Database sync failed: %s", exc)

        optimized_route.recommendation = get_model_recommendation(
            len(db_locations),
            model,
        )
        return optimized_route

    def _greedy_reorder(
        self,
        locations: List[PydanticLocation],
    ) -> List[PydanticLocation]:
        """
        Жадный алгоритм ближайшего соседа.
        Начинаем с точки наивысшего приоритета (A>B>C>D),
        далее выбираем ближайшую ещё не посещённую точку.
        """
        if len(locations) <= 1:
            return locations

        loc_dicts = [{"lat": loc.lat, "lon": loc.lon} for loc in locations]
        matrix = compute_distance_matrix(loc_dicts)
        n = len(locations)

        # Старт — точка с наивысшим приоритетом
        priority_rank = {"A": 0, "B": 1, "C": 2, "D": 3}
        start = min(
            range(n),
            key=lambda i: priority_rank.get(
                infer_category(getattr(locations[i], "priority", "C")), 3
            ),
        )

        visited = [False] * n
        order = [start]
        visited[start] = True

        for _ in range(n - 1):
            cur = order[-1]
            nearest = min(
                (j for j in range(n) if not visited[j]),
                key=lambda j: matrix[cur][j],
            )
            order.append(nearest)
            visited[nearest] = True

        return [locations[i] for i in order]

    async def _generate_with_fallback(
        self,
        locs: List[PydanticLocation],
        constr: Dict[str, Any],
        model_name: str,
    ) -> PydanticRoute:
        """
        Пытается получить маршрут от основной модели, затем от запасной,
        затем использует чистый greedy-алгоритм как последний fallback.
        Всегда применяет greedy для определения реального порядка точек —
        результат LLM используется только для логирования/метрик.
        """
        valid_ids = {loc.ID for loc in locs}

        async def _try_model(client) -> PydanticRoute | None:
            try:
                return await client.generate_route(locs, constr)
            except Exception as exc:
                logger.warning("Model %s failed: %s", type(client).__name__, exc)
                return None

        primary = (
            self.qwen_client if model_name == MODEL_QWEN else self.llama_client
        )
        alt = (
            self.llama_client if model_name == MODEL_QWEN else self.qwen_client
        )

        route = await _try_model(primary)
        if route is None:
            logger.warning("Primary model failed, trying alternative.")
            route = await _try_model(alt)

        # Применяем greedy reorder для получения реального оптимального порядка.
        # LLM-модели ненадёжны для малых моделей (0.5B–1.2B),
        # поэтому Python всегда определяет итоговый порядок.
        reordered = self._greedy_reorder(locs)

        if route is None:
            # Оба LLM упали — создаём маршрут на основе greedy
            logger.warning("Both LLMs failed, using pure greedy route.")
            import uuid
            from datetime import datetime
            route = PydanticRoute(
                ID=str(uuid.uuid4()),
                name="Оптимизированный маршрут (Greedy)",
                locations=reordered,
                total_distance_km=0.0,
                total_time_hours=0.0,
                total_cost_rub=0.0,
                model_used="greedy",
                created_at=datetime.now(),
            )
        else:
            # Заменяем порядок локаций на greedy-оптимальный
            route.locations = reordered

        return route
