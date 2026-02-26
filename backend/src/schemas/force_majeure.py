from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ForceMajeureRequest(BaseModel):
    type: Literal["illness", "weather", "vehicle_breakdown", "other"] = Field(
        ..., description="Тип форс-мажора"
    )
    rep_id: str = Field(..., description="ID торгового представителя")
    event_date: date = Field(..., description="Дата инцидента")
    description: Optional[str] = Field(None, description="Описание")


class RedistributedItem(BaseModel):
    rep_id: str
    rep_name: str
    location_ids: List[str]
    new_date: date


class ForceMajeureResponse(BaseModel):
    id: str
    type: str
    rep_id: str
    rep_name: str
    event_date: date
    description: Optional[str]
    affected_tt_count: int
    redistributed_to: List[RedistributedItem]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
