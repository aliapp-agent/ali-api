"""RAG (Retrieval-Augmented Generation) model definitions."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """Document types."""
    
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"


class Document(BaseModel):
    """Document model for RAG system."""
    
    document_id: str = Field(..., description="Unique document identifier")
    user_id: str = Field(..., description="Firebase user UID")
    filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(None, description="Document title")
    document_type: DocumentType = Field(..., description="Type of document")
    status: DocumentStatus = Field(DocumentStatus.PENDING, description="Processing status")
    file_size: int = Field(..., description="File size in bytes")
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")
    storage_path: Optional[str] = Field(None, description="Storage path in Firebase Storage")
    chunk_count: int = Field(0, description="Number of text chunks extracted")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentChunk(BaseModel):
    """Document chunk model for RAG embeddings."""
    
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    user_id: str = Field(..., description="Firebase user UID")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Chunk position in document")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    embedding_vector: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }