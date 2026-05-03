from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import atan2, cos, radians, sin, sqrt
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class TradePoint:
    """
    Торговая точка (ТТ).

    category: категория обслуживания (например, A/B/C/D)
    """

    id: str
    category: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class VisitTask:
    """Конкретный визит в ТТ (внутри месяца может быть несколько визитов одной ТТ)."""

    trade_point_id: str
    category: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DayRoute:
    rep_id: str
    day: date
    visits: Tuple[VisitTask, ...]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по сфере (км). Достаточно для сравнения подходов на датасете."""
    r = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def route_distance_km(visits: Sequence[VisitTask]) -> float:
    """Сумма расстояний по порядку следования визитов (без возврата в депо)."""
    if len(visits) <= 1:
        return 0.0
    total = 0.0
    for a, b in zip(visits, visits[1:]):
        total += haversine_km(a.latitude, a.longitude, b.latitude, b.longitude)
    return total


def nearest_neighbour_order(visits: Sequence[VisitTask], start_idx: int = 0) -> List[int]:
    """Жадный порядок (NN): от текущей точки к ближайшей непосещённой."""
    n = len(visits)
    if n <= 1:
        return list(range(n))
    start_idx = max(0, min(n - 1, start_idx))
    order = [start_idx]
    unvisited = set(range(n))
    unvisited.remove(start_idx)
    while unvisited:
        cur = order[-1]
        nxt = min(
            unvisited,
            key=lambda j: haversine_km(
                visits[cur].latitude,
                visits[cur].longitude,
                visits[j].latitude,
                visits[j].longitude,
            ),
        )
        order.append(nxt)
        unvisited.remove(nxt)
    return order


def reorder(visits: Sequence[VisitTask], order: Sequence[int]) -> Tuple[VisitTask, ...]:
    return tuple(visits[i] for i in order)


def monthly_visit_counts(
    category: str,
    month: date,
    quarterly_months: Tuple[int, int, int] = (1, 4, 7, 10),
    freq_a_per_month: int = 3,
    freq_d_per_quarter: int = 1,
) -> int:
    """
    Правила частоты визитов (минимум необходимый для ТЗ):
    - A: 3 раза в месяц
    - D: 1 раз в квартал (в первый месяц квартала по умолчанию)
    Остальные категории: 1 раз в месяц.
    """
    cat = (category or "").strip().upper()
    if cat == "A":
        return int(freq_a_per_month)
    if cat == "D":
        return int(freq_d_per_quarter) if month.month in set(quarterly_months) else 0
    return 1


def expand_monthly_tasks(trade_points: Sequence[TradePoint], month: date) -> List[VisitTask]:
    tasks: List[VisitTask] = []
    for tp in trade_points:
        k = monthly_visit_counts(tp.category, month)
        for _ in range(k):
            tasks.append(
                VisitTask(
                    trade_point_id=tp.id,
                    category=tp.category,
                    latitude=tp.latitude,
                    longitude=tp.longitude,
                )
            )
    return tasks


def _category_only_assignment(
    tasks: Sequence[VisitTask],
    rep_ids: Sequence[str],
) -> Dict[str, List[VisitTask]]:
    """
    Baseline: распределение только по категориям без географии.
    Делит задачи каждой категории по reps round-robin.
    """
    buckets: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}
    by_cat: Dict[str, List[VisitTask]] = {}
    for t in tasks:
        by_cat.setdefault(t.category, []).append(t)

    for cat, cat_tasks in sorted(by_cat.items(), key=lambda x: x[0]):
        for i, task in enumerate(cat_tasks):
            rep = rep_ids[i % len(rep_ids)]
            buckets[rep].append(task)
    return buckets


class SchedulePlanner:
    """
    Планировщик месячного расписания.

    Минимально нужное под ТЗ:
    - учитывает частоты категорий (A=3/мес, D=1/квартал),
    - умеет baseline "только категории",
    - умеет geo-aware распределение: кластеризация задач по координатам перед раскладкой по дням.
    """

    def __init__(
        self,
        rep_ids: Sequence[str],
        work_days: Sequence[int] = (0, 1, 2, 3, 4),  # Mon..Fri
        max_visits_per_day: int = 12,
        geo_clusterer: Optional[
            Callable[[Sequence[VisitTask], int], Dict[str, List[VisitTask]]]
        ] = None,
    ):
        self.rep_ids = list(rep_ids)
        self.work_days = tuple(work_days)
        self.max_visits_per_day = int(max_visits_per_day)
        self.geo_clusterer = geo_clusterer

    @staticmethod
    def make_default_geo_clusterer(rep_ids: Sequence[str]):
        """
        Финальный выбранный подход (T2-5): K-Means по координатам + балансировка размеров.
        Возвращает функцию clusterer(tasks, k) -> dict(rep_id -> tasks).

        Важно: реализация без scikit-learn (чтобы работало в backend окружении).
        """
        import numpy as np

        rep_ids = list(rep_ids)

        def clusterer(tasks: Sequence[VisitTask], k: int) -> Dict[str, List[VisitTask]]:
            if k != len(rep_ids):
                raise ValueError("k must equal number of rep_ids")

            x = np.array([[t.latitude, t.longitude] for t in tasks], dtype=float)
            n = x.shape[0]
            if n == 0:
                return {r: [] for r in rep_ids}

            # init центроидов: равномерные точки по индексу (детерминированно)
            init_idx = np.linspace(0, n - 1, num=k).round().astype(int)
            centroids = x[init_idx].copy()

            # Lloyd iterations
            labels = np.zeros(n, dtype=int)
            for _ in range(15):
                # assign
                d2 = ((x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
                new_labels = d2.argmin(axis=1)
                if np.array_equal(new_labels, labels):
                    break
                labels = new_labels
                # update
                for c in range(k):
                    mask = labels == c
                    if mask.any():
                        centroids[c] = x[mask].mean(axis=0)

            buckets: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}
            for task, c in zip(tasks, labels.tolist()):
                buckets[rep_ids[int(c)]].append(task)

            # балансировка размеров (по "стоимости" расстояния до центроида целевого кластера)
            target = int(np.ceil(n / k))

            def cost_to_cluster(task: VisitTask, c: int) -> float:
                lat, lon = float(centroids[c][0]), float(centroids[c][1])
                return haversine_km(task.latitude, task.longitude, lat, lon)

            changed = True
            while changed:
                changed = False
                sizes = {r: len(v) for r, v in buckets.items()}
                over = [r for r, sz in sizes.items() if sz > target]
                under = [r for r, sz in sizes.items() if sz < target]
                if not over or not under:
                    break

                r_over = max(over, key=lambda r: sizes[r])
                r_under = min(under, key=lambda r: sizes[r])
                c_under = rep_ids.index(r_under)

                if not buckets[r_over]:
                    break
                best = min(
                    buckets[r_over],
                    key=lambda t: (cost_to_cluster(t, c_under), str(t.category)),
                )
                buckets[r_over].remove(best)
                buckets[r_under].append(best)
                changed = True

            return buckets

        return clusterer

    def plan_month(
        self,
        trade_points: Sequence[TradePoint],
        month: date,
        use_geo: bool = True,
    ) -> List[DayRoute]:
        tasks = expand_monthly_tasks(trade_points, month)
        if not tasks:
            return []

        if use_geo and self.geo_clusterer is not None:
            per_rep = self.geo_clusterer(tasks, len(self.rep_ids))
            # гарантируем ключи для всех reps
            for r in self.rep_ids:
                per_rep.setdefault(r, [])
        else:
            per_rep = _category_only_assignment(tasks, self.rep_ids)

        # раскладка по дням: по reps, затем пачками max_visits_per_day, внутри дня оптимизируем NN
        days = self._month_workdays(month)
        routes: List[DayRoute] = []
        for rep in self.rep_ids:
            rep_tasks = list(per_rep.get(rep, []))
            day_idx = 0
            while rep_tasks:
                if day_idx >= len(days):
                    # если задач больше, чем слотов дней, просто продолжаем последним днём
                    day = days[-1]
                else:
                    day = days[day_idx]
                chunk = rep_tasks[: self.max_visits_per_day]
                rep_tasks = rep_tasks[self.max_visits_per_day :]

                order = nearest_neighbour_order(chunk, start_idx=0)
                visits = reorder(chunk, order)
                routes.append(DayRoute(rep_id=rep, day=day, visits=visits))
                day_idx += 1
        return routes

    def total_distance_km(self, routes: Sequence[DayRoute]) -> float:
        return sum(route_distance_km(r.visits) for r in routes)

    def load_balance(self, routes: Sequence[DayRoute]) -> Dict[str, int]:
        counts: Dict[str, int] = {r: 0 for r in self.rep_ids}
        for rt in routes:
            counts[rt.rep_id] = counts.get(rt.rep_id, 0) + len(rt.visits)
        return counts

    def _month_workdays(self, month: date) -> List[date]:
        # берём все дни месяца, фильтруем по weekday
        first = date(month.year, month.month, 1)
        if month.month == 12:
            next_month = date(month.year + 1, 1, 1)
        else:
            next_month = date(month.year, month.month + 1, 1)
        days: List[date] = []
        cur = first
        while cur < next_month:
            if cur.weekday() in self.work_days:
                days.append(cur)
            cur = date.fromordinal(cur.toordinal() + 1)
        return days or [first]

