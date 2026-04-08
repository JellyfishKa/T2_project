import logging
import os
from typing import Any, Sequence, Optional

import httpx

from src.models.geo_utils import (
    detect_region_info,
    estimate_fuel_cost, # Оставляем как фолбэк, если машина не передана
    haversine,
)
from src.schemas.vehicle import Vehicle 

logger = logging.getLogger("routing")


class RoutingService:
    def __init__(self) -> None:
        self.router_url = os.getenv(
            "ROAD_ROUTER_URL",
            "https://router.project-osrm.org/route/v1/driving",
        ).rstrip("/")
        self.timeout = float(os.getenv("ROAD_ROUTER_TIMEOUT_SEC", "8"))

    # ─── Новый метод для расчета топлива ──────────────────────────────────────
    def _calculate_dynamic_cost(
        self, 
        distance_km: float, 
        region_classification: str, 
        vehicle: Optional[Vehicle]
    ) -> float:
        """Считает стоимость топлива на основе типа местности и параметров авто."""
        if not vehicle:
            # Если машину не передали, используем старую логику по умолчанию
            return estimate_fuel_cost(distance_km)

        # Выбираем расход в зависимости от классификации региона
        if region_classification == "urban":
            consumption = vehicle.consumption_city_l_100km
        else:
            # Для трассы / пригорода
            consumption = vehicle.consumption_highway_l_100km

        liters_used = (distance_km / 100) * consumption
        return round(liters_used * vehicle.fuel_price_rub, 2)

    async def build_route_preview(
        self,
        points: Sequence[Any],
        vehicle: Optional[Vehicle] = None,
    ) -> dict[str, Any]:
        valid_points = [
            {"lat": float(point.lat), "lon": float(point.lon)}
            for point in points
            if point is not None
        ]

        if not valid_points:
            return {
                "geometry": [],
                "distance_km": 0.0,
                "time_minutes": 0.0,
                "cost_rub": 0.0,
                "traffic_lights_count": 0,
                "source": "empty",
            }

        if len(valid_points) == 1:
            lat = valid_points[0]["lat"]
            lon = valid_points[0]["lon"]
            return {
                "geometry": [(lat, lon)],
                "distance_km": 0.0,
                "time_minutes": 0.0,
                "cost_rub": 0.0,
                "traffic_lights_count": 0,
                "source": "single_point",
            }

        # Определяем регион один раз для всего маршрута
        region_info = detect_region_info(valid_points)

        road_preview = await self._fetch_osrm_preview(valid_points, region_info, vehicle)
        if road_preview is not None:
            return road_preview

        return self._build_fallback_preview(valid_points, region_info, vehicle)

    async def _fetch_osrm_preview(
        self,
        points: list[dict[str, float]],
        region_info: dict[str, Any],
        vehicle: Optional[Vehicle],
    ) -> dict[str, Any] | None:
        coordinates = ";".join(
            f"{point['lon']:.6f},{point['lat']:.6f}" for point in points
        )
        url = (
            f"{self.router_url}/{coordinates}"
            "?overview=full&geometries=geojson&steps=false&alternatives=false"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
        except Exception as exc:
            logger.warning("Road routing unavailable, fallback to heuristic: %s", exc)
            return None

        try:
            payload = response.json()
            route = (payload.get("routes") or [None])[0]
            if not route:
                return None

            coordinates = route.get("geometry", {}).get("coordinates") or []
            geometry = [
                (float(lat), float(lon))
                for lon, lat in coordinates
            ]
            distance_km = round(float(route.get("distance", 0.0)) / 1000, 2)
            base_time_minutes = float(route.get("duration", 0.0)) / 60
            
            traffic_lights_count, traffic_delay_minutes = self._estimate_traffic_delay(
                points,
                distance_km,
                region_info, # Передаем уже вычисленный регион
            )
            total_time_minutes = round(
                base_time_minutes + traffic_delay_minutes,
                2,
            )
            
            # Динамический расчет стоимости
            cost_rub = self._calculate_dynamic_cost(
                distance_km, 
                region_info.get("classification", "urban"), 
                vehicle
            )

            return {
                "geometry": geometry,
                "distance_km": distance_km,
                "time_minutes": total_time_minutes,
                "cost_rub": cost_rub,
                "traffic_lights_count": traffic_lights_count,
                "source": "road_network",
            }
        except Exception as exc:
            logger.warning("Road routing response parse failed: %s", exc)
            return None

    def _build_fallback_preview(
        self,
        points: list[dict[str, float]],
        region_info: dict[str, Any],
        vehicle: Optional[Vehicle],
    ) -> dict[str, Any]:
        total_distance = 0.0
        for start, end in zip(points, points[1:]):
            total_distance += self._estimate_fallback_leg_distance(start, end, region_info)

        traffic_lights_count, traffic_delay_minutes = self._estimate_traffic_delay(
            points,
            total_distance,
            region_info,
        )
        
        classification = region_info.get("classification", "urban")
        speed_kmh = 60.0 if classification == "urban" else 90.0
        drive_time_minutes = (total_distance / speed_kmh) * 60 if speed_kmh else 0.0

        # Динамический расчет стоимости
        cost_rub = self._calculate_dynamic_cost(total_distance, classification, vehicle)

        return {
            "geometry": [(point["lat"], point["lon"]) for point in points],
            "distance_km": round(total_distance, 2),
            "time_minutes": round(drive_time_minutes + traffic_delay_minutes, 2),
            "cost_rub": cost_rub,
            "traffic_lights_count": traffic_lights_count,
            "source": "fallback",
        }

    def _estimate_fallback_leg_distance(
        self,
        start: dict[str, float],
        end: dict[str, float],
        region_info: dict[str, Any],
    ) -> float:
        direct_km = haversine(start["lat"], start["lon"], end["lat"], end["lon"])
        road_factor = 1.22 if region_info.get("classification") == "urban" else 1
        return direct_km * road_factor

    def _estimate_traffic_delay(
        self,
        points: list[dict[str, float]],
        distance_km: float,
        region_info: dict[str, Any],
    ) -> tuple[int, float]:
        if region_info.get("classification") == "urban":
            lights_per_km = 0.6
            delay_per_light_minutes = 0.25
        else:
            lights_per_km = 0.18
            delay_per_light_minutes = 0.2

        lights_count = max(
            len(points) - 1,
            int(round(distance_km * lights_per_km)),
        )
        delay_minutes = lights_count * delay_per_light_minutes
        return lights_count, delay_minutes