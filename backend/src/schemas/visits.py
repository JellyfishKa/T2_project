from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VisitCreate(BaseModel):
    location_id: str
    rep_id: str
    visited_date: date
    schedule_id: Optional[str] = None
    time_in: Optional[time] = None
    time_out: Optional[time] = None
    notes: Optional[str] = None


class VisitResponse(BaseModel):
    id: str
    location_id: str
    rep_id: str
    visited_date: date
    schedule_id: Optional[str]
    time_in: Optional[time]
    time_out: Optional[time]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VisitStats(BaseModel):
    month: str
    total_visits: int
    unique_locations: int
    unique_reps: int
    by_category: dict
    by_rep: list
