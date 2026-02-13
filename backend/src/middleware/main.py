import logging
import time
import uuid

from fastapi import Request, status
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedMiddleware(BaseHTTPMiddleware):
    """Middleware for logging, performance monitoring, and error handling."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Добавляем кастомные заголовки
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"

            logger.info(
                f"Request {request.method} {request.url.path} "
                f"completed in {process_time:.4f}s with status {response.status_code}"
            )
            return response

        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(f"Error processing request {request_id}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal Server Error",
                    "request_id": request_id,
                },
            )