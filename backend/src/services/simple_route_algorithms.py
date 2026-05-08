from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from src.config import settings
from src.models.geo_utils import compute_distance_matrix
from src.models.schemas import Location, Route


def nearest_neighbour_route(
    locations: List[Location],
    model_used: str = "algorithm-nn",
) -> Route:
    if len(locations) <= 1:
        ordered = list(locations)
    else:
        all_points = [{"lat": settings.default_depot_lat, "lon": settings.default_depot_lon}] + [
            {"lat": loc.lat, "lon": loc.lon} for loc in locations
        ]
        matrix = compute_distance_matrix(all_points)
        visited = [False] * len(all_points)
        order = [0]
        visited[0] = True
        for _ in range(len(all_points) - 1):
            cur = order[-1]
            nxt = min(
                (i for i in range(1, len(all_points)) if not visited[i]),
                key=lambda i: matrix[cur][i],
            )
            order.append(nxt)
            visited[nxt] = True
        ordered = [locations[i - 1] for i in order if i != 0]

    # В lightweight fallback-режиме не считаем дорогую дорожную метрику.
    return Route(
        ID=str(uuid.uuid4()),
        name=f"Алгоритмический маршрут ({model_used})",
        locations=ordered,
        total_distance_km=0.0,
        total_time_hours=0.0,
        total_cost_rub=0.0,
        model_used=model_used,
        created_at=datetime.now(timezone.utc),
    )


def normalize_constraints(constraints: Dict | None) -> Dict:
    if isinstance(constraints, dict):
        return constraints
    return {}
