"""
Планировщик месячных маршрутов торговых представителей.

Алгоритм:
1. Определяет рабочие дни месяца (пн–пт).
2. По категории ТТ вычисляет плановые даты визитов:
   A → 3 визита (1-я, 2-я, 3-я рабочие недели месяца)
   B → 2 визита (1-я и 3-я рабочие недели)
   C → 1 визит (середина месяца)
   D → 1 визит в квартал (если текущий квартал совпадает)
3. Собирает пул (location_id, planned_date, category).
4. Сортирует задачи по (дата, приоритет A→B→C→D).
5. Для каждой задачи ищет ближайший свободный слот (date, rep)
   начиная с целевой даты — сотрудника с наибольшим остатком слотов.
6. Сохраняет в visit_schedule (batch insert).
"""

import logging
import math
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Location, SalesRep, VisitSchedule

logger = logging.getLogger("schedule_planner")

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
WORK_START_HOUR = 9
WORK_END_HOUR = 18
VISIT_DURATION_MIN = 15        # минут на одну ТТ
AVG_TRAVEL_MIN_PER_TT = 20    # средние затраты времени на переезд к ТТ
LUNCH_BREAK_MIN = 30           # обед
WORK_MINUTES = (WORK_END_HOUR - WORK_START_HOUR) * 60   # 540 мин

MAX_TT_PER_DAY = math.floor(
    (WORK_MINUTES - LUNCH_BREAK_MIN) / (VISIT_DURATION_MIN + AVG_TRAVEL_MIN_PER_TT)
)   # floor(510/35) = 14 ТТ/день

CATEGORY_PRIORITY = {"A": 1, "B": 2, "C": 3, "D": 4}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _working_days(year: int, month: int) -> List[date]:
    """Возвращает список рабочих дней месяца (пн–пт)."""
    _, last = monthrange(year, month)
    return [
        date(year, month, d)
        for d in range(1, last + 1)
        if date(year, month, d).weekday() < 5  # 0=пн … 4=пт
    ]


def _week_groups(days: List[date]) -> List[List[date]]:
    """Разбивает рабочие дни на рабочие недели (по номеру ISO-недели)."""
    groups: Dict[int, List[date]] = defaultdict(list)
    for d in days:
        groups[d.isocalendar()[1]].append(d)
    return [v for v in groups.values()]


def _visit_dates(
    category: str,
    work_weeks: List[List[date]],
    all_days: List[date],
    quarter_month: int,   # номер первого месяца квартала (1, 4, 7, 10)
    current_month: int,
) -> List[date]:
    """Вычисляет плановые даты визитов для ТТ с данной категорией."""
    if not work_weeks or not all_days:
        return []

    def _first_day(week_idx: int) -> Optional[date]:
        if week_idx < len(work_weeks):
            return work_weeks[week_idx][0]
        return None

    if category == "A":
        # 3 визита: 1-я, 2-я, 3-я рабочие недели
        dates = [_first_day(i) for i in [0, 1, 2]]
        return [d for d in dates if d]

    elif category == "B":
        # 2 визита: 1-я и 3-я (или 2-я если нет 3-й) рабочие недели
        d1 = _first_day(0)
        d2 = _first_day(2) or _first_day(1)
        return [d for d in [d1, d2] if d]

    elif category == "C":
        # 1 визит: середина месяца
        mid = all_days[len(all_days) // 2]
        return [mid]

    elif category == "D":
        # 1 визит в квартал: только если текущий месяц = первый в квартале
        if current_month == quarter_month:
            return [all_days[0]]
        return []

    return []


def _next_working_day(d: date) -> date:
    """Следующий рабочий день после d."""
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


# ---------------------------------------------------------------------------
# Основной планировщик
# ---------------------------------------------------------------------------

class SchedulePlanner:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_monthly_plan(
        self,
        month_str: str,
        rep_ids: Optional[List[str]] = None,
        overwrite: bool = True,
    ) -> dict:
        """
        Генерирует план визитов на месяц и сохраняет его в БД.

        :param month_str: Строка вида "YYYY-MM"
        :param rep_ids:   Список ID сотрудников. None → все активные.
        :param overwrite: Если True — удаляет старый план на этот месяц.
        :return: Словарь со статистикой.
        """
        year, month = map(int, month_str.split("-"))

        # --- Загрузка данных ---
        locations = await self._load_locations()
        reps = await self._load_reps(rep_ids)
        if not reps:
            return {"error": "Нет активных сотрудников"}
        if not locations:
            return {"error": "Нет торговых точек с категорией A/B/C/D в базе"}

        # --- Рабочие дни и недели ---
        all_days = _working_days(year, month)
        work_weeks = _week_groups(all_days)

        # Первый месяц текущего квартала
        quarter_start_month = ((month - 1) // 3) * 3 + 1

        # --- Строим пул задач: [(location_id, date, category), ...] ---
        task_pool: List[Tuple[str, date, str]] = []
        for loc in locations:
            cat = loc.category  # уже отфильтровано до A/B/C/D
            dates = _visit_dates(cat, work_weeks, all_days, quarter_start_month, month)
            for d in dates:
                task_pool.append((loc.id, d, cat))

        # --- Удаляем старый план если нужно ---
        if overwrite:
            month_start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            month_end = date(year, month, last_day)
            await self.db.execute(
                delete(VisitSchedule).where(
                    VisitSchedule.planned_date >= month_start,
                    VisitSchedule.planned_date <= month_end,
                )
            )
            await self.db.flush()

        # --- Распределение по сотрудникам ---
        # Сортируем задачи по (целевая дата, приоритет категории)
        sorted_tasks = sorted(
            task_pool,
            key=lambda t: (t[1], CATEGORY_PRIORITY.get(t[2], 4))
        )

        # Для каждой (дата, сотрудник) храним оставшиеся слоты
        rep_day_slots: Dict[Tuple[str, date], int] = defaultdict(lambda: MAX_TT_PER_DAY)
        schedule_rows: List[VisitSchedule] = []

        for (loc_id, target_d, cat) in sorted_tasks:
            check_date = target_d
            assigned = False

            # Ограниченный lookahead: не дальше ~2 месяца
            for _ in range(len(all_days) + 31):
                # Пропускаем выходные
                if check_date.weekday() >= 5:
                    check_date = _next_working_day(check_date)
                    continue

                # Выбираем сотрудника с наибольшим остатком слотов (fairness)
                best_rep = max(
                    reps,
                    key=lambda r: rep_day_slots[(r.id, check_date)],
                )
                if rep_day_slots[(best_rep.id, check_date)] > 0:
                    schedule_rows.append(VisitSchedule(
                        location_id=loc_id,
                        rep_id=best_rep.id,
                        planned_date=check_date,
                        status="planned",
                    ))
                    rep_day_slots[(best_rep.id, check_date)] -= 1
                    assigned = True
                    break

                check_date = _next_working_day(check_date)

            if not assigned:
                logger.warning(
                    "Не удалось запланировать ТТ %s в месяце %s", loc_id, month_str
                )

        # --- Batch insert ---
        for row in schedule_rows:
            self.db.add(row)
        await self.db.commit()

        # --- Статистика ---
        total_locations = len(locations)
        planned_locs = {row.location_id for row in schedule_rows}
        coverage_pct = (
            round(len(planned_locs) / total_locations * 100, 1) if total_locations else 0
        )

        logger.info(
            "Месячный план %s: %d визитов, %d ТТ охвачено (%.1f%%), max %d ТТ/день/сотрудник",
            month_str, len(schedule_rows), len(planned_locs), coverage_pct, MAX_TT_PER_DAY,
        )
        return {
            "month": month_str,
            "total_visits_planned": len(schedule_rows),
            "total_tt_planned": len(planned_locs),
            "total_locations": total_locations,
            "coverage_pct": coverage_pct,
            "reps_count": len(reps),
        }

    async def _load_locations(self) -> List[Location]:
        """Загружает только ТТ с категорией A/B/C/D (исключает данные без категории)."""
        result = await self.db.execute(
            select(Location).where(Location.category.in_(["A", "B", "C", "D"]))
        )
        return result.scalars().all()

    async def _load_reps(self, rep_ids: Optional[List[str]]) -> List[SalesRep]:
        stmt = select(SalesRep).where(SalesRep.status == "active")
        if rep_ids:
            stmt = stmt.where(SalesRep.id.in_(rep_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()
