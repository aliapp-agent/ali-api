"""Domain layer for Ali API.

This package contains the core business logic and domain models.
It is independent of any external dependencies like databases or APIs.
"""

from . import entities, repositories, services
from .exceptions import (
    DomainError,
    RepositoryError,
    UserError,
    UserNotFoundError,
    UserAlreadyExistsError,
    SessionError,
    SessionNotFoundError,
    MessageError,
    MessageNotFoundError,
    DocumentError,
    DocumentNotFoundError,
    BusinessRuleViolationError,
)

__all__ = [
    "entities",
    "repositories", 
    "services",
    # Exceptions
    "DomainError",
    "RepositoryError",
    "UserError",
    "UserNotFoundError", 
    "UserAlreadyExistsError",
    "SessionError",
    "SessionNotFoundError",
    "MessageError",
    "MessageNotFoundError",
    "DocumentError",
    "DocumentNotFoundError",
    "BusinessRuleViolationError",
]