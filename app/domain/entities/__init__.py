"""Domain entities for Ali API.

This module contains pure domain entities that represent
the core business objects without any external dependencies.
"""

from .document_entity import (
    DocumentCategory,
    DocumentContent,
    DocumentEntity,
    DocumentMetadata,
    DocumentSource,
    DocumentStatus,
    DocumentType,
)
from .message_entity import (
    MessageContext,
    MessageEntity,
    MessageMetadata,
    MessageRole,
    MessageStatus,
)
from .session_entity import (
    SessionEntity,
    SessionMetadata,
    SessionStats,
    SessionStatus,
    SessionType,
)
from .user_entity import (
    UserEntity,
    UserPreferences,
    UserProfile,
    UserRole,
    UserStatus,
)

__all__ = [
    # User
    "UserEntity",
    "UserRole",
    "UserStatus",
    "UserProfile",
    "UserPreferences",
    # Session
    "SessionEntity",
    "SessionStatus",
    "SessionType",
    "SessionMetadata",
    "SessionStats",
    # Message
    "MessageEntity",
    "MessageRole",
    "MessageStatus",
    "MessageMetadata",
    "MessageContext",
    # Document
    "DocumentEntity",
    "DocumentStatus",
    "DocumentType",
    "DocumentCategory",
    "DocumentMetadata",
    "DocumentSource",
    "DocumentContent",
]
