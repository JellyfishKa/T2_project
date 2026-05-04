from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

BENCH_DIR = Path(__file__).resolve().parent
ML_DIR = BENCH_DIR.parent
PROJECT_ROOT = ML_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.geo_clustering import (
    GeoClusteringResult,
    dbscan_then_pack_clusters,
    greedy_geo_assignment,
    kmeans_geo_then_balance_by_category,
)
from schedule_planner import DayRoute, SchedulePlanner, TradePoint, VisitTask, route_distance_km


DATA_DIR = ML_DIR / "data"


def load_trade_points_csv(path: Path) -> List[TradePoint]:
    tps: List[TradePoint] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tps.append(
                TradePoint(
                    id=row["id"],
                    category=row["category"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                )
            )
    return tps


def _geo_clusterer_from_result(
    rep_ids: Sequence[str],
    result: GeoClusteringResult,
) -> Dict[str, List[VisitTask]]:
    # маппинг "безопасный": если result вернул не те ключи, нормализуем
    out: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}
    for r, tasks in result.assignments.items():
        if r in out:
            out[r].extend(tasks)
    return out


def _planner_geo_clusterer_factory(rep_ids: Sequence[str], algo: str):
    rep_ids = list(rep_ids)

    def clusterer(tasks: Sequence[VisitTask], k: int) -> Dict[str, List[VisitTask]]:
        assert k == len(rep_ids)
        if algo == "kmeans+balance":
            res = kmeans_geo_then_balance_by_category(tasks, rep_ids)
        elif algo == "dbscan+pack":
            res = dbscan_then_pack_clusters(tasks, rep_ids)
        elif algo == "greedy-geo":
            res = greedy_geo_assignment(tasks, rep_ids)
        elif algo == "final-schedule-planner":
            # путь интеграции (T2-6): тот же подход, но без sklearn (используется в backend)
            from schedule_planner import SchedulePlanner

            tmp = SchedulePlanner(rep_ids=rep_ids, geo_clusterer=SchedulePlanner.make_default_geo_clusterer(rep_ids))
            return tmp.geo_clusterer(tasks, k)  # type: ignore[misc]
        else:
            raise ValueError(f"Unknown algo: {algo}")
        return _geo_clusterer_from_result(rep_ids, res)

    return clusterer


def _distance_stats(routes: Sequence[DayRoute]) -> Dict[str, float]:
    per_day = [route_distance_km(r.visits) for r in routes]
    if not per_day:
        return {"sum_km": 0.0, "avg_km": 0.0, "p95_km": 0.0}
    per_day_sorted = sorted(per_day)
    p95 = per_day_sorted[int(0.95 * (len(per_day_sorted) - 1))]
    return {
        "sum_km": round(sum(per_day), 2),
        "avg_km": round(sum(per_day) / len(per_day), 2),
        "p95_km": round(p95, 2),
    }


def _load_balance(routes: Sequence[DayRoute], rep_ids: Sequence[str]) -> Dict[str, int]:
    counts = {r: 0 for r in rep_ids}
    for r in routes:
        counts[r.rep_id] += len(r.visits)
    return counts


def _balance_score(load: Dict[str, int]) -> float:
    # 0..1: 1 = идеально ровно
    vals = list(load.values())
    if not vals:
        return 1.0
    mx, mn = max(vals), min(vals)
    if mx == 0:
        return 1.0
    return round(1.0 - ((mx - mn) / mx), 4)


def run_benchmark(
    csv_path: Path,
    rep_ids: Sequence[str] = ("tp-1", "tp-2", "tp-3", "tp-4", "tp-5"),
    month: Tuple[int, int, int] = (2026, 5, 1),
    max_visits_per_day: int = 12,
) -> Dict:
    tps = load_trade_points_csv(csv_path)
    rep_ids = list(rep_ids)

    planner_baseline = SchedulePlanner(rep_ids=rep_ids, max_visits_per_day=max_visits_per_day)
    month_date = time.strptime(f"{month[0]}-{month[1]:02d}-{month[2]:02d}", "%Y-%m-%d")
    from datetime import date

    month_d = date(month_date.tm_year, month_date.tm_mon, month_date.tm_mday)

    t0 = time.perf_counter()
    baseline_routes = planner_baseline.plan_month(tps, month_d, use_geo=False)
    baseline_ms = (time.perf_counter() - t0) * 1000.0

    baseline_dist = _distance_stats(baseline_routes)
    baseline_load = _load_balance(baseline_routes, rep_ids)

    results: Dict[str, Dict] = {}

    for algo in ("kmeans+balance", "dbscan+pack", "greedy-geo", "final-schedule-planner"):
        clusterer = _planner_geo_clusterer_factory(rep_ids, algo)
        planner = SchedulePlanner(
            rep_ids=rep_ids,
            max_visits_per_day=max_visits_per_day,
            geo_clusterer=clusterer,
        )
        t1 = time.perf_counter()
        routes = planner.plan_month(tps, month_d, use_geo=True)
        elapsed_ms = (time.perf_counter() - t1) * 1000.0

        dist = _distance_stats(routes)
        load = _load_balance(routes, rep_ids)

        improvement_pct = 0.0
        if baseline_dist["sum_km"] > 0:
            improvement_pct = round(
                ((baseline_dist["sum_km"] - dist["sum_km"]) / baseline_dist["sum_km"]) * 100.0,
                2,
            )

        results[algo] = {
            "elapsed_ms": round(elapsed_ms, 2),
            "distance": dist,
            "load": load,
            "balance_score": _balance_score(load),
            "improvement_vs_baseline_pct": improvement_pct,
        }

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset": str(csv_path),
        "trade_points": len(tps),
        "reps": rep_ids,
        "baseline": {
            "algo": "category-only",
            "elapsed_ms": round(baseline_ms, 2),
            "distance": baseline_dist,
            "load": baseline_load,
            "balance_score": _balance_score(baseline_load),
        },
        "candidates": results,
    }
    return payload


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / "tt_250.csv"
    if not csv_path.exists():
        raise SystemExit(
            f"Dataset not found: {csv_path}. Create it (250 TT) before running benchmark."
        )

    payload = run_benchmark(csv_path)
    out_json = BENCH_DIR / "geo_clustering_results.json"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

