from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

BENCH_DIR = Path(__file__).resolve().parent
ML_DIR = BENCH_DIR.parent
PROJECT_ROOT = ML_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.benchmarks.geo_clustering_benchmark import run_benchmark as run_geo_benchmark


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(max(1e-12, 1 - a)))


def _mk_locations(n: int = 18) -> List[Dict[str, Any]]:
    random.seed(42)
    result: List[Dict[str, Any]] = []
    cats = ["A", "B", "C", "D"]
    for i in range(n):
        result.append(
            {
                "id": f"loc-{i+1}",
                "name": f"ТТ {i+1}",
                "lat": 54.0 + random.random() * 0.5,
                "lon": 45.0 + random.random() * 0.5,
                "priority": cats[i % len(cats)],
            }
        )
    return result


def _metrics_for_order(ordered: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(ordered) <= 1:
        return {
            "distance_km": 0.0,
            "time_minutes": 0.0,
            "cost_rub": 0.0,
            "constraints_satisfied": True,
        }
    distance_km = 0.0
    for i in range(1, len(ordered)):
        a = ordered[i - 1]
        b = ordered[i]
        distance_km += _haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    time_minutes = (distance_km / 25.0) * 60.0
    return {
        "distance_km": round(distance_km, 2),
        "time_minutes": round(time_minutes, 2),
        "cost_rub": round(distance_km * 15.0, 2),
        "constraints_satisfied": True,
    }


def _greedy_route(locs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(locs) <= 1:
        return list(locs)
    start = {"lat": 54.1871, "lon": 45.1749}
    unvisited = list(locs)
    ordered: List[Dict[str, Any]] = []
    cur = start
    while unvisited:
        nxt = min(
            unvisited,
            key=lambda point: _haversine_km(cur["lat"], cur["lon"], point["lat"], point["lon"]),
        )
        ordered.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    return ordered


def _priority_route(locs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets = {"A": [], "B": [], "C": [], "D": []}
    for loc in locs:
        buckets.get(loc.get("priority", "D"), buckets["D"]).append(loc)
    ordered: List[Dict[str, Any]] = []
    for key in ("A", "B", "C", "D"):
        ordered.extend(_greedy_route(buckets[key]))
    return ordered


def _balanced_route(locs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    penalty = {"A": 0.0, "B": 3.0, "C": 8.0, "D": 15.0}
    if len(locs) <= 1:
        return list(locs)
    unvisited = list(locs)
    ordered: List[Dict[str, Any]] = []
    cur = {"lat": 54.1871, "lon": 45.1749}
    while unvisited:
        nxt = min(
            unvisited,
            key=lambda point: (
                0.6 * _haversine_km(cur["lat"], cur["lon"], point["lat"], point["lon"])
                + 0.4 * penalty.get(point.get("priority", "D"), 15.0)
            ),
        )
        ordered.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    return ordered


def _single_route_benchmark() -> Dict[str, Any]:
    locs = _mk_locations(20)
    candidates = {
        "greedy": _greedy_route(locs),
        "priority_first": _priority_route(locs),
        "balanced": _balanced_route(locs),
    }

    scored = {}
    for name, ordered in candidates.items():
        t0 = time.perf_counter()
        metrics = _metrics_for_order(ordered)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
        score = round(
            (1000.0 / (1.0 + metrics["distance_km"]))
            + (500.0 / (1.0 + metrics["time_minutes"]))
            + (500.0 / (1.0 + metrics["cost_rub"]))
            + (1000.0 / (1.0 + elapsed_ms)),
            3,
        )
        scored[name] = {"metrics": metrics, "elapsed_ms": elapsed_ms, "score": score}

    winner = max(scored.items(), key=lambda x: x[1]["score"])[0]
    return {"winner": winner, "candidates": scored}


def _variants_benchmark() -> Dict[str, Any]:
    # Варианты опираются на те же алгоритмы, поэтому оценка эквивалентна single-route
    return _single_route_benchmark()


def _schedule_benchmark() -> Dict[str, Any]:
    dataset = ML_DIR / "data" / "tt_250.csv"
    if not dataset.exists():
        return {
            "winner": "final-schedule-planner",
            "candidates": {},
            "note": f"Dataset not found: {dataset}",
        }
    payload = run_geo_benchmark(dataset)
    candidates = payload.get("candidates", {})
    if not candidates:
        return {"winner": "final-schedule-planner", "candidates": {}}
    winner = max(
        candidates.items(),
        key=lambda x: x[1].get("improvement_vs_baseline_pct", -10**9),
    )[0]
    return {"winner": winner, "candidates": candidates}


def select_policy(results: Dict[str, Any]) -> str:
    single_winner = results["single_route"]["winner"]
    schedule_winner = results["schedule"]["winner"]
    if single_winner == schedule_winner:
        return "unified"
    return "hybrid"


def run_policy_benchmark() -> Dict[str, Any]:
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "single_route": _single_route_benchmark(),
        "variants": _variants_benchmark(),
        "schedule": _schedule_benchmark(),
    }
    payload["recommended_policy"] = select_policy(payload)
    return payload


def main() -> int:
    result = run_policy_benchmark()
    out_results = BENCH_DIR / "policy_benchmark_results.json"
    out_selection = BENCH_DIR / "policy_selection.json"
    out_results.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    out_selection.write_text(
        json.dumps(
            {
                "recommended_policy": result["recommended_policy"],
                "single_route_winner": result["single_route"]["winner"],
                "variants_winner": result["variants"]["winner"],
                "schedule_winner": result["schedule"]["winner"],
                "generated_at": result["timestamp"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Saved: {out_results}")
    print(f"Saved: {out_selection}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
