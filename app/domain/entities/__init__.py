"""Domain entities for Ali API.

This module contains pure domain entities that represent
the core business objects without any external dependencies.
"""

from .user_entity import UserEntity, UserRole, UserStatus, UserProfile, UserPreferences
from .session_entity import SessionEntity, SessionStatus, SessionType, SessionMetadata, SessionStats
from .message_entity import MessageEntity, MessageRole, MessageStatus, MessageMetadata, MessageContext
from .document_entity import (
    DocumentEntity, 
    DocumentStatus, 
    DocumentType, 
    DocumentCategory,
    DocumentMetadata,
    DocumentSource,
    DocumentContent
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