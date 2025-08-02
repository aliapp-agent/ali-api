"""API-related exceptions."""

from typing import (
    Any,
    Dict,
    Optional,
)


class APIError(Exception):
    """Base class for API-related errors."""

    def __init__(
        self,
        message: str = "API error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        result = {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            result["details"] = self.details
        return result


class BadRequestError(APIError):
    """Raised for HTTP 400 Bad Request errors."""

    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 400, details)


class UnauthorizedError(APIError):
    """Raised for HTTP 401 Unauthorized errors."""

    def __init__(
        self,
        message: str = "Unauthorized",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 401, details)


class ForbiddenError(APIError):
    """Raised for HTTP 403 Forbidden errors."""

    def __init__(self, message: str = "Forbidden", resource: Optional[str] = None):
        details = {"resource": resource} if resource else None
        super().__init__(message, 403, details)


class NotFoundError(APIError):
    """Raised for HTTP 404 Not Found errors."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, 404, details if details else None)


class MethodNotAllowedError(APIError):
    """Raised for HTTP 405 Method Not Allowed errors."""

    def __init__(self, method: str, allowed_methods: Optional[list] = None):
        message = f"Method '{method}' not allowed"
        details = {"method": method}
        if allowed_methods:
            details["allowed_methods"] = allowed_methods
            message += f". Allowed methods: {', '.join(allowed_methods)}"
        super().__init__(message, 405, details)


class ConflictError(APIError):
    """Raised for HTTP 409 Conflict errors."""

    def __init__(
        self,
        message: str = "Resource conflict",
        resource: Optional[str] = None,
    ):
        details = {"resource": resource} if resource else None
        super().__init__(message, 409, details)


class UnprocessableEntityError(APIError):
    """Raised for HTTP 422 Unprocessable Entity errors."""

    def __init__(
        self,
        message: str = "Unprocessable entity",
        validation_errors: Optional[Dict[str, Any]] = None,
    ):
        details = (
            {"validation_errors": validation_errors} if validation_errors else None
        )
        super().__init__(message, 422, details)


class RateLimitExceededError(APIError):
    """Raised for HTTP 429 Too Many Requests errors."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[str] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["limit"] = limit
        super().__init__(message, 429, details if details else None)


class InternalServerError(APIError):
    """Raised for HTTP 500 Internal Server Error."""

    def __init__(
        self,
        message: str = "Internal server error",
        error_id: Optional[str] = None,
    ):
        details = {"error_id": error_id} if error_id else None
        super().__init__(message, 500, details)


class BadGatewayError(APIError):
    """Raised for HTTP 502 Bad Gateway errors."""

    def __init__(
        self,
        message: str = "Bad gateway",
        upstream_service: Optional[str] = None,
    ):
        details = {"upstream_service": upstream_service} if upstream_service else None
        super().__init__(message, 502, details)


class ServiceUnavailableError(APIError):
    """Raised for HTTP 503 Service Unavailable errors."""

    def __init__(
        self,
        message: str = "Service unavailable",
        retry_after: Optional[int] = None,
        service: Optional[str] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if service:
            details["service"] = service
        super().__init__(message, 503, details if details else None)


class GatewayTimeoutError(APIError):
    """Raised for HTTP 504 Gateway Timeout errors."""

    def __init__(self, message: str = "Gateway timeout", timeout: Optional[int] = None):
        details = {"timeout": timeout} if timeout else None
        super().__init__(message, 504, details)


class RequestTooLargeError(APIError):
    """Raised for HTTP 413 Request Entity Too Large errors."""

    def __init__(
        self,
        message: str = "Request too large",
        max_size: Optional[int] = None,
        actual_size: Optional[int] = None,
    ):
        details = {}
        if max_size:
            details["max_size"] = max_size
        if actual_size:
            details["actual_size"] = actual_size
        super().__init__(message, 413, details if details else None)


class UnsupportedMediaTypeError(APIError):
    """Raised for HTTP 415 Unsupported Media Type errors."""

    def __init__(self, media_type: str, supported_types: Optional[list] = None):
        message = f"Unsupported media type: {media_type}"
        details = {"media_type": media_type}
        if supported_types:
            details["supported_types"] = supported_types
            message += f". Supported types: {', '.join(supported_types)}"
        super().__init__(message, 415, details)


class RequestTimeoutError(APIError):
    """Raised for HTTP 408 Request Timeout errors."""

    def __init__(self, message: str = "Request timeout", timeout: Optional[int] = None):
        details = {"timeout": timeout} if timeout else None
        super().__init__(message, 408, details)


class LengthRequiredError(APIError):
    """Raised for HTTP 411 Length Required errors."""

    def __init__(self, message: str = "Content-Length header required"):
        super().__init__(message, 411)


class PreconditionFailedError(APIError):
    """Raised for HTTP 412 Precondition Failed errors."""

    def __init__(
        self,
        message: str = "Precondition failed",
        condition: Optional[str] = None,
    ):
        details = {"condition": condition} if condition else None
        super().__init__(message, 412, details)


class ExpectationFailedError(APIError):
    """Raised for HTTP 417 Expectation Failed errors."""

    def __init__(
        self,
        message: str = "Expectation failed",
        expectation: Optional[str] = None,
    ):
        details = {"expectation": expectation} if expectation else None
        super().__init__(message, 417, details)


class TooManyRequestsError(APIError):
    """Raised when client makes too many requests."""

    def __init__(
        self,
        message: str = "Too many requests",
        window: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        details = {}
        if window:
            details["window"] = window
        if limit:
            details["limit"] = limit
        super().__init__(message, 429, details if details else None)


class InvalidAPIVersionError(APIError):
    """Raised when API version is invalid or unsupported."""

    def __init__(self, version: str, supported_versions: Optional[list] = None):
        message = f"Invalid API version: {version}"
        details = {"version": version}
        if supported_versions:
            details["supported_versions"] = supported_versions
            message += f". Supported versions: {', '.join(supported_versions)}"
        super().__init__(message, 400, details)


class MaintenanceModeError(APIError):
    """Raised when API is in maintenance mode."""

    def __init__(
        self,
        message: str = "API is currently under maintenance",
        estimated_completion: Optional[str] = None,
    ):
        details = (
            {"estimated_completion": estimated_completion}
            if estimated_completion
            else None
        )
        super().__init__(message, 503, details)


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""

    def __init__(
        self,
        message: str = "API quota exceeded",
        quota_type: Optional[str] = None,
        reset_time: Optional[str] = None,
    ):
        details = {}
        if quota_type:
            details["quota_type"] = quota_type
        if reset_time:
            details["reset_time"] = reset_time
        super().__init__(message, 402, details if details else None)


class DependencyError(APIError):
    """Raised when external dependency fails."""

    def __init__(self, service: str, message: str = "External service error"):
        details = {"service": service}
        super().__init__(f"{message}: {service}", 502, details)


class CircuitBreakerOpenError(APIError):
    """Raised when circuit breaker is open."""

    def __init__(self, service: str, retry_after: Optional[int] = None):
        message = f"Circuit breaker open for service: {service}"
        details = {"service": service}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, 503, details)
