from fastapi import Header, HTTPException, status

from src.config import settings


def _normalize_key(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def ensure_api_access(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.security_enable_api_key_auth:
        return
    expected = _normalize_key(settings.security_api_key)
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key auth is enabled but SECURITY_API_KEY is missing",
        )
    if _normalize_key(x_api_key) != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def ensure_admin_access(x_admin_api_key: str | None = Header(default=None)) -> None:
    expected_admin = _normalize_key(settings.security_admin_api_key)

    if settings.security_enable_api_key_auth and expected_admin is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin auth is enabled but SECURITY_ADMIN_API_KEY is missing",
        )

    if settings.security_enable_api_key_auth:
        if _normalize_key(x_admin_api_key) != expected_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )


def ensure_bulk_location_delete_enabled() -> None:
    if not settings.security_allow_bulk_location_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bulk location delete is disabled by configuration",
        )


def ensure_benchmark_run_enabled() -> None:
    if not settings.security_allow_benchmark_run:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benchmark run endpoints are disabled by configuration",
        )
