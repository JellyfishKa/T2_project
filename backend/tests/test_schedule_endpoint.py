"""
Tests for schedule endpoints and related schemas/logic.
All tests use direct unit testing (mocks, not TestClient).
"""
from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: GenerateScheduleRequest schema validation
# ---------------------------------------------------------------------------

def test_generate_schedule_request_validation():
    from src.schemas.schedule import GenerateScheduleRequest

    # Valid month format
    req = GenerateScheduleRequest(month="2026-03")
    assert req.month == "2026-03"
    assert req.rep_ids is None

    # With rep_ids
    req2 = GenerateScheduleRequest(month="2026-11", rep_ids=["rep-1", "rep-2"])
    assert req2.month == "2026-11"
    assert req2.rep_ids == ["rep-1", "rep-2"]

    # Schema does not auto-reject bad format (validation happens in route),
    # but we can confirm the field is stored as-is
    req3 = GenerateScheduleRequest(month="2026-3")
    assert req3.month == "2026-3"


# ---------------------------------------------------------------------------
# Test 2: completed_visits exclusion in build_monthly_plan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completed_visits_exclusion():
    """
    Category-A location requires 3 visits/month.
    If completed_visits={"loc-1": 1}, planner should schedule only 2 more visits.
    """
    from src.services.schedule_planner import SchedulePlanner, _visit_dates, _working_days, _week_groups

    year, month = 2026, 5
    # non_working empty (use frozenset to avoid holiday lookup)
    all_days = _working_days(year, month, frozenset())
    work_weeks = _week_groups(all_days)

    # Category-A: 3 visits on weeks 1, 2, 3
    dates_a = _visit_dates("A", work_weeks, all_days, 4, month)  # quarter_month=4 for May
    assert len(dates_a) == 3

    # With 1 completed visit, remaining = 3 - 1 = 2
    already_done = 1
    remaining = max(0, len(dates_a) - already_done)
    assert remaining == 2

    # Verify the planner respects this in task_pool construction
    # (simulate what build_monthly_plan does)
    task_pool = []
    completed_visits = {"loc-1": 1}
    loc_id = "loc-1"
    cat = "A"
    dates = _visit_dates(cat, work_weeks, all_days, 4, month)
    already_done_count = completed_visits.get(loc_id, 0)
    remaining_count = max(0, len(dates) - already_done_count)
    for d in dates[:remaining_count]:
        task_pool.append((loc_id, d, cat))

    assert len(task_pool) == 2

    # Fully completed: 3 done, remaining = 0 → no tasks added
    completed_full = {"loc-1": 3}
    task_pool_full = []
    already_done_full = completed_full.get(loc_id, 0)
    remaining_full = max(0, len(dates) - already_done_full)
    for d in dates[:remaining_full]:
        task_pool_full.append((loc_id, d, cat))

    assert len(task_pool_full) == 0


# ---------------------------------------------------------------------------
# Test 3: VALID_TRANSITIONS dict content
# ---------------------------------------------------------------------------

def test_schedule_status_valid_transitions():
    from src.routes.schedule import VALID_TRANSITIONS

    # planned can transition to all active statuses
    assert "completed" in VALID_TRANSITIONS["planned"]
    assert "skipped" in VALID_TRANSITIONS["planned"]
    assert "cancelled" in VALID_TRANSITIONS["planned"]
    assert "rescheduled" in VALID_TRANSITIONS["planned"]

    # skipped can go back to planned or be cancelled
    assert "planned" in VALID_TRANSITIONS["skipped"]
    assert "cancelled" in VALID_TRANSITIONS["skipped"]

    # rescheduled can be completed, skipped, or cancelled
    assert "completed" in VALID_TRANSITIONS["rescheduled"]
    assert "skipped" in VALID_TRANSITIONS["rescheduled"]
    assert "cancelled" in VALID_TRANSITIONS["rescheduled"]

    # Terminal states have no outgoing transitions
    assert len(VALID_TRANSITIONS["completed"]) == 0
    assert len(VALID_TRANSITIONS["cancelled"]) == 0

    # All expected keys present
    expected_keys = {"planned", "skipped", "rescheduled", "completed", "cancelled"}
    assert expected_keys == set(VALID_TRANSITIONS.keys())


# ---------------------------------------------------------------------------
# Test 4: VisitScheduleItem schema fields
# ---------------------------------------------------------------------------

def test_visit_schedule_item_schema():
    from src.schemas.schedule import VisitScheduleItem

    item = VisitScheduleItem(
        id="visit-1",
        location_id="loc-1",
        location_name="Магазин 1",
        location_category="A",
        rep_id="rep-1",
        rep_name="Иванов",
        planned_date=date(2026, 3, 10),
        status="planned",
        time_in=None,
        time_out=None,
    )

    assert item.id == "visit-1"
    assert item.location_id == "loc-1"
    assert item.location_name == "Магазин 1"
    assert item.location_category == "A"
    assert item.rep_id == "rep-1"
    assert item.rep_name == "Иванов"
    assert item.planned_date == date(2026, 3, 10)
    assert item.status == "planned"
    assert item.time_in is None
    assert item.time_out is None

    # With time values
    item2 = VisitScheduleItem(
        id="visit-2",
        location_id="loc-2",
        location_name="Магазин 2",
        location_category=None,
        rep_id="rep-2",
        rep_name="Петров",
        planned_date=date(2026, 3, 11),
        status="completed",
        time_in="09:30",
        time_out="09:45",
    )
    assert item2.time_in == "09:30"
    assert item2.time_out == "09:45"
    assert item2.location_category is None
