from datetime import datetime
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
    """Формат совместим с интерфейсом Route фронтенда."""
    id: str
    name: str
    locations: List[str]          # порядок ID после оптимизации
    total_distance_km: float
    total_time_hours: float
    total_cost_rub: float
    model_used: str
    quality_score: float
    response_time_ms: int
    fallback_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
