"""
Unit-тесты для оценки качества оптимизации маршрута (ML-4).
Проверяют evaluate_route_quality и get_route_quality_metrics для контракта,
общего для всех трёх моделей (GigaChat, Cotype, T-Pro).
"""

import pytest
from src.services.quality_evaluator import (
    evaluate_route_quality,
    get_route_quality_metrics,
    WEIGHT_DISTANCE,
    WEIGHT_TIME,
    WEIGHT_COST,
    WEIGHT_CONSTRAINTS,
)


def _route(distance_km: float, time_minutes: float, cost_rub: float, constraints_satisfied: bool):
    """Хелпер: маршрут в формате, ожидаемом evaluator (подходит для любой из 3 моделей)."""
    return {
        "distance_km": distance_km,
        "time_minutes": time_minutes,
        "cost_rub": cost_rub,
        "constraints_satisfied": constraints_satisfied,
    }


class TestEvaluateRouteQuality:
    """Тесты evaluate_route_quality(original, optimized) -> float 0-100."""

    def test_returns_float_in_range(self):
        """Оценка всегда в диапазоне 0–100."""
        original = _route(100.0, 60.0, 50.0, True)
        optimized = _route(80.0, 45.0, 40.0, True)
        score = evaluate_route_quality(original, optimized)
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_perfect_optimization(self):
        """Максимальное улучшение по всем метрикам и ограничения соблюдены -> высокая оценка."""
        original = _route(100.0, 60.0, 100.0, False)
        optimized = _route(0.0, 0.0, 0.0, True)
        score = evaluate_route_quality(original, optimized)
        # 40%*100 + 30%*100 + 20%*100 + 10%*100 = 100
        assert score == 100.0

    def test_no_improvement_zero_constraints(self):
        """Без улучшений и без соблюдения ограничений -> 0."""
        original = _route(50.0, 30.0, 25.0, False)
        optimized = _route(50.0, 30.0, 25.0, False)
        score = evaluate_route_quality(original, optimized)
        assert score == 0.0

    def test_weighted_average(self):
        """Итоговая оценка — взвешенное среднее 40/30/20/10."""
        # 20% снижение расстояния, 0% времени и стоимости, ограничения да
        original = _route(100.0, 10.0, 10.0, False)
        optimized = _route(80.0, 10.0, 10.0, True)
        score = evaluate_route_quality(original, optimized)
        expected = WEIGHT_DISTANCE * 20 + WEIGHT_TIME * 0 + WEIGHT_COST * 0 + WEIGHT_CONSTRAINTS * 100
        assert abs(score - round(expected, 2)) < 0.01

    def test_worse_optimized_caps_at_zero(self):
        """Если оптимизированный маршрут хуже по метрикам — компоненты не уходят в минус."""
        original = _route(50.0, 20.0, 10.0, True)
        optimized = _route(60.0, 25.0, 15.0, False)
        score = evaluate_route_quality(original, optimized)
        assert score == 0.0

    def test_partial_improvement(self):
        """Частичное улучшение: только расстояние и ограничения."""
        original = _route(100.0, 60.0, 50.0, False)
        optimized = _route(70.0, 60.0, 50.0, True)  # -30% distance, constraints ok
        score = evaluate_route_quality(original, optimized)
        expected = WEIGHT_DISTANCE * 30 + WEIGHT_TIME * 0 + WEIGHT_COST * 0 + WEIGHT_CONSTRAINTS * 100
        assert abs(score - round(expected, 2)) < 0.01

    def test_works_with_gigachat_style_output(self):
        """Контракт маршрута совместим с выходом «модели» GigaChat (словарь с полями)."""
        original = _route(10.5, 15.0, 100.0, True)
        optimized = _route(8.0, 12.0, 80.0, True)
        score = evaluate_route_quality(original, optimized)
        assert isinstance(score, float) and 0 <= score <= 100

    def test_works_with_cotype_style_output(self):
        """Контракт маршрута совместим с выходом «модели» Cotype."""
        original = _route(20.0, 30.0, 200.0, False)
        optimized = _route(14.0, 21.0, 140.0, True)
        score = evaluate_route_quality(original, optimized)
        assert isinstance(score, float) and 0 <= score <= 100

    def test_works_with_tpro_style_output(self):
        """Контракт маршрута совместим с выходом «модели» T-Pro."""
        original = _route(5.0, 10.0, 50.0, True)
        optimized = _route(4.0, 8.0, 40.0, True)
        score = evaluate_route_quality(original, optimized)
        assert isinstance(score, float) and 0 <= score <= 100

    def test_missing_keys_use_zero_or_false(self):
        """Отсутствующие ключи обрабатываются: числа как 0, constraints_satisfied как False."""
        original = _route(100.0, 50.0, 25.0, True)
        optimized = {}  # пустой — нет улучшений
        score = evaluate_route_quality(original, optimized)
        assert score == 0.0


class TestGetRouteQualityMetrics:
    """Тесты метрик: снижение %, удовлетворение ограничений."""

    def test_reduction_percentages(self):
        """Снижение расстояния/времени/стоимости в процентах."""
        original = _route(100.0, 60.0, 100.0, True)
        optimized = _route(70.0, 30.0, 50.0, True)
        m = get_route_quality_metrics(original, optimized)
        assert m["distance_reduction_pct"] == 30.0
        assert m["time_reduction_pct"] == 50.0
        assert m["cost_reduction_pct"] == 50.0
        assert m["constraints_satisfied"] is True

    def test_constraints_unsatisfied(self):
        """constraints_satisfied = False даёт constraints_score = 0."""
        original = _route(10.0, 10.0, 10.0, True)
        optimized = _route(5.0, 5.0, 5.0, False)
        m = get_route_quality_metrics(original, optimized)
        assert m["constraints_satisfied"] is False
        assert m["constraints_score"] == 0.0

    def test_constraints_satisfied(self):
        """constraints_satisfied = True даёт constraints_score = 100."""
        original = _route(10.0, 10.0, 10.0, False)
        optimized = _route(10.0, 10.0, 10.0, True)
        m = get_route_quality_metrics(original, optimized)
        assert m["constraints_satisfied"] is True
        assert m["constraints_score"] == 100.0

    def test_zero_original_no_division_error(self):
        """Исходные нули не вызывают деление на ноль."""
        original = _route(0.0, 0.0, 0.0, False)
        optimized = _route(0.0, 0.0, 0.0, True)
        m = get_route_quality_metrics(original, optimized)
        assert m["distance_reduction_pct"] == 0.0
        assert m["time_reduction_pct"] == 0.0
        assert m["cost_reduction_pct"] == 0.0
        assert m["constraints_score"] == 100.0

    def test_component_scores_capped(self):
        """Компонентные оценки в границах 0–100."""
        original = _route(100.0, 100.0, 100.0, True)
        optimized = _route(10.0, 5.0, 1.0, True)
        m = get_route_quality_metrics(original, optimized)
        assert m["distance_score"] == 90.0
        assert m["time_score"] == 95.0
        assert m["cost_score"] == 99.0
        for key in ("distance_score", "time_score", "cost_score", "constraints_score"):
            assert 0 <= m[key] <= 100
