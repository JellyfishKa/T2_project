from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Location, OptimizationResult, Route, get_session
from src.schemas.locations import LocationResponse
from src.schemas.routes import (
    ComparisonDiff,
    ComparisonPoint,
    PaginatedRoutes,
    RouteComparisonResponse,
    RouteDetailResponse,
    RouteResponse,
)


router = APIRouter(prefix="/routes", tags=["Routes"])

COMPARISON_SNAPSHOT_FIELDS = (
    "original_distance_km",
    "original_time_hours",
    "original_cost_rub",
    "optimized_distance_km",
    "optimized_time_hours",
    "optimized_cost_rub",
)


def has_complete_comparison_snapshot(
    optimization_result: OptimizationResult | None,
) -> bool:
    return optimization_result is not None and all(
        getattr(optimization_result, field_name) is not None
        for field_name in COMPARISON_SNAPSHOT_FIELDS
    )


async def load_latest_comparison_results(
    session: AsyncSession,
    route_ids: list[str],
) -> dict[str, OptimizationResult]:
    normalized_ids = [route_id for route_id in dict.fromkeys(route_ids) if route_id]
    if not normalized_ids:
        return {}

    stmt = (
        select(OptimizationResult)
        .where(OptimizationResult.route_id.in_(normalized_ids))
        .order_by(
            OptimizationResult.route_id.asc(),
            OptimizationResult.created_at.desc(),
            OptimizationResult.id.desc(),
        )
    )
    result = await session.execute(stmt)

    latest_by_route: dict[str, OptimizationResult] = {}
    for item in result.scalars().all():
        if item.route_id and item.route_id not in latest_by_route:
            latest_by_route[item.route_id] = item
    return latest_by_route


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
    latest_comparisons = await load_latest_comparison_results(
        session,
        [route.id for route in routes],
    )

    return PaginatedRoutes(
        total=total,
        items=[
            RouteResponse(
                id=route.id,
                name=route.name,
                locations=route.locations_order or [],
                total_distance_km=route.total_distance or 0.0,
                total_time_hours=route.total_time or 0.0,
                total_cost_rub=route.total_cost or 0.0,
                model_used=route.model_used or "unknown",
                has_comparison=has_complete_comparison_snapshot(
                    latest_comparisons.get(route.id)
                ),
                created_at=route.created_at,
            )
            for route in routes
        ],
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
            "model": m.model_name,
            "route_id": m.route_id,
            "response_time_ms": m.response_time_ms,
            "quality_score": m.quality_score,
            "cost_rub": m.cost,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in route.metrics
    ]

    locations_result = await session.execute(
        select(Location).where(Location.id.in_(route.locations_order or []))
    )
    locations_by_id = {
        location.id: location for location in locations_result.scalars().all()
    }
    ordered_locations = [
        LocationResponse.model_validate(locations_by_id[location_id])
        for location_id in (route.locations_order or [])
        if location_id in locations_by_id
    ]
    latest_comparison = (
        await load_latest_comparison_results(session, [route.id])
    ).get(route.id)

    return RouteDetailResponse(
        id=route.id,
        name=route.name,
        locations=route.locations_order or [],
        locations_sequence=route.locations_order or [],
        locations_data=ordered_locations,
        total_distance_km=route.total_distance or 0.0,
        total_time_hours=route.total_time or 0.0,
        total_cost_rub=route.total_cost or 0.0,
        model_used=route.model_used or "unknown",
        has_comparison=has_complete_comparison_snapshot(latest_comparison),
        created_at=route.created_at,
        metrics=metrics_data,
    )


@router.get(
    "/{route_id}/comparison",
    response_model=RouteComparisonResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Before/after comparison for a re-optimised route"},
        404: {"description": "Route or comparison data not found"},
    },
)
async def get_route_comparison(
    route_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Return original vs current location order with diff metrics."""
    route_stmt = select(Route).where(Route.id == route_id)
    route_result = await session.execute(route_stmt)
    route = route_result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Route {route_id} not found")

    opt = (await load_latest_comparison_results(session, [route_id])).get(route_id)
    if not has_complete_comparison_snapshot(opt):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comparison data for this route",
        )

    original_ids_ordered = opt.original_route or []
    current_ids_ordered = opt.optimized_route or []
    all_ids = list(dict.fromkeys(original_ids_ordered + current_ids_ordered))
    locs_result = await session.execute(
        select(Location).where(Location.id.in_(all_ids))
    )
    locs_by_id = {loc.id: loc for loc in locs_result.scalars().all()}

    def build_points(id_list: list) -> list[ComparisonPoint]:
        points = []
        for order, loc_id in enumerate(id_list, start=1):
            loc = locs_by_id.get(loc_id)
            if loc:
                points.append(ComparisonPoint(
                    id=loc.id,
                    name=loc.name,
                    lat=loc.lat,
                    lon=loc.lon,
                    order=order,
                    address=getattr(loc, "address", None),
                    category=getattr(loc, "category", None),
                ))
        return points

    original_points = build_points(opt.original_route or [])
    current_points = build_points(opt.optimized_route or [])

    original_positions = {
        loc_id: index for index, loc_id in enumerate(original_ids_ordered)
    }
    current_positions = {
        loc_id: index for index, loc_id in enumerate(current_ids_ordered)
    }
    changed_stops = sum(
        1
        for loc_id in set(original_positions) | set(current_positions)
        if original_positions.get(loc_id) != current_positions.get(loc_id)
    )

    return RouteComparisonResponse(
        route_id=route_id,
        original=original_points,
        current=current_points,
        diff=ComparisonDiff(
            distance_delta_km=round(
                (opt.optimized_distance_km or 0.0) - (opt.original_distance_km or 0.0),
                2,
            ),
            time_delta_hours=round(
                (opt.optimized_time_hours or 0.0) - (opt.original_time_hours or 0.0),
                2,
            ),
            cost_delta_rub=round(
                (opt.optimized_cost_rub or 0.0) - (opt.original_cost_rub or 0.0),
                2,
            ),
            changed_stops_count=changed_stops,
            improvement_percentage=opt.improvement_percentage or 0.0,
        ),
        model_used=opt.model_used or "unknown",
        created_at=opt.created_at,
    )
