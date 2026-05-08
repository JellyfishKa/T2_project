import pytest
from fastapi import HTTPException

from src.config import settings
from src.security import ensure_benchmark_run_enabled, ensure_bulk_location_delete_enabled


def test_bulk_delete_disabled_by_default():
    old_value = settings.security_allow_bulk_location_delete
    settings.security_allow_bulk_location_delete = False
    try:
        with pytest.raises(HTTPException) as exc:
            ensure_bulk_location_delete_enabled()
        assert exc.value.status_code == 403
    finally:
        settings.security_allow_bulk_location_delete = old_value


def test_benchmark_run_disabled_by_default():
    old_value = settings.security_allow_benchmark_run
    settings.security_allow_benchmark_run = False
    try:
        with pytest.raises(HTTPException) as exc:
            ensure_benchmark_run_enabled()
        assert exc.value.status_code == 403
    finally:
        settings.security_allow_benchmark_run = old_value
