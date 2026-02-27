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
    haversine,
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
        # Используем реальную категорию ТТ; при её отсутствии — "C" (средний приоритет)
        priority = db_loc.category if db_loc.category in ("A", "B", "C", "D") else "C"
        return PydanticLocation(
            ID=db_loc.id,
            name=db_loc.name,
            address=getattr(db_loc, "address", None) or db_loc.name,
            lat=db_loc.lat,
            lon=db_loc.lon,
            time_window_start=db_loc.time_window_start,
            time_window_end=db_loc.time_window_end,
            priority=priority,
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

    # ─── Вспомогательный greedy для подмножества точек ──────────────────────────

    def _greedy_subset(
        self,
        locations: List[PydanticLocation],
        start_idx: int = 0,
    ) -> List[PydanticLocation]:
        """Greedy nearest-neighbor внутри подмножества точек."""
        n = len(locations)
        if n <= 1:
            return list(locations)

        loc_dicts = [{"lat": loc.lat, "lon": loc.lon} for loc in locations]
        matrix = compute_distance_matrix(loc_dicts)

        visited = [False] * n
        order = [start_idx]
        visited[start_idx] = True

        for _ in range(n - 1):
            cur = order[-1]
            nearest = min(
                (j for j in range(n) if not visited[j]),
                key=lambda j: matrix[cur][j],
            )
            order.append(nearest)
            visited[nearest] = True

        return [locations[i] for i in order]

    # ─── Алгоритм 2: Приоритет категорий (A→B→C→D) ──────────────────────────────

    def _priority_first_reorder(
        self,
        locations: List[PydanticLocation],
    ) -> List[PydanticLocation]:
        """
        Сначала посещаем все точки категории A (greedy),
        затем B, C, D — каждую группу greedy от последней посещённой точки.
        """
        if len(locations) <= 1:
            return list(locations)

        groups: Dict[str, List[PydanticLocation]] = {"A": [], "B": [], "C": [], "D": []}
        for loc in locations:
            cat = infer_category(getattr(loc, "priority", "C"))
            groups[cat].append(loc)

        result: List[PydanticLocation] = []
        for cat in ("A", "B", "C", "D"):
            group = groups[cat]
            if not group:
                continue

            if result:
                last = result[-1]
                distances = [
                    haversine(last.lat, last.lon, loc.lat, loc.lon)
                    for loc in group
                ]
                start_idx = distances.index(min(distances))
            else:
                start_idx = 0

            result.extend(self._greedy_subset(group, start_idx))

        return result

    # ─── Алгоритм 3: Взвешенный баланс (60% расстояние + 40% приоритет) ─────────

    def _balanced_reorder(
        self,
        locations: List[PydanticLocation],
    ) -> List[PydanticLocation]:
        """
        Взвешенный алгоритм: score = 0.6 × distance + 0.4 × priority_penalty.
        A-точки получают нулевой штраф, D-точки — 15 км эквивалент.
        """
        if len(locations) <= 1:
            return list(locations)

        loc_dicts = [{"lat": loc.lat, "lon": loc.lon} for loc in locations]
        matrix = compute_distance_matrix(loc_dicts)
        n = len(locations)

        priority_penalty_km = {"A": 0.0, "B": 3.0, "C": 8.0, "D": 15.0}
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
                key=lambda j: (
                    0.6 * matrix[cur][j]
                    + 0.4 * priority_penalty_km.get(
                        infer_category(getattr(locations[j], "priority", "C")), 8.0
                    )
                ),
            )
            order.append(nearest)
            visited[nearest] = True

        return [locations[i] for i in order]

    # ─── Генерация вариантов маршрута (без сохранения в БД) ──────────────────────

    async def generate_variants(
        self,
        db_locations: List[DBLocation],
        model: str = "qwen",
    ):
        """
        Генерирует 3 детерминированных варианта маршрута,
        затем запрашивает у LLM pros/cons для каждого.
        БД не используется — результат возвращается напрямую.
        """
        from src.schemas.optimize import (
            OptimizeVariantsResponse,
            RouteVariant,
            RouteVariantMetrics,
        )

        start_time_ms = int(time.time() * 1000)

        pydantic_locations = [
            self._convert_db_to_pydantic(loc) for loc in db_locations
        ]

        # Базовые метрики (неупорядоченный маршрут)
        baseline = self._calculate_real_metrics(pydantic_locations)

        # ── Три варианта ────────────────────────────────────────────────────────
        variant_configs = [
            {
                "id": 1,
                "name": "Минимум расстояния",
                "description": "Кратчайший путь между точками (жадный алгоритм)",
                "algorithm": "greedy",
                "locations_ordered": self._greedy_reorder(pydantic_locations),
            },
            {
                "id": 2,
                "name": "По приоритету категорий",
                "description": "Сначала точки A, затем B, C, D — внутри группы кратчайший путь",
                "algorithm": "priority_first",
                "locations_ordered": self._priority_first_reorder(pydantic_locations),
            },
            {
                "id": 3,
                "name": "Оптимальный баланс",
                "description": "Взвешенный подход: 60% расстояние + 40% важность точки",
                "algorithm": "balanced",
                "locations_ordered": self._balanced_reorder(pydantic_locations),
            },
        ]

        # Считаем метрики для каждого варианта
        variants_data = []
        for vc in variant_configs:
            real = self._calculate_real_metrics(vc["locations_ordered"])
            q_score = evaluate_route_quality(
                {**baseline, "constraints_satisfied": True},
                {**real, "constraints_satisfied": True},
            )
            variants_data.append({
                "id": vc["id"],
                "name": vc["name"],
                "description": vc["description"],
                "algorithm": vc["algorithm"],
                "locations_ordered": vc["locations_ordered"],
                "metrics": {
                    "distance_km": real["distance_km"],
                    "time_hours": real["time_minutes"] / 60,
                    "cost_rub": real["cost_rub"],
                    "quality_score": q_score,
                },
                "pros": [],
                "cons": [],
            })

        # ── LLM: генерируем pros/cons (graceful fallback при ошибке) ───────────
        llm_success = False
        try:
            client = (
                self.qwen_client if model == "qwen" else self.llama_client
            )
            evaluation = await client.evaluate_variants(variants_data)
            if evaluation:
                eval_by_id = {item["id"]: item for item in evaluation}
                for v in variants_data:
                    ev = eval_by_id.get(v["id"])
                    if ev:
                        v["pros"] = ev.get("pros", [])[:3]
                        v["cons"] = ev.get("cons", [])[:3]
                llm_success = True
        except Exception as exc:
            logger.warning("LLM evaluate_variants failed: %s", exc)

        # ── Строим ответ ────────────────────────────────────────────────────────
        response_variants = [
            RouteVariant(
                id=v["id"],
                name=v["name"],
                description=v["description"],
                algorithm=v["algorithm"],
                pros=v["pros"],
                cons=v["cons"],
                locations=[loc.ID for loc in v["locations_ordered"]],
                metrics=RouteVariantMetrics(**v["metrics"]),
            )
            for v in variants_data
        ]

        return OptimizeVariantsResponse(
            variants=response_variants,
            model_used=model,
            response_time_ms=int(time.time() * 1000) - start_time_ms,
            llm_evaluation_success=llm_success,
        )

    # ─── Сохранение выбранного варианта в БД ─────────────────────────────────────

    async def confirm_variant(
        self,
        name: str,
        locations_order: List[str],
        total_distance_km: float,
        total_time_hours: float,
        total_cost_rub: float,
        quality_score: float,
        model_used: str,
        original_location_ids: List[str],
    ):
        """
        Сохраняет выбранный пользователем вариант маршрута в БД.
        Возвращает OptimizeResponse-совместимый словарь.
        """
        start_time_ms = int(time.time() * 1000)
        route_id = str(uuid.uuid4())

        improvement_pct = 0.0
        try:
            new_route = DBRoute(
                id=route_id,
                name=name,
                locations_order=locations_order,
                total_distance=total_distance_km,
                total_time=total_time_hours,
                total_cost=total_cost_rub,
                model_used=model_used,
            )
            self.db.add(new_route)

            self.db.add(
                DBMetric(
                    route_id=route_id,
                    model_name=model_used,
                    response_time_ms=int(time.time() * 1000) - start_time_ms,
                    quality_score=quality_score,
                    cost=0.0,
                )
            )

            self.db.add(
                DBOptimizationResult(
                    original_route=original_location_ids,
                    optimized_route=locations_order,
                    improvement_percentage=round(improvement_pct, 2),
                    model_used=model_used,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )

            await self.db.commit()
            logger.info("Confirmed variant saved as route %s.", route_id)

        except Exception as exc:
            await self.db.rollback()
            logger.error("confirm_variant DB save failed: %s", exc)
            raise

        return {
            "id": route_id,
            "name": name,
            "locations": locations_order,
            "total_distance_km": total_distance_km,
            "total_time_hours": total_time_hours,
            "total_cost_rub": total_cost_rub,
            "model_used": model_used,
            "quality_score": quality_score,
            "response_time_ms": int(time.time() * 1000) - start_time_ms,
            "fallback_reason": None,
            "created_at": datetime.now().isoformat(),
        }

    # ─── Оригинальный greedy (алгоритм 1, также используется как fallback) ───────

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
        Строит маршрут чистым greedy-алгоритмом (мгновенно, < 100 мс).

        Ранее здесь вызывалась LLM, но малые модели (0.5B–1.2B) стабильно
        выдают невалидный JSON и занимают 30–120 с при нулевом улучшении:
        greedy всё равно перезаписывал LLM-порядок.

        Для LLM-оценки вариантов используйте /optimize/variants, где
        generate_variants() вызывает evaluate_variants() (pros/cons),
        а не generate_route() — это задача, с которой малые модели справляются.
        """
        reordered = self._greedy_reorder(locs)
        label = model_name if model_name not in ("auto",) else "greedy"
        return PydanticRoute(
            ID=str(uuid.uuid4()),
            name=f"Оптимизированный маршрут ({label})",
            locations=reordered,
            total_distance_km=0.0,
            total_time_hours=0.0,
            total_cost_rub=0.0,
            model_used=label,
            created_at=datetime.now(),
        )
