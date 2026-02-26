"""
Сервис обработки форс-мажорных ситуаций.

При инциденте:
1. Находит все плановые визиты сотрудника на дату события.
2. Равномерно перераспределяет ТТ между другими активными сотрудниками.
3. Для каждого сотрудника ищет ближайший рабочий день с запасом.
4. Записывает событие в force_majeure_events.
5. Если тип «illness» — меняет статус сотрудника на «sick».
"""

import logging
import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ForceMajeureEvent, SalesRep, VisitSchedule

logger = logging.getLogger("force_majeure")

MAX_TT_PER_DAY = 15  # синхронизировать с schedule_planner


def _next_working_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
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
    ) -> Dict[str, Any]:
        # --- 1. Загружаем сотрудника ---
        rep = await self.db.get(SalesRep, rep_id)
        if not rep:
            raise ValueError(f"Сотрудник {rep_id} не найден")

        # --- 2. Плановые визиты на день события ---
        stmt = select(VisitSchedule).where(
            VisitSchedule.rep_id == rep_id,
            VisitSchedule.planned_date == event_date,
            VisitSchedule.status == "planned",
        )
        result = await self.db.execute(stmt)
        affected_schedules = result.scalars().all()
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

            if active_reps:
                chunks = _chunked_round_robin(affected_tt_ids, len(active_reps))

                for target_rep, loc_ids in zip(active_reps, chunks):
                    if not loc_ids:
                        continue
                    # Ищем ближайший рабочий день с запасом
                    target_date = await self._find_available_day(
                        target_rep.id, event_date
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
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    async def _find_available_day(self, rep_id: str, after_date: date) -> date:
        """Ищет ближайший рабочий день после after_date, где у сотрудника < MAX_TT_PER_DAY."""
        candidate = _next_working_day(after_date)
        for _ in range(30):  # не дальше месяца вперёд
            # Считаем сколько уже запланировано
            count_stmt = select(VisitSchedule).where(
                VisitSchedule.rep_id == rep_id,
                VisitSchedule.planned_date == candidate,
                VisitSchedule.status.in_(["planned", "rescheduled"]),
            )
            count_result = await self.db.execute(count_stmt)
            existing = len(count_result.scalars().all())
            if existing < MAX_TT_PER_DAY:
                return candidate
            candidate = _next_working_day(candidate)
        return candidate
