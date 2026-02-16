from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    """Schema for incoming location data."""

    name: str = Field(..., example="Warehouse A")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    time_window_start: str = Field(..., example="09:00")
    time_window_end: str = Field(..., example="18:00")


class LocationResponse(LocationCreate):
    """Schema for outgoing location data."""

    id: str
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
