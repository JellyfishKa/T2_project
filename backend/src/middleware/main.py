import logging
import time
import uuid

from fastapi import Request, status
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware

from src.logging_config import request_id_var

logger = logging.getLogger(__name__)


class AdvancedMiddleware(BaseHTTPMiddleware):
    """Middleware for logging, performance monitoring, and error handling."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"

            logger.info(
                "%s %s → %d (%.0fms) rid=%s",
                request.method,
                request.url.path,
                response.status_code,
                process_time * 1000,
                request_id,
            )
            return response

        except Exception as exc:
            process_time = time.time() - start_time
            logger.error("Unhandled exception rid=%s: %s", request_id, exc)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal Server Error",
                    "request_id": request_id,
                },
            )
        finally:
            request_id_var.reset(token)
