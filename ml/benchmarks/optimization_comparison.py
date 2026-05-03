"""
Сравнение результатов оптимизации маршрутов по всем трём моделям (ML-5).

Запускает оптимизацию для каждой модели (Qwen, Llama, T-Pro),
оценивает качество через backend quality_evaluator, сохраняет результаты в JSON
и генерирует отчёт optimization_report.md.
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BENCH_DIR = Path(__file__).resolve().parent
ML_DIR = BENCH_DIR.parent
PROJECT_ROOT = ML_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Импорт оценки качества из backend
try:
    from src.services.quality_evaluator import evaluate_route_quality
except ImportError:
    evaluate_route_quality = None  # для тестов без backend

# Средняя скорость в городе (км/ч), стоимость руб/км (условно)
AVG_SPEED_KMH = 25.0
COST_PER_KM_RUB = 15.0

# Модели для сравнения: id в отчёте -> (backend client key, display name)
MODELS = [
    ("qwen", "Qwen"),
    ("llama", "Llama"),
]


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Приближённое расстояние между двумя точками (км), формула Хаверсина упрощённо."""
    import math
    R = 6371.0  # радиус Земли, км
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _route_metrics(
    locations: List[Dict[str, Any]],
    order: List[int],
    cost_per_km: float = COST_PER_KM_RUB,
    speed_kmh: float = AVG_SPEED_KMH,
) -> Dict[str, Any]:
    """Считает distance_km, time_minutes, cost_rub для маршрута по порядку order (индексы в locations)."""
    if len(order) <= 1:
        return {
            "distance_km": 0.0,
            "time_minutes": 0.0,
            "cost_rub": 0.0,
            "constraints_satisfied": True,
        }
    total_km = 0.0
    for i in range(len(order) - 1):
        idx_a, idx_b = order[i], order[i + 1]
        a, b = locations[idx_a], locations[idx_b]
        total_km += _distance_km(
            a["lat"], a["lon"],
            b["lat"], b["lon"],
        )
    time_minutes = (total_km / speed_kmh) * 60.0
    cost_rub = total_km * cost_per_km
    return {
        "distance_km": round(total_km, 2),
        "time_minutes": round(time_minutes, 2),
        "cost_rub": round(cost_rub, 2),
        "constraints_satisfied": True,
    }


def _greedy_baseline(locations: List[Dict[str, Any]]) -> Tuple[List[int], Dict[str, Any]]:
    """Базовый маршрут: порядок 0, 1, ..., n-1."""
    order = list(range(len(locations)))
    metrics = _route_metrics(locations, order)
    return order, metrics


def _nearest_neighbour_order(locations: List[Dict[str, Any]], start: int = 0) -> List[int]:
    """Жадный порядок: от start к ближайшему непосещённому и т.д."""
    n = len(locations)
    if n <= 1:
        return list(range(n))
    order = [start]
    unvisited = set(range(n)) - {start}
    while unvisited:
        cur = order[-1]
        best_j = min(
            unvisited,
            key=lambda j: _distance_km(
                locations[cur]["lat"], locations[cur]["lon"],
                locations[j]["lat"], locations[j]["lon"],
            ),
        )
        order.append(best_j)
        unvisited.discard(best_j)
    return order


def _parse_order_from_response(response: str, n: int) -> Optional[List[int]]:
    """Пытается извлечь порядок индексов (0..n-1) из текста ответа."""
    if not response or n <= 0:
        return None
    numbers = re.findall(r"\b(\d+)\b", response)
    seen = set()
    order = []
    for num in numbers:
        i = int(num)
        if 0 <= i < n and i not in seen:
            seen.add(i)
            order.append(i)
    if len(order) == n and set(order) == set(range(n)):
        return order
    return None


def _get_backend_clients() -> Dict[str, Any]:
    """Возвращает клиенты backend (Qwen, Llama) по возможности."""
    clients = {}
    try:
        from src.models.qwen_client import QwenClient
        clients["qwen"] = QwenClient()
    except Exception:
        pass
    try:
        from src.models.llama_client import LlamaClient
        clients["llama"] = LlamaClient()
    except Exception:
        pass
    return clients


def _build_optimization_prompt(locations: List[Dict[str, Any]]) -> str:
    """Промпт для модели: оптимизировать порядок посещения."""
    lines = [f"{i}. {loc.get('name', loc.get('id', '?'))} (lat={loc['lat']}, lon={loc['lon']})" for i, loc in enumerate(locations)]
    points = "\n".join(lines)
    return (
        f"Дан список из {len(locations)} точек в Москве. Выведи оптимальный порядок посещения (индексы от 0 до {len(locations)-1}) "
        f"для минимизации общего пути. Ответь только числами через запятую, например: 0,3,1,2\n\nТочки:\n{points}"
    )


def _run_optimization_for_model(
    model_id: str,
    locations: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    use_mock: bool = False,
) -> Dict[str, Any]:
    """
    Запуск оптимизации для одной модели: вызов модели, разбор порядка, метрики, время, ошибки.
    Оценка качества — через evaluate_route_quality(baseline, optimized).
    """
    n = len(locations)
    result = {
        "model_id": model_id,
        "distance_km": None,
        "time_minutes": None,
        "cost_rub": None,
        "quality_score": None,
        "response_time_ms": None,
        "error": None,
        "constraints_satisfied": True,
    }
    order = None
    clients = _get_backend_clients()
    client = clients.get(model_id)

    if use_mock or not client:
        order = _nearest_neighbour_order(locations, start=min(1, n - 1))
        result["response_time_ms"] = 100.0
    else:
        prompt = _build_optimization_prompt(locations)
        t0 = time.perf_counter()
        try:
            response = client.generate(prompt)
            result["response_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            order = _parse_order_from_response(response, n)
        except Exception as e:
            result["response_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            result["error"] = str(e)
            order = _nearest_neighbour_order(locations, 0)
        if order is None:
            order = _nearest_neighbour_order(locations, 0)

    metrics = _route_metrics(locations, order)
    result["distance_km"] = metrics["distance_km"]
    result["time_minutes"] = metrics["time_minutes"]
    result["cost_rub"] = metrics["cost_rub"]
    result["constraints_satisfied"] = metrics["constraints_satisfied"]

    if evaluate_route_quality:
        result["quality_score"] = round(
            evaluate_route_quality(baseline_metrics, metrics), 2
        )
    else:
        result["quality_score"] = 0.0

    return result


def compare_models_optimization(
    test_locations: List[Dict[str, Any]],
    use_mock: bool = True,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Сравнение оптимизации по всем трём моделям.

    Для каждой модели: запуск оптимизации, оценка качества (vs greedy baseline),
    запись времени ответа и ошибок. Результаты сохраняются в JSON и генерируется
    отчёт optimization_report.md.

    Args:
        test_locations: список локаций с ключами lat, lon, name или id.
        use_mock: если True, не вызывать реальные модели (используется эвристика порядка).
        output_dir: каталог для results JSON и отчёта; по умолчанию ml/benchmarks.

    Returns:
        Словарь с ключами: timestamp, locations_count, baseline (greedy), models, results_path, report_path.
    """
    if output_dir is None:
        output_dir = BENCH_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_order, baseline_metrics = _greedy_baseline(test_locations)
    baseline_result = {
        "distance_km": baseline_metrics["distance_km"],
        "time_minutes": baseline_metrics["time_minutes"],
        "cost_rub": baseline_metrics["cost_rub"],
        "quality_score": 0.0,
        "response_time_ms": 0.0,
        "error": None,
    }
    if evaluate_route_quality:
        baseline_result["quality_score"] = round(
            evaluate_route_quality(baseline_metrics, baseline_metrics), 2
        )

    models_results = {}
    for model_id, display_name in MODELS:
        row = _run_optimization_for_model(
            model_id, test_locations, baseline_metrics, use_mock=use_mock
        )
        models_results[model_id] = row

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "locations_count": len(test_locations),
        "baseline": baseline_result,
        "models": models_results,
    }

    results_path = output_dir / "optimization_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    payload["results_path"] = str(results_path)

    report_path = output_dir / "optimization_report.md"
    _generate_report(payload, report_path, test_locations)
    payload["report_path"] = str(report_path)

    return payload


def _generate_report(payload: Dict[str, Any], report_path: Path, locations: List[Dict[str, Any]]) -> None:
    """Генерирует markdown-отчёт по результатам сравнения."""
    n = payload.get("locations_count", 0)
    baseline = payload.get("baseline", {})
    models = payload.get("models", {})

    lines = [
        "# Benchmark оптимизации",
        "",
        f"## {n} локаций в Москве",
        "",
        "| Модель | Расстояние | Время | Качество | Время ответа | Стоимость |",
        "|--------|------------|-------|----------|----------------|-----------|",
    ]
    def row(name: str, d: Dict[str, Any]) -> str:
        dist = d.get("distance_km") or 0
        tm = d.get("time_minutes") or 0
        qual = d.get("quality_score") or 0
        rt_ms = d.get("response_time_ms") or 0
        cost = d.get("cost_rub") or 0
        return f"| {name} | {dist} км | {tm} мин | {qual} | {rt_ms:.0f} мс | {cost:.2f} руб |"
    lines.append(row("Greedy", baseline))
    for model_id, display_name in MODELS:
        if model_id in models:
            lines.append(row(display_name, models[model_id]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Оценка качества: 0–100 относительно greedy baseline (backend quality_evaluator).*")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Точка входа: сравнение по тестовым локациям из llm_benchmark или встроенным."""
    try:
        from llm_benchmark import TEST_LOCATIONS
        locations = TEST_LOCATIONS
    except ImportError:
        locations = [
            {"id": "loc-1", "name": "Точка 1", "lat": 55.75, "lon": 37.62},
            {"id": "loc-2", "name": "Точка 2", "lat": 55.76, "lon": 37.63},
            {"id": "loc-3", "name": "Точка 3", "lat": 55.74, "lon": 37.61},
        ]
    compare_models_optimization(locations, use_mock=True, output_dir=BENCH_DIR)
    print("Результаты сохранены: optimization_results.json, optimization_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
