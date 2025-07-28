"""Message domain entity for Ali API.

This module contains the pure domain model for chat messages,
independent of any external dependencies or frameworks.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import uuid
import re


class MessageRole(str, Enum):
    """Message role in the conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status in the system."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    DELETED = "deleted"


@dataclass
class MessageMetadata:
    """Message metadata and processing information."""
    model_used: Optional[str] = None
    tokens_used: int = 0
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    context_documents: Optional[List[str]] = None
    error_details: Optional[str] = None
    retry_count: int = 0


@dataclass
class MessageContext:
    """Additional context for message processing."""
    user_location: Optional[str] = None
    user_agent: Optional[str] = None
    session_context: Optional[Dict] = None
    previous_messages_count: int = 0


class MessageEntity:
    """Pure domain entity for chat messages.
    
    This class contains the core business logic for messages
    without any external dependencies.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: int,
        role: MessageRole,
        content: str,
        status: MessageStatus = MessageStatus.PENDING,
        metadata: Optional[MessageMetadata] = None,
        context: Optional[MessageContext] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        message_id: Optional[str] = None,
    ):
        """Initialize a Message entity.
        
        Args:
            session_id: ID of the session this message belongs to
            user_id: ID of the user who created/received this message
            role: Role of the message sender
            content: Message content
            status: Current message status
            metadata: Message metadata and processing info
            context: Additional message context
            created_at: Creation timestamp
            updated_at: Last update timestamp
            message_id: Unique message identifier
        """
        self.id = message_id or str(uuid.uuid4())
        self.session_id = session_id
        self.user_id = user_id
        self.role = role
        self.content = self._validate_and_sanitize_content(content)
        self.status = status
        self.metadata = metadata or MessageMetadata()
        self.context = context or MessageContext()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def _validate_and_sanitize_content(self, content: str) -> str:
        """Validate and sanitize message content."""
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")
        
        content = content.strip()
        
        # Length validation
        if len(content) > 10000:  # 10K character limit
            raise ValueError("Message content exceeds maximum length")
        
        # Check for potentially harmful content
        if re.search(r"<script.*?>.*?</script>", content, re.IGNORECASE | re.DOTALL):
            raise ValueError("Content contains potentially harmful script tags")
        
        # Check for null bytes
        if "\0" in content:
            raise ValueError("Content contains null bytes")
        
        return content

    def update_content(self, new_content: str) -> None:
        """Update message content (only for user messages)."""
        if self.role != MessageRole.USER:
            raise ValueError("Only user messages can be edited")
        
        if self.status != MessageStatus.PENDING:
            raise ValueError("Cannot edit message that has been processed")
        
        self.content = self._validate_and_sanitize_content(new_content)
        self.updated_at = datetime.utcnow()

    def mark_processing(self) -> None:
        """Mark message as being processed."""
        if self.status != MessageStatus.PENDING:
            raise ValueError(f"Cannot mark as processing from status: {self.status}")
        
        self.status = MessageStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, metadata_update: Optional[Dict] = None) -> None:
        """Mark message as completed with optional metadata."""
        if self.status not in [MessageStatus.PENDING, MessageStatus.PROCESSING]:
            raise ValueError(f"Cannot mark as completed from status: {self.status}")
        
        self.status = MessageStatus.COMPLETED
        
        if metadata_update:
            self.update_metadata(metadata_update)
        
        self.updated_at = datetime.utcnow()

    def mark_error(self, error_details: str) -> None:
        """Mark message as error with details."""
        self.status = MessageStatus.ERROR
        self.metadata.error_details = error_details
        self.metadata.retry_count += 1
        self.updated_at = datetime.utcnow()

    def mark_deleted(self) -> None:
        """Mark message as deleted (soft delete)."""
        self.status = MessageStatus.DELETED
        self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata_update: Dict) -> None:
        """Update message metadata."""
        if 'model_used' in metadata_update:
            self.metadata.model_used = metadata_update['model_used']
        if 'tokens_used' in metadata_update:
            tokens = metadata_update['tokens_used']
            if tokens < 0:
                raise ValueError("Tokens used cannot be negative")
            self.metadata.tokens_used = tokens
        if 'processing_time' in metadata_update:
            proc_time = metadata_update['processing_time']
            if proc_time < 0:
                raise ValueError("Processing time cannot be negative")
            self.metadata.processing_time = proc_time
        if 'confidence_score' in metadata_update:
            confidence = metadata_update['confidence_score']
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("Confidence score must be between 0.0 and 1.0")
            self.metadata.confidence_score = confidence
        if 'context_documents' in metadata_update:
            self.metadata.context_documents = metadata_update['context_documents']
        
        self.updated_at = datetime.utcnow()

    def update_context(self, context_update: Dict) -> None:
        """Update message context."""
        if 'user_location' in context_update:
            self.context.user_location = context_update['user_location']
        if 'user_agent' in context_update:
            self.context.user_agent = context_update['user_agent']
        if 'session_context' in context_update:
            self.context.session_context = context_update['session_context']
        if 'previous_messages_count' in context_update:
            count = context_update['previous_messages_count']
            if count < 0:
                raise ValueError("Previous messages count cannot be negative")
            self.context.previous_messages_count = count
        
        self.updated_at = datetime.utcnow()

    def can_be_edited(self) -> bool:
        """Check if message can be edited."""
        return (
            self.role == MessageRole.USER and 
            self.status == MessageStatus.PENDING
        )

    def can_be_retried(self) -> bool:
        """Check if message can be retried."""
        return (
            self.status == MessageStatus.ERROR and 
            self.metadata.retry_count < 3
        )

    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM

    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT

    def belongs_to_session(self, session_id: str) -> bool:
        """Check if message belongs to a specific session."""
        return self.session_id == session_id

    def belongs_to_user(self, user_id: int) -> bool:
        """Check if message belongs to a specific user."""
        return self.user_id == user_id

    def get_content_preview(self, max_length: int = 100) -> str:
        """Get a preview of the message content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length-3] + "..."

    def get_word_count(self) -> int:
        """Get the word count of the message."""
        return len(self.content.split())

    def get_character_count(self) -> int:
        """Get the character count of the message."""
        return len(self.content)

    def has_context_documents(self) -> bool:
        """Check if message has associated context documents."""
        return bool(self.metadata.context_documents)

    def get_processing_summary(self) -> Dict:
        """Get a summary of message processing."""
        return {
            "status": self.status.value,
            "tokens_used": self.metadata.tokens_used,
            "processing_time": self.metadata.processing_time,
            "confidence_score": self.metadata.confidence_score,
            "model_used": self.metadata.model_used,
            "retry_count": self.metadata.retry_count,
            "has_error": bool(self.metadata.error_details),
            "word_count": self.get_word_count(),
            "character_count": self.get_character_count(),
        }

    def __str__(self) -> str:
        """String representation of the message."""
        preview = self.get_content_preview(50)
        return f"Message(id={self.id}, role={self.role.value}, content='{preview}')"

    def __repr__(self) -> str:
        """Detailed representation of the message."""
        return (
            f"MessageEntity(id='{self.id}', session_id='{self.session_id}', "
            f"user_id={self.user_id}, role={self.role.value}, "
            f"status={self.status.value})"
        )