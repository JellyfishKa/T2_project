from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (Metric as DBMetric,
                                 get_session,
                                 )
from src.services.routing_observability import get_routing_observability_snapshot

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

        routing_snapshot = get_routing_observability_snapshot()
        algorithm_runs = routing_snapshot.get("algorithm_runs_total", 0)
        fallback_attempts = routing_snapshot.get("llm_fallback_attempts_total", 0)
        fallback_success = routing_snapshot.get("llm_fallback_success_total", 0)
        fallback_rate = (
            round((fallback_attempts / algorithm_runs) * 100, 2)
            if algorithm_runs > 0
            else 0.0
        )
        fallback_success_rate = (
            round((fallback_success / fallback_attempts) * 100, 2)
            if fallback_attempts > 0
            else 0.0
        )

        return {
            "metrics": metrics_list,
            "routing_observability": {
                **routing_snapshot,
                "llm_fallback_rate_pct": fallback_rate,
                "llm_fallback_success_rate_pct": fallback_success_rate,
                "storage_mode": "in_process_counter",
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {exc}",
        ) from exc
