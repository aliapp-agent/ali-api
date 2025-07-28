"""Repository interfaces for Ali API.

This module contains abstract repository interfaces that define
the contracts for data access without specifying implementation details.
"""

from .user_repository import UserRepositoryInterface
from .session_repository import SessionRepositoryInterface
from .message_repository import MessageRepositoryInterface
from .document_repository import DocumentRepositoryInterface

__all__ = [
    "UserRepositoryInterface",
    "SessionRepositoryInterface", 
    "MessageRepositoryInterface",
    "DocumentRepositoryInterface",
]