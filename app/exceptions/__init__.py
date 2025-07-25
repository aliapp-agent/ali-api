"""Custom exceptions for the application.

This module defines custom exception classes that provide better error handling
and more specific error messages throughout the application.
"""

from .api import *
from .auth import *
from .database import *
from .validation import *

__all__ = [
    # Authentication exceptions
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "TokenInvalidError",
    "SessionNotFoundError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    # Database exceptions
    "DatabaseConnectionError",
    "DatabaseOperationError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "DatabaseTimeoutError",
    # Validation exceptions
    "ValidationError",
    "InvalidInputError",
    "InvalidEmailError",
    "InvalidPasswordError",
    "InvalidSessionIdError",
    "StringTooLongError",
    "SecurityViolationError",
    # API exceptions
    "APIError",
    "RateLimitExceededError",
    "RequestTooLargeError",
    "UnsupportedMediaTypeError",
    "ServiceUnavailableError",
    "InternalServerError",
]
