from datetime import date
from typing import List, Literal, Optional

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
    total_tt: int
    estimated_duration_hours: float
    lunch_break_at: Optional[str] = None  # "HH:MM", фиксированный обед


class MonthlyPlan(BaseModel):
    month: str
    total_tt_planned: int
    coverage_pct: float
    routes: List[DailyRoute]
