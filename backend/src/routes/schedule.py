import json
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    AuditLog,
    DailyRouteOverride,
    Holiday,
    Location,
    SalesRep,
    SkippedVisitStash,
    VisitLog,
    VisitSchedule,
    get_session,
)
from src.schemas.schedule import (
    DayRouteOverrideRequest,
    DailyRoute,
    GenerateScheduleRequest,
    MonthlyPlan,
    ResolveAIRequest,
    ResolveManualRequest,
    SkippedStashItem,
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

# ── Машина состояний визита ──────────────────────────────────────────────────
VALID_TRANSITIONS: Dict[str, set] = {
    "planned":     {"completed", "skipped", "cancelled", "rescheduled"},
    "skipped":     {"planned", "cancelled"},
    "rescheduled": {"completed", "skipped", "cancelled"},
    "completed":   set(),
    "cancelled":   set(),
}

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
    force: bool = Query(False, description="Если true — удалить существующие planned и создать заново"),
    session: AsyncSession = Depends(get_session),
):
    """Сгенерировать план визитов на месяц."""
    # Защита от дублирования: проверяем наличие planned-визитов за месяц
    try:
        year, m = map(int, req.month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")
    _, last_day = monthrange(year, m)
    month_start = date(year, m, 1)
    month_end = date(year, m, last_day)

    existing_q = await session.execute(
        select(func.count()).where(
            VisitSchedule.planned_date.between(month_start, month_end),
            VisitSchedule.status == "planned",
        )
    )
    existing_count = existing_q.scalar() or 0

    if existing_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Расписание на {req.month} уже существует ({existing_count} плановых визитов). "
                           "Используйте ?force=true для перегенерации.",
                "existing_count": existing_count,
            },
        )

    if existing_count > 0 and force:
        # Удаляем существующие planned-визиты за этот месяц
        planned_q = await session.execute(
            select(VisitSchedule).where(
                VisitSchedule.planned_date.between(month_start, month_end),
                VisitSchedule.status == "planned",
            )
        )
        for vs in planned_q.scalars().all():
            await session.delete(vs)
        await session.flush()

    # Загружаем нерабочие праздники из БД за этот месяц
    holidays_q = await session.execute(
        select(Holiday.date).where(
            Holiday.date.between(month_start, month_end),
            Holiday.is_working.is_(False),
        )
    )
    non_working = set(holidays_q.scalars().all())

    planner = SchedulePlanner(session, non_working_dates=non_working)
    result = await planner.build_monthly_plan(req.month, req.rep_ids)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # AuditLog: генерация расписания
    audit = AuditLog(
        action="schedule_generated",
        table_name="visit_schedule",
        record_id=req.month,
        new_value=json.dumps({
            "month": req.month,
            "total_visits_planned": result.get("total_visits_planned"),
            "coverage_pct": result.get("coverage_pct"),
            "forced": force,
        }, ensure_ascii=False),
    )
    session.add(audit)
    await session.commit()

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

    # ── Проверка машины состояний ────────────────────────────────────────────
    current_status = sched.status
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Переход {current_status!r} → {data.status!r} не разрешён.",
                "current_status": current_status,
                "requested_status": data.status,
                "allowed_transitions": sorted(allowed),
            },
        )

    old_status = sched.status
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
        # ── Добавляем в стеш для ручного перераспределения ───────────────────
        await _add_to_skipped_stash(session, sched)

    # AuditLog: смена статуса визита
    audit = AuditLog(
        action="visit_status_change",
        table_name="visit_schedule",
        record_id=sched.id,
        old_value=json.dumps({"status": old_status}, ensure_ascii=False),
        new_value=json.dumps({"status": data.status}, ensure_ascii=False),
        details=json.dumps({
            "location_id": sched.location_id,
            "rep_id": sched.rep_id,
            "planned_date": str(sched.planned_date),
        }, ensure_ascii=False),
    )
    session.add(audit)

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
    from src.services.schedule_planner import _is_working_day
    log = logging.getLogger("schedule")

    start_from = skipped.planned_date + timedelta(days=1)
    lookahead_end = start_from + timedelta(days=60)

    # Загружаем нерабочие праздники на период поиска
    holidays_q = await session.execute(
        select(Holiday.date).where(
            Holiday.date.between(start_from, lookahead_end),
            Holiday.is_working.is_(False),
        )
    )
    non_working = frozenset(holidays_q.scalars().all())

    async def _find_slot(rep_id: str) -> Optional[date]:
        candidate = start_from
        for _ in range(60):
            if not _is_working_day(candidate, non_working):
                candidate += timedelta(days=1)
                continue
            count_q = select(func.count()).where(
                VisitSchedule.rep_id == rep_id,
                VisitSchedule.planned_date == candidate,
                VisitSchedule.status.in_(["planned", "rescheduled"]),
            )
            cnt = (await session.execute(count_q)).scalar() or 0
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


async def _add_to_skipped_stash(
    session: AsyncSession,
    sched: VisitSchedule,
) -> None:
    """Добавляет пропущенный визит в стеш для ручного перераспределения."""
    entry = SkippedVisitStash(
        visit_schedule_id=sched.id,
        location_id=sched.location_id,
        rep_id=sched.rep_id,
        original_date=sched.planned_date,
    )
    session.add(entry)


# ── Стеш пропущенных визитов ──────────────────────────────────────────────────

def _stash_to_item(entry: SkippedVisitStash) -> SkippedStashItem:
    loc_name = entry.location.name if entry.location else entry.location_id
    loc_cat = entry.location.category if entry.location else None
    rep_name = entry.rep.name if entry.rep else entry.rep_id
    return SkippedStashItem(
        id=entry.id,
        visit_schedule_id=entry.visit_schedule_id,
        location_id=entry.location_id,
        location_name=loc_name,
        location_category=loc_cat,
        rep_id=entry.rep_id,
        rep_name=rep_name,
        original_date=entry.original_date,
        resolution=entry.resolution,
        resolved_at=entry.resolved_at,
        created_at=entry.created_at,
    )


@router.get("/stash", response_model=List[SkippedStashItem])
async def list_stash(
    session: AsyncSession = Depends(get_session),
):
    """Список пропущенных визитов, ожидающих перераспределения."""
    from sqlalchemy.orm import selectinload as sil
    stmt = (
        select(SkippedVisitStash)
        .where(SkippedVisitStash.resolution.is_(None))
        .options(sil(SkippedVisitStash.location), sil(SkippedVisitStash.rep))
        .order_by(SkippedVisitStash.original_date, SkippedVisitStash.created_at)
    )
    result = await session.execute(stmt)
    return [_stash_to_item(e) for e in result.scalars().all()]


@router.post("/stash/{stash_id}/resolve/manual", response_model=SkippedStashItem)
async def resolve_stash_manual(
    stash_id: str,
    payload: ResolveManualRequest,
    session: AsyncSession = Depends(get_session),
):
    """Ручное назначение: создаёт rescheduled-визит на указанную дату/сотрудника."""
    import uuid as uuid_mod
    from sqlalchemy.orm import selectinload as sil
    from datetime import timezone as tz

    entry = await session.get(
        SkippedVisitStash,
        stash_id,
        options=[sil(SkippedVisitStash.location), sil(SkippedVisitStash.rep)],
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись стеша не найдена")
    if entry.resolution is not None:
        raise HTTPException(status_code=409, detail="Запись уже решена")

    new_sched = VisitSchedule(
        id=str(uuid_mod.uuid4()),
        location_id=entry.location_id,
        rep_id=payload.rep_id,
        planned_date=payload.target_date,
        status="rescheduled",
    )
    session.add(new_sched)
    await session.flush()

    entry.resolution = "manual"
    entry.resolved_at = datetime.now(tz.utc)
    entry.resolved_schedule_id = new_sched.id

    await session.commit()
    await session.refresh(entry)
    return _stash_to_item(entry)


@router.post("/stash/{stash_id}/resolve/carry_over", response_model=SkippedStashItem)
async def resolve_stash_carry_over(
    stash_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Авто-перенос: использует существующую логику _reschedule_skipped_visit."""
    from sqlalchemy.orm import selectinload as sil
    from datetime import timezone as tz

    entry = await session.get(
        SkippedVisitStash,
        stash_id,
        options=[sil(SkippedVisitStash.location), sil(SkippedVisitStash.rep)],
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись стеша не найдена")
    if entry.resolution is not None:
        raise HTTPException(status_code=409, detail="Запись уже решена")

    # Создаём фиктивный VisitSchedule для переиспользования логики
    fake_sched = VisitSchedule(
        id=entry.visit_schedule_id or "",
        location_id=entry.location_id,
        rep_id=entry.rep_id,
        planned_date=entry.original_date,
        status="skipped",
    )
    await _reschedule_skipped_visit(session, fake_sched)
    await session.flush()

    entry.resolution = "carry_over"
    entry.resolved_at = datetime.now(tz.utc)

    await session.commit()
    await session.refresh(entry)
    return _stash_to_item(entry)


@router.post("/stash/resolve/ai", response_model=List[SkippedStashItem])
async def resolve_stash_ai(
    payload: ResolveAIRequest,
    session: AsyncSession = Depends(get_session),
):
    """Перераспределение через ИИ (round-robin по активным сотрудникам)."""
    from sqlalchemy.orm import selectinload as sil
    from datetime import timezone as tz
    from src.services.force_majeure_service import ForceMajeureService, _chunked_round_robin

    if not payload.stash_ids:
        return []

    stmt = (
        select(SkippedVisitStash)
        .where(
            SkippedVisitStash.id.in_(payload.stash_ids),
            SkippedVisitStash.resolution.is_(None),
        )
        .options(sil(SkippedVisitStash.location), sil(SkippedVisitStash.rep))
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    if not entries:
        return []

    # Загружаем активных сотрудников
    reps_q = select(SalesRep).where(SalesRep.status == "active")
    active_reps = (await session.execute(reps_q)).scalars().all()
    if not active_reps:
        raise HTTPException(status_code=422, detail="Нет активных сотрудников для перераспределения")

    service = ForceMajeureService(session)
    loc_ids = [e.location_id for e in entries]
    chunks = _chunked_round_robin(loc_ids, len(active_reps))

    loc_to_entry = {e.location_id: e for e in entries}
    import uuid as uuid_mod

    for target_rep, chunk in zip(active_reps, chunks):
        for loc_id in chunk:
            entry = loc_to_entry.get(loc_id)
            if not entry:
                continue
            target_date = await service._find_available_day(
                target_rep.id, entry.original_date, chunk_size=1
            )
            new_sched = VisitSchedule(
                id=str(uuid_mod.uuid4()),
                location_id=loc_id,
                rep_id=target_rep.id,
                planned_date=target_date,
                status="rescheduled",
            )
            session.add(new_sched)
            await session.flush()
            entry.resolution = "ai"
            entry.resolved_at = datetime.now(tz.utc)
            entry.resolved_schedule_id = new_sched.id

    await session.commit()
    for e in entries:
        await session.refresh(e)
    return [_stash_to_item(e) for e in entries]


@router.delete("/stash/{stash_id}", status_code=204)
async def discard_stash_entry(
    stash_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Отменить запись стеша без переноса визита."""
    from datetime import timezone as tz

    entry = await session.get(SkippedVisitStash, stash_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Запись стеша не найдена")
    entry.resolution = "discarded"
    entry.resolved_at = datetime.now(tz.utc)
    await session.commit()


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
        .order_by(VisitSchedule.rep_id, VisitSchedule.created_at, VisitSchedule.id)
        .options(selectinload(VisitSchedule.location), selectinload(VisitSchedule.rep))
    )
    result = await session.execute(stmt)
    schedules = result.scalars().all()

    schedule_ids = [s.id for s in schedules]
    logs_by_schedule = await _load_logs_by_schedule(session, schedule_ids)

    by_rep = defaultdict(list)
    for s in schedules:
        by_rep[s.rep_id].append(s)

    override_map = await _load_route_overrides(
        session,
        rep_ids=list(by_rep.keys()),
        start_date=target_date,
        end_date=target_date,
    )

    routes: List[DailyRoute] = []
    for rep_id, rep_schedules in by_rep.items():
        routes.append(
            _build_daily_route(
                rep_schedules,
                logs_by_schedule,
                override_map.get((rep_id, target_date)),
            )
        )
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
    from_date: Optional[str] = Query(None, description="Фильтр с даты YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="Фильтр по дату YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    """Полный план всех сотрудников на месяц с опциональной фильтрацией по датам."""
    return await _build_monthly_plan_response(session, month, from_date=from_date, to_date=to_date)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _build_monthly_plan_response(
    session: AsyncSession,
    month: str,
    rep_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> MonthlyPlan:
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    month_start = date(year, m, 1)
    month_end = date(year, m, last_day)

    # Применяем опциональные фильтры by date range
    effective_start = month_start
    effective_end = month_end
    if from_date:
        try:
            effective_start = max(month_start, date.fromisoformat(from_date))
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат from_date. Используй YYYY-MM-DD")
    if to_date:
        try:
            effective_end = min(month_end, date.fromisoformat(to_date))
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат to_date. Используй YYYY-MM-DD")

    stmt = (
        select(VisitSchedule)
        .where(
            VisitSchedule.planned_date >= effective_start,
            VisitSchedule.planned_date <= effective_end,
        )
        .order_by(VisitSchedule.planned_date, VisitSchedule.rep_id, VisitSchedule.created_at, VisitSchedule.id)
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
    total_tt_result = await session.execute(select(func.count()).select_from(Location))
    total_tt = total_tt_result.scalar() or 0

    by_rep_date = defaultdict(lambda: defaultdict(list))
    for s in schedules:
        by_rep_date[s.rep_id][s.planned_date].append(s)

    override_map = await _load_route_overrides(
        session,
        rep_ids=list(by_rep_date.keys()),
        start_date=effective_start,
        end_date=effective_end,
    )

    routes: List[DailyRoute] = []
    for r_id, date_map in by_rep_date.items():
        for d, day_schedules in sorted(date_map.items()):
            routes.append(
                _build_daily_route(
                    day_schedules,
                    logs_by_schedule,
                    override_map.get((r_id, d)),
                )
            )

    planned_locs = {s.location_id for s in schedules}
    coverage_pct = round(len(planned_locs) / total_tt * 100, 1) if total_tt else 0.0

    return MonthlyPlan(
        month=month,
        total_tt_planned=len(planned_locs),
        coverage_pct=coverage_pct,
        routes=routes,
    )


@router.put("/day-route", response_model=DailyRoute)
async def save_day_route_override(
    payload: DayRouteOverrideRequest,
    session: AsyncSession = Depends(get_session),
):
    schedules = await _load_schedules_for_rep_day(session, payload.rep_id, payload.date)
    if not schedules:
        raise HTTPException(status_code=404, detail="Маршрут дня не найден")

    schedule_location_ids = [s.location_id for s in schedules]
    if set(schedule_location_ids) != set(payload.location_ids):
        raise HTTPException(
            status_code=422,
            detail="Набор точек маршрута не совпадает с расписанием дня",
        )

    existing_override = await _get_route_override(session, payload.rep_id, payload.date)
    original_location_ids = (
        payload.original_location_ids
        if payload.original_location_ids
        else (
            existing_override.original_location_order
            if existing_override and existing_override.original_location_order
            else schedule_location_ids
        )
    )

    if existing_override:
        existing_override.current_location_order = payload.location_ids
        existing_override.original_location_order = original_location_ids
        existing_override.source = payload.source
        existing_override.label = payload.label
        existing_override.updated_at = datetime.now(timezone.utc)
        override = existing_override
    else:
        override = DailyRouteOverride(
            rep_id=payload.rep_id,
            route_date=payload.date,
            original_location_order=original_location_ids,
            current_location_order=payload.location_ids,
            source=payload.source,
            label=payload.label,
        )
        session.add(override)

    session.add(
        AuditLog(
            action="day_route_override_saved",
            table_name="daily_route_overrides",
            record_id=f"{payload.rep_id}:{payload.date}",
            old_value=json.dumps({
                "original_location_ids": schedule_location_ids,
            }, ensure_ascii=False),
            new_value=json.dumps({
                "location_ids": payload.location_ids,
                "source": payload.source,
                "label": payload.label,
            }, ensure_ascii=False),
        )
    )

    await session.commit()
    return await _build_daily_route_response(session, payload.rep_id, payload.date)


@router.delete("/day-route", response_model=DailyRoute)
async def revert_day_route_override(
    rep_id: str = Query(...),
    date_str: str = Query(..., alias="date"),
    session: AsyncSession = Depends(get_session),
):
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используй YYYY-MM-DD")

    override = await _get_route_override(session, rep_id, target_date)
    if override is None:
        raise HTTPException(status_code=404, detail="Переопределение маршрута не найдено")

    session.add(
        AuditLog(
            action="day_route_override_reverted",
            table_name="daily_route_overrides",
            record_id=f"{rep_id}:{target_date}",
            old_value=json.dumps({
                "location_ids": override.current_location_order,
                "source": override.source,
                "label": override.label,
            }, ensure_ascii=False),
            new_value=json.dumps({
                "location_ids": override.original_location_order,
                "source": "generated",
            }, ensure_ascii=False),
        )
    )

    await session.delete(override)
    await session.commit()
    return await _build_daily_route_response(session, rep_id, target_date)


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


async def _get_route_override(
    session: AsyncSession,
    rep_id: str,
    target_date: date,
) -> Optional[DailyRouteOverride]:
    result = await session.execute(
        select(DailyRouteOverride).where(
            DailyRouteOverride.rep_id == rep_id,
            DailyRouteOverride.route_date == target_date,
        )
    )
    return result.scalars().first()


async def _load_route_overrides(
    session: AsyncSession,
    rep_ids: List[str],
    start_date: date,
    end_date: date,
) -> Dict[tuple[str, date], DailyRouteOverride]:
    if not rep_ids:
        return {}
    result = await session.execute(
        select(DailyRouteOverride).where(
            DailyRouteOverride.rep_id.in_(rep_ids),
            DailyRouteOverride.route_date >= start_date,
            DailyRouteOverride.route_date <= end_date,
        )
    )
    overrides = result.scalars().all()
    return {(override.rep_id, override.route_date): override for override in overrides}


async def _load_schedules_for_rep_day(
    session: AsyncSession,
    rep_id: str,
    target_date: date,
) -> List[VisitSchedule]:
    result = await session.execute(
        select(VisitSchedule)
        .where(
            VisitSchedule.rep_id == rep_id,
            VisitSchedule.planned_date == target_date,
        )
        .order_by(VisitSchedule.created_at, VisitSchedule.id)
        .options(selectinload(VisitSchedule.location), selectinload(VisitSchedule.rep))
    )
    return result.scalars().all()


async def _build_daily_route_response(
    session: AsyncSession,
    rep_id: str,
    target_date: date,
) -> DailyRoute:
    schedules = await _load_schedules_for_rep_day(session, rep_id, target_date)
    if not schedules:
        raise HTTPException(status_code=404, detail="Маршрут дня не найден")

    logs_by_schedule = await _load_logs_by_schedule(session, [s.id for s in schedules])
    override = await _get_route_override(session, rep_id, target_date)
    return _build_daily_route(schedules, logs_by_schedule, override)


def _sort_schedules_by_location_order(
    schedules: List[VisitSchedule],
    location_order: List[str],
) -> List[VisitSchedule]:
    order_index = {location_id: index for index, location_id in enumerate(location_order)}
    with_known_order = []
    without_order = []

    for idx, schedule in enumerate(schedules):
        if schedule.location_id in order_index:
            with_known_order.append(schedule)
        else:
            without_order.append((idx, schedule))

    with_known_order.sort(key=lambda schedule: order_index[schedule.location_id])
    without_order.sort(key=lambda item: item[0])

    return with_known_order + [schedule for _, schedule in without_order]


def _build_daily_route(
    schedules: List[VisitSchedule],
    logs_by_schedule: Dict[str, VisitLog],
    override: Optional[DailyRouteOverride],
) -> DailyRoute:
    if not schedules:
        raise HTTPException(status_code=404, detail="Маршрут дня не найден")

    rep = schedules[0].rep
    target_date = schedules[0].planned_date
    original_location_ids = [schedule.location_id for schedule in schedules]
    active_location_order = (
        override.current_location_order
        if override and override.current_location_order
        else original_location_ids
    )
    sorted_schedules = _sort_schedules_by_location_order(schedules, active_location_order)
    visits = [_schedule_to_item(schedule, logs_by_schedule.get(schedule.id)) for schedule in sorted_schedules]

    return DailyRoute(
        rep_id=schedules[0].rep_id,
        rep_name=rep.name if rep else schedules[0].rep_id,
        date=target_date,
        visits=visits,
        current_location_ids=[schedule.location_id for schedule in sorted_schedules],
        original_location_ids=(
            override.original_location_order
            if override and override.original_location_order
            else original_location_ids
        ),
        route_source=override.source if override else "generated",
        route_label=override.label if override else None,
        route_updated_at=override.updated_at if override else None,
        has_route_override=override is not None,
        total_tt=len(visits),
        estimated_duration_hours=_estimated_duration(len(visits)),
        lunch_break_at=LUNCH_BREAK_TIME,
    )
