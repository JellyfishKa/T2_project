from calendar import monthrange
from collections import defaultdict
from datetime import date, time, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Location, SalesRep, VisitLog, VisitSchedule, get_session
from src.schemas.schedule import (
    DailyRoute,
    GenerateScheduleRequest,
    MonthlyPlan,
    VisitScheduleItem,
    VisitStatusUpdate,
)
from src.services.schedule_planner import (
    AVG_TRAVEL_MIN_PER_TT,
    MAX_TT_PER_DAY,
    VISIT_DURATION_MIN,
    SchedulePlanner,
)

router = APIRouter(prefix="/schedule", tags=["Schedule"])

LUNCH_BREAK_TIME = "13:00"  # фиксированный обед


async def _load_logs_by_schedule(
    session: AsyncSession, schedule_ids: List[str]
) -> Dict[str, VisitLog]:
    """Загружает VisitLog-записи для переданных schedule_id одним запросом."""
    if not schedule_ids:
        return {}
    result = await session.execute(
        select(VisitLog).where(VisitLog.schedule_id.in_(schedule_ids))
    )
    return {log.schedule_id: log for log in result.scalars().all()}


def _estimated_duration(visit_count: int) -> float:
    """Расчёт длительности маршрута в часах."""
    return round(visit_count * (VISIT_DURATION_MIN + AVG_TRAVEL_MIN_PER_TT) / 60, 1)


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


@router.patch("/{visit_id}", response_model=VisitScheduleItem)
async def update_visit_status(
    visit_id: str,
    data: VisitStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Обновить статус визита и зафиксировать время прихода/ухода.

    - status="completed" + time_in/time_out → создаёт запись в visit_log
    - status="skipped" → обновляет статус + автоматически создаёт новый визит
      на ближайший доступный день (требование: 100% охват базы ТТ)
    - status="cancelled" → только обновляет статус
    """
    sched = await session.get(
        VisitSchedule,
        visit_id,
        options=[
            selectinload(VisitSchedule.location),
            selectinload(VisitSchedule.rep),
        ],
    )
    if not sched:
        raise HTTPException(status_code=404, detail="Визит не найден")

    sched.status = data.status

    if data.status == "completed":
        def _parse_time(t: Optional[str]) -> Optional[time]:
            if not t:
                return None
            try:
                return time.fromisoformat(t)
            except ValueError:
                return None

        log = VisitLog(
            schedule_id=sched.id,
            location_id=sched.location_id,
            rep_id=sched.rep_id,
            visited_date=sched.planned_date,
            time_in=_parse_time(data.time_in),
            time_out=_parse_time(data.time_out),
            notes=data.notes,
        )
        session.add(log)

    elif data.status == "skipped":
        # ── Автоматический перенос пропущенной ТТ ─────────────────────────────
        # Конкурсное требование: гарантия 100% охвата базы ТТ, включая механизм
        # добавления ТТ из пройденного маршрута в случае, если точка не работала.
        await _reschedule_skipped_visit(session, sched)

    await session.commit()
    await session.refresh(sched, ["location", "rep"])
    # Загружаем связанный VisitLog чтобы вернуть time_in/time_out
    visit_log = None
    if sched.status == "completed":
        log_result = await session.execute(
            select(VisitLog).where(VisitLog.schedule_id == sched.id)
        )
        visit_log = log_result.scalars().first()
    return _schedule_to_item(sched, visit_log)


async def _reschedule_skipped_visit(
    session: AsyncSession,
    skipped: VisitSchedule,
) -> None:
    """
    Создаёт новую запись в расписании для пропущенной ТТ на ближайший
    доступный день. Пытается назначить тому же сотруднику; если у него нет
    свободных слотов в ближайшие 30 дней — назначает любому активному.
    """
    import logging
    import uuid as uuid_mod
    log = logging.getLogger("schedule")

    start_from = skipped.planned_date + timedelta(days=1)

    async def _find_slot(rep_id: str) -> Optional[date]:
        candidate = start_from
        for _ in range(30):
            if candidate.weekday() >= 5:
                candidate += timedelta(days=1)
                continue
            count_q = select(VisitSchedule).where(
                VisitSchedule.rep_id == rep_id,
                VisitSchedule.planned_date == candidate,
                VisitSchedule.status.in_(["planned", "rescheduled"]),
            )
            cnt = len((await session.execute(count_q)).scalars().all())
            if cnt < MAX_TT_PER_DAY:
                return candidate
            candidate += timedelta(days=1)
        return None

    target_rep_id = skipped.rep_id
    target_date = await _find_slot(target_rep_id)

    if target_date is None:
        # Нет слота у исходного сотрудника — ищем любого активного
        reps_q = select(SalesRep).where(
            SalesRep.status == "active",
            SalesRep.id != target_rep_id,
        )
        active_reps = (await session.execute(reps_q)).scalars().all()
        for rep in active_reps:
            d = await _find_slot(rep.id)
            if d is not None:
                target_rep_id = rep.id
                target_date = d
                break

    if target_date is None:
        log.warning(
            "Не удалось найти слот для переноса ТТ %s после пропуска",
            skipped.location_id,
        )
        return

    session.add(VisitSchedule(
        id=str(uuid_mod.uuid4()),
        location_id=skipped.location_id,
        rep_id=target_rep_id,
        planned_date=target_date,
        status="rescheduled",
    ))
    log.info(
        "ТТ %s перенесена на %s (сотрудник %s) после пропуска",
        skipped.location_id,
        target_date,
        target_rep_id,
    )


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

    schedule_ids = [s.id for s in schedules]
    logs_by_schedule = await _load_logs_by_schedule(session, schedule_ids)

    by_rep = defaultdict(list)
    for s in schedules:
        by_rep[s.rep_id].append(s)

    routes: List[DailyRoute] = []
    for rep_id, rep_schedules in by_rep.items():
        rep = rep_schedules[0].rep
        visits = [_schedule_to_item(s, logs_by_schedule.get(s.id)) for s in rep_schedules]
        routes.append(DailyRoute(
            rep_id=rep_id,
            rep_name=rep.name if rep else rep_id,
            date=target_date,
            visits=visits,
            total_tt=len(visits),
            estimated_duration_hours=_estimated_duration(len(visits)),
            lunch_break_at=LUNCH_BREAK_TIME,
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

    # Загружаем VisitLog для всех найденных визитов одним запросом
    schedule_ids = [s.id for s in schedules]
    logs_by_schedule = await _load_logs_by_schedule(session, schedule_ids)

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
            visits = [_schedule_to_item(s, logs_by_schedule.get(s.id)) for s in day_schedules]
            routes.append(DailyRoute(
                rep_id=r_id,
                rep_name=rep.name if rep else r_id,
                date=d,
                visits=visits,
                total_tt=len(visits),
                estimated_duration_hours=_estimated_duration(len(visits)),
                lunch_break_at=LUNCH_BREAK_TIME,
            ))

    planned_locs = {s.location_id for s in schedules}
    coverage_pct = round(len(planned_locs) / total_tt * 100, 1) if total_tt else 0.0

    return MonthlyPlan(
        month=month,
        total_tt_planned=len(planned_locs),
        coverage_pct=coverage_pct,
        routes=routes,
    )


def _schedule_to_item(s: VisitSchedule, log: Optional[VisitLog] = None) -> VisitScheduleItem:
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
        time_in=str(log.time_in)[:5] if log and log.time_in else None,
        time_out=str(log.time_out)[:5] if log and log.time_out else None,
    )
