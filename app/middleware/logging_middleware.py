import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every incoming API request with method, path, status, and latency."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
        )
        return response
