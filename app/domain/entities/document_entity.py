"""Document domain entity for Ali API.

This module contains the pure domain model for documents,
independent of any external dependencies or frameworks.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Union,
)


class DocumentStatus(str, Enum):
    """Document status in the system."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PROCESSING = "processing"
    ERROR = "error"


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
    OTHER = "other"


@dataclass
class DocumentMetadata:
    """Document metadata and processing information."""

    file_size: int = 0
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    encoding: str = "utf-8"
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    language: str = "pt-BR"
    extraction_method: Optional[str] = None
    processing_time: Optional[float] = None
    indexed_at: Optional[datetime] = None


@dataclass
class DocumentSource:
    """Document source information."""

    url: Optional[str] = None
    original_filename: Optional[str] = None
    upload_user_id: Optional[int] = None
    source_system: Optional[str] = None
    source_reference: Optional[str] = None
    scraped_at: Optional[datetime] = None


@dataclass
class DocumentContent:
    """Document content information."""

    raw_text: str = ""
    processed_text: str = ""
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    entities: Optional[List[Dict]] = None
    chunks: Optional[List[Dict]] = None


class DocumentEntity:
    """Pure domain entity for documents.

    This class contains the core business logic for documents
    without any external dependencies.
    """

    def __init__(
        self,
        title: str,
        content: DocumentContent,
        user_id: int,
        document_type: DocumentType = DocumentType.MANUAL,
        category: DocumentCategory = DocumentCategory.OTHER,
        status: DocumentStatus = DocumentStatus.DRAFT,
        metadata: Optional[DocumentMetadata] = None,
        source: Optional[DocumentSource] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        document_id: Optional[str] = None,
    ):
        """Initialize a Document entity.

        Args:
            title: Document title
            content: Document content information
            user_id: ID of the user who owns this document
            document_type: Type of document
            category: Document category
            status: Current document status
            metadata: Document metadata
            source: Document source information
            tags: Document tags
            description: Document description
            is_public: Whether document is publicly accessible
            created_at: Creation timestamp
            updated_at: Last update timestamp
            document_id: Unique document identifier
        """
        self.id = document_id or str(uuid.uuid4())
        self.title = self._validate_title(title)
        self.content = content
        self.user_id = user_id
        self.document_type = document_type
        self.category = category
        self.status = status
        self.metadata = metadata or DocumentMetadata()
        self.source = source or DocumentSource()
        self.tags = tags or []
        self.description = description
        self.is_public = is_public
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

        # Calculate content hash if not provided
        if not self.metadata.file_hash and self.content.raw_text:
            self.metadata.file_hash = self._calculate_content_hash()

    def _validate_title(self, title: str) -> str:
        """Validate document title."""
        if not title or not title.strip():
            raise ValueError("Document title cannot be empty")

        title = title.strip()

        if len(title) > 200:
            raise ValueError("Document title cannot exceed 200 characters")

        return title

    def _calculate_content_hash(self) -> str:
        """Calculate hash of document content."""
        content_bytes = self.content.raw_text.encode("utf-8")
        return hashlib.sha256(content_bytes).hexdigest()

    def update_title(self, new_title: str) -> None:
        """Update document title."""
        self.title = self._validate_title(new_title)
        self.updated_at = datetime.utcnow()

    def update_content(self, new_content: DocumentContent) -> None:
        """Update document content."""
        self.content = new_content

        # Recalculate hash and metadata
        self.metadata.file_hash = self._calculate_content_hash()
        self.metadata.word_count = len(new_content.raw_text.split())
        self.metadata.character_count = len(new_content.raw_text)

        self.updated_at = datetime.utcnow()

    def update_description(self, description: str) -> None:
        """Update document description."""
        if len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")

        self.description = description.strip() if description else None
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document."""
        tag = tag.strip().lower()
        if not tag:
            raise ValueError("Tag cannot be empty")

        if len(tag) > 50:
            raise ValueError("Tag cannot exceed 50 characters")

        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document."""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def set_tags(self, tags: List[str]) -> None:
        """Set document tags, replacing existing ones."""
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip().lower()
            if tag and len(tag) <= 50 and tag not in cleaned_tags:
                cleaned_tags.append(tag)

        self.tags = cleaned_tags
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """Publish the document (make it public and active)."""
        self.status = DocumentStatus.ACTIVE
        self.is_public = True
        self.updated_at = datetime.utcnow()

    def unpublish(self) -> None:
        """Unpublish the document."""
        self.is_public = False
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the document."""
        self.status = DocumentStatus.ARCHIVED
        self.is_public = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the document."""
        self.status = DocumentStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def mark_deleted(self) -> None:
        """Mark document as deleted (soft delete)."""
        self.status = DocumentStatus.DELETED
        self.is_public = False
        self.updated_at = datetime.utcnow()

    def mark_processing(self) -> None:
        """Mark document as being processed."""
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_error(self, error_details: str) -> None:
        """Mark document processing as error."""
        self.status = DocumentStatus.ERROR
        self.metadata.processing_time = None
        self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata_update: Dict) -> None:
        """Update document metadata."""
        if "file_size" in metadata_update:
            size = metadata_update["file_size"]
            if size < 0:
                raise ValueError("File size cannot be negative")
            self.metadata.file_size = size

        if "mime_type" in metadata_update:
            self.metadata.mime_type = metadata_update["mime_type"]

        if "page_count" in metadata_update:
            pages = metadata_update["page_count"]
            if pages < 0:
                raise ValueError("Page count cannot be negative")
            self.metadata.page_count = pages

        if "language" in metadata_update:
            self.metadata.language = metadata_update["language"]

        if "extraction_method" in metadata_update:
            self.metadata.extraction_method = metadata_update["extraction_method"]

        if "processing_time" in metadata_update:
            proc_time = metadata_update["processing_time"]
            if proc_time < 0:
                raise ValueError("Processing time cannot be negative")
            self.metadata.processing_time = proc_time

        self.updated_at = datetime.utcnow()

    def update_source(self, source_update: Dict) -> None:
        """Update document source information."""
        if "url" in source_update:
            self.source.url = source_update["url"]

        if "original_filename" in source_update:
            self.source.original_filename = source_update["original_filename"]

        if "source_system" in source_update:
            self.source.source_system = source_update["source_system"]

        if "source_reference" in source_update:
            self.source.source_reference = source_update["source_reference"]

        self.updated_at = datetime.utcnow()

    def is_owned_by(self, user_id: int) -> bool:
        """Check if document is owned by a specific user."""
        return self.user_id == user_id

    def can_be_accessed_by(self, user_id: int, user_role: str = "viewer") -> bool:
        """Check if a user can access this document."""
        # Owner can always access
        if self.is_owned_by(user_id):
            return True

        # Admin can access any document
        if user_role == "admin":
            return True

        # Public documents can be accessed by anyone
        if self.is_public and self.status == DocumentStatus.ACTIVE:
            return True

        return False

    def can_be_edited_by(self, user_id: int, user_role: str = "viewer") -> bool:
        """Check if a user can edit this document."""
        # Admin can edit any document
        if user_role == "admin":
            return True

        # Owner can edit if document is not deleted
        if self.is_owned_by(user_id) and self.status != DocumentStatus.DELETED:
            return True

        return False

    def is_searchable(self) -> bool:
        """Check if document is searchable."""
        return (
            self.status in [DocumentStatus.ACTIVE, DocumentStatus.ARCHIVED]
            and self.content.raw_text.strip() != ""
        )

    def get_file_extension(self) -> Optional[str]:
        """Get file extension from original filename."""
        if self.source.original_filename:
            return Path(self.source.original_filename).suffix.lower()
        return None

    def get_size_mb(self) -> float:
        """Get file size in megabytes."""
        return round(self.metadata.file_size / (1024 * 1024), 2)

    def get_content_preview(self, max_length: int = 200) -> str:
        """Get a preview of the document content."""
        text = self.content.processed_text or self.content.raw_text
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def get_document_summary(self) -> Dict:
        """Get a summary of document information."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.document_type.value,
            "category": self.category.value,
            "status": self.status.value,
            "is_public": self.is_public,
            "word_count": self.metadata.word_count,
            "page_count": self.metadata.page_count,
            "file_size_mb": self.get_size_mb(),
            "tags_count": len(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "has_content": bool(self.content.raw_text.strip()),
            "has_summary": bool(self.content.summary),
            "language": self.metadata.language,
        }

    def __str__(self) -> str:
        """String representation of the document."""
        return (
            f"Document(id={self.id}, title='{self.title}', status={self.status.value})"
        )

    def __repr__(self) -> str:
        """Detailed representation of the document."""
        return (
            f"DocumentEntity(id='{self.id}', title='{self.title}', "
            f"type={self.document_type.value}, category={self.category.value}, "
            f"status={self.status.value})"
        )
