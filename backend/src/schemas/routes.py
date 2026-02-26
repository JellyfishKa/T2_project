from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteResponse(BaseModel):
    """Schema for route list items.

    Алиасы читают поля из ORM (DB column names),
    JSON-ответ использует field names (что ожидает фронтенд).
    """

    id: str
    name: str
    # DB: locations_order → JSON: locations
    locations: List[str] = Field(alias="locations_order", default_factory=list)
    # DB: total_distance → JSON: total_distance_km
    total_distance_km: float = Field(alias="total_distance", default=0.0)
    # DB: total_time → JSON: total_time_hours
    total_time_hours: float = Field(alias="total_time", default=0.0)
    # DB: total_cost → JSON: total_cost_rub
    total_cost_rub: float = Field(alias="total_cost", default=0.0)
    model_used: str = "unknown"
    fallback_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RouteDetailResponse(RouteResponse):
    """Schema for detailed route info with metrics."""

    metrics: List[dict] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginatedRoutes(BaseModel):
    """Schema for paginated route list."""

    total: int
    items: List[RouteResponse]
