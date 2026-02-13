"""
Генерация отчёта анализа бенчмарков (ML-3) из ml/benchmarks/results.json.

Читает results.json, строит сравнительную таблицу, ASCII-графики и рекомендации
Primary/Fallback/Tertiary для настройки fallback в backend.
Запуск: python ml/benchmarks/generate_analysis_report.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

BENCH_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BENCH_DIR / "results.json"
REPORT_FILE = BENCH_DIR / "analysis_report.md"

# Пример данных, если results.json отсутствует (для шаблона отчёта)
SAMPLE_RESULTS = {
    "timestamp": "2026-02-09T12:00:00",
    "num_iterations": 5,
    "test_data_count": 5,
    "models": {
        "qwen": {
            "model_name": "Qwen/Qwen2-0.5B-Instruct",
            "model_id": "qwen",
            "use_mock": False,
            "metrics": {
                "response_time_ms": 1250.5,
                "quality_score": 72.3,
                "success_rate": 100.0,
                "cost_rub": 0.125,
                "total_tests": 25,
                "successful_tests": 25,
            },
        },
        "llama": {
            "model_name": "meta-llama/Llama-3.2-1B-Instruct",
            "model_id": "llama",
            "use_mock": False,
            "metrics": {
                "response_time_ms": 2100.2,
                "quality_score": 78.5,
                "success_rate": 100.0,
                "cost_rub": 0.105,
                "total_tests": 25,
                "successful_tests": 25,
            },
        },
        "tpro": {
            "model_name": "t-tech/T-pro-it-1.0",
            "model_id": "tpro",
            "use_mock": True,
            "metrics": {
                "response_time_ms": 2.1,
                "quality_score": 74.0,
                "success_rate": 100.0,
                "cost_rub": 0.0,
                "total_tests": 25,
                "successful_tests": 25,
            },
        },
    },
}


def load_results() -> Tuple[Dict[str, Any], bool]:
    """Загружает results.json или возвращает пример данных. Второй элемент — использованы ли реальные данные."""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("models"):
                return data, True
        except (json.JSONDecodeError, IOError):
            pass
    return SAMPLE_RESULTS, False


def _ascii_bar(value: float, max_val: float, width: int = 20, char: str = "█") -> str:
    """Строка ASCII-полоски: value/max_val от 0 до width символов."""
    if max_val <= 0:
        return ""
    ratio = min(1.0, value / max_val)
    n = int(ratio * width)
    return char * n + "░" * (width - n)


def _build_table(data: Dict[str, Any]) -> List[str]:
    lines = []
    lines.append("| Модель | Время ответа, мс | Качество (0–100) | Успешность, % | Стоимость, руб | Режим |")
    lines.append("|--------|-------------------|------------------|---------------|----------------|-------|")
    models = data.get("models", {})
    for model_id, m in models.items():
        metrics = m.get("metrics", {})
        rt = metrics.get("response_time_ms", 0)
        q = metrics.get("quality_score", 0)
        sr = metrics.get("success_rate", 0)
        cost = metrics.get("cost_rub", 0)
        mode = "mock" if m.get("use_mock") else "real"
        name = m.get("model_name", model_id)
        if len(name) > 35:
            name = name[:32] + "..."
        lines.append(f"| {name} | {rt:.1f} | {q:.1f} | {sr:.1f} | {cost:.4f} | {mode} |")
    return lines


def _build_ascii_charts(data: Dict[str, Any]) -> List[str]:
    lines = []
    models = data.get("models", {})
    if not models:
        return lines
    ids = list(models.keys())
    metrics_list = [models[m].get("metrics", {}) for m in ids]
    rt_vals = [m.get("response_time_ms", 0) for m in metrics_list]
    q_vals = [m.get("quality_score", 0) for m in metrics_list]
    cost_vals = [m.get("cost_rub", 0) for m in metrics_list]
    max_rt = max(rt_vals) or 1
    max_q = max(q_vals) or 1
    max_cost = max(cost_vals) or 1
    lines.append("#### Время ответа (мс) — меньше лучше")
    for i, mid in enumerate(ids):
        bar = _ascii_bar(rt_vals[i], max_rt)
        lines.append(f"- **{mid}**: {bar} `{rt_vals[i]:.0f}`")
    lines.append("")
    lines.append("#### Качество (0–100) — больше лучше")
    for i, mid in enumerate(ids):
        bar = _ascii_bar(q_vals[i], max_q)
        lines.append(f"- **{mid}**: {bar} `{q_vals[i]:.1f}`")
    lines.append("")
    lines.append("#### Стоимость (руб) — меньше лучше")
    for i, mid in enumerate(ids):
        bar = _ascii_bar(cost_vals[i], max_cost)
        lines.append(f"- **{mid}**: {bar} `{cost_vals[i]:.4f}`")
    return lines


def _choose_primary_fallback(data: Dict[str, Any]) -> Dict[str, str]:
    """По метрикам выбирает primary, fallback и tertiary. Обоснование: баланс качество/время/успешность."""
    models = data.get("models", {})
    if not models:
        return {"primary": "—", "fallback": "—", "tertiary": "—"}
    scores = []
    for mid, m in models.items():
        metrics = m.get("metrics", {})
        sr = metrics.get("success_rate", 0)
        if sr < 95:
            continue
        q = metrics.get("quality_score", 0)
        rt = metrics.get("response_time_ms", 999999)
        cost = metrics.get("cost_rub", 0)
        use_mock = m.get("use_mock", False)
        # Композитный балл: качество важно, время и стоимость штрафуют; mock не ставим primary
        composite = q - (rt / 5000) - (cost * 50)
        if use_mock:
            composite -= 100
        scores.append((mid, composite, q, rt, cost, use_mock))
    scores.sort(key=lambda x: -x[1])
    ordered = [s[0] for s in scores]
    if len(ordered) >= 3:
        return {"primary": ordered[0], "fallback": ordered[1], "tertiary": ordered[2]}
    if len(ordered) == 2:
        return {"primary": ordered[0], "fallback": ordered[1], "tertiary": ordered[1]}
    if len(ordered) == 1:
        return {"primary": ordered[0], "fallback": ordered[0], "tertiary": ordered[0]}
    return {"primary": "—", "fallback": "—", "tertiary": "—"}


def generate_report() -> None:
    data, from_real = load_results()
    rec = _choose_primary_fallback(data)
    table_lines = _build_table(data)
    chart_lines = _build_ascii_charts(data)
    ts = data.get("timestamp", "")
    n_iter = data.get("num_iterations", 0)
    n_tests = data.get("test_data_count", 0)
    source_note = "" if from_real else "**Примечание:** использованы примерные данные (results.json отсутствовал). Запустите бенчмарк и перегенерируйте отчёт: `python ml/benchmarks/generate_analysis_report.py`."

    md = []
    md.append("# Отчёт по результатам бенчмарков LLM (ML-3)")
    md.append("")
    md.append("Анализ результатов бенчмарков для выбора Primary / Fallback / Tertiary модели и рекомендаций по использованию в backend.")
    md.append("")
    if source_note:
        md.append(source_note)
        md.append("")
    md.append("## Исходные данные")
    md.append("")
    md.append(f"- Файл: `results.json`")
    md.append(f"- Время прогона: {ts}")
    md.append(f"- Итераций на модель: {n_iter}, промптов в итерации: {n_tests}")
    md.append("")
    md.append("## Сравнительная таблица")
    md.append("")
    md.extend(table_lines)
    md.append("")
    md.append("## Графики (ASCII)")
    md.append("")
    md.extend(chart_lines)
    md.append("")
    md.append("## Выводы и рекомендации по моделям")
    md.append("")
    md.append("### Назначение моделей")
    md.append("")
    md.append("| Роль | Модель | Обоснование |")
    md.append("|------|--------|-------------|")
    md.append(f"| **Primary** | **{rec['primary']}** | Основная модель по композитному баллу (качество, время, успешность). Рекомендуется для штатного использования. |")
    md.append(f"| **Fallback** | **{rec['fallback']}** | Резерв при недоступности Primary. Выбрана по следующему лучшему балансу метрик. |")
    md.append(f"| **Tertiary** | **{rec['tertiary']}** | Третья линия при каскадном отказе. |")
    md.append("")
    md.append("### Когда переходить на Fallback")
    md.append("")
    md.append("- **Таймаут:** время ответа Primary превысило порог (рекомендуемый порог: 30–60 с для одного запроса).")
    md.append("- **Ошибка:** ответ с кодом/исключением или success_rate по скользящему окну ниже 95%.")
    md.append("- **Деградация качества:** качество ответов (если измеряется) ниже допустимого порога.")
    md.append("- **Явная недоступность:** сервис Primary не отвечает (connection error, 5xx).")
    md.append("")
    md.append("Переход на Tertiary — при тех же условиях для Fallback (после повторной попытки Fallback).")
    md.append("")
    md.append("## Edge cases и обработка сбоев")
    md.append("")
    md.append("| Ситуация | Рекомендация |")
    md.append("|----------|--------------|")
    md.append("| Модель падает (exception, OOM) | Считать запрос неуспешным, переключиться на Fallback; залогировать ошибку. |")
    md.append("| Модель отвечает очень медленно | Задать таймаут на запрос (например 45 с); при превышении — Fallback. |")
    md.append("| success_rate &lt; 95% по окну запросов | Включить режим «деградация»: направлять часть трафика на Fallback или сменить Primary. |")
    md.append("| Все три модели недоступны | Возвращать 503 с Retry-After; уведомить мониторинг. |")
    md.append("| Mock-режим в результатах | Не использовать mock-модель как Primary в проде; перегенерировать отчёт после реального бенчмарка. |")
    md.append("")
    md.append("## Использование в Backend")
    md.append("")
    md.append("Рекомендуется настроить fallback-цепочку в порядке: **Primary → Fallback → Tertiary**. При конфигурировании использовать идентификаторы моделей из данного отчёта и пороги из раздела «Когда переходить на Fallback» и таблицы edge cases.")
    md.append("")

    REPORT_FILE.write_text("\n".join(md), encoding="utf-8")
    print(f"Отчёт записан: {REPORT_FILE}")


if __name__ == "__main__":
    generate_report()
