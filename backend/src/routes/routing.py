import json
from typing import List

from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.schemas.routing import (
    RoutePreviewRequest,
    RoutePreviewResponse,
)
from src.database.models import get_session
from src.database.models import Vehicle as DBVehicle
from src.schemas.vehicle import Vehicle, VehicleCreate, VehicleResponse
from src.services.routing import RoutingService


router = APIRouter(prefix="/routing", tags=["Routing"])


@router.post("/preview", response_model=RoutePreviewResponse)
async def preview_route(
    payload: RoutePreviewRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(DBVehicle).limit(1))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="No vehicles found in database")

    routing_service = RoutingService()
    preview = await routing_service.build_route_preview(
        points=payload.points, 
        vehicle=vehicle
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
    """Upload vehicles from JSON file"""

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

    created: list[Vehicle] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        try:
            vehicle_data = VehicleCreate(**row)
            
            new_vehicle = DBVehicle(**vehicle_data.model_dump())

            session.add(new_vehicle)
            await session.flush() 

            created.append(new_vehicle)

        except Exception as exc:
            errors.append({
                "row": idx + 1,
                "error": str(exc),
                "data": row
            })

    if created:
        await session.commit()
        for v in created:
            await session.refresh(v)

    return [VehicleResponse.model_validate(v) for v in created]


def _parse_json(content: bytes) -> list[dict]:
    """Parse JSON file content into list of dicts."""
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list):
        return data

    raise ValueError("JSON file must contain an array of objects")