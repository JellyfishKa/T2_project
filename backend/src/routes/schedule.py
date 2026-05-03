from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.models.schedule_schemas import (
    GenerateOptimizedScheduleAccepted,
    GenerateOptimizedScheduleJobStatus,
    GenerateOptimizedScheduleRequest,
    GenerateOptimizedScheduleResult,
)
from src.services.osrm_service import osrm_trip_order

from schedule_planner import (
    SchedulePlanner,
    TradePoint,
    route_distance_km,
)


router = APIRouter(prefix="/api/v1/schedule", tags=["Schedule"])

# in-memory job store (минимум под ТЗ)
_JOBS: Dict[str, Dict] = {}
# защита от двойной генерации по ключу (month+reps+tp_count) без force
_GENERATED_KEYS: Dict[str, str] = {}


def _month_key(req: GenerateOptimizedScheduleRequest) -> str:
    return f"{req.month.isoformat()}|{','.join(req.reps)}|tp={len(req.trade_points)}"


def _build_schedule(req: GenerateOptimizedScheduleRequest) -> GenerateOptimizedScheduleResult:
    reps = list(req.reps)
    trade_points = [
        TradePoint(
            id=tp.id,
            category=tp.category,
            latitude=tp.latitude,
            longitude=tp.longitude,
        )
        for tp in req.trade_points
    ]

    planner = SchedulePlanner(
        rep_ids=reps,
        max_visits_per_day=req.max_visits_per_day,
        geo_clusterer=SchedulePlanner.make_default_geo_clusterer(reps),
    )
    routes = planner.plan_month(trade_points, req.month, use_geo=True)

    days = []
    total = 0.0
    for r in routes:
        ids = [v.trade_point_id for v in r.visits]
        coords = [(v.latitude, v.longitude) for v in r.visits]
        order = osrm_trip_order(coords, osrm_url=req.osrm_url)
        if order is not None:
            # применяем порядок OSRM
            ids = [ids[i] for i in order]
            coords = [coords[i] for i in order]
            routing_method = "osrm-trip"
            # считаем distance haversine по новому порядку
            from schedule_planner import VisitTask

            visits = tuple(
                VisitTask(
                    trade_point_id=r.visits[i].trade_point_id,
                    category=r.visits[i].category,
                    latitude=r.visits[i].latitude,
                    longitude=r.visits[i].longitude,
                )
                for i in order
            )
            dist_km = route_distance_km(visits)
        else:
            routing_method = "heuristic-nn"
            dist_km = route_distance_km(r.visits)

        total += dist_km
        days.append(
            {
                "rep_id": r.rep_id,
                "day": r.day,
                "trade_point_ids": ids,
                "total_distance_km": round(dist_km, 2),
                "routing_method": routing_method,
            }
        )

    return GenerateOptimizedScheduleResult(
        status="completed",
        month=req.month,
        reps=reps,
        created_at=datetime.utcnow(),
        total_distance_km=round(total, 2),
        days=days,
        meta={
            "geo_clustering": "kmeans+balance (no-sklearn backend impl)",
            "max_visits_per_day": req.max_visits_per_day,
        },
    )


def _run_job(job_id: str, req: GenerateOptimizedScheduleRequest) -> None:
    try:
        _JOBS[job_id]["status"] = "in_progress"
        result = _build_schedule(req)
        _JOBS[job_id]["status"] = "completed"
        _JOBS[job_id]["result"] = result.model_dump()
    except Exception as e:
        _JOBS[job_id]["status"] = "failed"
        _JOBS[job_id]["error"] = str(e)


@router.post(
    "/generate-optimized",
    response_model=GenerateOptimizedScheduleAccepted | GenerateOptimizedScheduleResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_optimized(req: GenerateOptimizedScheduleRequest, bg: BackgroundTasks):
    key = _month_key(req)
    if not req.force and key in _GENERATED_KEYS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schedule already generated for key={key}. Use force=true to regenerate.",
        )

    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {"status": "in_progress", "result": None, "error": None, "key": key}
    _GENERATED_KEYS[key] = job_id

    # небольшой объём — можно синхронно
    if not req.async_mode or len(req.trade_points) <= 25:
        result = _build_schedule(req)
        _JOBS[job_id]["status"] = "completed"
        _JOBS[job_id]["result"] = result.model_dump()
        return result

    bg.add_task(_run_job, job_id, req)
    return GenerateOptimizedScheduleAccepted(status="accepted", job_id=job_id)


@router.get("/jobs/{job_id}", response_model=GenerateOptimizedScheduleJobStatus)
async def get_job(job_id: str):
    row = _JOBS.get(job_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return GenerateOptimizedScheduleJobStatus(
        status=row["status"],
        job_id=job_id,
        result=row["result"],
        error=row["error"],
    )

