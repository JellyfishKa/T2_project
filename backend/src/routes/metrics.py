from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (Metric as DBMetric,
                                 OptimizationResult as DBOptimizationResult,
                                 get_session,
                                 )
from src.services.quality_evaluator import get_route_quality_metrics

router = APIRouter(tags=["Metrics"])


@router.get("/api/v1/metrics")
async def get_all_metrics(
    db: AsyncSession = Depends(get_session),
):
    try:
        stmt = (
            select(DBOptimizationResult)
            .order_by(DBOptimizationResult.created_at.desc())
            .limit(10)
        )

        result = await db.execute(stmt)
        optimizations = result.scalars().all()

        detailed_metrics = []

        for opt in optimizations:
            original_data = {
                "distance_km": 100.0,
                "time_minutes": 120.0,
                "cost_rub": 1000.0,
            }

            optimized_data = {
                "distance_km": opt.optimized_route.get(
                    "total_distance",
                    80.0,
                ),
                "time_minutes": opt.optimized_route.get(
                    "total_time",
                    100.0,
                ),
                "cost_rub": opt.optimized_route.get(
                    "total_cost",
                    800.0,
                ),
                "constraints_satisfied": True,
            }

            quality_data = get_route_quality_metrics(
                original_data,
                optimized_data,
            )

            detailed_metrics.append(
                {
                    "optimization_id": opt.id,
                    "model_used": opt.model_used,
                    "quality_scores": quality_data,
                    "created_at": opt.created_at,
                },
            )

        stats_stmt = (
            select(
                DBMetric.model_name,
                func.avg(DBMetric.response_time_ms).label(
                    "avg_latency",
                ),
                func.avg(DBMetric.quality_score).label(
                    "avg_score",
                ),
                func.count(DBMetric.id).label("total_calls"),
            )
            .group_by(DBMetric.model_name)
        )

        stats_result = await db.execute(stats_stmt)

        model_stats = [
            {
                "model": row.model_name,
                "avg_response_time_ms": round(row.avg_latency, 2),
                "avg_quality_score": round(row.avg_score, 2),
                "total_runs": row.total_calls,
            }
            for row in stats_result
        ]

        return {
            "summary": model_stats,
            "recent_optimizations": detailed_metrics,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {exc}",
        ) from exc
