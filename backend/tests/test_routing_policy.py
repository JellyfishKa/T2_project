from unittest.mock import AsyncMock, patch

import pytest

from src.services.routing_policy import (
    MODE_ALGORITHM_PRIMARY,
    MODE_COMPARE,
    MODE_LLM_FALLBACK_ONLY,
    resolve_routing_policy,
    should_use_llm_fallback,
)


def test_resolve_routing_policy_supports_legacy_model_aliases():
    legacy_auto = resolve_routing_policy(None, "auto")
    assert legacy_auto.mode == MODE_ALGORITHM_PRIMARY

    legacy_compare = resolve_routing_policy("compare", "qwen")
    assert legacy_compare.mode == MODE_COMPARE
    assert legacy_compare.requested_fallback_model == "qwen"
    assert legacy_compare.llm_fallback_model == "qwen"

    legacy_llm = resolve_routing_policy("llama", "llama")
    assert legacy_llm.mode == MODE_LLM_FALLBACK_ONLY
    assert legacy_llm.requested_fallback_model == "llama"


def test_should_use_llm_fallback_by_mode_and_quality():
    fallback_only = resolve_routing_policy("llm_fallback_only", "llama")
    assert should_use_llm_fallback(fallback_only, quality_score=99.0) is True

    algo_mode = resolve_routing_policy("algorithm_primary", "llama")
    assert should_use_llm_fallback(algo_mode, quality_score=10.0) is True
    assert should_use_llm_fallback(algo_mode, quality_score=99.0) is False


@pytest.mark.asyncio
async def test_qwen_route_uses_algorithm_path_by_default():
    from src.routes.qwen import optimize_route
    from src.models.schemas import Location

    locations = [
        Location(
            ID="1",
            name="A",
            address="A",
            lat=54.2,
            lon=45.1,
            time_window_start="09:00",
            time_window_end="18:00",
            priority="A",
        ),
        Location(
            ID="2",
            name="B",
            address="B",
            lat=54.3,
            lon=45.2,
            time_window_start="09:00",
            time_window_end="18:00",
            priority="B",
        ),
    ]

    with patch("src.routes.qwen.QwenClient") as qwen_cls:
        qwen_cls.return_value.generate_route = AsyncMock()
        route = await optimize_route(locations, constraints={})
        assert route.model_used.startswith("algorithm")
        qwen_cls.return_value.generate_route.assert_not_called()


@pytest.mark.asyncio
async def test_metrics_response_contains_routing_observability():
    from src.routes.metrics import get_all_metrics

    class _Scalars:
        def all(self):
            return []

    class _ExecResult:
        def scalars(self):
            return _Scalars()

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_ExecResult())

    with patch(
        "src.routes.metrics.get_routing_observability_snapshot",
        return_value={"llm_fallback_attempts_total": 1},
    ):
        payload = await get_all_metrics(db=db, route_id=None)
        assert "metrics" in payload
        assert payload["routing_observability"]["llm_fallback_attempts_total"] == 1
