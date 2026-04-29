
import logging
import math
from collections import defaultdict
from datetime import date, time, timedelta
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    DailyRouteOverride,
    ForceMajeureEvent,
    Holiday,
    Location,
    SalesRep,
    VisitSchedule,
)
from src.services.schedule_planner import (
    AVG_TRAVEL_MIN_PER_TT,
    MAX_ROUTE_HOURS_PER_DAY,
    MAX_TT_PER_DAY,
    VISIT_DURATION_MIN,
    _estimate_route_hours,
)

logger = logging.getLogger("force_majeure")

WORK_START_HOUR = 9  # 09:00
SLOT_MINUTES = VISIT_DURATION_MIN + AVG_TRAVEL_MIN_PER_TT  # 35


def _estimated_visit_time(visit_index: int) -> time:
    """Оценочное время начала визита по его порядковому номеру (0-based).
    Визит 0 → 09:00, визит 1 → 09:35, визит N → 09:00 + N*35 мин.
    """
    total_minutes = WORK_START_HOUR * 60 + visit_index * SLOT_MINUTES
    h, m = divmod(total_minutes, 60)
    return time(hour=h % 24, minute=m)


def _next_working_day(d: date, non_working: FrozenSet[date] = frozenset()) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5 or nxt in non_working:
        nxt += timedelta(days=1)
    return nxt


def _chunked_round_robin(items: list, n: int) -> List[list]:
    """Равномерно делит список items на n частей."""
    if n <= 0:
        return [items]
    chunks: List[list] = [[] for _ in range(n)]
    for i, item in enumerate(items):
        chunks[i % n].append(item)
    return chunks


class ForceMajeureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(
        self,
        rep_id: str,
        event_date: date,
        fm_type: str,
        description: str | None,
        return_time: Optional[time] = None,
    ) -> Dict[str, Any]:
        # --- 1. Загружаем сотрудника ---
        rep = await self.db.get(SalesRep, rep_id)
        if not rep:
            raise ValueError(f"Сотрудник {rep_id} не найден")

        # --- 1b. Загружаем нерабочие праздники на 60 дней вперёд ---
        lookahead_end = event_date + timedelta(days=60)
        holidays_q = await self.db.execute(
            select(Holiday.date).where(
                Holiday.date.between(event_date, lookahead_end),
                Holiday.is_working.is_(False),
            )
        )
        non_working: FrozenSet[date] = frozenset(holidays_q.scalars().all())

        # --- 2. Плановые визиты на день события ---
        stmt = select(VisitSchedule).where(
            VisitSchedule.rep_id == rep_id,
            VisitSchedule.planned_date == event_date,
            VisitSchedule.status == "planned",
        ).order_by(VisitSchedule.created_at, VisitSchedule.id)
        result = await self.db.execute(stmt)
        all_planned = list(result.scalars().all())

        # Если есть переопределение маршрута — сортируем по нему
        override_stmt = select(DailyRouteOverride).where(
            DailyRouteOverride.rep_id == rep_id,
            DailyRouteOverride.route_date == event_date,
        )
        override_result = await self.db.execute(override_stmt)
        override = override_result.scalars().first()
        if override and override.current_location_order:
            loc_order = {
                loc_id: idx
                for idx, loc_id in enumerate(override.current_location_order)
            }
            all_planned = sorted(
                all_planned, key=lambda s: loc_order.get(s.location_id, 999)
            )

        # Частичный ФМ: переносим только визиты ПОСЛЕ return_time
        if return_time is not None:
            affected_schedules = [
                s for i, s in enumerate(all_planned)
                if _estimated_visit_time(i) >= return_time
            ]
            logger.info(
                "Частичный ФМ: return_time=%s, всего=%d, затронуто=%d",
                return_time, len(all_planned), len(affected_schedules),
            )
        else:
            affected_schedules = all_planned
            logger.info(
                "Полный ФМ: rep=%s date=%s, затронуто=%d визитов",
                rep_id, event_date, len(affected_schedules),
            )

        affected_tt_ids = [s.location_id for s in affected_schedules]

        redistributed_to: List[Dict] = []

        if affected_tt_ids:
            # --- 3. Активные сотрудники (кроме пострадавшего) ---
            active_stmt = select(SalesRep).where(
                SalesRep.status == "active",
                SalesRep.id != rep_id,
            )
            active_result = await self.db.execute(active_stmt)
            active_reps = active_result.scalars().all()

            if not active_reps:
                logger.warning(
                    "FM rep=%s date=%s: нет активных сотрудников для перераспределения %d визитов",
                    rep_id, event_date, len(affected_tt_ids),
                )
            if active_reps:
                locations_result = await self.db.execute(
                    select(Location).where(Location.id.in_(affected_tt_ids))
                )
                location_map = {
                    location.id: location
                    for location in locations_result.scalars().all()
                }
                chunks = _chunked_round_robin(affected_tt_ids, len(active_reps))

                for target_rep, loc_ids in zip(active_reps, chunks):
                    if not loc_ids:
                        continue
                    chunk_locations = [
                        location_map[loc_id]
                        for loc_id in loc_ids
                        if loc_id in location_map
                    ]
                    # Ищем ближайший рабочий день с запасом для всего чанка
                    target_date = await self._find_available_day(
                        target_rep.id,
                        event_date,
                        chunk_size=len(loc_ids),
                        non_working=non_working,
                        chunk_locations=chunk_locations,
                    )
                    # Создаём новые плановые записи
                    for loc_id in loc_ids:
                        self.db.add(VisitSchedule(
                            location_id=loc_id,
                            rep_id=target_rep.id,
                            planned_date=target_date,
                            status="rescheduled",
                        ))
                    redistributed_to.append({
                        "rep_id": target_rep.id,
                        "rep_name": target_rep.name,
                        "location_ids": loc_ids,
                        "new_date": target_date.isoformat(),
                    })

            # --- 4. Отменяем старые записи ---
            for sched in affected_schedules:
                sched.status = "cancelled"

        # --- 5. Обновляем статус сотрудника если болезнь ---
        if fm_type == "illness":
            rep.status = "sick"

        # --- 6. Сохраняем событие ---
        event = ForceMajeureEvent(
            type=fm_type,
            rep_id=rep_id,
            event_date=event_date,
            description=description,
            affected_tt_ids=affected_tt_ids,
            redistributed_to=redistributed_to,
            return_time=return_time,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return {
            "id": event.id,
            "type": fm_type,
            "rep_id": rep_id,
            "rep_name": rep.name,
            "event_date": event_date.isoformat(),
            "description": description,
            "affected_tt_count": len(affected_tt_ids),
            "redistributed_to": redistributed_to,
            "return_time": return_time.isoformat() if return_time else None,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    async def _find_available_day(
        self, rep_id: str, after_date: date, chunk_size: int = 1,
        non_working: FrozenSet[date] = frozenset(),
        chunk_locations: Optional[List[Location]] = None,
    ) -> date:
        """Ищет ближайший рабочий день после after_date, где влезает chunk_size ТТ."""
        candidate = _next_working_day(after_date, non_working)
        for _ in range(30):  # не дальше месяца вперёд
            existing_stmt = (
                select(VisitSchedule)
                .where(
                    VisitSchedule.rep_id == rep_id,
                    VisitSchedule.planned_date == candidate,
                    VisitSchedule.status.in_(["planned", "rescheduled"]),
                )
                .options(selectinload(VisitSchedule.location))
            )
            existing_result = await self.db.execute(existing_stmt)
            existing_schedules = existing_result.scalars().all()
            existing = len(existing_schedules)
            if existing + chunk_size > MAX_TT_PER_DAY:
                candidate = _next_working_day(candidate, non_working)
                continue

            projected_locations = [
                schedule.location
                for schedule in existing_schedules
                if schedule.location is not None
            ] + (chunk_locations or [])
            projected_hours = _estimate_route_hours(projected_locations)
            if projected_hours <= MAX_ROUTE_HOURS_PER_DAY:
                return candidate
            candidate = _next_working_day(candidate, non_working)
        return candidate
