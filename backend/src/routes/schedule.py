from calendar import monthrange
from collections import defaultdict
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Location, VisitSchedule, get_session
from src.schemas.schedule import (
    DailyRoute,
    GenerateScheduleRequest,
    MonthlyPlan,
    VisitScheduleItem,
)
from src.services.schedule_planner import VISIT_DURATION_MIN, SchedulePlanner

router = APIRouter(prefix="/schedule", tags=["Schedule"])

VISIT_DURATION_HOURS = VISIT_DURATION_MIN / 60


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_schedule(
    req: GenerateScheduleRequest,
    session: AsyncSession = Depends(get_session),
):
    """Сгенерировать план визитов на месяц."""
    planner = SchedulePlanner(session)
    result = await planner.build_monthly_plan(req.month, req.rep_ids)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/daily", response_model=List[DailyRoute])
async def get_daily_schedule(
    date_str: str = Query(..., alias="date", description="Дата YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    """Маршруты всех сотрудников на конкретный день."""
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используй YYYY-MM-DD")

    stmt = (
        select(VisitSchedule)
        .where(VisitSchedule.planned_date == target_date)
        .options(selectinload(VisitSchedule.location), selectinload(VisitSchedule.rep))
    )
    result = await session.execute(stmt)
    schedules = result.scalars().all()

    by_rep = defaultdict(list)
    for s in schedules:
        by_rep[s.rep_id].append(s)

    routes: List[DailyRoute] = []
    for rep_id, rep_schedules in by_rep.items():
        rep = rep_schedules[0].rep
        visits = [_schedule_to_item(s) for s in rep_schedules]
        routes.append(DailyRoute(
            rep_id=rep_id,
            rep_name=rep.name if rep else rep_id,
            date=target_date,
            visits=visits,
            total_tt=len(visits),
            estimated_duration_hours=round(len(visits) * VISIT_DURATION_HOURS * 2, 2),
        ))
    return routes


@router.get("/{rep_id}", response_model=MonthlyPlan)
async def get_rep_schedule(
    rep_id: str,
    month: str = Query(..., description="Месяц YYYY-MM"),
    session: AsyncSession = Depends(get_session),
):
    """План конкретного сотрудника на месяц."""
    return await _build_monthly_plan_response(session, month, rep_id=rep_id)


@router.get("/", response_model=MonthlyPlan)
async def get_monthly_schedule(
    month: str = Query(..., description="Месяц YYYY-MM"),
    session: AsyncSession = Depends(get_session),
):
    """Полный план всех сотрудников на месяц."""
    return await _build_monthly_plan_response(session, month)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _build_monthly_plan_response(
    session: AsyncSession,
    month: str,
    rep_id: Optional[str] = None,
) -> MonthlyPlan:
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    month_start = date(year, m, 1)
    month_end = date(year, m, last_day)

    stmt = (
        select(VisitSchedule)
        .where(
            VisitSchedule.planned_date >= month_start,
            VisitSchedule.planned_date <= month_end,
        )
        .options(selectinload(VisitSchedule.location), selectinload(VisitSchedule.rep))
    )
    if rep_id:
        stmt = stmt.where(VisitSchedule.rep_id == rep_id)

    result = await session.execute(stmt)
    schedules = result.scalars().all()

    # Количество всех ТТ для расчёта покрытия
    total_tt_result = await session.execute(select(Location))
    total_tt = len(total_tt_result.scalars().all())

    by_rep_date = defaultdict(lambda: defaultdict(list))
    for s in schedules:
        by_rep_date[s.rep_id][s.planned_date].append(s)

    routes: List[DailyRoute] = []
    for r_id, date_map in by_rep_date.items():
        for d, day_schedules in sorted(date_map.items()):
            rep = day_schedules[0].rep
            visits = [_schedule_to_item(s) for s in day_schedules]
            routes.append(DailyRoute(
                rep_id=r_id,
                rep_name=rep.name if rep else r_id,
                date=d,
                visits=visits,
                total_tt=len(visits),
                estimated_duration_hours=round(len(visits) * VISIT_DURATION_HOURS * 2, 2),
            ))

    planned_locs = {s.location_id for s in schedules}
    coverage_pct = round(len(planned_locs) / total_tt * 100, 1) if total_tt else 0.0

    return MonthlyPlan(
        month=month,
        total_tt_planned=len(planned_locs),
        coverage_pct=coverage_pct,
        routes=routes,
    )


def _schedule_to_item(s: VisitSchedule) -> VisitScheduleItem:
    loc = s.location
    rep = s.rep
    return VisitScheduleItem(
        id=s.id,
        location_id=s.location_id,
        location_name=loc.name if loc else s.location_id,
        location_category=loc.category if loc else None,
        rep_id=s.rep_id,
        rep_name=rep.name if rep else s.rep_id,
        planned_date=s.planned_date,
        status=s.status,
    )
