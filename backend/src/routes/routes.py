from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Route, get_session
from src.schemas.routes import (
    PaginatedRoutes,
    RouteDetailResponse,
    RouteResponse,
)


router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get(
    "",
    response_model=PaginatedRoutes,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Paginated list of routes"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_routes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    session: AsyncSession = Depends(get_session),
):
    """Get paginated list of all routes."""
    count_stmt = select(func.count(Route.id))
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = (
        select(Route)
        .order_by(Route.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    routes = result.scalars().all()

    return PaginatedRoutes(
        total=total,
        items=[RouteResponse.model_validate(r) for r in routes],
    )


@router.get(
    "/{route_id}",
    response_model=RouteDetailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Route details with metrics"},
        404: {"description": "Route not found"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_route_detail(
    route_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get detailed information about a specific route."""
    stmt = (
        select(Route)
        .options(selectinload(Route.metrics))
        .where(Route.id == route_id)
    )
    result = await session.execute(stmt)
    route = result.scalar_one_or_none()

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found",
        )

    metrics_data = [
        {
            "id": m.id,
            "model_name": m.model_name,
            "response_time_ms": m.response_time_ms,
            "quality_score": m.quality_score,
            "cost": m.cost,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in route.metrics
    ]

    return RouteDetailResponse(
        id=route.id,
        name=route.name,
        locations=route.locations_order or [],
        total_distance_km=route.total_distance or 0.0,
        total_time_hours=route.total_time or 0.0,
        total_cost_rub=route.total_cost or 0.0,
        model_used=route.model_used or "unknown",
        created_at=route.created_at,
        metrics=metrics_data,
    )
