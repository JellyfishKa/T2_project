from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    """Schema for incoming location data."""

    name: str = Field(..., example="Магазин Саранск-1")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    time_window_start: str = Field(..., example="09:00")
    time_window_end: str = Field(..., example="18:00")
    category: Optional[Literal["A", "B", "C", "D"]] = Field(
        None, description="Категория ТТ: A/B/C/D"
    )
    city: Optional[str] = Field(None, example="Саранск")
    district: Optional[str] = Field(None, example="г.о. Саранск")
    address: Optional[str] = Field(None, example="ул. Советская, 35")


class LocationResponse(LocationCreate):
    """Schema for outgoing location data."""

    id: str
    model_config = ConfigDict(from_attributes=True)


class UploadLocationsResponse(BaseModel):
    """Schema for bulk location upload results."""

    created: list[LocationResponse] = []
    errors: list[dict] = []
    total_processed: int = 0


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
