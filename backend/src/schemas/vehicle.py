from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Vehicle(BaseModel):
    id: str
    name: str
    fuel_price_rub: float
    consumption_city_l_100km: float
    consumption_highway_l_100km: float
    model_config = ConfigDict(from_attributes=True)


class VehicleCreate(BaseModel):
    name: str
    fuel_price_rub: float
    consumption_city_l_100km: float
    consumption_highway_l_100km: float

    @field_validator('fuel_price_rub', 'consumption_city_l_100km', 'consumption_highway_l_100km')
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('must be > 0')
        return v


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    fuel_price_rub: Optional[float] = None
    consumption_city_l_100km: Optional[float] = None
    consumption_highway_l_100km: Optional[float] = None

    @field_validator('fuel_price_rub', 'consumption_city_l_100km', 'consumption_highway_l_100km')
    @classmethod
    def must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError('must be > 0')
        return v


class VehicleResponse(VehicleCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)
