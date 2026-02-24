"""
Логика выбора модели для оптимизации маршрута (ML-6).

Схема:
- Primary: всегда qwen (QwenClient);
- Fallback: llama (LlamaClient), если qwen недоступен
или результат не устраивает.

Этот модуль только объявляет primary (qwen). Фактический переход на llama
происходит в клиентах/роутах при ошибках или деградации качества.
"""

from typing import Optional

# Идентификаторы моделей, совпадают с роутами/клиентами: /qwen, /llama
MODEL_QWEN = "qwen"
MODEL_LLAMA = "llama"

# Пороги и режимы оставлены на будущее (если логика станет сложнее)
THRESHOLD_SMALL = 20
THRESHOLD_LARGE = 100

CONSTRAINT_URGENT = "urgent"
CONSTRAINT_QUALITY = "quality"
CONSTRAINT_RELIABILITY = "reliability"


def select_best_model(
    num_locations: int,
    time_constraint: Optional[str] = None,
) -> str:
    """
    Возвращает primary-модель для оптимизации маршрута.

    Текущая стратегия:
    - всегда используем qwen как основную модель;
    - fallback на llama реализован на уровне клиентов/роутов
      (при ошибке или неудовлетворительном результате qwen).

    Аргументы оставлены на будущее (для возможного усложнения логики).
    """
    return MODEL_QWEN


def get_model_recommendation(
    num_locations: int,
    time_constraint: Optional[str] = None,
) -> dict:
    """
    То же что select_best_model, но возвращает структуру для API:
    модель + текст рекомендации.

    Удобно класть в опциональное поле ответа (например recommendation).
    """
    model = select_best_model(num_locations, time_constraint)
    reason = _reason_text(num_locations, time_constraint, model)
    return {"model": model, "reason": reason}


def _reason_text(
    num_locations: int, time_constraint: Optional[str],
        model: str) -> str:
    """Краткое обоснование выбора для логов и API."""
    if model == MODEL_LLAMA:
        return "fallback — Llama после отказа/низкого качества Qwen"
    return "primary — Qwen; fallback при сбоях/деградации качества — Llama"
