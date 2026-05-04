from __future__ import annotations

import csv
from pathlib import Path

from fastapi.testclient import TestClient


def _load_trade_points(n: int = 10):
    path = Path(__file__).resolve().parents[2] / "ml/data/tt_250.csv"
    out = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= n:
                break
            out.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
            )
    return out


def test_generate_optimized_schedule_sync_and_force_conflict():
    # импортируем app напрямую
    try:
        from main import app  # when tests run with cwd=backend/
    except Exception:
        from backend.main import app  # fallback when repo root is on sys.path

    client = TestClient(app)
    payload = {
        "month": "2026-05-01",
        "reps": ["tp-1", "tp-2", "tp-3"],
        "trade_points": _load_trade_points(15),
        "force": False,
        "async_mode": False,
        "max_visits_per_day": 12,
        "osrm_url": None,
    }

    r1 = client.post("/api/v1/schedule/generate-optimized", json=payload)
    assert r1.status_code == 202 or r1.status_code == 200
    data = r1.json()
    assert data["status"] == "completed"
    assert "days" in data
    assert data["total_distance_km"] >= 0

    # повтор без force должен дать conflict
    r2 = client.post("/api/v1/schedule/generate-optimized", json=payload)
    assert r2.status_code == 409

    # с force — ок
    payload["force"] = True
    r3 = client.post("/api/v1/schedule/generate-optimized", json=payload)
    assert r3.status_code == 202 or r3.status_code == 200

