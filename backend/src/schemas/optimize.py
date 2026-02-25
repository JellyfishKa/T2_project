from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    location_ids: List[str]
    model: str = "auto"
    constraints: Optional[Dict] = Field(default_factory=lambda: {
        "max_stops_per_route": 50,
        "time_window_minutes": 480,
    })


class OptimizeResponse(BaseModel):
    route_order: List[str]
    total_distance: float
    total_time_minutes: float
    total_cost: float
    model_used: str
    quality_score: float
    response_time_ms: int
    fallback_reason: Optional[str] = None
