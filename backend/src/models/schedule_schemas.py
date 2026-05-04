from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TradePointIn(BaseModel):
    id: str
    category: str = Field(..., description="A/B/C/D etc")
    latitude: float
    longitude: float


class DayPlan(BaseModel):
    rep_id: str
    day: date
    trade_point_ids: List[str]
    total_distance_km: float
    routing_method: Literal["osrm-trip", "heuristic-nn"]


class GenerateOptimizedScheduleRequest(BaseModel):
    month: date = Field(..., description="Любая дата внутри месяца, например 2026-05-01")
    reps: List[str] = Field(..., min_length=1)
    trade_points: List[TradePointIn] = Field(..., min_length=1)
    force: bool = False
    async_mode: bool = True
    max_visits_per_day: int = 12
    osrm_url: Optional[str] = Field(
        default=None,
        description="Если задано, используем OSRM trip service; иначе heuristic fallback",
    )


class GenerateOptimizedScheduleAccepted(BaseModel):
    status: Literal["accepted"]
    job_id: str


class GenerateOptimizedScheduleResult(BaseModel):
    status: Literal["completed"]
    month: date
    reps: List[str]
    created_at: datetime
    total_distance_km: float
    days: List[DayPlan]
    meta: Dict = {}


class GenerateOptimizedScheduleJobStatus(BaseModel):
    status: Literal["in_progress", "completed", "failed"]
    job_id: str
    result: Optional[GenerateOptimizedScheduleResult] = None
    error: Optional[str] = None

