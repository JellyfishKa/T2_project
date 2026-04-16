import json
from typing import List, Optional

from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.schemas.routing import (
    RoutePreviewRequest,
    RoutePreviewResponse,
)
from src.database.models import get_session
from src.database.models import Vehicle as DBVehicle
from src.schemas.vehicle import VehicleCreate, VehicleResponse
from src.services.routing import RoutingService


router = APIRouter(prefix="/routing", tags=["Routing"])


@router.get("/", response_model=List[VehicleResponse])
async def list_vehicles(session: AsyncSession = Depends(get_session)):
    """Список всех автомобилей."""
    result = await session.execute(select(DBVehicle).order_by(DBVehicle.name))
    return [VehicleResponse.model_validate(v) for v in result.scalars().all()]


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Добавить автомобиль вручную."""
    vehicle = DBVehicle(**data.model_dump())
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Удалить автомобиль."""
    vehicle = await session.get(DBVehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    await session.delete(vehicle)
    await session.commit()


@router.post("/preview", response_model=RoutePreviewResponse)
async def preview_route(
    payload: RoutePreviewRequest,
    session: AsyncSession = Depends(get_session),
):
    """Предпросмотр маршрута с расчётом транспортных расходов ТП.

    transport_mode:
      car  — расход топлива (требует vehicle_id или первый авто из БД)
      taxi — тариф ₽/км
      bus  — тариф ₽ за каждую пересадку
    """
    vehicle: Optional[DBVehicle] = None

    if payload.transport_mode == "car":
        if payload.vehicle_id:
            vehicle = await session.get(DBVehicle, payload.vehicle_id)
            if not vehicle:
                raise HTTPException(status_code=404, detail="Автомобиль не найден")
        else:
            # Фоллбэк: первый авто из БД; если нет — используем estimate_fuel_cost
            result = await session.execute(select(DBVehicle).limit(1))
            vehicle = result.scalar_one_or_none()

    from src.schemas.vehicle import Vehicle as VehicleSchema
    vehicle_schema = VehicleSchema.model_validate(vehicle, from_attributes=True) if vehicle else None

    routing_service = RoutingService()
    preview = await routing_service.build_route_preview(
        points=payload.points,
        vehicle=vehicle_schema,
        transport_mode=payload.transport_mode,
    )
    return RoutePreviewResponse(**preview)


@router.post(
    "/upload_cars",
    response_model=List[VehicleResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Unsupported file format"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)
async def upload_cars(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    """Загрузить автомобили из JSON-файла."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if not filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON format is supported",
        )

    try:
        rows = _parse_json(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    created: list[DBVehicle] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        try:
            vehicle_data = VehicleCreate(**row)
            new_vehicle = DBVehicle(**vehicle_data.model_dump())
            session.add(new_vehicle)
            await session.flush()
            created.append(new_vehicle)
        except Exception as exc:
            errors.append({"row": idx + 1, "error": str(exc), "data": row})

    if created:
        await session.commit()
        for v in created:
            await session.refresh(v)

    return [VehicleResponse.model_validate(v) for v in created]


def _parse_json(content: bytes) -> list[dict]:
    data = json.loads(content.decode("utf-8"))
    if isinstance(data, list):
        return data
    raise ValueError("JSON file must contain an array of objects")
