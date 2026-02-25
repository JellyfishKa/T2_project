"""
Оценка качества оптимизации маршрута (ML-4).

Функция evaluate_route_quality сравнивает исходный и оптимизированный маршруты
по метрикам: снижение расстояния, времени, стоимости и соблюдение ограничений.
Результат — взвешенная оценка 0–100. Модель-агностик: подходит для результатов
любой из трёх моделей (GigaChat, Cotype, T-Pro).
"""

from typing import Any, Dict

# Веса метрик в итоговой оценке (сумма = 1.0)
WEIGHT_DISTANCE = 0.40
WEIGHT_TIME = 0.30
WEIGHT_COST = 0.20
WEIGHT_CONSTRAINTS = 0.10

# Ожидаемые ключи в словаре маршрута (original / optimized)
KEY_DISTANCE_KM = "distance_km"
KEY_TIME_MINUTES = "time_minutes"
KEY_COST_RUB = "cost_rub"
KEY_CONSTRAINTS_SATISFIED = "constraints_satisfied"


def _reduction_pct(original: float, optimized: float) -> float:
    """Процент снижения: (original - optimized) / original * 100.
    При original <= 0 возвращаем 0."""
    if original is None or original <= 0:
        return 0.0
    opt = optimized if optimized is not None else original
    diff = original - opt
    return (diff / original) * 100.0


def _component_score(reduction_pct: float) -> float:
    """Оценка компоненты по проценту снижения: 0–100,
    отрицательное снижение даёт 0."""
    return max(0.0, min(100.0, reduction_pct))


def get_route_quality_metrics(
    original: Dict[str, Any], optimized: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Вычисляет метрики качества оптимизации без итоговой оценки.

    Ожидаемые ключи в original и optimized:
    - distance_km (float): расстояние, км
    - time_minutes (float): время, мин
    - cost_rub (float): стоимость, руб
    - constraints_satisfied (bool): соблюдены ли ограничения

    Returns:
        Словарь: distance_reduction_pct,
        time_reduction_pct, cost_reduction_pct,
        constraints_satisfied, distance_score,
        time_score, cost_score, constraints_score.
    """
    o_d = original.get(KEY_DISTANCE_KM) or 0.0
    o_t = original.get(KEY_TIME_MINUTES) or 0.0
    o_c = original.get(KEY_COST_RUB) or 0.0
    opt_d = (optimized.get(KEY_DISTANCE_KM)
             if KEY_DISTANCE_KM in optimized else o_d)
    opt_t = (optimized.get(KEY_TIME_MINUTES)
             if KEY_TIME_MINUTES in optimized else o_t)
    opt_c = optimized.get(KEY_COST_RUB) if KEY_COST_RUB in optimized else o_c
    if opt_d is None:
        opt_d = o_d
    if opt_t is None:
        opt_t = o_t
    if opt_c is None:
        opt_c = o_c

    dist_red = _reduction_pct(o_d, opt_d)
    time_red = _reduction_pct(o_t, opt_t)
    cost_red = _reduction_pct(o_c, opt_c)
    const_ok = bool(optimized.get(KEY_CONSTRAINTS_SATISFIED, False))

    return {
        "distance_reduction_pct": round(dist_red, 2),
        "time_reduction_pct": round(time_red, 2),
        "cost_reduction_pct": round(cost_red, 2),
        "constraints_satisfied": const_ok,
        "distance_score": _component_score(dist_red),
        "time_score": _component_score(time_red),
        "cost_score": _component_score(cost_red),
        "constraints_score": 100.0 if const_ok else 0.0,
    }


def evaluate_route_quality(original: Dict[str, Any],
                           optimized: Dict[str, Any]) -> float:
    """
    Оценка качества оптимизации маршрута: 0–100.

    Взвешенное среднее:
    - 40% — снижение расстояния (%);
    - 30% — снижение времени (%);
    - 20% — снижение стоимости (%);
    - 10% — соблюдение ограничений (да = 100, нет = 0).

    Подходит для результатов любой из двух моделей (Qwen, Llama):
    на вход ожидаются словари с полями distance_km, time_minutes, cost_rub,
    constraints_satisfied.

    Args:
        original: исходный маршрут (distance_km, time_minutes,
        cost_rub, constraints_satisfied).
        optimized: оптимизированный маршрут (те же поля).

    Returns:
        Оценка 0–100.
    """
    m = get_route_quality_metrics(original, optimized)
    total = (
        WEIGHT_DISTANCE * m["distance_score"]
        + WEIGHT_TIME * m["time_score"]
        + WEIGHT_COST * m["cost_score"]
        + WEIGHT_CONSTRAINTS * m["constraints_score"]
    )
    return round(max(0.0, min(100.0, total)), 2)
