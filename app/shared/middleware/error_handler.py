"""Error handling middleware for Ali API.

This module provides centralized error handling middleware
to ensure consistent error responses across the application.
"""

import traceback
from typing import Callable

from fastapi import (
    HTTPException,
    Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import logger
from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DocumentNotFoundError,
    DomainException,
    InsufficientPermissionsError,
    MessageNotFoundError,
    QuotaExceededError,
    RateLimitExceededError,
    ResourceNotFoundError,
    SessionNotFoundError,
    UserNotFoundError,
    ValidationError,
)
from app.shared.response_models import (
    ErrorResponse,
    ValidationErrorResponse,
)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and errors consistently."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions that occur.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the handler or error response
        """
        try:
            response = await call_next(request)
            return response

        except HTTPException as exc:
            # FastAPI HTTP exceptions - let them pass through
            raise exc

        except RequestValidationError as exc:
            # Pydantic validation errors
            logger.warning(
                "validation_error",
                path=request.url.path,
                method=request.method,
                errors=exc.errors(),
            )

            field_errors = {}
            for error in exc.errors():
                field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
                if field not in field_errors:
                    field_errors[field] = []
                field_errors[field].append(error["msg"])

            error_response = ValidationErrorResponse(
                message="Validation failed", field_errors=field_errors
            )

            return JSONResponse(status_code=422, content=error_response.model_dump())

        except DomainException as exc:
            # Domain-specific exceptions
            status_code = self._get_status_code_for_domain_exception(exc)

            logger.warning(
                "domain_exception",
                exception_type=type(exc).__name__,
                message=str(exc),
                path=request.url.path,
                method=request.method,
            )

            error_response = ErrorResponse(
                error=type(exc).__name__,
                message=str(exc),
                details=getattr(exc, "details", None),
            )

            return JSONResponse(
                status_code=status_code, content=error_response.model_dump()
            )

        except Exception as exc:
            # Unexpected errors
            error_id = logger.error(
                "unexpected_error",
                exception_type=type(exc).__name__,
                message=str(exc),
                path=request.url.path,
                method=request.method,
                traceback=traceback.format_exc(),
            )

            error_response = ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred",
                details={"error_id": error_id} if error_id else None,
            )

            return JSONResponse(status_code=500, content=error_response.model_dump())

    def _get_status_code_for_domain_exception(self, exc: DomainException) -> int:
        """Get the appropriate HTTP status code for a domain exception.

        Args:
            exc: The domain exception

        Returns:
            int: HTTP status code
        """
        exception_status_map = {
            # 400 Bad Request
            ValidationError: 400,
            BusinessRuleViolationError: 400,
            # 401 Unauthorized
            AuthenticationError: 401,
            # 403 Forbidden
            AuthorizationError: 403,
            InsufficientPermissionsError: 403,
            # 404 Not Found
            ResourceNotFoundError: 404,
            UserNotFoundError: 404,
            SessionNotFoundError: 404,
            MessageNotFoundError: 404,
            DocumentNotFoundError: 404,
            # 409 Conflict
            ConflictError: 409,
            # 429 Too Many Requests
            RateLimitExceededError: 429,
            QuotaExceededError: 429,
        }

        return exception_status_map.get(type(exc), 500)


def create_error_handler() -> ErrorHandlerMiddleware:
    """Create and configure the error handler middleware.

    Returns:
        ErrorHandlerMiddleware: Configured middleware instance
    """
    return ErrorHandlerMiddleware()
