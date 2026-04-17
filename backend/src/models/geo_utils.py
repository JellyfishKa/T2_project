"""
Universal geo utilities for route optimization.
Region-agnostic: all context derived from input data.
"""

import math
from typing import Dict, List, Optional, Tuple

DEFAULT_FUEL_COST_RUB_PER_KM = 7.0


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two GPS points using Haversine formula."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_distance_matrix(
    locations: List[Dict],
) -> List[List[float]]:
    """Pairwise road-estimated distances. Auto-detects urban/rural factor."""
    n = len(locations)
    profile = build_route_profile(locations)
    factor = float(profile["road_factor"])

    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(
                locations[i]["lat"], locations[i]["lon"],
                locations[j]["lat"], locations[j]["lon"],
            ) * factor
            matrix[i][j] = round(d, 2)
            matrix[j][i] = round(d, 2)
    return matrix


def detect_region_info(locations: List[Dict]) -> Dict:
    """Detect center, bounding box, area,
    density, classification from points."""
    if not locations:
        return {
            "center": (0.0, 0.0),
            "bbox": (0.0, 0.0, 0.0, 0.0),
            "area_km2": 0.0,
            "point_density": 0.0,
            "classification": "rural",
        }

    lats = [loc["lat"] for loc in locations]
    lons = [loc["lon"] for loc in locations]

    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    width_km = haversine(center_lat, min_lon, center_lat, max_lon)
    height_km = haversine(min_lat, center_lon, max_lat, center_lon)
    area_km2 = max(width_km * height_km, 0.01)

    density = len(locations) / area_km2
    classification = "urban" if density > 5.0 else "rural"

    return {
        "center": (round(center_lat, 4), round(center_lon, 4)),
        "bbox": (round(min_lat, 4), round(min_lon, 4),
                 round(max_lat, 4), round(max_lon, 4)),
        "area_km2": round(area_km2, 2),
        "point_density": round(density, 2),
        "classification": classification,
    }


def estimate_fuel_cost(
    distance_km: float,
    rate: float = DEFAULT_FUEL_COST_RUB_PER_KM,
) -> float:
    """Fuel cost = distance * rate (rub/km).
    Rate overridable via constraints."""
    return round(distance_km * rate, 2)


def average_nearest_neighbor_distance_km(locations: List[Dict]) -> float:
    if len(locations) < 2:
        return 0.0

    nearest_distances: List[float] = []
    for idx, location in enumerate(locations):
        nearest = min(
            haversine(
                location["lat"],
                location["lon"],
                other["lat"],
                other["lon"],
            )
            for other_idx, other in enumerate(locations)
            if other_idx != idx
        )
        nearest_distances.append(nearest)

    return sum(nearest_distances) / len(nearest_distances)


def collect_ordered_leg_distances_km(locations: List[Dict]) -> List[float]:
    if len(locations) < 2:
        return []

    return [
        haversine(
            locations[idx]["lat"],
            locations[idx]["lon"],
            locations[idx + 1]["lat"],
            locations[idx + 1]["lon"],
        )
        for idx in range(len(locations) - 1)
    ]


def build_route_profile(
    locations: List[Dict],
    leg_distances_km: Optional[List[float]] = None,
) -> Dict[str, float | str]:
    region = detect_region_info(locations)
    if len(locations) < 2:
        return {
            "classification": region["classification"],
            "urban_share": 0.0,
            "road_factor": 1.0,
            "effective_speed_kmh": 0.0,
            "transition_buffer_per_leg_min": 0.0,
            "traffic_lights_per_km": 0.0,
            "traffic_light_delay_min": 0.0,
            "reference_leg_km": 0.0,
        }

    bbox = region["bbox"]
    bbox_diag_km = haversine(bbox[0], bbox[1], bbox[2], bbox[3])
    reference_distances = leg_distances_km or collect_ordered_leg_distances_km(locations)
    if not reference_distances:
        reference_distances = [average_nearest_neighbor_distance_km(locations)]

    reference_leg_km = sum(reference_distances) / len(reference_distances)
    urban_share = 0.45 if region["classification"] == "urban" else 0.15

    if reference_leg_km <= 2.0:
        urban_share += 0.35
    elif reference_leg_km <= 5.0:
        urban_share += 0.2
    elif reference_leg_km <= 12.0:
        urban_share += 0.08

    if bbox_diag_km <= 10.0:
        urban_share += 0.18
    elif bbox_diag_km <= 30.0:
        urban_share += 0.1

    urban_share = clamp(urban_share, 0.05, 0.95)
    road_factor = clamp(
        1.08
        + urban_share * 0.16
        + (0.04 if reference_leg_km <= 2.0 else 0.02 if reference_leg_km <= 5.0 else 0.0),
        1.08,
        1.3,
    )
    effective_speed_kmh = clamp(
        74.0
        - urban_share * 22.0
        - (10.0 if reference_leg_km <= 2.0 else 5.0 if reference_leg_km <= 5.0 else 0.0),
        22.0,
        72.0,
    )
    transition_buffer_per_leg_min = round(1.0 + urban_share * 0.8, 2)
    traffic_lights_per_km = round(0.08 + urban_share * 0.72, 3)
    traffic_light_delay_min = round(0.35 + urban_share * 0.3, 3)

    return {
        "classification": region["classification"],
        "urban_share": round(urban_share, 3),
        "road_factor": round(road_factor, 3),
        "effective_speed_kmh": round(effective_speed_kmh, 2),
        "transition_buffer_per_leg_min": transition_buffer_per_leg_min,
        "traffic_lights_per_km": traffic_lights_per_km,
        "traffic_light_delay_min": traffic_light_delay_min,
        "reference_leg_km": round(reference_leg_km, 2),
    }


def estimate_transition_buffer_minutes(
    leg_count: int,
    route_profile: Dict[str, float | str],
) -> float:
    if leg_count <= 0:
        return 0.0
    return leg_count * float(route_profile["transition_buffer_per_leg_min"])


def estimate_traffic_delay(
    distance_km: float,
    leg_count: int,
    route_profile: Dict[str, float | str],
) -> Tuple[int, float]:
    if leg_count <= 0 or distance_km <= 0:
        return 0, 0.0

    lights_per_km = float(route_profile["traffic_lights_per_km"])
    delay_per_light = float(route_profile["traffic_light_delay_min"])
    lights_count = max(leg_count, int(round(distance_km * lights_per_km)))
    return lights_count, round(lights_count * delay_per_light, 2)


def infer_category(priority: str) -> str:
    """Map priority string to A/B/C/D category."""
    p = priority.strip().upper()
    if p in ("A", "B", "C", "D"):
        return p
    mapping = {
        "HIGH": "A", "CRITICAL": "A", "URGENT": "A",
        "MEDIUM": "B", "NORMAL": "B",
        "LOW": "C", "MINOR": "C",
        "MINIMAL": "D", "QUARTERLY": "D", "RARE": "D",
    }
    return mapping.get(p, "C")


def build_nearest_neighbors(
    distance_matrix: List[List[float]],
    k: int = 3,
) -> List[List[Tuple[int, float]]]:
    """Top-k nearest neighbors per point (for token-limited prompts)."""
    n = len(distance_matrix)
    result = []
    for i in range(n):
        neighbors = []
        for j in range(n):
            if i != j:
                neighbors.append((j, distance_matrix[i][j]))
        neighbors.sort(key=lambda x: x[1])
        result.append(neighbors[:k])
    return result


def format_locations_compact(locations: List[Dict]) -> str:
    """Format locations as compact lines: ID|name|lat,lon|priority=X."""
    lines = []
    for loc in locations:
        cat = infer_category(loc.get("priority", "C"))
        lines.append(
            f"{loc['ID']}|{loc['name']}|"
            f"{loc['lat']},{loc['lon']}|priority={cat}",
        )
    return "\n".join(lines)


def format_distance_pairs(
    locations: List[Dict],
    distance_matrix: List[List[float]],
) -> str:
    """Format all distance pairs as compact text."""
    lines = []
    n = len(locations)
    for i in range(n):
        for j in range(i + 1, n):
            lines.append(
                f"{locations[i]['ID']}->"
                f"{locations[j]['ID']}:{distance_matrix[i][j]}km",
            )
    return "\n".join(lines)


def format_nearest_neighbors(
    locations: List[Dict],
    neighbors: List[List[Tuple[int, float]]],
) -> str:
    """Format nearest neighbors as compact text (for Qwen's token limit)."""
    lines = []
    for i, nn_list in enumerate(neighbors):
        nn_str = ",".join(
            f"{locations[j]['ID']}:{d}km" for j, d in nn_list
        )
        lines.append(f"{locations[i]['ID']}->nearest:[{nn_str}]")
    return "\n".join(lines)


def compute_route_metrics(
    locations: List[Dict],
    sequence_ids: List[str],
    constraints: Optional[Dict] = None,
) -> tuple:
    """Compute (total_distance_km, total_time_hours, total_cost_rub)
    from an ordered sequence of location IDs."""
    id_to_loc = {loc["ID"]: loc for loc in locations}
    fuel_rate = float((constraints or {}).get("fuel_rate", DEFAULT_FUEL_COST_RUB_PER_KM))

    ordered = [id_to_loc[sid] for sid in sequence_ids if sid in id_to_loc]
    leg_distances = collect_ordered_leg_distances_km(ordered)
    profile = build_route_profile(ordered, leg_distances)
    speed = float(profile["effective_speed_kmh"])
    factor = float(profile["road_factor"])
    total_distance = 0.0
    for i in range(len(ordered) - 1):
        d = haversine(
            ordered[i]["lat"], ordered[i]["lon"],
            ordered[i + 1]["lat"], ordered[i + 1]["lon"],
        ) * factor
        total_distance += d

    drive_time_minutes = (total_distance / speed) * 60 if speed else 0.0
    leg_count = max(len(ordered) - 1, 0)
    _, traffic_delay_minutes = estimate_traffic_delay(
        total_distance,
        leg_count,
        profile,
    )
    transition_buffer_minutes = estimate_transition_buffer_minutes(
        leg_count,
        profile,
    )
    service_time_minutes = len(ordered) * 15
    total_time = (
        drive_time_minutes
        + traffic_delay_minutes
        + transition_buffer_minutes
        + service_time_minutes
    ) / 60
    total_cost = total_distance * fuel_rate
    return round(total_distance, 2), round(total_time, 2), round(total_cost, 2)


def build_constraints_text(constraints: Optional[Dict]) -> str:
    """Build human-readable constraints text from dict."""
    if not constraints:
        return (
            "Team: 1 worker. Hours: 09:00-18:00. "
            f"Fuel: {DEFAULT_FUEL_COST_RUB_PER_KM:.1f} rub/km."
        )

    parts = []

    team_size = constraints.get("team_size", 1)
    parts.append(f"Team: {team_size} workers")

    hours = constraints.get("working_hours", {})
    start = hours.get("start", "09:00") if isinstance(hours, dict) else "09:00"
    end = hours.get("end", "18:00") if isinstance(hours, dict) else "18:00"
    parts.append(f"Hours: {start}-{end}")

    fuel_rate = constraints.get("fuel_rate", DEFAULT_FUEL_COST_RUB_PER_KM)
    parts.append(f"Fuel: {fuel_rate} rub/km")

    cat_rules = constraints.get("category_rules")
    if cat_rules:
        for cat, rules in sorted(cat_rules.items()):
            if "visits_per_month" in rules:
                parts.append(f"Cat {cat}: {rules['visits_per_month']}x/month")
            elif "visits_per_quarter" in rules:
                parts.append(f"Cat {cat}:"
                             f"{rules['visits_per_quarter']}x/quarter")

    max_dist = constraints.get("maxDistance")
    if max_dist:
        parts.append(f"Max distance: {max_dist}km")

    capacity = constraints.get("vehicleCapacity")
    if capacity:
        parts.append(f"Vehicle capacity: {capacity}")

    return ". ".join(parts) + "."
