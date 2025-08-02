"""Session domain entity for Ali API.

This module contains the pure domain model for chat sessions,
independent of any external dependencies or frameworks.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)


class SessionStatus(str, Enum):
    """Session status in the system."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SessionType(str, Enum):
    """Type of chat session."""

    CHAT = "chat"
    DOCUMENT_ANALYSIS = "document_analysis"
    RAG_QUERY = "rag_query"
    GENERAL = "general"


@dataclass
class SessionMetadata:
    """Session metadata and configuration."""

    model_used: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    context_window: int = 4000
    language: str = "pt-BR"


@dataclass
class SessionStats:
    """Session statistics."""

    message_count: int = 0
    total_tokens_used: int = 0
    avg_response_time: float = 0.0
    last_activity: Optional[datetime] = None


class SessionEntity:
    """Pure domain entity for chat sessions.

    This class contains the core business logic for sessions
    without any external dependencies.
    """

    def __init__(
        self,
        user_id: int,
        name: str = "",
        session_type: SessionType = SessionType.CHAT,
        status: SessionStatus = SessionStatus.ACTIVE,
        metadata: Optional[SessionMetadata] = None,
        stats: Optional[SessionStats] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        session_id: Optional[str] = None,
    ):
        """Initialize a Session entity.

        Args:
            user_id: ID of the user who owns this session
            name: Human-readable name for the session
            session_type: Type of session
            status: Current session status
            metadata: Session configuration and metadata
            stats: Session statistics
            created_at: Creation timestamp
            updated_at: Last update timestamp
            session_id: Unique session identifier
        """
        self.id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.name = name or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        self.session_type = session_type
        self.status = status
        self.metadata = metadata or SessionMetadata()
        self.stats = stats or SessionStats()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def update_name(self, new_name: str) -> None:
        """Update session name."""
        if not new_name or not new_name.strip():
            raise ValueError("Session name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the session."""
        self.status = SessionStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the session."""
        self.status = SessionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the session."""
        self.status = SessionStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def mark_deleted(self) -> None:
        """Mark session as deleted (soft delete)."""
        self.status = SessionStatus.DELETED
        self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata_update: Dict) -> None:
        """Update session metadata."""
        if "model_used" in metadata_update:
            self.metadata.model_used = metadata_update["model_used"]
        if "temperature" in metadata_update:
            temp = metadata_update["temperature"]
            if not 0.0 <= temp <= 2.0:
                raise ValueError("Temperature must be between 0.0 and 2.0")
            self.metadata.temperature = temp
        if "max_tokens" in metadata_update:
            max_tokens = metadata_update["max_tokens"]
            if max_tokens <= 0:
                raise ValueError("Max tokens must be positive")
            self.metadata.max_tokens = max_tokens
        if "system_prompt" in metadata_update:
            self.metadata.system_prompt = metadata_update["system_prompt"]
        if "context_window" in metadata_update:
            context = metadata_update["context_window"]
            if context <= 0:
                raise ValueError("Context window must be positive")
            self.metadata.context_window = context
        if "language" in metadata_update:
            self.metadata.language = metadata_update["language"]

        self.updated_at = datetime.utcnow()

    def record_message(self, tokens_used: int = 0, response_time: float = 0.0) -> None:
        """Record a new message in the session."""
        self.stats.message_count += 1
        self.stats.total_tokens_used += tokens_used

        # Update average response time
        if response_time > 0:
            current_avg = self.stats.avg_response_time
            count = self.stats.message_count
            self.stats.avg_response_time = (
                current_avg * (count - 1) + response_time
            ) / count

        self.stats.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE

    def is_owned_by(self, user_id: int) -> bool:
        """Check if session belongs to a specific user."""
        return self.user_id == user_id

    def can_be_accessed_by(self, user_id: int, user_role: str = "viewer") -> bool:
        """Check if a user can access this session."""
        # Owner can always access
        if self.is_owned_by(user_id):
            return True

        # Admin can access any session
        if user_role == "admin":
            return True

        # Others cannot access
        return False

    def get_activity_summary(self) -> Dict:
        """Get a summary of session activity."""
        return {
            "message_count": self.stats.message_count,
            "total_tokens": self.stats.total_tokens_used,
            "avg_response_time": round(self.stats.avg_response_time, 2),
            "last_activity": self.stats.last_activity,
            "created": self.created_at,
            "duration_hours": self._calculate_duration_hours(),
            "messages_per_hour": self._calculate_messages_per_hour(),
        }

    def _calculate_duration_hours(self) -> float:
        """Calculate session duration in hours."""
        end_time = self.stats.last_activity or self.updated_at
        duration = end_time - self.created_at
        return round(duration.total_seconds() / 3600, 2)

    def _calculate_messages_per_hour(self) -> float:
        """Calculate average messages per hour."""
        duration_hours = self._calculate_duration_hours()
        if duration_hours == 0:
            return 0.0
        return round(self.stats.message_count / duration_hours, 2)

    def reset_stats(self) -> None:
        """Reset session statistics."""
        self.stats = SessionStats()
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the session."""
        return f"Session(id={self.id}, name='{self.name}', user_id={self.user_id})"

    def __repr__(self) -> str:
        """Detailed representation of the session."""
        return (
            f"SessionEntity(id='{self.id}', name='{self.name}', "
            f"user_id={self.user_id}, type={self.session_type.value}, "
            f"status={self.status.value})"
        )
