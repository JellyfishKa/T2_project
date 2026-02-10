from datetime import datetime

from pydantic import BaseModel


class Location(BaseModel):
    ID: str
    name: str
    address: str
    lat: float
    lon: float
    time_window_start: str
    time_window_end: str
    priority: str


class Route(BaseModel):
    ID: str
    name: str
    locations: list
    total_distance_km: float
    total_time_hours: float
    total_cost_rub: float
    model_used: str
    created_at: datetime
