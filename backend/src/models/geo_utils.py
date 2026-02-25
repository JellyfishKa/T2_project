"""
Universal geo utilities for route optimization.
Region-agnostic: all context derived from input data.
"""

import math
from typing import Dict, List, Optional, Tuple


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
    info = detect_region_info(locations)
    factor = 1.15 if info["classification"] == "urban" else 1.3

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


def estimate_fuel_cost(distance_km: float, rate: float = 7.0) -> float:
    """Fuel cost = distance * rate (rub/km).
    Rate overridable via constraints."""
    return round(distance_km * rate, 2)


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


def build_constraints_text(constraints: Optional[Dict]) -> str:
    """Build human-readable constraints text from dict."""
    if not constraints:
        return "Team: 1 worker. Hours: 09:00-18:00. Fuel: 7.0 rub/km."

    parts = []

    team_size = constraints.get("team_size", 1)
    parts.append(f"Team: {team_size} workers")

    hours = constraints.get("working_hours", {})
    start = hours.get("start", "09:00") if isinstance(hours, dict) else "09:00"
    end = hours.get("end", "18:00") if isinstance(hours, dict) else "18:00"
    parts.append(f"Hours: {start}-{end}")

    fuel_rate = constraints.get("fuel_rate", 7.0)
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
