from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from src.models.exceptions import (
    LlamaAuthError,
    LlamaRateLimitError,
    LlamaServerError,
    LlamaTimeoutError,
    LlamaValidationError,
)
from src.models.llama_client import LlamaClient
from src.models.schemas import Location, Route
from src.services.routing_observability import (
    track_algorithm_run,
    track_llm_fallback_attempt,
    track_llm_fallback_failure,
    track_llm_fallback_success,
)
from src.services.routing_policy import resolve_routing_policy
from src.services.simple_route_algorithms import nearest_neighbour_route, normalize_constraints


router = APIRouter(prefix="/llama", tags=["Llama LLM"])


@router.post("/optimize", response_model=Route, status_code=status.HTTP_200_OK)
async def optimize_route_llama(locations: List[Location],
                               constraints: Dict | None = None,
                               policy_mode: str = "algorithm_primary"):
    normalized_constraints = normalize_constraints(constraints)
    policy = resolve_routing_policy(policy_mode, "llama")
    track_algorithm_run(policy.mode)

    use_llm_now = policy.llm_fallback_only or (
        policy.compare_mode and bool(normalized_constraints.get("force_llm"))
    )
    if not use_llm_now:
        return nearest_neighbour_route(locations, model_used="algorithm-nn")

    client = LlamaClient()
    try:
        track_llm_fallback_attempt("llama")
        route = await client.generate_route(locations, constraints)
        track_llm_fallback_success("llama")
        return route

    except LlamaValidationError as e:
        track_llm_fallback_failure("llama", "validation_error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации данных: {str(e)}",
        )
    except LlamaAuthError:
        track_llm_fallback_failure("llama", "auth_error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка авторизации Llama API",
        )
    except LlamaRateLimitError:
        track_llm_fallback_failure("llama", "rate_limited")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит запросов к Llama",
        )
    except LlamaTimeoutError:
        track_llm_fallback_failure("llama", "timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Llama API не ответил вовремя (timeout > 20s)",
        )
    except LlamaServerError as e:
        track_llm_fallback_failure("llama", "server_error")
        if policy.llm_fallback_enabled:
            return nearest_neighbour_route(locations, model_used="algorithm-nn-fallback")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка сервера Llama: {str(e)}")
    except Exception as e:
        track_llm_fallback_failure("llama", "unexpected_error")
        if policy.llm_fallback_enabled:
            return nearest_neighbour_route(locations, model_used="algorithm-nn-fallback")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Критическая ошибка Llama: {str(e)}")
