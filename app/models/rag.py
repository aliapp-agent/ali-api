"""RAG models for Ali API.

This module contains SQLModel models for documents and RAG functionality.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Field, SQLModel

from app.models.base import BaseModel


class Document(BaseModel, table=True):
    """Document model for RAG system."""
    
    __tablename__ = "documents"
    
    id: str = Field(primary_key=True)
    title: str = Field()
    content: str = Field()
    user_id: int = Field(foreign_key="user.id")
    document_type: str = Field(default="manual")
    category: str = Field(default="other")
    status: str = Field(default="active")
    tags: Optional[str] = Field(default=None)  # Simplified as text for now
    description: Optional[str] = Field(default=None)
    is_public: bool = Field(default=False)
    document_metadata: Optional[str] = Field(default=None)  # Renamed to avoid conflict
    source: Optional[str] = Field(default=None)