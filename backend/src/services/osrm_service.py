from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

import requests

logger = logging.getLogger("osrm_service")


def osrm_trip_order(
    coords: List[Tuple[float, float]],
    osrm_url: Optional[str] = None,
    timeout_s: float = 5.0,
) -> Optional[List[int]]:
    """
    Пытается получить порядок точек через OSRM trip service.

    coords: список (lat, lon)
    returns: waypoint_order (индексы исходного coords) или None при ошибке.
    """
    if osrm_url is None:
        osrm_url = os.getenv("OSRM_URL")
    if not osrm_url:
        return None

    # OSRM ожидает lon,lat
    coord_str = ";".join([f"{lon},{lat}" for (lat, lon) in coords])
    url = osrm_url.rstrip("/") + f"/trip/v1/driving/{coord_str}"
    params = {"source": "first", "roundtrip": "false", "overview": "false"}
    try:
        r = requests.get(url, params=params, timeout=timeout_s)
        r.raise_for_status()
        payload = r.json()
        trips = payload.get("trips") or []
        waypoints = payload.get("waypoints") or []
        if not trips or not waypoints:
            return None
        order = [int(w.get("waypoint_index")) for w in waypoints]
        # OSRM возвращает список waypoint_index по исходным координатам;
        # приводим к permutation 0..n-1 в порядке посещения.
        # waypoints уже отсортированы по trip order.
        if len(order) != len(coords):
            return None
        if set(order) != set(range(len(coords))):
            return None
        return order
    except Exception as exc:
        logger.debug("OSRM waypoint order parse failed: %s", exc)
        return None

