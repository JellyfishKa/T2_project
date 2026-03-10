from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SalesRepCreate(BaseModel):
    name: str = Field(..., example="Иванов Иван Иванович")
    status: Literal["active", "sick", "vacation", "unavailable"] = "active"


class SalesRepUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["active", "sick", "vacation", "unavailable"]] = None


class SalesRepResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    warning: Optional[str] = None           # "Есть N незакрытых визитов..."
    pending_visits_count: int = 0

    model_config = ConfigDict(from_attributes=True)
