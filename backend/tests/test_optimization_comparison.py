"""
Unit-тесты для сравнения оптимизации моделей (ML-5).

Проверяют compare_models_optimization, метрики маршрутов и генерацию отчёта.
"""

import json
import sys
from pathlib import Path

import pytest

# Путь к ml/benchmarks для импорта optimization_comparison
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_BENCHMARKS = PROJECT_ROOT / "ml" / "benchmarks"
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(ML_BENCHMARKS))


@pytest.fixture
def sample_locations():
    """Минимальный набор локаций для тестов."""
    return [
        {"id": "a", "name": "A", "lat": 55.75, "lon": 37.62},
        {"id": "b", "name": "B", "lat": 55.76, "lon": 37.63},
        {"id": "c", "name": "C", "lat": 55.74, "lon": 37.61},
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path


class TestCompareModelsOptimization:
    """Тесты compare_models_optimization(test_locations)."""

    def test_returns_dict_with_required_keys(self, sample_locations, temp_output_dir):
        """Возвращает словарь с timestamp, locations_count, baseline, models, results_path, report_path."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        assert "timestamp" in result
        assert result["locations_count"] == 3
        assert "baseline" in result
        assert "models" in result
        assert "results_path" in result
        assert "report_path" in result

    def test_baseline_has_metrics(self, sample_locations, temp_output_dir):
        """Базовый маршрут (Greedy) содержит distance_km, time_minutes, cost_rub."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        base = result["baseline"]
        assert "distance_km" in base
        assert "time_minutes" in base
        assert "cost_rub" in base
        assert "quality_score" in base
        assert "response_time_ms" in base

    def test_all_three_models_present(self, sample_locations, temp_output_dir):
        """В результатах есть все три модели: qwen, llama, tpro."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        models = result["models"]
        assert "qwen" in models
        assert "llama" in models
        assert "tpro" in models

    def test_each_model_has_quality_and_response_time(self, sample_locations, temp_output_dir):
        """У каждой модели есть quality_score и response_time_ms."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        for mid, data in result["models"].items():
            assert "quality_score" in data
            assert "response_time_ms" in data
            assert "distance_km" in data
            assert "error" in data

    def test_json_saved(self, sample_locations, temp_output_dir):
        """Результаты сохранены в JSON по results_path."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        path = Path(result["results_path"])
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["locations_count"] == 3
        assert "models" in data and "baseline" in data

    def test_report_generated(self, sample_locations, temp_output_dir):
        """Генерируется optimization_report.md с заголовком и таблицей."""
        import optimization_comparison as oc
        result = oc.compare_models_optimization(
            sample_locations, use_mock=True, output_dir=temp_output_dir
        )
        path = Path(result["report_path"])
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "Benchmark оптимизации" in text or "оптимизации" in text
        assert "Greedy" in text
        assert "Qwen" in text
        assert "|" in text


class TestRouteHelpers:
    """Тесты вспомогательных функций (через модуль)."""

    def test_distance_km_positive(self):
        """_distance_km возвращает положительное число для двух разных точек."""
        import optimization_comparison as oc
        d = oc._distance_km(55.75, 37.62, 55.76, 37.63)
        assert d > 0
        assert d < 100

    def test_distance_km_same_point_zero(self):
        """_distance_km для одной и той же точки даёт 0."""
        import optimization_comparison as oc
        d = oc._distance_km(55.75, 37.62, 55.75, 37.62)
        assert d == 0.0

    def test_parse_order_from_response(self):
        """_parse_order_from_response извлекает порядок индексов из текста."""
        import optimization_comparison as oc
        order = oc._parse_order_from_response("Answer: 0, 2, 1", 3)
        assert order == [0, 2, 1]
        order = oc._parse_order_from_response("1 0 2", 3)
        assert order == [1, 0, 2]
        assert oc._parse_order_from_response("", 3) is None
        assert oc._parse_order_from_response("0, 1", 3) is None  # не все индексы
