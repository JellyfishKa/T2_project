from dataclasses import dataclass
from typing import Optional

from src.config import settings

MODE_ALGORITHM_PRIMARY = "algorithm_primary"
MODE_COMPARE = "compare_mode"
MODE_LLM_FALLBACK_ONLY = "llm_fallback_only"

ALLOWED_MODES = {
    MODE_ALGORITHM_PRIMARY,
    MODE_COMPARE,
    MODE_LLM_FALLBACK_ONLY,
}

LEGACY_MODEL_TO_MODE = {
    "auto": MODE_ALGORITHM_PRIMARY,
    "none": MODE_ALGORITHM_PRIMARY,
    "algorithm": MODE_ALGORITHM_PRIMARY,
    "compare": MODE_COMPARE,
    "qwen": MODE_LLM_FALLBACK_ONLY,
    "llama": MODE_LLM_FALLBACK_ONLY,
}


@dataclass(frozen=True)
class RoutingPolicy:
    mode: str
    requested_fallback_model: str
    llm_fallback_model: str
    llm_fallback_enabled: bool
    quality_floor: float

    @property
    def compare_mode(self) -> bool:
        return self.mode == MODE_COMPARE

    @property
    def llm_fallback_only(self) -> bool:
        return self.mode == MODE_LLM_FALLBACK_ONLY


def _normalize_mode(raw_mode: Optional[str]) -> str:
    if not raw_mode:
        return settings.routing_primary_mode
    cleaned = raw_mode.strip().lower()
    if cleaned in ALLOWED_MODES:
        return cleaned
    return LEGACY_MODEL_TO_MODE.get(cleaned, settings.routing_primary_mode)


def _normalize_model(raw_model: Optional[str]) -> str:
    if not raw_model:
        return settings.routing_llm_fallback_model
    cleaned = raw_model.strip().lower()
    if cleaned in ("qwen", "llama"):
        return cleaned
    return settings.routing_llm_fallback_model


def resolve_routing_policy(
    requested_mode: Optional[str],
    requested_fallback_model: Optional[str],
) -> RoutingPolicy:
    mode = _normalize_mode(requested_mode)
    model = _normalize_model(requested_fallback_model)
    return RoutingPolicy(
        mode=mode,
        requested_fallback_model=model,
        llm_fallback_model=model,
        llm_fallback_enabled=settings.routing_enable_llm_fallback,
        quality_floor=settings.routing_quality_floor,
    )


def should_use_llm_fallback(policy: RoutingPolicy, quality_score: float) -> bool:
    if not policy.llm_fallback_enabled:
        return False
    if policy.llm_fallback_only:
        return True
    return quality_score < policy.quality_floor
