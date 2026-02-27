import time

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Location as DBLocation, get_session
from src.schemas.optimize import (
    ConfirmVariantRequest,
    OptimizeRequest,
    OptimizeResponse,
    OptimizeVariantsRequest,
    OptimizeVariantsResponse,
)
from src.services.optimize import Optimizer

router = APIRouter(tags=['Optimization'])


@router.post('/optimize', response_model=OptimizeResponse)
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

        from datetime import datetime
        return OptimizeResponse(
            id=optimized_route.ID,
            name=optimized_route.name or "Оптимизированный маршрут",
            locations=[loc.ID for loc in optimized_route.locations],
            total_distance_km=optimized_route.total_distance_km,
            total_time_hours=optimized_route.total_time_hours,
            total_cost_rub=optimized_route.total_cost_rub,
            model_used=optimized_route.model_used,
            quality_score=getattr(optimized_route, 'quality_score', 0.0),
            response_time_ms=execution_time_ms,
            fallback_reason=fallback_reason,
            created_at=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Optimization failed: {str(e)}',
        )


@router.post('/optimize/variants', response_model=OptimizeVariantsResponse)
async def get_optimization_variants(
    payload: OptimizeVariantsRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Генерирует 3 варианта оптимизации маршрута без сохранения в БД.
    LLM выбранной модели оценивает каждый вариант и добавляет pros/cons.
    """
    if len(payload.location_ids) < 2:
        raise HTTPException(
            status_code=422,
            detail='Необходимо минимум 2 точки для оптимизации',
        )

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
        return await optimizer.generate_variants(
            db_locations=ordered_locations,
            model=payload.model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f'Variants generation failed: {str(exc)}',
        )


@router.post('/optimize/confirm', response_model=OptimizeResponse)
async def confirm_variant(
    payload: ConfirmVariantRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Сохраняет выбранный пользователем вариант маршрута в БД.
    """
    if not payload.locations:
        raise HTTPException(
            status_code=422,
            detail='Список точек не может быть пустым',
        )

    optimizer = Optimizer(db)

    try:
        saved = await optimizer.confirm_variant(
            name=payload.name,
            locations_order=payload.locations,
            total_distance_km=payload.total_distance_km,
            total_time_hours=payload.total_time_hours,
            total_cost_rub=payload.total_cost_rub,
            quality_score=payload.quality_score,
            model_used=payload.model_used,
            original_location_ids=payload.original_location_ids,
        )
        return OptimizeResponse(**saved)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to save variant: {str(exc)}',
        )
