import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

router = APIRouter(tags=["Benchmark"])

benchmark_status: Dict[str, str] = {}

backend_dir = Path(os.getcwd())
project_root = backend_dir.parent

BENCH_DIR = project_root / "ml" / "benchmarks"
script_path = BENCH_DIR / "llm_benchmark.py"
LOG_FILE = BENCH_DIR / "results_log.json"
RESULTS_FILE = BENCH_DIR / "results.json"


def _run_benchmark_process(
    task_id: str,
    iterations: int,
    use_mock: bool,
    use_backend: bool,
):
    benchmark_status[task_id] = "running"

    if not script_path.exists():
        benchmark_status[task_id] = (
            f"failed: script not found at {script_path}"
        )
        return

    cmd = [
        sys.executable,
        str(script_path),
        "--iterations",
        str(iterations),
    ]

    if use_mock:
        cmd.append("--mock")
    if use_backend:
        cmd.append("--backend")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            benchmark_status[task_id] = "completed"
        else:
            error_detail = (
                result.stderr.strip()
                or f"Exit code {result.returncode}"
            )
            benchmark_status[task_id] = (
                f"failed: {error_detail[:200]}"
            )

    except Exception as exc:
        benchmark_status[task_id] = f"error: {exc}"


@router.post("/api/v1/benchmark/run")
async def start_benchmark(
    background_tasks: BackgroundTasks,
    iterations: int = Query(5, ge=1, le=20),
    use_mock: bool = Query(
        True,
        description="Использовать заглушки вместо моделей",
    ),
    use_backend: bool = Query(
        False,
        description="Использовать клиенты GigaChat/T-Pro",
    ),
):
    task_id = f"bench_{int(time.time())}"

    background_tasks.add_task(
        _run_benchmark_process,
        task_id,
        iterations,
        use_mock,
        use_backend,
    )

    return {
        "status": "started",
        "task_id": task_id,
        "mode": (
            "mock"
            if use_mock
            else ("backend" if use_backend else "hf_models")
        ),
    }


@router.get("/api/v1/benchmark/status")
async def get_benchmark_status():
    return benchmark_status


@router.get("/api/v1/benchmark/compare")
async def compare_models():
    """
    Возвращает сравнение моделей в формате, совместимом с фронтендом:
    {models: [{name, avg_response_time_ms, avg_quality_score,
               total_cost_rub, success_rate, usage_count}],
     recommendations: []}
    """
    # Пробуем загрузить результаты последнего бенчмарка
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)

            models_list = []
            for model_id, model_data in results.get("models", {}).items():
                metrics = model_data.get("metrics", {})
                models_list.append({
                    "name": model_id,
                    "avg_response_time_ms": metrics.get(
                        "response_time_ms", 0.0
                    ),
                    "avg_quality_score": metrics.get("quality_score", 0.0),
                    "total_cost_rub": metrics.get("cost_rub", 0.0),
                    "success_rate": metrics.get("success_rate", 0.0),
                    "usage_count": metrics.get("total_tests", 0),
                })

            return {
                "models": models_list,
                "recommendations": [
                    {
                        "scenario": "general",
                        "recommended_model": "qwen",
                        "reason": (
                            "Primary model; Llama as fallback"
                        ),
                    }
                ],
            }
        except (json.JSONDecodeError, KeyError):
            pass

    # Нет данных — возвращаем пустую структуру нужного формата
    return {
        "models": [],
        "recommendations": [],
    }


@router.get("/api/v1/benchmark/latest")
async def get_latest_result():
    if not RESULTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Последний результат не найден",
        )

    with open(RESULTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)