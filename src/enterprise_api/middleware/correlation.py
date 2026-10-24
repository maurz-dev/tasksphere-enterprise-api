"""Correlation ID and performance tracing middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from enterprise_api.core.logging import logger


class CorrelationAndTimingMiddleware(BaseHTTPMiddleware):
    """Injects X-Request-ID and tracks request execution latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract or generate Correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Request {request.method} {request.url.path} failed after {process_time_ms:.2f}ms "
                f"[request_id={request_id}]"
            )
            raise

        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

        # Filter out noisy health checks from verbose logging
        if not request.url.path.endswith("/health"):
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} "
                f"({process_time_ms:.2f}ms) [id={request_id}]"
            )

        return response
