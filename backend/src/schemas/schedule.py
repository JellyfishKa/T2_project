from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerateScheduleRequest(BaseModel):
    month: str = Field(..., example="2026-03",
                       description="Месяц для генерации плана (YYYY-MM)")
    rep_ids: Optional[List[str]] = Field(
        None, description="Список ID сотрудников. Если пусто — все активные"
    )


class VisitScheduleItem(BaseModel):
    id: str
    location_id: str
    location_name: str
    location_category: Optional[Literal["A", "B", "C", "D"]]
    rep_id: str
    rep_name: str
    planned_date: date
    status: str
    time_in: Optional[str] = None   # HH:MM из visit_log
    time_out: Optional[str] = None  # HH:MM из visit_log

    model_config = ConfigDict(from_attributes=True)


class VisitStatusUpdate(BaseModel):
    """Тело запроса для PATCH /schedule/{visit_id}."""
    status: Literal["completed", "skipped", "cancelled", "rescheduled", "planned"]
    time_in: Optional[str] = None    # "HH:MM" — время прихода
    time_out: Optional[str] = None   # "HH:MM" — время выхода
    notes: Optional[str] = None


class DailyRoute(BaseModel):
    rep_id: str
    rep_name: str
    date: date
    visits: List[VisitScheduleItem]
    current_location_ids: List[str] = []
    original_location_ids: List[str] = []
    route_source: Literal["generated", "ai", "manual"] = "generated"
    route_label: Optional[str] = None
    route_updated_at: Optional[datetime] = None
    has_route_override: bool = False
    total_tt: int
    estimated_duration_hours: float
    lunch_break_at: Optional[str] = None  # "HH:MM", фиксированный обед


class DayRouteOverrideRequest(BaseModel):
    rep_id: str
    date: date
    location_ids: List[str]
    original_location_ids: Optional[List[str]] = None
    source: Literal["ai", "manual"] = "manual"
    label: Optional[str] = None


class MonthlyPlan(BaseModel):
    month: str
    total_tt_planned: int
    coverage_pct: float
    routes: List[DailyRoute]


# ── Стеш пропущенных визитов ─────────────────────────────────────────────────

class SkippedStashItem(BaseModel):
    id: str
    visit_schedule_id: Optional[str] = None
    location_id: str
    location_name: str
    location_category: Optional[Literal["A", "B", "C", "D"]] = None
    rep_id: str
    rep_name: str
    original_date: date
    resolution: Optional[str] = None   # manual | ai | carry_over | None = pending
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResolveManualRequest(BaseModel):
    rep_id: str
    target_date: date


class ResolveAIRequest(BaseModel):
    stash_ids: List[str]
