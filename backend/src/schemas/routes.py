from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteResponse(BaseModel):
    """Schema for route list items.

    Поля total_distance_km / total_time_hours / total_cost_rub —
    алиасы для совместимости с фронтендом; в БД хранятся как
    total_distance / total_time / total_cost.
    """

    id: str
    name: str
    locations_order: List[str]
    # Алиасы: фронтенд ожидает _km / _hours / _rub
    total_distance_km: float = Field(alias="total_distance", default=0.0)
    total_time_hours: float = Field(alias="total_time", default=0.0)
    total_cost_rub: float = Field(alias="total_cost", default=0.0)
    model_used: str = "unknown"
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
