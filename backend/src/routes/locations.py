from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Location, get_session
from src.schemas.locations import LocationCreate, LocationResponse


router = APIRouter(prefix="/locations", tags=["Locations"])


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
