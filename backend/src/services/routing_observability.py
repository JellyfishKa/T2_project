from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Dict

_LOCK = Lock()
_COUNTERS = Counter()


def _inc(metric: str, value: int = 1) -> None:
    with _LOCK:
        _COUNTERS[metric] += value


def track_algorithm_run(mode: str) -> None:
    _inc("algorithm_runs_total")
    _inc(f"algorithm_runs_by_mode.{mode}")


def track_llm_fallback_attempt(model: str) -> None:
    _inc("llm_fallback_attempts_total")
    _inc(f"llm_fallback_attempts_by_model.{model}")


def track_llm_fallback_success(model: str) -> None:
    _inc("llm_fallback_success_total")
    _inc(f"llm_fallback_success_by_model.{model}")


def track_llm_fallback_failure(model: str, reason: str) -> None:
    _inc("llm_fallback_failure_total")
    _inc(f"llm_fallback_failure_by_model.{model}")
    _inc(f"llm_fallback_failure_reason.{reason}")


def get_routing_observability_snapshot() -> Dict[str, int]:
    with _LOCK:
        return dict(_COUNTERS)
