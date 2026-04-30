from typing import Literal, Optional

from pydantic import BaseModel, Field


class RoutingPoint(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class RoutePreviewRequest(BaseModel):
    points: list[RoutingPoint]
    vehicle_id: Optional[str] = None
    transport_mode: Literal["car", "taxi", "bus"] = "car"


class RoutePreviewResponse(BaseModel):
    geometry: list[tuple[float, float]]
    distance_km: float
    time_minutes: float
    cost_rub: float
    traffic_lights_count: int
    source: str
    transport_mode: str = "car"
