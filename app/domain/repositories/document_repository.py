"""Document repository interface for Ali API.

This module defines the contract for document data access operations
without specifying implementation details.
"""

from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from typing import (
    List,
    Optional,
    Tuple,
)

from app.domain.entities import (
    DocumentCategory,
    DocumentEntity,
    DocumentStatus,
    DocumentType,
)


class DocumentRepositoryInterface(ABC):
    """Abstract repository interface for Document operations.

    This interface defines all the operations that can be performed
    on document data without coupling to any specific database implementation.
    """

    @abstractmethod
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document.

        Args:
            document: Document entity to create

        Returns:
            DocumentEntity: Created document with assigned ID

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """Get document by ID.

        Args:
            document_id: Document ID to lookup

        Returns:
            DocumentEntity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update an existing document.

        Args:
            document: Document entity with updated data

        Returns:
            DocumentEntity: Updated document

        Raises:
            DocumentNotFoundError: If document doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document (soft delete).

        Args:
            document_id: ID of document to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        pass

    @abstractmethod
    async def get_user_documents(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        category: Optional[DocumentCategory] = None,
        is_public: Optional[bool] = None,
    ) -> List[DocumentEntity]:
        """Get documents for a specific user.

        Args:
            user_id: User ID to get documents for
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            status: Filter by document status
            document_type: Filter by document type
            category: Filter by document category
            is_public: Filter by public status

        Returns:
            List[DocumentEntity]: List of user documents
        """
        pass

    @abstractmethod
    async def count_user_documents(
        self,
        user_id: int,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        category: Optional[DocumentCategory] = None,
        is_public: Optional[bool] = None,
    ) -> int:
        """Count documents for a specific user.

        Args:
            user_id: User ID to count documents for
            status: Filter by document status
            document_type: Filter by document type
            category: Filter by document category
            is_public: Filter by public status

        Returns:
            int: Number of documents matching criteria
        """
        pass

    @abstractmethod
    async def get_public_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None,
        document_type: Optional[DocumentType] = None,
    ) -> List[DocumentEntity]:
        """Get public documents.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            category: Filter by document category
            document_type: Filter by document type

        Returns:
            List[DocumentEntity]: List of public documents
        """
        pass

    @abstractmethod
    async def get_documents_by_category(
        self,
        category: DocumentCategory,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
    ) -> List[DocumentEntity]:
        """Get documents by category.

        Args:
            category: Document category to filter by
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            user_id: Filter by specific user (optional)

        Returns:
            List[DocumentEntity]: List of documents in category
        """
        pass

    @abstractmethod
    async def get_documents_by_type(
        self,
        document_type: DocumentType,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
    ) -> List[DocumentEntity]:
        """Get documents by type.

        Args:
            document_type: Document type to filter by
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            user_id: Filter by specific user (optional)

        Returns:
            List[DocumentEntity]: List of documents of specified type
        """
        pass

    @abstractmethod
    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None,
    ) -> List[DocumentEntity]:
        """Search documents by title, content, or tags.

        Args:
            query: Search query
            user_id: Filter by specific user (optional)
            include_public: Include public documents in search
            limit: Maximum number of results
            offset: Number of results to skip
            category: Filter by document category

        Returns:
            List[DocumentEntity]: List of documents matching search
        """
        pass

    @abstractmethod
    async def get_documents_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
    ) -> List[DocumentEntity]:
        """Get documents by tags.

        Args:
            tags: List of tags to search for
            match_all: Whether to match all tags or any tag
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            user_id: Filter by specific user (optional)

        Returns:
            List[DocumentEntity]: List of documents matching tags
        """
        pass

    @abstractmethod
    async def get_recent_documents(
        self,
        limit: int = 20,
        user_id: Optional[int] = None,
        include_public: bool = True,
    ) -> List[DocumentEntity]:
        """Get recently created or updated documents.

        Args:
            limit: Maximum number of documents to return
            user_id: Filter by specific user (optional)
            include_public: Include public documents

        Returns:
            List[DocumentEntity]: List of recent documents
        """
        pass

    @abstractmethod
    async def get_popular_documents(
        self,
        limit: int = 10,
        time_period_days: int = 30,
        category: Optional[DocumentCategory] = None,
    ) -> List[DocumentEntity]:
        """Get most accessed documents in a time period.

        Args:
            limit: Maximum number of documents to return
            time_period_days: Time period in days to consider
            category: Filter by document category

        Returns:
            List[DocumentEntity]: List of popular documents
        """
        pass

    @abstractmethod
    async def get_document_statistics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get document statistics.

        Args:
            user_id: Filter by specific user (optional)
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            dict: Statistics including document counts, categories, etc.
        """
        pass

    @abstractmethod
    async def get_documents_by_hash(self, file_hash: str) -> List[DocumentEntity]:
        """Get documents with matching content hash (duplicates).

        Args:
            file_hash: Content hash to search for

        Returns:
            List[DocumentEntity]: List of documents with same hash
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self, document_ids: List[str], status: DocumentStatus
    ) -> int:
        """Bulk update document status.

        Args:
            document_ids: List of document IDs to update
            status: New status to set

        Returns:
            int: Number of documents updated
        """
        pass

    @abstractmethod
    async def bulk_update_category(
        self, document_ids: List[str], category: DocumentCategory
    ) -> int:
        """Bulk update document category.

        Args:
            document_ids: List of document IDs to update
            category: New category to set

        Returns:
            int: Number of documents updated
        """
        pass

    @abstractmethod
    async def archive_old_documents(
        self, older_than: datetime, exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Archive documents older than specified date.

        Args:
            older_than: Cutoff date for archiving
            exclude_user_ids: User IDs to exclude from archiving

        Returns:
            int: Number of documents archived
        """
        pass

    @abstractmethod
    async def cleanup_deleted_documents(self, deleted_before: datetime) -> int:
        """Permanently remove documents marked as deleted.

        Args:
            deleted_before: Remove documents deleted before this date

        Returns:
            int: Number of documents permanently removed
        """
        pass

    @abstractmethod
    async def get_large_documents(
        self, size_threshold_mb: float = 10.0, limit: int = 50
    ) -> List[DocumentEntity]:
        """Get documents larger than threshold.

        Args:
            size_threshold_mb: Size threshold in megabytes
            limit: Maximum number of documents to return

        Returns:
            List[DocumentEntity]: List of large documents
        """
        pass

    @abstractmethod
    async def get_processing_documents(
        self, older_than_minutes: int = 30
    ) -> List[DocumentEntity]:
        """Get documents stuck in processing state.

        Args:
            older_than_minutes: Processing for longer than this many minutes

        Returns:
            List[DocumentEntity]: List of stuck processing documents
        """
        pass

    @abstractmethod
    async def get_all_tags(
        self, user_id: Optional[int] = None, min_usage_count: int = 1
    ) -> List[Tuple[str, int]]:
        """Get all tags with usage counts.

        Args:
            user_id: Filter by specific user (optional)
            min_usage_count: Minimum number of documents using the tag

        Returns:
            List[Tuple[str, int]]: List of (tag, count) tuples
        """
        pass
