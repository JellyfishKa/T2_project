from calendar import monthrange
from collections import defaultdict
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Location, VisitLog, get_session
from src.schemas.visits import VisitCreate, VisitResponse, VisitStats

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.post("/", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    data: VisitCreate,
    session: AsyncSession = Depends(get_session),
):
    """Отметить фактический визит."""
    visit = VisitLog(
        location_id=data.location_id,
        rep_id=data.rep_id,
        visited_date=data.visited_date,
        schedule_id=data.schedule_id,
        time_in=data.time_in,
        time_out=data.time_out,
        notes=data.notes,
    )
    session.add(visit)
    await session.commit()
    await session.refresh(visit)
    return visit


@router.get("/stats", response_model=VisitStats)
async def get_visit_stats(
    month: str = Query(..., description="Месяц YYYY-MM"),
    session: AsyncSession = Depends(get_session),
):
    """Статистика посещаемости за месяц."""
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    month_start = date(year, m, 1)
    month_end = date(year, m, last_day)

    # Загружаем визиты с локациями
    stmt = (
        select(VisitLog)
        .where(
            VisitLog.visited_date >= month_start,
            VisitLog.visited_date <= month_end,
        )
        .options(selectinload(VisitLog.location))
    )
    result = await session.execute(stmt)
    visits = result.scalars().all()

    unique_locs = {v.location_id for v in visits}
    unique_reps = {v.rep_id for v in visits}

    # По категориям
    by_cat: dict = defaultdict(int)
    by_rep_map: dict = defaultdict(lambda: {"visits": 0, "locs": set()})

    for v in visits:
        cat = v.location.category if v.location else "?"
        by_cat[cat] += 1
        by_rep_map[v.rep_id]["visits"] += 1
        by_rep_map[v.rep_id]["locs"].add(v.location_id)

    by_rep_list = [
        {
            "rep_id": rep_id,
            "total_visits": data["visits"],
            "unique_locations": len(data["locs"]),
        }
        for rep_id, data in by_rep_map.items()
    ]

    return VisitStats(
        month=month,
        total_visits=len(visits),
        unique_locations=len(unique_locs),
        unique_reps=len(unique_reps),
        by_category=dict(by_cat),
        by_rep=by_rep_list,
    )


@router.get("/", response_model=List[VisitResponse])
async def list_visits(
    month: str = Query(..., description="Месяц YYYY-MM"),
    rep_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """История фактических визитов с фильтрами."""
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    stmt = select(VisitLog).where(
        VisitLog.visited_date >= date(year, m, 1),
        VisitLog.visited_date <= date(year, m, last_day),
    )
    if rep_id:
        stmt = stmt.where(VisitLog.rep_id == rep_id)
    stmt = stmt.order_by(VisitLog.visited_date)

    result = await session.execute(stmt)
    return result.scalars().all()
