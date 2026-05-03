from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from schedule_planner import VisitTask, haversine_km


@dataclass(frozen=True)
class GeoClusteringResult:
    algo: str
    elapsed_ms: float
    assignments: Dict[str, List[VisitTask]]


def _coords(tasks: Sequence[VisitTask]) -> np.ndarray:
    return np.array([[t.latitude, t.longitude] for t in tasks], dtype=float)


def kmeans_geo_then_balance_by_category(
    tasks: Sequence[VisitTask],
    rep_ids: Sequence[str],
    random_state: int = 42,
) -> GeoClusteringResult:
    """
    Подход 1: K-Means по координатам -> пост-балансировка по reps с учётом категорий.

    Идея: сначала географически компактные группы, затем ограничиваем перекос по числу задач
    и стараемся не "ломать" категории слишком сильно (эвристика).
    """
    from sklearn.cluster import KMeans

    t0 = time.perf_counter()
    rep_ids = list(rep_ids)
    k = len(rep_ids)
    x = _coords(tasks)
    km = KMeans(n_clusters=k, random_state=random_state, n_init="auto")
    labels = km.fit_predict(x)

    # первичное назначение: кластер -> rep
    cluster_to_rep = {c: rep_ids[c] for c in range(k)}
    buckets: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}
    for task, c in zip(tasks, labels):
        buckets[cluster_to_rep[int(c)]].append(task)

    # балансировка нагрузки: ограничиваем max-min <= 1 (в пределах разумного)
    target = int(np.ceil(len(tasks) / k))
    # сортируем кандидатов для переноса по "стоимости": расстояние до центроида альтернативного кластера
    centroids = km.cluster_centers_

    def cost_to_cluster(task: VisitTask, c: int) -> float:
        lat, lon = float(centroids[c][0]), float(centroids[c][1])
        return haversine_km(task.latitude, task.longitude, lat, lon)

    # пока есть перегруженные reps — перетаскиваем самые "дешёвые" точки в недогруженные
    changed = True
    while changed:
        changed = False
        sizes = {r: len(v) for r, v in buckets.items()}
        over = [r for r, n in sizes.items() if n > target]
        under = [r for r, n in sizes.items() if n < target]
        if not over or not under:
            break

        # выбираем самый перегруженный и самый недогруженный
        r_over = max(over, key=lambda r: sizes[r])
        r_under = min(under, key=lambda r: sizes[r])

        # индекс кластера для under
        c_under = rep_ids.index(r_under)

        # переносим одну задачу: предпочитаем ту, которая ближе к центроиду under
        candidates = buckets[r_over]
        if not candidates:
            break
        best = min(candidates, key=lambda t: (cost_to_cluster(t, c_under), str(t.category)))
        buckets[r_over].remove(best)
        buckets[r_under].append(best)
        changed = True

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return GeoClusteringResult(
        algo="kmeans+balance",
        elapsed_ms=round(elapsed_ms, 2),
        assignments=buckets,
    )


def dbscan_then_pack_clusters(
    tasks: Sequence[VisitTask],
    rep_ids: Sequence[str],
    eps_km: float = 2.0,
    min_samples: int = 4,
) -> GeoClusteringResult:
    """
    Подход 2: DBSCAN по координатам (в км) -> пакуем полученные кластеры в reps.
    Шумовые точки (-1) считаем отдельными мини-кластерами.
    """
    from sklearn.cluster import DBSCAN

    t0 = time.perf_counter()
    rep_ids = list(rep_ids)
    k = len(rep_ids)

    # DBSCAN ожидает метрику расстояния; используем precomputed матрицу haversine
    n = len(tasks)
    d = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_km(
                tasks[i].latitude, tasks[i].longitude, tasks[j].latitude, tasks[j].longitude
            )
            d[i, j] = dist
            d[j, i] = dist

    model = DBSCAN(eps=float(eps_km), min_samples=int(min_samples), metric="precomputed")
    labels = model.fit_predict(d)

    # собираем "кластеры" как списки индексов
    clusters: Dict[int, List[int]] = {}
    for idx, c in enumerate(labels):
        clusters.setdefault(int(c), []).append(idx)

    # шум (-1) дробим на одиночки, чтобы pack был гибче
    packed_clusters: List[List[int]] = []
    for c, idxs in clusters.items():
        if c == -1:
            for i in idxs:
                packed_clusters.append([i])
        else:
            packed_clusters.append(idxs)

    # сортируем крупные кластеры первыми
    packed_clusters.sort(key=len, reverse=True)

    buckets: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}
    sizes = {r: 0 for r in rep_ids}

    # greedy bin packing: кладём кластер в наименее загруженного rep
    for idxs in packed_clusters:
        r = min(rep_ids, key=lambda rr: sizes[rr])
        for i in idxs:
            buckets[r].append(tasks[i])
            sizes[r] += 1

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return GeoClusteringResult(
        algo="dbscan+pack",
        elapsed_ms=round(elapsed_ms, 2),
        assignments=buckets,
    )


def greedy_geo_assignment(
    tasks: Sequence[VisitTask],
    rep_ids: Sequence[str],
) -> GeoClusteringResult:
    """
    Подход 3 (контрольный): жадное распределение по расстоянию.
    Идём по точкам в случайно-стабильном порядке и кладём в rep, у которого текущий
    "центр" (средняя координата назначенных) ближе.
    """
    t0 = time.perf_counter()
    rep_ids = list(rep_ids)
    buckets: Dict[str, List[VisitTask]] = {r: [] for r in rep_ids}

    # центры reps, обновляются как mean
    centers: Dict[str, Optional[Tuple[float, float]]] = {r: None for r in rep_ids}

    def dist_to_center(task: VisitTask, rep: str) -> float:
        c = centers[rep]
        if c is None:
            return 0.0
        return haversine_km(task.latitude, task.longitude, c[0], c[1])

    for t in tasks:
        rep = min(rep_ids, key=lambda r: (dist_to_center(t, r), len(buckets[r])))
        buckets[rep].append(t)
        lat = float(np.mean([x.latitude for x in buckets[rep]]))
        lon = float(np.mean([x.longitude for x in buckets[rep]]))
        centers[rep] = (lat, lon)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return GeoClusteringResult(
        algo="greedy-geo",
        elapsed_ms=round(elapsed_ms, 2),
        assignments=buckets,
    )

