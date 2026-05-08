from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.models.qwen_client import QwenClient
from src.models.schemas import Location, Route
from src.services.model_selector import get_model_recommendation
from src.services.routing_observability import (
    track_algorithm_run,
    track_llm_fallback_attempt,
    track_llm_fallback_failure,
    track_llm_fallback_success,
)
from src.services.routing_policy import resolve_routing_policy
from src.services.simple_route_algorithms import nearest_neighbour_route, normalize_constraints


router = APIRouter(prefix="/qwen", tags=["Qwen LLM"])


@router.post("/optimize", response_model=Route)
async def optimize_route(
    locations: List[Location],
    constraints: Dict | None = None,
    policy_mode: str = "algorithm_primary",
    include_recommendation: bool = Query(False, description="Добавить в ответ"
                                         "recommendation (model + reason)"),
    time_constraint: Optional[str] = Query(None,
                                           description="urgent |"
                                           "quality | reliability"),
):
    normalized_constraints = normalize_constraints(constraints)
    policy = resolve_routing_policy(policy_mode, "qwen")
    track_algorithm_run(policy.mode)

    use_llm_now = policy.llm_fallback_only or (
        policy.compare_mode and bool(normalized_constraints.get("force_llm"))
    )

    if not use_llm_now:
        route = nearest_neighbour_route(locations, model_used="algorithm-nn")
        if include_recommendation:
            rec = get_model_recommendation(len(locations), time_constraint)
            route = route.model_copy(update={"recommendation": rec})
        return route

    client = QwenClient()
    try:
        track_llm_fallback_attempt("qwen")
        route = await client.generate_route(locations, constraints)
        track_llm_fallback_success("qwen")
        if include_recommendation:
            rec = get_model_recommendation(len(locations), time_constraint)
            route = route.model_copy(update={"recommendation": rec})
        return route
    except Exception as e:
        track_llm_fallback_failure("qwen", "direct_qwen_failed")
        if not policy.llm_fallback_enabled:
            raise HTTPException(status_code=500, detail=str(e))
        # Последний защитный контур: алгоритм вместо LLM.
        fallback_route = nearest_neighbour_route(locations, model_used="algorithm-nn-fallback")
        if include_recommendation:
            rec = get_model_recommendation(len(locations), time_constraint)
            fallback_route = fallback_route.model_copy(update={"recommendation": rec})
        return fallback_route
