from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SalesRepCreate(BaseModel):
    name: str = Field(..., examples=["Иванов Иван Иванович"])
    status: Literal["active", "sick", "vacation", "unavailable"] = "active"
    vehicle_id: Optional[str] = None
    home_lat: float = Field(54.1871, description="Стартовая точка (широта)")
    home_lon: float = Field(45.1749, description="Стартовая точка (долгота)")


class SalesRepUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["active", "sick", "vacation", "unavailable"]] = None
    vehicle_id: Optional[str] = None
    home_lat: Optional[float] = None
    home_lon: Optional[float] = None


class SalesRepResponse(BaseModel):
    id: str
    name: str
    status: str
    vehicle_id: Optional[str] = None
    vehicle_name: Optional[str] = None
    home_lat: float = 54.1871
    home_lon: float = 45.1749
    created_at: datetime
    warning: Optional[str] = None           # "Есть N незакрытых визитов..."
    pending_visits_count: int = 0

    model_config = ConfigDict(from_attributes=True)
