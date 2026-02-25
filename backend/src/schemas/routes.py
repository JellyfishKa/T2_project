from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RouteResponse(BaseModel):
    """Schema for route list items."""

    id: str
    name: str
    locations_order: List[str]
    total_distance: float
    total_time: float
    total_cost: float
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RouteDetailResponse(RouteResponse):
    """Schema for detailed route info with metrics."""

    metrics: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedRoutes(BaseModel):
    """Schema for paginated route list."""

    total: int
    items: List[RouteResponse]
