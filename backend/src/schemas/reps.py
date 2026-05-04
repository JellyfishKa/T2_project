from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SalesRepCreate(BaseModel):
    name: str = Field(..., examples=["Иванов Иван Иванович"])
    status: Literal["active", "sick", "vacation", "unavailable"] = "active"
    vehicle_id: Optional[str] = None


class SalesRepUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["active", "sick", "vacation", "unavailable"]] = None
    vehicle_id: Optional[str] = None


class SalesRepResponse(BaseModel):
    id: str
    name: str
    status: str
    vehicle_id: Optional[str] = None
    vehicle_name: Optional[str] = None
    created_at: datetime
    warning: Optional[str] = None           # "Есть N незакрытых визитов..."
    pending_visits_count: int = 0

    model_config = ConfigDict(from_attributes=True)
