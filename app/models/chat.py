"""Chat models for Ali API.

This module contains SQLModel models for chat messages and sessions.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import JSON

from app.models.base import BaseModel


class ChatSession(BaseModel, table=True):
    """Chat session model (alias for Session for compatibility)."""
    
    __tablename__ = "chat_sessions"
    
    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(default="")
    session_type: str = Field(default="chat")
    status: str = Field(default="active")
    context: Optional[str] = Field(default=None)  # Simplified as text for now
    message_count: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_response_time: float = Field(default=0.0)


class ChatMessage(BaseModel, table=True):
    """Chat message model for storing conversation history."""
    
    __tablename__ = "chat_messages"
    
    id: str = Field(primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.id")
    user_id: int = Field(foreign_key="user.id")
    role: str = Field()  # "user" or "assistant"
    content: str = Field()
    status: str = Field(default="completed")
    message_metadata: Optional[str] = Field(default=None)  # Renamed to avoid conflict
    context: Optional[str] = Field(default=None)