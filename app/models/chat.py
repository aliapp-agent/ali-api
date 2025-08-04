"""Chat model definitions."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message roles."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Chat message types."""
    
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model."""
    
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: str = Field(..., description="Firebase user UID")
    role: MessageRole = Field(..., description="Message role (user/assistant/system)")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message data")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for threading")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """Chat session model."""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Firebase user UID")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    is_active: bool = Field(True, description="Whether session is active")
    message_count: int = Field(0, description="Number of messages in session")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session data")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }