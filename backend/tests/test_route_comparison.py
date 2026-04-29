import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

sys.modules.setdefault("asyncpg", MagicMock())

from src.database.models import Location, Metric, OptimizationResult, Route
from src.models.schemas import Location as PydanticLocation
from src.models.schemas import Route as PydanticRoute
from src.routes.routes import get_route_comparison, get_route_detail, get_routes
from src.services.optimize import Optimizer


class ScalarValueResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class ScalarsResult:
    def __init__(self, items):
        self._items = items

    class _Scalars:
        def __init__(self, items):
            self._items = items

        def all(self):
            return list(self._items)

    def scalars(self):
        return self._Scalars(self._items)


class FakeDbSession:
    def __init__(self):
        self.added = []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    def add(self, obj):
        self.added.append(obj)


def build_db_location(location_id: str, name: str, lat: float, lon: float) -> Location:
    return Location(
        id=location_id,
        name=name,
        lat=lat,
        lon=lon,
        time_window_start="09:00",
        time_window_end="18:00",
        category="A",
        address=f"{name} address",
    )


def build_pydantic_location(location_id: str, name: str, lat: float, lon: float) -> PydanticLocation:
    return PydanticLocation(
        ID=location_id,
        name=name,
        address=f"{name} address",
        lat=lat,
        lon=lon,
        time_window_start="09:00",
        time_window_end="18:00",
        priority="A",
    )


@pytest.mark.asyncio
async def test_confirm_variant_saves_route_id_and_snapshot_metrics():
    db = FakeDbSession()

    with patch("src.services.optimize.QwenClient"), patch("src.services.optimize.LlamaClient"), patch(
        "src.services.optimize.RoutingService"
    ):
        optimizer = Optimizer(db)

    result = await optimizer.confirm_variant(
        name="Saved route",
        locations_order=["loc-2", "loc-1"],
        total_distance_km=18.4,
        total_time_hours=2.1,
        total_cost_rub=940.0,
        quality_score=88.0,
        model_used="qwen",
        original_location_ids=["loc-1", "loc-2"],
        original_total_distance_km=21.0,
        original_total_time_hours=2.6,
        original_total_cost_rub=1100.0,
    )

    saved_route = next(item for item in db.added if isinstance(item, Route))
    saved_comparison = next(
        item for item in db.added if isinstance(item, OptimizationResult)
    )

    assert result["id"] == saved_route.id
    assert saved_comparison.route_id == saved_route.id
    assert saved_comparison.original_route == ["loc-1", "loc-2"]
    assert saved_comparison.optimized_route == ["loc-2", "loc-1"]
    assert saved_comparison.original_distance_km == 21.0
    assert saved_comparison.original_time_hours == 2.6
    assert saved_comparison.original_cost_rub == 1100.0
    assert saved_comparison.optimized_distance_km == 18.4
    assert saved_comparison.optimized_time_hours == 2.1
    assert saved_comparison.optimized_cost_rub == 940.0
    assert saved_comparison.improvement_percentage == pytest.approx(12.38, abs=0.01)


@pytest.mark.asyncio
async def test_optimize_saves_comparison_snapshot_metrics():
    db = FakeDbSession()

    with patch("src.services.optimize.QwenClient"), patch("src.services.optimize.LlamaClient"), patch(
        "src.services.optimize.RoutingService"
    ), patch("src.services.optimize.get_model_recommendation", return_value={"model": "qwen"}):
        optimizer = Optimizer(db)

    optimizer._calculate_real_metrics = AsyncMock(
        side_effect=[
            {"distance_km": 24.2, "time_minutes": 180.0, "cost_rub": 1400.0},
            {"distance_km": 18.1, "time_minutes": 132.0, "cost_rub": 1010.0},
        ]
    )
    optimizer._generate_with_fallback = AsyncMock(
        return_value=PydanticRoute(
            ID="ai-route",
            name="Optimized route",
            locations=[
                build_pydantic_location("loc-2", "Store 2", 54.19, 45.17),
                build_pydantic_location("loc-1", "Store 1", 54.18, 45.18),
            ],
            total_distance_km=0.0,
            total_time_hours=0.0,
            total_cost_rub=0.0,
            model_used="qwen",
            created_at=datetime(2026, 4, 22, 12, 0, 0),
        )
    )

    optimized = await optimizer.optimize(
        [
            build_db_location("loc-1", "Store 1", 54.18, 45.18),
            build_db_location("loc-2", "Store 2", 54.19, 45.17),
        ],
        model="qwen",
    )

    saved_route = next(item for item in db.added if isinstance(item, Route))
    saved_comparison = next(
        item for item in db.added if isinstance(item, OptimizationResult)
    )

    assert optimized.total_distance_km == 18.1
    assert optimized.ID == saved_route.id
    assert getattr(optimized, "comparison_saved", False) is True
    assert saved_comparison.route_id == saved_route.id
    assert saved_comparison.original_distance_km == 24.2
    assert saved_comparison.original_time_hours == 3.0
    assert saved_comparison.original_cost_rub == 1400.0
    assert saved_comparison.optimized_distance_km == 18.1
    assert saved_comparison.optimized_time_hours == 2.2
    assert saved_comparison.optimized_cost_rub == 1010.0


@pytest.mark.asyncio
async def test_get_routes_marks_has_comparison_only_for_complete_latest_snapshot():
    route_with_snapshot = Route(
        id="route-1",
        name="Route 1",
        locations_order=["loc-1"],
        total_distance=10.0,
        total_time=1.0,
        total_cost=100.0,
        model_used="qwen",
    )
    route_without_snapshot = Route(
        id="route-2",
        name="Route 2",
        locations_order=["loc-2"],
        total_distance=14.0,
        total_time=1.5,
        total_cost=150.0,
        model_used="llama",
    )
    complete_snapshot = OptimizationResult(
        route_id="route-1",
        original_route=["loc-1"],
        optimized_route=["loc-1"],
        original_distance_km=12.0,
        original_time_hours=1.3,
        original_cost_rub=120.0,
        optimized_distance_km=10.0,
        optimized_time_hours=1.0,
        optimized_cost_rub=100.0,
        improvement_percentage=16.67,
        model_used="qwen",
    )
    incomplete_snapshot = OptimizationResult(
        route_id="route-2",
        original_route=["loc-2"],
        optimized_route=["loc-2"],
        improvement_percentage=0.0,
        model_used="llama",
    )

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            ScalarValueResult(2),
            ScalarsResult([route_with_snapshot, route_without_snapshot]),
            ScalarsResult([complete_snapshot, incomplete_snapshot]),
        ]
    )

    payload = await get_routes(skip=0, limit=100, session=session)

    assert payload.total == 2
    assert payload.items[0].id == "route-1"
    assert payload.items[0].has_comparison is True
    assert payload.items[1].id == "route-2"
    assert payload.items[1].has_comparison is False


@pytest.mark.asyncio
async def test_get_route_detail_includes_has_comparison_flag():
    route = Route(
        id="route-1",
        name="Detailed route",
        locations_order=["loc-1", "loc-2"],
        total_distance=18.0,
        total_time=2.4,
        total_cost=920.0,
        model_used="qwen",
    )
    route.metrics = [
        Metric(
            id="metric-1",
            route_id="route-1",
            model_name="qwen",
            response_time_ms=800,
            quality_score=91.0,
            cost=0.0,
        )
    ]
    complete_snapshot = OptimizationResult(
        route_id="route-1",
        original_route=["loc-1", "loc-2"],
        optimized_route=["loc-2", "loc-1"],
        original_distance_km=21.0,
        original_time_hours=2.8,
        original_cost_rub=1010.0,
        optimized_distance_km=18.0,
        optimized_time_hours=2.4,
        optimized_cost_rub=920.0,
        improvement_percentage=14.29,
        model_used="qwen",
    )

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            ScalarValueResult(route),
            ScalarsResult(
                [
                    build_db_location("loc-1", "Store 1", 54.18, 45.18),
                    build_db_location("loc-2", "Store 2", 54.19, 45.17),
                ]
            ),
            ScalarsResult([complete_snapshot]),
        ]
    )

    payload = await get_route_detail("route-1", session=session)

    assert payload.id == "route-1"
    assert payload.has_comparison is True
    assert len(payload.locations_data) == 2
    assert len(payload.metrics) == 1


@pytest.mark.asyncio
async def test_get_route_comparison_returns_points_and_metric_deltas():
    route = Route(
        id="route-1",
        name="Route with comparison",
        locations_order=["loc-2", "loc-1", "loc-3"],
        total_distance=18.0,
        total_time=2.4,
        total_cost=920.0,
        model_used="qwen",
    )
    comparison = OptimizationResult(
        route_id="route-1",
        original_route=["loc-1", "loc-2", "loc-3"],
        optimized_route=["loc-2", "loc-1", "loc-3"],
        original_distance_km=21.5,
        original_time_hours=2.8,
        original_cost_rub=1100.0,
        optimized_distance_km=18.0,
        optimized_time_hours=2.4,
        optimized_cost_rub=920.0,
        improvement_percentage=16.28,
        model_used="qwen",
    )

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            ScalarValueResult(route),
            ScalarsResult([comparison]),
            ScalarsResult(
                [
                    build_db_location("loc-1", "Store 1", 54.18, 45.18),
                    build_db_location("loc-2", "Store 2", 54.19, 45.17),
                    build_db_location("loc-3", "Store 3", 54.20, 45.16),
                ]
            ),
        ]
    )

    payload = await get_route_comparison("route-1", session=session)

    assert [point.id for point in payload.original] == ["loc-1", "loc-2", "loc-3"]
    assert [point.id for point in payload.current] == ["loc-2", "loc-1", "loc-3"]
    assert payload.diff.distance_delta_km == -3.5
    assert payload.diff.time_delta_hours == -0.4
    assert payload.diff.cost_delta_rub == -180.0
    assert payload.diff.changed_stops_count == 2


@pytest.mark.asyncio
async def test_get_route_comparison_returns_404_for_legacy_snapshots():
    route = Route(
        id="route-legacy",
        name="Legacy route",
        locations_order=["loc-1"],
        total_distance=10.0,
        total_time=1.0,
        total_cost=100.0,
        model_used="qwen",
    )
    incomplete_snapshot = OptimizationResult(
        route_id="route-legacy",
        original_route=["loc-1"],
        optimized_route=["loc-1"],
        improvement_percentage=0.0,
        model_used="qwen",
    )

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            ScalarValueResult(route),
            ScalarsResult([incomplete_snapshot]),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_route_comparison("route-legacy", session=session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No comparison data for this route"


def test_optimization_result_model_contains_snapshot_columns():
    columns = set(OptimizationResult.__table__.c.keys())

    assert "route_id" in columns
    assert "original_distance_km" in columns
    assert "original_time_hours" in columns
    assert "original_cost_rub" in columns
    assert "optimized_distance_km" in columns
    assert "optimized_time_hours" in columns
    assert "optimized_cost_rub" in columns
