"""Request logging middleware for Ali API.

This module provides middleware for logging HTTP requests and responses
with performance metrics and security information.
"""

import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the handler
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        user_agent = request.headers.get("user-agent")
        client_ip = self._get_client_ip(request)

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            query_params=query_params,
            user_agent=user_agent,
            client_ip=client_ip,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful request
            logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                process_time=process_time,
                response_size=response.headers.get("content-length"),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log failed request
            logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                process_time=process_time,
                exception=str(exc),
            )

            # Re-raise the exception
            raise exc

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Args:
            request: The incoming request

        Returns:
            str: Client IP address
        """
        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header (some proxies use this)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"


def create_request_logging_middleware() -> RequestLoggingMiddleware:
    """Create and configure the request logging middleware.

    Returns:
        RequestLoggingMiddleware: Configured middleware instance
    """
    return RequestLoggingMiddleware()
