import json
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
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
from src.models.geo_utils import compute_distance_matrix, compute_route_metrics, infer_category
from src.models.schedule_schemas import (
    GenerateOptimizedScheduleAccepted,
    GenerateOptimizedScheduleJobStatus,
    GenerateOptimizedScheduleRequest,
    GenerateOptimizedScheduleResult,
)
from src.services.osrm_service import osrm_trip_order
from src.services.schedule_planner import (
    AVG_TRAVEL_MIN_PER_TT,
    MAX_TT_PER_DAY,
    VISIT_DURATION_MIN,
    SchedulePlanner,
)

router = APIRouter(prefix="/schedule", tags=["Schedule"])

# ---------------------------------------------------------------------------
# T2-7: generate optimized month in one call (in-memory async jobs)
# ---------------------------------------------------------------------------

import threading

_GEN_OPT_JOBS: Dict[str, Dict] = {}
_GEN_OPT_KEYS: Dict[str, str] = {}
_GEN_OPT_LOCK = threading.Lock()


def _gen_opt_key(req: GenerateOptimizedScheduleRequest) -> str:
    return f"{req.month.isoformat()}|{','.join(req.reps)}|tp={len(req.trade_points)}"


def _gen_opt_build(req: GenerateOptimizedScheduleRequest) -> GenerateOptimizedScheduleResult:
    """
    Heuristic round-robin scheduler: distributes trade_points across reps by day
    using nearest-neighbour ordering within each day-batch.
    """
    from src.models.geo_utils import haversine

    reps = list(req.reps)
    tps = list(req.trade_points)
    max_per_day = req.max_visits_per_day
    n_reps = len(reps)

    # Simple round-robin: assign trade_points to reps evenly
    rep_tps: Dict[str, list] = {r: [] for r in reps}
    for i, tp in enumerate(tps):
        rep_tps[reps[i % n_reps]].append(tp)

    days = []
    total_km = 0.0

    for rep_id, assigned_tps in rep_tps.items():
        # Chunk into days of max_per_day each
        for chunk_start in range(0, len(assigned_tps), max_per_day):
            chunk = assigned_tps[chunk_start:chunk_start + max_per_day]
            if not chunk:
                continue

            ids = [tp.id for tp in chunk]
            coords = [(tp.latitude, tp.longitude) for tp in chunk]

            # Try OSRM ordering; fall back to heuristic-NN
            order = osrm_trip_order(coords, osrm_url=req.osrm_url)
            if order is not None:
                routing_method = "osrm-trip"
                ids = [ids[i] for i in order]
                ordered_coords = [coords[i] for i in order]
            else:
                routing_method = "heuristic-nn"
                ordered_coords = coords

            # Compute approximate distance (haversine sum)
            dist_km = 0.0
            for j in range(1, len(ordered_coords)):
                dist_km += haversine(
                    ordered_coords[j - 1][0], ordered_coords[j - 1][1],
                    ordered_coords[j][0], ordered_coords[j][1],
                )

            total_km += dist_km
            day_offset = chunk_start // max_per_day
            # Assign sequential weekdays starting from month start
            from calendar import monthrange as _mr
            import datetime as _dt
            month_date = req.month if isinstance(req.month, _dt.date) else _dt.date.fromisoformat(str(req.month))
            candidate = _dt.date(month_date.year, month_date.month, 1)
            weekdays_found = 0
            while weekdays_found <= day_offset:
                if candidate.weekday() < 5:
                    weekdays_found += 1
                if weekdays_found <= day_offset:
                    candidate += _dt.timedelta(days=1)

            days.append(
                {
                    "rep_id": rep_id,
                    "day": candidate,
                    "trade_point_ids": ids,
                    "total_distance_km": round(dist_km, 2),
                    "routing_method": routing_method,
                }
            )

    return GenerateOptimizedScheduleResult(
        status="completed",
        month=req.month,
        reps=reps,
        created_at=datetime.now(timezone.utc),
        total_distance_km=round(total_km, 2),
        days=days,
        meta={
            "algorithm": "round-robin + heuristic-nn",
            "max_visits_per_day": req.max_visits_per_day,
        },
    )


def _gen_opt_run_job(job_id: str, req: GenerateOptimizedScheduleRequest) -> None:
    with _GEN_OPT_LOCK:
        _GEN_OPT_JOBS[job_id]["status"] = "in_progress"
    try:
        result = _gen_opt_build(req)
        with _GEN_OPT_LOCK:
            _GEN_OPT_JOBS[job_id]["status"] = "completed"
            _GEN_OPT_JOBS[job_id]["result"] = result.model_dump()
    except Exception as e:
        with _GEN_OPT_LOCK:
            _GEN_OPT_JOBS[job_id]["status"] = "failed"
            _GEN_OPT_JOBS[job_id]["error"] = str(e)
            # Remove key so user can retry without force=true (BUG-4)
            failed_key = next((k for k, v in _GEN_OPT_KEYS.items() if v == job_id), None)
            if failed_key:
                del _GEN_OPT_KEYS[failed_key]


@router.post(
    "/generate-optimized",
    response_model=GenerateOptimizedScheduleAccepted | GenerateOptimizedScheduleResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_optimized_month(req: GenerateOptimizedScheduleRequest, bg: BackgroundTasks):
    key = _gen_opt_key(req)
    with _GEN_OPT_LOCK:
        if not req.force and key in _GEN_OPT_KEYS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Schedule already generated. Use force=true to regenerate.",
            )

        job_id = str(uuid.uuid4())
        _GEN_OPT_JOBS[job_id] = {"status": "in_progress", "result": None, "error": None, "key": key}
        _GEN_OPT_KEYS[key] = job_id

    if not req.async_mode or len(req.trade_points) <= 25:
        result = _gen_opt_build(req)
        with _GEN_OPT_LOCK:
            _GEN_OPT_JOBS[job_id]["status"] = "completed"
            _GEN_OPT_JOBS[job_id]["result"] = result.model_dump()
        return result

    bg.add_task(_gen_opt_run_job, job_id, req)
    return GenerateOptimizedScheduleAccepted(status="accepted", job_id=job_id)


@router.get("/jobs/{job_id}", response_model=GenerateOptimizedScheduleJobStatus)
async def get_generate_optimized_job(job_id: str):
    row = _GEN_OPT_JOBS.get(job_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return GenerateOptimizedScheduleJobStatus(
        status=row["status"],
        job_id=job_id,
        result=row["result"],
        error=row["error"],
    )

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


def _estimate_duration_hours_from_route(
    schedules: List[VisitSchedule],
    preview_cache: Dict[tuple[str, ...], float],
    depot_lat: float = 54.1871,
    depot_lon: float = 45.1749,
) -> float:
    visit_count = len(schedules)
    if visit_count == 0:
        return 0.0
    if visit_count == 1:
        return round(VISIT_DURATION_MIN / 60, 1)

    cache_key = tuple(schedule.location_id for schedule in schedules)
    cached = preview_cache.get(cache_key)
    if cached is not None:
        return cached

    route_points = [
        {
            "ID": schedule.location_id,
            "name": schedule.location.name,
            "lat": schedule.location.lat,
            "lon": schedule.location.lon,
            "priority": infer_category(schedule.location.category or "C"),
        }
        for schedule in schedules
        if schedule.location is not None
        and schedule.location.lat is not None
        and schedule.location.lon is not None
    ]
    if len(route_points) < 2:
        fallback = _estimated_duration(visit_count)
        preview_cache[cache_key] = fallback
        return fallback

    try:
        # Apply nearest-neighbour ordering (same as schedule_planner) so
        # displayed time matches the planner's budget estimate.
        # Depot is the first point of the route
        depot_point = {
            "ID": "__depot__",
            "name": "Depot",
            "lat": depot_lat,
            "lon": depot_lon,
            "priority": "A",
        }
        all_points = [depot_point] + route_points
        matrix = compute_distance_matrix(all_points)

        visited = [False] * len(all_points)
        nn_order = [0]  # Start from depot (index 0)
        visited[0] = True

        for _ in range(len(all_points) - 1):
            cur = nn_order[-1]
            nxt = min(
                (i for i in range(len(all_points)) if not visited[i]),
                key=lambda i: matrix[cur][i],
            )
            nn_order.append(nxt)
            visited[nxt] = True

        # Remove depot from ordered_ids for metrics calculation
        ordered_ids = [all_points[i]["ID"] for i in nn_order if all_points[i]["ID"] != "__depot__"]
        _, total_time_hours, _ = compute_route_metrics(route_points, ordered_ids)
        duration_hours = round(total_time_hours, 1)
    except Exception:
        duration_hours = _estimated_duration(visit_count)

    preview_cache[cache_key] = duration_hours
    return duration_hours


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

    _ACTIVE_STATUSES = ("planned", "rescheduled", "skipped")
    existing_q = await session.execute(
        select(func.count()).where(
            VisitSchedule.planned_date.between(month_start, month_end),
            VisitSchedule.status.in_(_ACTIVE_STATUSES),
        )
    )
    existing_count = existing_q.scalar() or 0

    if existing_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Расписание на {req.month} уже существует ({existing_count} записей). "
                           "Используйте ?force=true для перегенерации.",
                "existing_count": existing_count,
            },
        )

    if existing_count > 0 and force:
        schedules_q = await session.execute(
            select(VisitSchedule).where(
                VisitSchedule.planned_date.between(month_start, month_end),
                VisitSchedule.status.in_(_ACTIVE_STATUSES),
            )
        )
        schedules_to_delete = schedules_q.scalars().all()
        schedule_ids = [vs.id for vs in schedules_to_delete]

        if schedule_ids:
            logs_q = await session.execute(
                select(VisitLog).where(VisitLog.schedule_id.in_(schedule_ids))
            )
            for log in logs_q.scalars().all():
                await session.delete(log)

        for vs in schedules_to_delete:
            await session.delete(vs)

        overrides_q = await session.execute(
            select(DailyRouteOverride).where(
                DailyRouteOverride.route_date.between(month_start, month_end)
            )
        )
        for override in overrides_q.scalars().all():
            await session.delete(override)

        stash_q = await session.execute(
            select(SkippedVisitStash).where(
                SkippedVisitStash.original_date.between(month_start, month_end)
            )
        )
        for stash_entry in stash_q.scalars().all():
            await session.delete(stash_entry)

        await session.flush()

    # Загружаем нерабочие праздники из БД за месяц + 31 день lookahead
    from datetime import timedelta as _td
    holidays_q = await session.execute(
        select(Holiday.date).where(
            Holiday.date.between(month_start, month_end + _td(days=31)),
            Holiday.is_working.is_(False),
        )
    )
    non_working = set(holidays_q.scalars().all())

    # Collect completed visits for this month so planner can skip already-done locations
    month_num = m
    completed_q = await session.execute(
        select(VisitSchedule.location_id, func.count().label("cnt"))
        .where(
            VisitSchedule.planned_date >= month_start,
            VisitSchedule.planned_date <= month_end,
            VisitSchedule.status == "completed",
            *(
                [VisitSchedule.rep_id.in_(req.rep_ids)]
                if req.rep_ids
                else []
            ),
        )
        .group_by(VisitSchedule.location_id)
    )
    completed_visits: Dict[str, int] = {
        row.location_id: row.cnt for row in completed_q.all()
    }

    planner = SchedulePlanner(session, non_working_dates=non_working)
    # Route already deleted planned/rescheduled/skipped above; skip planner's delete pass
    result = await planner.build_monthly_plan(
        req.month, req.rep_ids, overwrite=False, completed_visits=completed_visits
    )
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
) -> Optional[str]:
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
        return None

    new_id = str(uuid_mod.uuid4())
    session.add(VisitSchedule(
        id=new_id,
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
    return new_id


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
    await session.refresh(entry, ["location", "rep"])
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
    new_schedule_id = await _reschedule_skipped_visit(session, fake_sched)
    await session.flush()

    entry.resolution = "carry_over"
    entry.resolved_at = datetime.now(tz.utc)
    entry.resolved_schedule_id = new_schedule_id

    await session.commit()
    await session.refresh(entry, ["location", "rep"])
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
    import uuid as uuid_mod

    # Chunk stash entries directly (not location_ids) to handle duplicate location_ids correctly
    entry_chunks = _chunked_round_robin(list(entries), len(active_reps))

    for target_rep, chunk_entries in zip(active_reps, entry_chunks):
        for entry in chunk_entries:
            target_date = await service._find_available_day(
                target_rep.id, entry.original_date, chunk_size=1
            )
            if target_date is None:
                continue
            new_sched = VisitSchedule(
                id=str(uuid_mod.uuid4()),
                location_id=entry.location_id,
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
    preview_cache: Dict[tuple[str, ...], float] = {}
    for rep_id, rep_schedules in by_rep.items():
        routes.append(
            await _build_daily_route(
                rep_schedules,
                logs_by_schedule,
                override_map.get((rep_id, target_date)),
                preview_cache,
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

    # Только ТТ с категорией A/B/C/D — знаменатель совпадает с тем, что планирует planner
    total_tt_result = await session.execute(
        select(func.count()).select_from(Location).where(
            Location.category.in_(["A", "B", "C", "D"])
        )
    )
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
    preview_cache: Dict[tuple[str, ...], float] = {}
    for r_id, date_map in by_rep_date.items():
        for d, day_schedules in sorted(date_map.items()):
            routes.append(
                await _build_daily_route(
                    day_schedules,
                    logs_by_schedule,
                    override_map.get((r_id, d)),
                    preview_cache,
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
        time_in=log.time_in.strftime("%H:%M") if log and log.time_in else None,
        time_out=log.time_out.strftime("%H:%M") if log and log.time_out else None,
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
    return await _build_daily_route(
        schedules,
        logs_by_schedule,
        override,
        {},
    )


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


async def _build_daily_route(
    schedules: List[VisitSchedule],
    logs_by_schedule: Dict[str, VisitLog],
    override: Optional[DailyRouteOverride],
    preview_cache: Optional[Dict[tuple[str, ...], float]] = None,
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
    route_duration_hours = _estimate_duration_hours_from_route(
        sorted_schedules,
        preview_cache if preview_cache is not None else {},
        depot_lat=getattr(rep, 'home_lat', 54.1871),
        depot_lon=getattr(rep, 'home_lon', 45.1749),
    )

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
        estimated_duration_hours=route_duration_hours,
        lunch_break_at=LUNCH_BREAK_TIME,
    )
