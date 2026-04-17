from calendar import monthrange
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AuditLog, get_session

router = APIRouter(prefix="/audit-log", tags=["Audit"])

ACTION_LABELS = {
    "visit_status_change": "Смена статуса визита",
    "force_majeure_created": "Форс-мажор",
    "schedule_generated": "Генерация расписания",
}


@router.get("/monthly")
async def get_audit_log_monthly(
    month: str = Query(..., description="YYYY-MM"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Журнал изменений с фильтром по месяцу."""
    try:
        parts = month.split("-")
        if len(parts) != 2:
            raise ValueError
        year, m = int(parts[0]), int(parts[1])
        if not (1 <= m <= 12):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    start = datetime(year, m, 1, 0, 0, 0)
    end = datetime(year, m, last_day, 23, 59, 59)

    total_q = await session.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.created_at.between(start, end))
    )
    total = total_q.scalar() or 0

    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.created_at.between(start, end))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": item.id,
                "action": item.action,
                "action_label": ACTION_LABELS.get(item.action, item.action),
                "table_name": item.table_name,
                "record_id": item.record_id,
                "old_value": item.old_value,
                "new_value": item.new_value,
                "details": item.details,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        "total": total,
    }
