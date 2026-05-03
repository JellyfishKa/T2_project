from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    ForceMajeureEvent,
    Location,
    SalesRep,
    VisitLog,
    VisitSchedule,
    get_session,
)

router = APIRouter(tags=["Insights"])


@router.get("/insights")
async def get_insights(
    month: str = Query(
        None,
        description="Месяц YYYY-MM. По умолчанию — текущий месяц",
    ),
    session: AsyncSession = Depends(get_session),
):
    """
    Реальная аналитика по торговым точкам, сотрудникам и визитам.

    Возвращает:
    - Общее кол-во ТТ и % охвата
    - Визиты план/факт за месяц
    - Разбивку по категориям A/B/C/D
    - Покрытие по районам
    - Активность сотрудников
    - Кол-во форс-мажоров за месяц
    """
    # --- Определяем период ---
    now = datetime.now(timezone.utc)
    if month:
        try:
            year, m = map(int, month.split("-"))
        except ValueError:
            year, m = now.year, now.month
    else:
        year, m = now.year, now.month

    _, last_day = monthrange(year, m)
    month_start = date(year, m, 1)
    month_end = date(year, m, last_day)
    month_str = f"{year:04d}-{m:02d}"

    # --- Все ТТ ---
    loc_result = await session.execute(select(Location))
    all_locations = loc_result.scalars().all()
    total_tt = len(all_locations)

    # Мап location_id → category/district
    loc_map = {loc.id: loc for loc in all_locations}

    # --- Плановые визиты за месяц ---
    sched_stmt = select(VisitSchedule).where(
        VisitSchedule.planned_date >= month_start,
        VisitSchedule.planned_date <= month_end,
    )
    sched_result = await session.execute(sched_stmt)
    schedules = sched_result.scalars().all()
    total_planned = len(schedules)

    # --- Фактические визиты за месяц ---
    visit_stmt = (
        select(VisitLog)
        .where(
            VisitLog.visited_date >= month_start,
            VisitLog.visited_date <= month_end,
        )
        .options(selectinload(VisitLog.rep))
    )
    visit_result = await session.execute(visit_stmt)
    visits = visit_result.scalars().all()
    total_completed = len(visits)

    completion_rate = (
        round(total_completed / total_planned * 100, 1) if total_planned else 0.0
    )

    # --- % охвата ТТ (хотя бы 1 плановый визит в месяце) ---
    planned_loc_ids = {s.location_id for s in schedules}
    coverage_pct = round(len(planned_loc_ids) / total_tt * 100, 1) if total_tt else 0.0

    # --- По категориям ---
    cat_totals = defaultdict(int)
    cat_planned = defaultdict(int)
    cat_completed = defaultdict(set)  # set location_ids

    for loc in all_locations:
        cat = loc.category or "?"
        cat_totals[cat] += 1

    for sched in schedules:
        cat = loc_map.get(sched.location_id, None)
        if cat:
            cat_planned[cat.category or "?"] += 1

    for visit in visits:
        loc = loc_map.get(visit.location_id)
        if loc:
            cat_completed[loc.category or "?"].add(visit.location_id)

    by_category = {}
    for cat in ["A", "B", "C", "D"]:
        total_c = cat_totals.get(cat, 0)
        planned_c = cat_planned.get(cat, 0)
        completed_c = len(cat_completed.get(cat, set()))
        by_category[cat] = {
            "total": total_c,
            "planned": planned_c,
            "completed": completed_c,
            "pct": round(completed_c / total_c * 100, 1) if total_c else 0.0,
        }

    # --- По районам ---
    district_totals: dict = defaultdict(int)
    district_planned_locs: dict = defaultdict(set)

    for loc in all_locations:
        dist = loc.district or "Неизвестно"
        district_totals[dist] += 1

    for sched in schedules:
        loc = loc_map.get(sched.location_id)
        if loc:
            dist = loc.district or "Неизвестно"
            district_planned_locs[dist].add(sched.location_id)

    by_district = [
        {
            "district": dist,
            "total": district_totals[dist],
            "coverage_pct": round(
                len(district_planned_locs.get(dist, set())) / district_totals[dist] * 100, 1
            ),
        }
        for dist in sorted(district_totals.keys())
    ]

    # --- Активность сотрудников ---
    rep_result = await session.execute(select(SalesRep))
    all_reps = rep_result.scalars().all()
    rep_map = {r.id: r.name for r in all_reps}

    rep_outings: dict = defaultdict(set)   # rep_id → set of dates
    rep_locs: dict = defaultdict(set)      # rep_id → set of location_ids

    for visit in visits:
        rep_outings[visit.rep_id].add(visit.visited_date)
        rep_locs[visit.rep_id].add(visit.location_id)

    rep_activity = [
        {
            "rep_id": rep_id,
            "rep_name": rep_map.get(rep_id, rep_id),
            "outings_count": len(dates),
            "tt_visited": len(rep_locs[rep_id]),
        }
        for rep_id, dates in rep_outings.items()
    ]

    # --- Форс-мажоры за месяц ---
    fm_stmt = select(ForceMajeureEvent).where(
        ForceMajeureEvent.event_date >= month_start,
        ForceMajeureEvent.event_date <= month_end,
    )
    fm_result = await session.execute(fm_stmt)
    fm_count = len(fm_result.scalars().all())

    return {
        "month": month_str,
        "total_tt": total_tt,
        "coverage_pct": coverage_pct,
        "visits_this_month": {
            "planned": total_planned,
            "completed": total_completed,
            "completion_rate": completion_rate,
        },
        "by_category": by_category,
        "by_district": by_district,
        "rep_activity": rep_activity,
        "force_majeure_count": fm_count,
    }
