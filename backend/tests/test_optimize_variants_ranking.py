import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.modules.setdefault("asyncpg", MagicMock())

from src.services.optimize import Optimizer


class _DbLocation:
    def __init__(self, idx: int):
        self.id = f"loc-{idx}"
        self.name = f"Store {idx}"
        self.address = f"Address {idx}"
        self.lat = 54.18 + idx * 0.01
        self.lon = 45.17 + idx * 0.01
        self.time_window_start = "09:00"
        self.time_window_end = "18:00"
        self.category = "A"


@pytest.mark.asyncio
async def test_generate_variants_returns_ranked_alternatives():
    with patch("src.services.optimize.QwenClient"), patch("src.services.optimize.LlamaClient"), patch(
        "src.services.optimize.RoutingService"
    ):
        optimizer = Optimizer(db_session=MagicMock())

    optimizer._calculate_real_metrics = AsyncMock(
        side_effect=[
            {"distance_km": 100.0, "time_minutes": 240.0, "cost_rub": 1500.0},  # baseline
            {"distance_km": 72.0, "time_minutes": 170.0, "cost_rub": 1000.0},   # greedy
            {"distance_km": 84.0, "time_minutes": 190.0, "cost_rub": 1180.0},   # priority
            {"distance_km": 76.0, "time_minutes": 175.0, "cost_rub": 1060.0},   # balanced
        ]
    )

    db_locations = [_DbLocation(1), _DbLocation(2), _DbLocation(3)]
    response = await optimizer.generate_variants(
        db_locations=db_locations,
        model="llama",
        policy_mode="algorithm_primary",
        max_alternatives=3,
        transport_mode="car",
    )

    assert len(response.variants) == 3
    assert response.variants[0].rank == 1
    assert response.variants[0].is_recommended is True
    assert response.variants[1].rank == 2
    assert response.variants[2].rank == 3
    assert response.variants[0].selection_score >= response.variants[1].selection_score


def test_resolve_policy_uses_requested_fallback_model():
    from src.services.routing_policy import resolve_routing_policy

    policy = resolve_routing_policy("compare_mode", "qwen")
    assert policy.llm_fallback_model == "qwen"
    assert policy.requested_fallback_model == "qwen"
