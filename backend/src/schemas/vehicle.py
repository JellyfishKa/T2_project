from pydantic import BaseModel, ConfigDict

class Vehicle(BaseModel):
    id: str
    name: str
    fuel_price_rub: float                 # Стоимость 1 литра топлива
    consumption_city_l_100km: float       # Расход в городе (л/100 км)
    consumption_highway_l_100km: float    # Расход на трассе (л/100 км)
    model_config = ConfigDict(from_attributes=True)


class VehicleCreate(BaseModel):
    name: str
    fuel_price_rub: float
    consumption_city_l_100km: float
    consumption_highway_l_100km: float


class VehicleResponse(VehicleCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)
