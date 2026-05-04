"""
Tests for recently added features:
- home_lat/home_lon on SalesRep schemas
- _estimate_route_hours with depot
- UploadLocationsResponse skipped field
- Optimizer._balanced_reorder
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Test 1: SalesRepCreate/SalesRepResponse home_lat/home_lon defaults
# ---------------------------------------------------------------------------

def test_sales_rep_schema_home_coords():
    from src.schemas.reps import SalesRepCreate, SalesRepResponse
    from datetime import datetime

    # SalesRepCreate: default coords
    rep = SalesRepCreate(name="Иванов Иван")
    assert rep.home_lat == pytest.approx(54.1871)
    assert rep.home_lon == pytest.approx(45.1749)
    assert rep.status == "active"

    # SalesRepCreate: custom coords
    rep2 = SalesRepCreate(name="Петров Пётр", home_lat=55.0, home_lon=46.0)
    assert rep2.home_lat == pytest.approx(55.0)
    assert rep2.home_lon == pytest.approx(46.0)

    # SalesRepResponse: has home_lat/home_lon with defaults
    resp = SalesRepResponse(
        id="rep-1",
        name="Иванов Иван",
        status="active",
        created_at=datetime(2026, 1, 1, 0, 0, 0),
    )
    assert resp.home_lat == pytest.approx(54.1871)
    assert resp.home_lon == pytest.approx(45.1749)


# ---------------------------------------------------------------------------
# Test 2: SalesRepUpdate accepts optional home_lat/home_lon
# ---------------------------------------------------------------------------

def test_sales_rep_update_home_coords():
    from src.schemas.reps import SalesRepUpdate

    # Empty update
    upd = SalesRepUpdate()
    assert upd.home_lat is None
    assert upd.home_lon is None

    # Partial update with only lat
    upd2 = SalesRepUpdate(home_lat=55.5)
    assert upd2.home_lat == pytest.approx(55.5)
    assert upd2.home_lon is None

    # Full coords update
    upd3 = SalesRepUpdate(home_lat=54.5, home_lon=45.5)
    assert upd3.home_lat == pytest.approx(54.5)
    assert upd3.home_lon == pytest.approx(45.5)

    # Status update without coords
    upd4 = SalesRepUpdate(status="sick")
    assert upd4.status == "sick"
    assert upd4.home_lat is None
    assert upd4.home_lon is None


# ---------------------------------------------------------------------------
# Test 3: _estimate_route_hours returns positive float
# ---------------------------------------------------------------------------

def test_estimate_route_hours_with_depot():
    from src.services.schedule_planner import _estimate_route_hours
    from src.database.models import Location

    # Build 3 mock Location objects
    def make_loc(loc_id: str, lat: float, lon: float, cat: str = "B") -> Location:
        loc = MagicMock(spec=Location)
        loc.id = loc_id
        loc.name = f"Магазин {loc_id}"
        loc.lat = lat
        loc.lon = lon
        loc.category = cat
        return loc

    locations = [
        make_loc("loc-1", 54.18, 45.17, "A"),
        make_loc("loc-2", 54.20, 45.20, "B"),
        make_loc("loc-3", 54.22, 45.15, "C"),
    ]

    result = _estimate_route_hours(
        locations,
        depot_lat=54.1871,
        depot_lon=45.1749,
    )
    assert isinstance(result, float)
    assert result > 0.0

    # Single location: returns VISIT_DURATION_MIN / 60
    from src.services.schedule_planner import VISIT_DURATION_MIN
    single = _estimate_route_hours([locations[0]])
    assert single == pytest.approx(VISIT_DURATION_MIN / 60, abs=0.01)

    # Empty list: returns 0.0
    empty = _estimate_route_hours([])
    assert empty == 0.0


# ---------------------------------------------------------------------------
# Test 4: UploadLocationsResponse has skipped field defaulting to []
# ---------------------------------------------------------------------------

def test_upload_response_has_skipped_field():
    from src.schemas.locations import UploadLocationsResponse

    resp = UploadLocationsResponse()
    assert hasattr(resp, "skipped")
    assert resp.skipped == []
    assert resp.created == []
    assert resp.errors == []
    assert resp.total_processed == 0

    # With skipped names
    resp2 = UploadLocationsResponse(
        skipped=["Дубль 1", "Дубль 2"],
        total_processed=4,
    )
    assert resp2.skipped == ["Дубль 1", "Дубль 2"]
    assert resp2.total_processed == 4


# ---------------------------------------------------------------------------
# Test 5: Optimizer._balanced_reorder returns all locations
# ---------------------------------------------------------------------------

def test_greedy_reorder_uses_depot():
    from src.services.optimize import Optimizer
    from src.models.schemas import Location as PydanticLocation

    mock_db = MagicMock()
    optimizer = Optimizer(db_session=mock_db)

    def make_ploc(loc_id: str, lat: float, lon: float, priority: str = "B") -> PydanticLocation:
        return PydanticLocation(
            ID=loc_id,
            name=f"Магазин {loc_id}",
            address=f"ул. Тестовая, {loc_id}",
            lat=lat,
            lon=lon,
            time_window_start="09:00",
            time_window_end="18:00",
            priority=priority,
        )

    locations = [
        make_ploc("loc-1", 54.18, 45.17, "A"),
        make_ploc("loc-2", 54.20, 45.20, "B"),
        make_ploc("loc-3", 54.22, 45.15, "C"),
    ]

    result = optimizer._balanced_reorder(locations)

    # All 3 locations returned — no more, no fewer
    assert len(result) == 3
    result_ids = {loc.ID for loc in result}
    assert result_ids == {"loc-1", "loc-2", "loc-3"}

    # Single location: returns same location
    single = optimizer._balanced_reorder([locations[0]])
    assert len(single) == 1
    assert single[0].ID == "loc-1"
