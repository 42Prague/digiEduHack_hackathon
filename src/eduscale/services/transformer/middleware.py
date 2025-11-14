"""Middleware for HTTP error logging."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class HTTPErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure all HTTP errors are logged.

    - 4xx responses: logged at WARN level
    - 5xx responses: logged at ERROR level with stack trace
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log errors.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Extract request details
        file_id = None
        region_id = None

        # Try to extract file_id and region_id from request body if available
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                file_id = body.get("file_id")
                region_id = body.get("region_id")
            except Exception:
                # Body may not be JSON or already consumed
                pass

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Log errors based on status code
        if 400 <= response.status_code < 500:
            # 4xx: Client errors - log at WARN level
            logger.warning(
                "Client error response",
                extra={
                    "http_status": response.status_code,
                    "method": request.method,
                    "path": request.url.path,
                    "file_id": file_id,
                    "region_id": region_id,
                    "duration_ms": duration_ms,
                },
            )
        elif response.status_code >= 500:
            # 5xx: Server errors - log at ERROR level with stack trace
            logger.error(
                "Server error response",
                extra={
                    "http_status": response.status_code,
                    "method": request.method,
                    "path": request.url.path,
                    "file_id": file_id,
                    "region_id": region_id,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )

        return response
