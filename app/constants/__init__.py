"""Application constants module."""

from .auth import *
from .database import *
from .http import *
from .validation import *

__all__ = [
    # Auth constants
    "JWT_ALGORITHM_DEFAULT",
    "ACCESS_TOKEN_EXPIRE_DAYS_DEFAULT",
    "PASSWORD_MIN_LENGTH",
    "TOKEN_TYPE_BEARER",
    # Database constants
    "DEFAULT_POOL_SIZE",
    "DEFAULT_MAX_OVERFLOW",
    "CONNECTION_TIMEOUT",
    "POOL_RECYCLE_TIME",
    # HTTP constants
    "DEFAULT_RATE_LIMIT",
    "CORS_MAX_AGE",
    "REQUEST_TIMEOUT",
    # Validation constants
    "EMAIL_REGEX",
    "PASSWORD_REGEX",
    "SESSION_ID_REGEX",
    "MAX_MESSAGE_LENGTH",
]
