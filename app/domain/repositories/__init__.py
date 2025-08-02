"""Repository interfaces for Ali API.

This module contains abstract repository interfaces that define
the contracts for data access without specifying implementation details.
"""

from .document_repository import DocumentRepositoryInterface
from .message_repository import MessageRepositoryInterface
from .session_repository import SessionRepositoryInterface
from .user_repository import UserRepositoryInterface

__all__ = [
    "UserRepositoryInterface",
    "SessionRepositoryInterface",
    "MessageRepositoryInterface",
    "DocumentRepositoryInterface",
]
