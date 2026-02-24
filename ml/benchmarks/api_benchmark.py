#!/usr/bin/env python3
"""
API Benchmark for T2 Route Optimization.

Tests route optimization endpoints with real Mordovia coordinates across
6 scenarios of increasing complexity. Measures response time, success rate,
JSON validation, and route plausibility.

Usage:
    python api_benchmark.py --url http://localhost:8000/api/v1 --models qwen llama --iterations 3 --html
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)


# --- Mordovia Test Data (real coordinates) ---

MORDOVIA_DISTRICTS = {
    "saransk": {"lat": 54.1838, "lon": 45.1749, "name": "Saransk"},
    "ruzaevka": {"lat": 54.0597, "lon": 44.9506, "name": "Ruzaevka"},
    "kovylkino": {"lat": 54.0404, "lon": 43.9192, "name": "Kovylkino"},
    "komsomolsky": {"lat": 54.0000, "lon": 45.3833, "name": "Komsomolsky"},
    "chamzinka": {"lat": 54.4000, "lon": 45.3333, "name": "Chamzinka"},
    "ardatov": {"lat": 54.8500, "lon": 46.2333, "name": "Ardatov"},
    "bolshie_berezniki": {"lat": 54.3667, "lon": 45.9500, "name": "Bolshie Berezniki"},
    "temnikov": {"lat": 54.6333, "lon": 43.2167, "name": "Temnikov"},
    "zubova_polyana": {"lat": 54.0667, "lon": 42.8333, "name": "Zubova Polyana"},
    "torbeevo": {"lat": 54.0500, "lon": 43.2333, "name": "Torbeevo"},
    "insar": {"lat": 53.8667, "lon": 44.3667, "name": "Insar"},
    "kadoshkino": {"lat": 54.0500, "lon": 44.5167, "name": "Kadoshkino"},
    "krasnoslobodsk": {"lat": 54.4333, "lon": 43.7667, "name": "Krasnoslobodsk"},
    "elniki": {"lat": 54.5667, "lon": 43.5000, "name": "Elniki"},
    "staroe_shaigovo": {"lat": 54.3167, "lon": 44.8167, "name": "Staroe Shaigovo"},
    "lyambir": {"lat": 54.3167, "lon": 45.3667, "name": "Lyambir"},
    "bolshoe_ignatovo": {"lat": 54.7833, "lon": 45.5333, "name": "Bolshoe Ignatovo"},
    "dubenki": {"lat": 54.7333, "lon": 46.5833, "name": "Dubenki"},
    "atyashevo": {"lat": 54.6000, "lon": 46.1833, "name": "Atyashevo"},
    "ichalkovo": {"lat": 54.9667, "lon": 45.3167, "name": "Ichalkovo"},
    "tengushevo": {"lat": 54.3500, "lon": 42.8833, "name": "Tengushevo"},
    "atyuryevo": {"lat": 54.3333, "lon": 42.6833, "name": "Atyuryevo"},
    "kochkurovo": {"lat": 54.0833, "lon": 45.5833, "name": "Kochkurovo"},
}

CATEGORIES = ["A", "B", "C", "D"]
CATEGORY_WEIGHTS = [0.2, 0.3, 0.2, 0.3]  # distribution

DEFAULT_CONSTRAINTS = {
    "team_size": 4,
    "fuel_rate": 7.0,
    "working_hours": {"start": "09:00", "end": "18:00"},
    "category_rules": {
        "A": {"visits_per_month": 3},
        "B": {"visits_per_month": 2},
        "C": {"visits_per_month": 1},
        "D": {"visits_per_quarter": 1},
    },
}


def _make_location(loc_id: str, district_key: str, idx: int, category: str) -> Dict:
    """Generate a trade point near a district center."""
    d = MORDOVIA_DISTRICTS[district_key]
    # Small offset to simulate different points in same district
    lat_offset = (idx % 5) * 0.005 - 0.01
    lon_offset = (idx % 3) * 0.007 - 0.01
    return {
        "ID": loc_id,
        "name": f"TT-{d['name']}-{idx}",
        "address": f"{d['name']}, point {idx}",
        "lat": round(d["lat"] + lat_offset, 6),
        "lon": round(d["lon"] + lon_offset, 6),
        "time_window_start": "09:00",
        "time_window_end": "18:00",
        "priority": category,
    }


def _assign_category(idx: int) -> str:
    """Deterministic category assignment matching distribution."""
    mod = idx % 10
    if mod < 2:
        return "A"
    elif mod < 5:
        return "B"
    elif mod < 7:
        return "C"
    else:
        return "D"


# --- 6 Scenarios ---

SCENARIOS = {
    "small_city": {
        "description": "Within Saransk (3 points)",
        "districts": ["saransk", "saransk", "saransk"],
        "expected_km": (5, 30),
    },
    "small_nearby": {
        "description": "Nearby districts (5 points)",
        "districts": ["saransk", "ruzaevka", "lyambir", "komsomolsky", "kadoshkino"],
        "expected_km": (40, 150),
    },
    "medium_cluster": {
        "description": "Eastern cluster (8 points)",
        "districts": [
            "saransk", "chamzinka", "ardatov", "bolshie_berezniki",
            "atyashevo", "dubenki", "lyambir", "bolshoe_ignatovo",
        ],
        "expected_km": (100, 350),
    },
    "medium_mixed": {
        "description": "Mixed A/B/C/D (10 points)",
        "districts": [
            "saransk", "ruzaevka", "kovylkino", "insar", "kadoshkino",
            "staroe_shaigovo", "krasnoslobodsk", "chamzinka", "lyambir",
            "komsomolsky",
        ],
        "expected_km": (150, 500),
    },
    "large_half": {
        "description": "Half of Mordovia (15 points)",
        "districts": [
            "saransk", "ruzaevka", "kovylkino", "insar", "chamzinka",
            "ardatov", "temnikov", "krasnoslobodsk", "lyambir",
            "bolshoe_ignatovo", "torbeevo", "elniki", "staroe_shaigovo",
            "kadoshkino", "komsomolsky",
        ],
        "expected_km": (300, 800),
    },
    "large_full": {
        "description": "Near-complete Mordovia (20 points)",
        "districts": [
            "saransk", "ruzaevka", "kovylkino", "komsomolsky", "chamzinka",
            "ardatov", "bolshie_berezniki", "temnikov", "zubova_polyana",
            "torbeevo", "insar", "kadoshkino", "krasnoslobodsk", "elniki",
            "staroe_shaigovo", "lyambir", "bolshoe_ignatovo", "dubenki",
            "atyashevo", "ichalkovo",
        ],
        "expected_km": (400, 1000),
    },
}


def build_scenario_data(scenario_name: str) -> Dict:
    """Build request payload for a scenario."""
    scenario = SCENARIOS[scenario_name]
    locations = []
    for i, district_key in enumerate(scenario["districts"]):
        cat = _assign_category(i)
        loc = _make_location(f"pt-{scenario_name}-{i}", district_key, i, cat)
        locations.append(loc)
    return {
        "locations": locations,
        "constraints": DEFAULT_CONSTRAINTS,
    }


# --- Metrics ---

@dataclass
class RunResult:
    scenario: str
    model: str
    iteration: int
    success: bool
    response_time_s: float
    status_code: int = 0
    error: str = ""
    distance_km: float = 0.0
    time_hours: float = 0.0
    cost_rub: float = 0.0
    valid_json: bool = False
    plausible: bool = False
    quality_score: int = 0


def validate_response(data: Dict, scenario_name: str) -> tuple:
    """Validate response JSON structure and plausibility. Returns (valid_json, plausible, quality, issues)."""
    issues = []
    required = ["route_id", "locations_sequence", "total_distance_km",
                 "total_time_hours", "total_cost_rub"]

    # JSON structure
    for key in required:
        if key not in data:
            issues.append(f"missing '{key}'")
    if issues:
        return False, False, 0, issues

    distance = float(data.get("total_distance_km", 0))
    time_h = float(data.get("total_time_hours", 0))
    cost = float(data.get("total_cost_rub", 0))

    exp_min, exp_max = SCENARIOS[scenario_name]["expected_km"]
    n_points = len(SCENARIOS[scenario_name]["districts"])

    score = 100

    # Distance plausibility
    if distance <= 0:
        issues.append("distance <= 0")
        score -= 40
    elif distance < exp_min * 0.3:
        issues.append(f"distance {distance:.1f} far below expected {exp_min}-{exp_max}")
        score -= 25
    elif distance > exp_max * 3:
        issues.append(f"distance {distance:.1f} far above expected {exp_min}-{exp_max}")
        score -= 25
    elif exp_min <= distance <= exp_max:
        pass  # perfect range
    else:
        score -= 10  # close enough

    # Time plausibility
    if time_h <= 0:
        issues.append("time <= 0")
        score -= 20
    elif time_h > 24:
        issues.append(f"time {time_h:.1f}h exceeds 24h")
        score -= 15

    # Cost/distance ratio
    if distance > 0 and cost > 0:
        ratio = cost / distance
        if ratio < 1.0 or ratio > 50.0:
            issues.append(f"cost/km ratio {ratio:.1f} unusual")
            score -= 10

    # Sequence check
    seq = data.get("locations_sequence", [])
    if len(seq) != n_points:
        issues.append(f"sequence has {len(seq)} points, expected {n_points}")
        score -= 15

    plausible = len(issues) == 0
    return True, plausible, max(score, 0), issues


def run_single(
    base_url: str,
    model: str,
    scenario_name: str,
    iteration: int,
) -> RunResult:
    """Run a single benchmark request."""
    payload = build_scenario_data(scenario_name)
    url = f"{base_url.rstrip('/')}/route/optimize"

    params = {"model": model}
    result = RunResult(
        scenario=scenario_name,
        model=model,
        iteration=iteration,
        success=False,
        response_time_s=0.0,
    )

    try:
        start = time.time()
        resp = requests.post(url, json=payload, params=params, timeout=180)
        result.response_time_s = round(time.time() - start, 2)
        result.status_code = resp.status_code

        if resp.status_code != 200:
            result.error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        data = resp.json()
        result.success = True
        result.distance_km = float(data.get("total_distance_km", 0))
        result.time_hours = float(data.get("total_time_hours", 0))
        result.cost_rub = float(data.get("total_cost_rub", 0))

        valid_json, plausible, quality, issues = validate_response(data, scenario_name)
        result.valid_json = valid_json
        result.plausible = plausible
        result.quality_score = quality
        if issues:
            result.error = "; ".join(issues)

    except requests.Timeout:
        result.error = "Request timeout (180s)"
        result.response_time_s = 180.0
    except requests.ConnectionError:
        result.error = "Connection refused"
    except Exception as e:
        result.error = str(e)[:200]

    return result


# --- Output Formatting ---

def print_ascii_table(results: List[RunResult], models: List[str]):
    """Print ASCII comparison table."""
    scenarios = list(SCENARIOS.keys())

    # Aggregate results per model+scenario
    agg = {}
    for r in results:
        key = (r.model, r.scenario)
        if key not in agg:
            agg[key] = []
        agg[key].append(r)

    header = f"{'Scenario':<16} | {'Points':>6}"
    for m in models:
        header += f" | {m:>8} time | {'ok':>3} | {'km':>8} | {'Q':>3}"
    print("\n" + "=" * len(header))
    print("T2 API BENCHMARK RESULTS")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for sc in scenarios:
        n_pts = len(SCENARIOS[sc]["districts"])
        row = f"{sc:<16} | {n_pts:>6}"

        for m in models:
            runs = agg.get((m, sc), [])
            if not runs:
                row += f" | {'N/A':>10}s | {'N/A':>3} | {'N/A':>8} | {'N/A':>3}"
                continue

            avg_time = sum(r.response_time_s for r in runs) / len(runs)
            ok_count = sum(1 for r in runs if r.success)
            ok_rate = f"{ok_count}/{len(runs)}"
            avg_dist = sum(r.distance_km for r in runs if r.success) / max(ok_count, 1)
            avg_q = sum(r.quality_score for r in runs if r.success) // max(ok_count, 1)

            row += f" | {avg_time:>10.1f}s | {ok_rate:>3} | {avg_dist:>7.1f}k | {avg_q:>3}"

        print(row)

    print("-" * len(header))

    # Summary per model
    for m in models:
        m_runs = [r for r in results if r.model == m]
        total = len(m_runs)
        success = sum(1 for r in m_runs if r.success)
        avg_time = sum(r.response_time_s for r in m_runs) / max(total, 1)
        avg_q = sum(r.quality_score for r in m_runs if r.success) / max(success, 1)
        print(f"  {m}: {success}/{total} success, avg {avg_time:.1f}s, avg quality {avg_q:.0f}/100")

    print()


def save_json_results(results: List[RunResult], output_dir: Path):
    """Save results as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"benchmark_{ts}.json"

    data = {
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "scenario": r.scenario,
                "model": r.model,
                "iteration": r.iteration,
                "success": r.success,
                "response_time_s": r.response_time_s,
                "status_code": r.status_code,
                "distance_km": r.distance_km,
                "time_hours": r.time_hours,
                "cost_rub": r.cost_rub,
                "valid_json": r.valid_json,
                "plausible": r.plausible,
                "quality_score": r.quality_score,
                "error": r.error,
            }
            for r in results
        ],
    }

    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON results saved to {filepath}")


def save_html_report(results: List[RunResult], models: List[str], output_dir: Path):
    """Save styled HTML report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"benchmark_{ts}.html"

    scenarios = list(SCENARIOS.keys())
    agg = {}
    for r in results:
        key = (r.model, r.scenario)
        if key not in agg:
            agg[key] = []
        agg[key].append(r)

    rows_html = ""
    for sc in scenarios:
        n_pts = len(SCENARIOS[sc]["districts"])
        desc = SCENARIOS[sc]["description"]
        exp = SCENARIOS[sc]["expected_km"]

        for m in models:
            runs = agg.get((m, sc), [])
            if not runs:
                continue
            ok = sum(1 for r in runs if r.success)
            avg_t = sum(r.response_time_s for r in runs) / len(runs)
            avg_d = sum(r.distance_km for r in runs if r.success) / max(ok, 1)
            avg_q = sum(r.quality_score for r in runs if r.success) // max(ok, 1)
            color = "#d4edda" if avg_q >= 70 else "#fff3cd" if avg_q >= 40 else "#f8d7da"

            rows_html += f"""<tr style="background:{color}">
                <td>{sc}</td><td>{desc}</td><td>{n_pts}</td><td>{m}</td>
                <td>{avg_t:.1f}s</td><td>{ok}/{len(runs)}</td>
                <td>{avg_d:.1f}</td><td>{exp[0]}-{exp[1]}</td>
                <td>{avg_q}/100</td></tr>\n"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>T2 API Benchmark</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
th {{ background: #343a40; color: white; }}
h1 {{ color: #343a40; }}
</style></head>
<body>
<h1>T2 Route Optimization - API Benchmark</h1>
<p>Generated: {datetime.now().isoformat()}</p>
<table>
<tr><th>Scenario</th><th>Description</th><th>Points</th><th>Model</th>
<th>Avg Time</th><th>Success</th><th>Avg km</th><th>Expected km</th>
<th>Quality</th></tr>
{rows_html}
</table>
</body></html>"""

    filepath.write_text(html, encoding="utf-8")
    print(f"HTML report saved to {filepath}")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="T2 API Benchmark")
    parser.add_argument("--url", default="http://localhost:8000/api/v1",
                        help="Base API URL")
    parser.add_argument("--models", nargs="+", default=["qwen", "llama"],
                        help="Models to test")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Iterations per scenario")
    parser.add_argument("--scenarios", nargs="+", default=None,
                        help="Specific scenarios (default: all)")
    parser.add_argument("--html", action="store_true",
                        help="Generate HTML report")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for results")
    args = parser.parse_args()

    scenarios = args.scenarios or list(SCENARIOS.keys())
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent / "results"

    print(f"T2 API Benchmark")
    print(f"URL: {args.url}")
    print(f"Models: {args.models}")
    print(f"Scenarios: {scenarios}")
    print(f"Iterations: {args.iterations}")
    print()

    all_results = []
    total_runs = len(scenarios) * len(args.models) * args.iterations
    current = 0

    for sc in scenarios:
        for model in args.models:
            for it in range(1, args.iterations + 1):
                current += 1
                print(f"  [{current}/{total_runs}] {sc} / {model} / iter {it}...",
                      end=" ", flush=True)

                result = run_single(args.url, model, sc, it)
                all_results.append(result)

                status = "OK" if result.success else "FAIL"
                print(f"{status} ({result.response_time_s}s)"
                      + (f" [{result.error[:60]}]" if result.error else ""))

    print_ascii_table(all_results, args.models)
    save_json_results(all_results, output_dir)

    if args.html:
        save_html_report(all_results, args.models, output_dir)


if __name__ == "__main__":
    main()
