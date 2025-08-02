"""Document management schemas for the API.

This module provides schemas for document CRUD operations, categorization,
search functionality, and cloud storage integration.
"""

from datetime import datetime
from enum import Enum
from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
)


class DocumentStatus(str, Enum):
    """Document status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """Document type enumeration."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    UPLOAD = "upload"
    SCRAPED = "scraped"
    MANUAL = "manual"


class DocumentCategory(str, Enum):
    """Document category enumeration."""

    LEI = "lei"
    DECRETO = "decreto"
    PORTARIA = "portaria"
    RESOLUCAO = "resolucao"
    INSTRUCAO_NORMATIVA = "instrucao_normativa"
    CIRCULAR = "circular"
    OFICIO = "oficio"
    MEMORANDO = "memorando"
    PARECER = "parecer"
    RELATORIO = "relatorio"
    ATA = "ata"
    EDITAL = "edital"
    CONTRATO = "contrato"
    CONVENIO = "convenio"
    OUTROS = "outros"


class DocumentBase(BaseModel):
    """Base document schema with common fields."""

    title: str = Field(..., description="Document title", max_length=500)
    content: str = Field(..., description="Document content")
    summary: str = Field("", description="Document summary", max_length=1000)
    categoria: DocumentCategory = Field(
        DocumentCategory.OUTROS, description="Document category"
    )
    tipo_documento: DocumentType = Field(
        DocumentType.MANUAL, description="Document type"
    )
    status: DocumentStatus = Field(DocumentStatus.ACTIVE, description="Document status")
    municipio: str = Field("", description="Municipality", max_length=100)
    legislatura: str = Field("", description="Legislature", max_length=50)
    autor: str = Field("", description="Author", max_length=200)
    source_type: str = Field("manual", description="Source type", max_length=50)
    file_path: Optional[str] = Field(
        None, description="File path or URL", max_length=500
    )
    tokens: int = Field(0, description="Token count", ge=0)
    tags: List[str] = Field(default_factory=list, description="Document tags")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and sanitize tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")

        sanitized_tags = []
        for tag in v:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                clean_tag = tag.strip().lower()[:50]  # Max 50 chars per tag
                if clean_tag not in sanitized_tags:
                    sanitized_tags.append(clean_tag)

        return sanitized_tags


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""

    pass


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""

    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None)
    summary: Optional[str] = Field(None, max_length=1000)
    categoria: Optional[DocumentCategory] = Field(None)
    tipo_documento: Optional[DocumentType] = Field(None)
    status: Optional[DocumentStatus] = Field(None)
    municipio: Optional[str] = Field(None, max_length=100)
    legislatura: Optional[str] = Field(None, max_length=50)
    autor: Optional[str] = Field(None, max_length=200)
    source_type: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(None)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and sanitize tags."""
        if v is None:
            return v

        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")

        sanitized_tags = []
        for tag in v:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                clean_tag = tag.strip().lower()[:50]
                if clean_tag not in sanitized_tags:
                    sanitized_tags.append(clean_tag)

        return sanitized_tags


class DocumentResponse(DocumentBase):
    """Schema for document responses."""

    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: int = Field(..., description="Creator user ID")
    updated_by: Optional[int] = Field(None, description="Last updater user ID")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_url: Optional[HttpUrl] = Field(None, description="File URL in cloud storage")
    search_vector: Optional[str] = Field(
        None, description="Search vector representation"
    )


class DocumentSearchRequest(BaseModel):
    """Schema for document search requests."""

    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    max_results: int = Field(10, description="Maximum results", ge=1, le=100)
    categoria: Optional[DocumentCategory] = Field(
        None, description="Filter by category"
    )
    status: Optional[DocumentStatus] = Field(None, description="Filter by status")
    tipo_documento: Optional[DocumentType] = Field(
        None, description="Filter by document type"
    )
    municipio: Optional[str] = Field(None, description="Filter by municipality")
    legislatura: Optional[str] = Field(None, description="Filter by legislature")
    autor: Optional[str] = Field(None, description="Filter by author")
    source_type: Optional[str] = Field(None, description="Filter by source type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    include_content: bool = Field(True, description="Include content in results")


class DocumentSearchResult(BaseModel):
    """Schema for document search results."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    summary: str = Field(..., description="Document summary")
    categoria: DocumentCategory = Field(..., description="Document category")
    tipo_documento: DocumentType = Field(..., description="Document type")
    status: DocumentStatus = Field(..., description="Document status")
    municipio: str = Field(..., description="Municipality")
    autor: str = Field(..., description="Author")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    relevance_score: float = Field(
        ..., description="Search relevance score", ge=0.0, le=1.0
    )
    content_snippet: Optional[str] = Field(None, description="Content snippet")
    file_url: Optional[HttpUrl] = Field(None, description="File URL")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentUploadRequest(BaseModel):
    """Schema for document upload requests."""

    title: Optional[str] = Field(None, description="Document title", max_length=500)
    categoria: DocumentCategory = Field(
        DocumentCategory.OUTROS, description="Document category"
    )
    municipio: str = Field("", description="Municipality", max_length=100)
    legislatura: str = Field("", description="Legislature", max_length=50)
    autor: str = Field("", description="Author", max_length=200)
    tags: List[str] = Field(default_factory=list, description="Document tags")
    auto_process: bool = Field(
        True, description="Auto-process with OCR/text extraction"
    )
    chunk_size: int = Field(
        1000, description="Text chunk size for processing", ge=100, le=5000
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and sanitize tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")

        sanitized_tags = []
        for tag in v:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                clean_tag = tag.strip().lower()[:50]
                if clean_tag not in sanitized_tags:
                    sanitized_tags.append(clean_tag)

        return sanitized_tags


class DocumentUploadResponse(BaseModel):
    """Schema for document upload responses."""

    success: bool = Field(..., description="Upload success status")
    document_ids: List[str] = Field(..., description="Created document IDs")
    message: str = Field(..., description="Response message")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_url: Optional[HttpUrl] = Field(None, description="File URL in cloud storage")
    chunks_created: int = Field(0, description="Number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")


class DocumentBulkOperation(BaseModel):
    """Schema for bulk document operations."""

    document_ids: List[str] = Field(
        ..., description="Document IDs", min_items=1, max_items=100
    )
    operation: str = Field(
        ..., description="Operation type (delete, archive, activate)"
    )

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        allowed_operations = [
            "delete",
            "archive",
            "activate",
            "change_category",
            "add_tags",
            "remove_tags",
        ]
        if v not in allowed_operations:
            raise ValueError(
                f"Operation must be one of: {', '.join(allowed_operations)}"
            )
        return v


class DocumentBulkUpdate(DocumentBulkOperation):
    """Schema for bulk document updates."""

    categoria: Optional[DocumentCategory] = Field(
        None, description="New category for change_category operation"
    )
    status: Optional[DocumentStatus] = Field(None, description="New status")
    tags: Optional[List[str]] = Field(
        None, description="Tags for add_tags/remove_tags operations"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and sanitize tags."""
        if v is None:
            return v

        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")

        sanitized_tags = []
        for tag in v:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                clean_tag = tag.strip().lower()[:50]
                if clean_tag not in sanitized_tags:
                    sanitized_tags.append(clean_tag)

        return sanitized_tags


class DocumentBulkResponse(BaseModel):
    """Schema for bulk operation responses."""

    success: bool = Field(..., description="Overall operation success")
    processed_count: int = Field(..., description="Number of documents processed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    message: str = Field(..., description="Response message")


class DocumentStats(BaseModel):
    """Schema for document statistics."""

    total_documents: int = Field(..., description="Total number of documents")
    by_category: dict = Field(..., description="Documents count by category")
    by_status: dict = Field(..., description="Documents count by status")
    by_type: dict = Field(..., description="Documents count by type")
    by_municipality: dict = Field(..., description="Documents count by municipality")
    total_storage_size: int = Field(..., description="Total storage size in bytes")
    recent_documents: int = Field(..., description="Documents created in last 30 days")
    updated_today: int = Field(..., description="Documents updated today")


class DocumentCategoryInfo(BaseModel):
    """Schema for document categories."""

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: str = Field("", description="Category description")
    document_count: int = Field(0, description="Number of documents in category")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_system: bool = Field(False, description="Whether this is a system category")


class DocumentCategoryCreate(BaseModel):
    """Schema for creating document categories."""

    name: str = Field(..., description="Category name", min_length=1, max_length=100)
    description: str = Field("", description="Category description", max_length=500)


class DocumentCategoryUpdate(BaseModel):
    """Schema for updating document categories."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class MessageResponse(BaseModel):
    """Generic response schema for simple operations."""

    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")
    data: Optional[dict] = Field(None, description="Additional response data")
