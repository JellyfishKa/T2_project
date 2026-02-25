import csv
import io
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Location, get_session
from src.schemas.locations import (
    LocationCreate,
    LocationResponse,
    UploadLocationsResponse,
)


router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get(
    "/",
    response_model=List[LocationResponse],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Успешное получение списка всех локаций"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_locations(
    session: AsyncSession = Depends(get_session),
):
    """
    Get all locations from the database.
    
    Returns a list of locations with their IDs, coordinates, and time windows.
    """
    # Создаем запрос на выборку всех записей из таблицы Location
    stmt = select(Location)
    result = await session.execute(stmt)
    
    # scalars() извлекает объекты моделей, а all() собирает их в список
    locations = result.scalars().all()
    
    return locations


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Bad Request"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)
async def create_location(
    location_data: LocationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new location in the database."""
    new_location = Location(**location_data.model_dump())
    session.add(new_location)
    await session.commit()
    await session.refresh(new_location)

    return new_location


@router.post(
    "/upload",
    response_model=UploadLocationsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Unsupported file format"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)
async def upload_locations(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    """Upload locations from a CSV or JSON file.

    CSV format: name,lat,lon,time_window_start,time_window_end
    JSON format: array of objects with the same fields.
    """
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".json"):
        rows = _parse_json(content)
    elif filename.endswith(".csv"):
        rows = _parse_csv(content)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Use .csv or .json",
        )

    created: list[Location] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        try:
            loc_data = LocationCreate(**row)
            new_location = Location(**loc_data.model_dump())
            session.add(new_location)
            await session.flush()
            created.append(new_location)
        except Exception as exc:
            errors.append({"row": idx + 1, "error": str(exc), "data": row})

    if created:
        await session.commit()
        for loc in created:
            await session.refresh(loc)

    return UploadLocationsResponse(
        created=[LocationResponse.model_validate(loc) for loc in created],
        errors=errors,
        total_processed=len(rows),
    )


def _parse_json(content: bytes) -> list[dict]:
    """Parse JSON file content into list of dicts."""
    data = json.loads(content.decode("utf-8"))
    if isinstance(data, list):
        return data
    raise ValueError("JSON file must contain an array of objects")


def _parse_csv(content: bytes) -> list[dict]:
    """Parse CSV file content into list of dicts."""
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        parsed = {}
        for key, value in row.items():
            key = key.strip()
            value = value.strip() if value else value
            if key in ("lat", "lon"):
                parsed[key] = float(value)
            else:
                parsed[key] = value
        rows.append(parsed)
    return rows