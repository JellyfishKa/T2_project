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


# ─── Variants (выбор из нескольких вариантов маршрута) ─────────────────────────

class RouteVariantMetrics(BaseModel):
    distance_km: float
    time_hours: float
    cost_rub: float
    quality_score: float


class RouteVariant(BaseModel):
    id: int
    name: str
    description: str
    algorithm: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    locations: List[str]          # упорядоченные ID точек
    metrics: RouteVariantMetrics


class OptimizeVariantsRequest(BaseModel):
    location_ids: List[str]
    model: str = "qwen"           # только одна модель за раз
    constraints: Optional[Dict] = Field(default_factory=dict)


class OptimizeVariantsResponse(BaseModel):
    variants: List[RouteVariant]
    model_used: str
    response_time_ms: int
    llm_evaluation_success: bool


class ConfirmVariantRequest(BaseModel):
    """Сохранение выбранного варианта в БД."""
    name: str
    locations: List[str]          # упорядоченные ID точек
    total_distance_km: float
    total_time_hours: float
    total_cost_rub: float
    quality_score: float
    model_used: str
    original_location_ids: List[str]
