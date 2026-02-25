from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (Metric as DBMetric,
                                 OptimizationResult as DBOptimizationResult,
                                 get_session,
                                 )

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def get_all_metrics(
    db: AsyncSession = Depends(get_session),
    route_id: Optional[str] = Query(None, description="Фильтр по route_id"),
):
    """
    Возвращает метрики в формате, совместимом с фронтендом:
    {metrics: [{id, route_id, model, response_time_ms,
                quality_score, cost_rub, timestamp}]}
    """
    try:
        stmt = select(DBMetric).order_by(DBMetric.timestamp.desc()).limit(100)
        if route_id:
            stmt = stmt.where(DBMetric.route_id == route_id)

        result = await db.execute(stmt)
        db_metrics = result.scalars().all()

        metrics_list = [
            {
                "id": m.id,
                "route_id": m.route_id or "",
                "model": m.model_name,
                "response_time_ms": m.response_time_ms,
                "quality_score": m.quality_score,
                "cost_rub": m.cost,
                "timestamp": (
                    m.timestamp.isoformat() if m.timestamp else None
                ),
            }
            for m in db_metrics
        ]

        return {"metrics": metrics_list}

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {exc}",
        ) from exc
