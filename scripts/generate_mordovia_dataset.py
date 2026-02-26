"""
Генератор датасета 250 торговых точек Мордовии.

Использование:
    python scripts/generate_mordovia_dataset.py

Результат записывается в data/locations_mordovia_250.json
"""

import json
import math
import random
import sys
from pathlib import Path

random.seed(42)

# ---------------------------------------------------------------------------
# Районы Мордовии с реальными координатами центров и радиусом разброса
# ---------------------------------------------------------------------------
DISTRICTS = {
    "г.о. Саранск":            {"count": 30, "lat": 54.1838, "lon": 45.1749, "radius_km": 8},
    "Ардатовский район":        {"count": 10, "lat": 54.8490, "lon": 46.2360, "radius_km": 3},
    "Атяшевский район":         {"count": 10, "lat": 54.5980, "lon": 45.8880, "radius_km": 3},
    "Атюрьевский район":        {"count": 10, "lat": 54.0310, "lon": 43.6820, "radius_km": 3},
    "Большеберезниковский район":{"count": 10, "lat": 54.2670, "lon": 45.7650, "radius_km": 3},
    "Большеигнатовский район":  {"count": 10, "lat": 54.4810, "lon": 44.8710, "radius_km": 3},
    "Дубёнский район":          {"count": 10, "lat": 54.2650, "lon": 46.0880, "radius_km": 3},
    "Ельниковский район":       {"count": 10, "lat": 54.3900, "lon": 43.5550, "radius_km": 3},
    "Зубово-Полянский район":   {"count": 10, "lat": 54.0520, "lon": 42.8310, "radius_km": 3},
    "Инсарский район":          {"count": 10, "lat": 53.8760, "lon": 44.3770, "radius_km": 3},
    "Ичалковский район":        {"count": 10, "lat": 54.1260, "lon": 46.5840, "radius_km": 3},
    "Кадошкинский район":       {"count": 10, "lat": 54.0200, "lon": 43.5360, "radius_km": 3},
    "Ковылкинский район":       {"count": 10, "lat": 53.9060, "lon": 43.9190, "radius_km": 3},
    "Кочкуровский район":       {"count": 10, "lat": 54.0500, "lon": 45.5710, "radius_km": 3},
    "Краснослободский район":   {"count": 10, "lat": 54.4190, "lon": 43.7770, "radius_km": 3},
    "Лямбирский район":         {"count": 10, "lat": 54.2350, "lon": 45.6250, "radius_km": 3},
    "Ромодановский район":      {"count": 10, "lat": 54.4300, "lon": 45.3710, "radius_km": 3},
    "Рузаевский район":         {"count": 10, "lat": 54.0570, "lon": 44.9520, "radius_km": 3},
    "Старошайговский район":    {"count": 10, "lat": 54.3500, "lon": 44.2580, "radius_km": 3},
    "Темниковский район":       {"count": 10, "lat": 54.6360, "lon": 43.1990, "radius_km": 3},
    "Теньгушевский район":      {"count": 10, "lat": 54.8440, "lon": 43.6140, "radius_km": 3},
    "Торбеевский район":        {"count": 10, "lat": 54.0880, "lon": 43.0920, "radius_km": 3},
    "Чамзинский район":         {"count": 10, "lat": 54.2310, "lon": 46.2890, "radius_km": 3},
}

# ---------------------------------------------------------------------------
# Распределение категорий
# ---------------------------------------------------------------------------
CATEGORY_DISTRIBUTION = {
    "A": {"share": 0.20, "time_window": ("09:00", "12:00")},
    "B": {"share": 0.30, "time_window": ("09:00", "15:00")},
    "C": {"share": 0.20, "time_window": ("09:00", "18:00")},
    "D": {"share": 0.30, "time_window": ("09:00", "18:00")},
}

# ---------------------------------------------------------------------------
# Типичные названия торговых точек
# ---------------------------------------------------------------------------
STORE_TYPES = [
    "Магазин", "Супермаркет", "Минимаркет", "Торговая точка",
    "Продуктовый", "Универмаг", "Гастроном", "Продукты",
    "Торговый павильон", "Киоск",
]

STORE_NAMES = [
    "Удача", "Перекрёсток", "Волга", "Мордовия", "Центральный",
    "Семёновский", "Уют", "Родник", "Ромашка", "Лидер",
    "Берёзка", "Колос", "Рябина", "Восток", "Север",
    "Заря", "Дружба", "Нива", "Сокол", "Юбилейный",
    "Победа", "Радуга", "Маяк", "Горизонт", "Полёт",
]


def _km_to_deg_lat(km: float) -> float:
    """Перевод км в градусы широты."""
    return km / 111.0


def _km_to_deg_lon(km: float, lat: float) -> float:
    """Перевод км в градусы долготы с учётом широты."""
    return km / (111.0 * math.cos(math.radians(lat)))


def _random_point_around(center_lat: float, center_lon: float, radius_km: float):
    """Генерирует случайную точку в пределах radius_km от центра."""
    r = radius_km * math.sqrt(random.random())
    angle = random.uniform(0, 2 * math.pi)
    d_lat = _km_to_deg_lat(r * math.cos(angle))
    d_lon = _km_to_deg_lon(r * math.sin(angle), center_lat)
    return round(center_lat + d_lat, 6), round(center_lon + d_lon, 6)


def _assign_categories(count: int) -> list:
    """Распределяет категории по заданным долям."""
    cats = []
    buckets = {
        cat: max(1, round(info["share"] * count))
        for cat, info in CATEGORY_DISTRIBUTION.items()
    }
    # Корректировка итогового количества
    total = sum(buckets.values())
    diff = count - total
    for cat in ["A", "B", "C", "D"]:
        if diff == 0:
            break
        buckets[cat] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1

    for cat, n in buckets.items():
        cats.extend([cat] * n)

    random.shuffle(cats)
    return cats[:count]


def generate_dataset() -> list:
    locations = []
    idx = 1

    for district, info in DISTRICTS.items():
        count = info["count"]
        center_lat = info["lat"]
        center_lon = info["lon"]
        radius_km = info["radius_km"]
        categories = _assign_categories(count)

        city = "Саранск" if "Саранск" in district else district.replace(" район", "")

        for i, category in enumerate(categories):
            lat, lon = _random_point_around(center_lat, center_lon, radius_km)
            tw = CATEGORY_DISTRIBUTION[category]["time_window"]
            store_type = random.choice(STORE_TYPES)
            store_name = random.choice(STORE_NAMES)
            name = f"{store_type} «{store_name}» {district[:3]}-{idx}"

            locations.append({
                "name": name,
                "lat": lat,
                "lon": lon,
                "time_window_start": tw[0],
                "time_window_end": tw[1],
                "category": category,
                "city": city,
                "district": district,
                "address": f"{district}, точка #{idx}",
            })
            idx += 1

    return locations


def main():
    project_root = Path(__file__).parent.parent
    output_path = project_root / "data" / "locations_mordovia_250.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    locations = generate_dataset()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    # Статистика
    total = len(locations)
    by_cat = {}
    by_dist = {}
    for loc in locations:
        cat = loc["category"]
        dist = loc["district"]
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_dist[dist] = by_dist.get(dist, 0) + 1

    print(f"Сгенерировано {total} ТТ → {output_path}")
    print("\nПо категориям:")
    for cat in ["A", "B", "C", "D"]:
        print(f"  {cat}: {by_cat.get(cat, 0)}")
    print(f"\nПо районам (всего {len(by_dist)}):")
    for dist, n in sorted(by_dist.items()):
        print(f"  {dist}: {n}")


if __name__ == "__main__":
    main()
