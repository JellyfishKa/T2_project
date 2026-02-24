import time

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Location as DBLocation, get_session
from src.schemas.optimize import OptimizeRequest, OptimizeResponse
from src.services.optimize import Optimizer

router = APIRouter(tags=['Optimization'])


@router.post('/api/v1/optimize', response_model=OptimizeResponse)
async def run_optimization(
    payload: OptimizeRequest,
    db: AsyncSession = Depends(get_session),
):
    start_time = time.time()

    query = select(DBLocation).where(
        DBLocation.id.in_(payload.location_ids),
    )
    result = await db.execute(query)
    db_locations = result.scalars().all()

    if not db_locations:
        raise HTTPException(
            status_code=404,
            detail='Locations not found',
        )

    loc_map = {loc.id: loc for loc in db_locations}
    ordered_locations = [
        loc_map[loc_id]
        for loc_id in payload.location_ids
        if loc_id in loc_map
    ]

    optimizer = Optimizer(db)

    try:
        optimized_route = await optimizer.optimize(
            db_locations=ordered_locations,
            model=payload.model,
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        fallback_reason = None
        if (
            payload.model != 'auto' and
            optimized_route.model_used != payload.model
        ):
            fallback_reason = (
                f'Model {payload.model} failed, '
                f'used {optimized_route.model_used} instead.'
            )

        return OptimizeResponse(
            route_order=[loc.ID for loc in optimized_route.locations],
            total_distance=optimized_route.total_distance_km,
            total_time_minutes=optimized_route.total_time_hours * 60,
            total_cost=optimized_route.total_cost_rub,
            model_used=optimized_route.model_used,
            quality_score=getattr(optimized_route, 'quality_score', 0.0),
            response_time_ms=execution_time_ms,
            fallback_reason=fallback_reason,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Optimization failed: {str(e)}',
        )
