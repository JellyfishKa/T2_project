"""
Unit tests for geo_utils module.
Tests haversine, distance matrix, region detection, and formatting utilities.
"""

import pytest
from src.models.geo_utils import (
    build_constraints_text,
    build_nearest_neighbors,
    compute_distance_matrix,
    detect_region_info,
    estimate_fuel_cost,
    format_locations_compact,
    format_distance_pairs,
    format_nearest_neighbors,
    haversine,
    infer_category,
)


class TestHaversine:
    def test_same_point_zero_distance(self):
        assert haversine(55.75, 37.62, 55.75, 37.62) == 0.0

    def test_known_distance_moscow_spb(self):
        """Moscow to Saint Petersburg ~634 km."""
        d = haversine(55.7558, 37.6173, 59.9343, 30.3351)
        assert 625 < d < 645

    def test_short_distance_within_city(self):
        """Two points ~1km apart in Saransk."""
        d = haversine(54.1838, 45.1749, 54.1928, 45.1749)
        assert 0.5 < d < 1.5

    def test_symmetric(self):
        d1 = haversine(54.18, 45.17, 54.85, 46.23)
        d2 = haversine(54.85, 46.23, 54.18, 45.17)
        assert abs(d1 - d2) < 0.001


class TestDistanceMatrix:
    @pytest.fixture
    def three_locations(self):
        return [
            {"ID": "a", "name": "A", "lat": 54.18, "lon": 45.17, "priority": "A"},
            {"ID": "b", "name": "B", "lat": 54.06, "lon": 44.95, "priority": "B"},
            {"ID": "c", "name": "C", "lat": 54.40, "lon": 45.33, "priority": "C"},
        ]

    def test_matrix_shape(self, three_locations):
        dm = compute_distance_matrix(three_locations)
        assert len(dm) == 3
        assert all(len(row) == 3 for row in dm)

    def test_diagonal_zero(self, three_locations):
        dm = compute_distance_matrix(three_locations)
        for i in range(3):
            assert dm[i][i] == 0.0

    def test_symmetric(self, three_locations):
        dm = compute_distance_matrix(three_locations)
        for i in range(3):
            for j in range(3):
                assert dm[i][j] == dm[j][i]

    def test_positive_distances(self, three_locations):
        dm = compute_distance_matrix(three_locations)
        for i in range(3):
            for j in range(3):
                if i != j:
                    assert dm[i][j] > 0


class TestDetectRegionInfo:
    def test_empty_locations(self):
        info = detect_region_info([])
        assert info["classification"] == "rural"
        assert info["area_km2"] == 0.0

    def test_urban_detection_dense_points(self):
        """Many points in small area should be urban."""
        locs = [
            {"lat": 54.183 + i * 0.001, "lon": 45.175 + j * 0.001}
            for i in range(5) for j in range(5)
        ]
        info = detect_region_info(locs)
        assert info["classification"] == "urban"

    def test_rural_detection_spread_points(self):
        """Points spread across Mordovia should be rural."""
        locs = [
            {"lat": 54.18, "lon": 45.17},
            {"lat": 54.85, "lon": 46.23},
            {"lat": 54.06, "lon": 42.83},
        ]
        info = detect_region_info(locs)
        assert info["classification"] == "rural"

    def test_center_point(self):
        locs = [
            {"lat": 54.0, "lon": 45.0},
            {"lat": 56.0, "lon": 47.0},
        ]
        info = detect_region_info(locs)
        assert info["center"] == (55.0, 46.0)

    def test_bbox(self):
        locs = [
            {"lat": 53.0, "lon": 42.0},
            {"lat": 55.0, "lon": 46.0},
        ]
        info = detect_region_info(locs)
        assert info["bbox"] == (53.0, 42.0, 55.0, 46.0)


class TestEstimateFuelCost:
    def test_default_rate(self):
        assert estimate_fuel_cost(100) == 700.0

    def test_custom_rate(self):
        assert estimate_fuel_cost(100, rate=10.0) == 1000.0

    def test_zero_distance(self):
        assert estimate_fuel_cost(0) == 0.0


class TestInferCategory:
    def test_direct_categories(self):
        assert infer_category("A") == "A"
        assert infer_category("b") == "B"
        assert infer_category("C") == "C"
        assert infer_category("D") == "D"

    def test_mapped_priorities(self):
        assert infer_category("high") == "A"
        assert infer_category("MEDIUM") == "B"
        assert infer_category("low") == "C"
        assert infer_category("QUARTERLY") == "D"

    def test_unknown_defaults_to_c(self):
        assert infer_category("unknown") == "C"


class TestBuildNearestNeighbors:
    def test_k3_with_4_points(self):
        dm = [
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 5],
            [30, 25, 5, 0],
        ]
        nn = build_nearest_neighbors(dm, k=3)
        assert len(nn) == 4
        # Point 0's nearest should be 1 (10km)
        assert nn[0][0] == (1, 10)

    def test_k_larger_than_points(self):
        dm = [[0, 5], [5, 0]]
        nn = build_nearest_neighbors(dm, k=5)
        assert len(nn[0]) == 1  # only 1 neighbor available


class TestFormatLocationsCompact:
    def test_basic_format(self):
        locs = [{"ID": "p1", "name": "Store", "lat": 54.18, "lon": 45.17, "priority": "high"}]
        text = format_locations_compact(locs)
        assert "p1|Store|54.18,45.17|priority=A" in text


class TestBuildConstraintsText:
    def test_defaults_when_none(self):
        text = build_constraints_text(None)
        assert "Team: 1" in text
        assert "09:00-18:00" in text
        assert "7.0" in text

    def test_custom_constraints(self):
        text = build_constraints_text({
            "team_size": 4,
            "fuel_rate": 8.5,
            "working_hours": {"start": "08:00", "end": "17:00"},
            "category_rules": {"A": {"visits_per_month": 3}},
        })
        assert "Team: 4" in text
        assert "08:00-17:00" in text
        assert "8.5" in text
        assert "Cat A: 3x/month" in text
