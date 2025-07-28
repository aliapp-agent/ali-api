"""Document domain service for Ali API.

This module contains business logic for document operations that involve
complex rules or multiple entities.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Union
import hashlib
from pathlib import Path

from app.domain.entities import (
    DocumentEntity,
    DocumentStatus,
    DocumentType,
    DocumentCategory,
    DocumentContent,
    DocumentMetadata,
    DocumentSource,
    UserEntity
)
from app.domain.repositories import DocumentRepositoryInterface, UserRepositoryInterface
from app.domain.exceptions import (
    DocumentNotFoundError,
    DocumentAccessDeniedError,
    DocumentProcessingError,
    DocumentTooLargeError,
    UnsupportedDocumentTypeError,
    UserNotFoundError,
    BusinessRuleViolationError,
    InsufficientPermissionsError,
    QuotaExceededError,
)


class DocumentDomainService:
    """Domain service for document-related business logic.
    
    This service encapsulates complex document operations that involve
    business rules, validations, and coordination between entities.
    """
    
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        user_repository: UserRepositoryInterface
    ):
        """Initialize the document domain service.
        
        Args:
            document_repository: Repository for document data access
            user_repository: Repository for user data access
        """
        self.document_repository = document_repository
        self.user_repository = user_repository

    async def create_document(
        self,
        title: str,
        content: DocumentContent,
        user_id: int,
        document_type: DocumentType = DocumentType.MANUAL,
        category: DocumentCategory = DocumentCategory.OTHER,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        source_info: Optional[Dict] = None
    ) -> DocumentEntity:
        """Create a new document with validation.
        
        Args:
            title: Document title
            content: Document content
            user_id: ID of user creating the document
            document_type: Type of document
            category: Document category
            tags: Document tags
            description: Document description
            is_public: Whether document should be public
            source_info: Source information for the document
            
        Returns:
            DocumentEntity: Created document
            
        Raises:
            UserNotFoundError: If user doesn't exist
            DocumentTooLargeError: If document exceeds size limits
            UnsupportedDocumentTypeError: If document type not supported
            QuotaExceededError: If user quota exceeded
            BusinessRuleViolationError: If business rules violated
        """
        # Validate user exists and is active
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        if not user.is_active:
            raise BusinessRuleViolationError(
                "Inactive users cannot create documents"
            )
        
        # Validate document size
        await self._validate_document_size(content, user.role.value)
        
        # Validate document type
        await self._validate_document_type(document_type, user.role.value)
        
        # Check user quotas
        await self._check_document_quotas(user_id, user.role.value)
        
        # Check for duplicate content
        await self._check_duplicate_content(content, user_id)
        
        # Create document metadata
        metadata = DocumentMetadata(
            word_count=len(content.raw_text.split()),
            character_count=len(content.raw_text),
            file_size=len(content.raw_text.encode('utf-8'))
        )
        
        # Create source information
        source = DocumentSource()
        if source_info:
            source.upload_user_id = user_id
            if 'url' in source_info:
                source.url = source_info['url']
            if 'original_filename' in source_info:
                source.original_filename = source_info['original_filename']
            if 'source_system' in source_info:
                source.source_system = source_info['source_system']
        
        # Create document entity
        document = DocumentEntity(
            title=title,
            content=content,
            user_id=user_id,
            document_type=document_type,
            category=category,
            status=DocumentStatus.DRAFT,
            metadata=metadata,
            source=source,
            tags=tags or [],
            description=description,
            is_public=is_public
        )
        
        # Save document
        created_document = await self.document_repository.create(document)
        
        return created_document

    async def update_document_content(
        self,
        document_id: str,
        user_id: int,
        new_content: DocumentContent,
        update_metadata: bool = True
    ) -> DocumentEntity:
        """Update document content with validation.
        
        Args:
            document_id: ID of document to update
            user_id: ID of user performing update
            new_content: New document content
            update_metadata: Whether to update metadata
            
        Returns:
            DocumentEntity: Updated document
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DocumentAccessDeniedError: If user cannot edit document
            DocumentTooLargeError: If new content exceeds limits
        """
        # Get and validate document access
        document = await self._get_document_with_edit_access(document_id, user_id)
        
        # Validate new content size
        user = await self.user_repository.get_by_id(user_id)
        await self._validate_document_size(new_content, user.role.value)
        
        # Update content
        document.update_content(new_content)
        
        # Update metadata if requested
        if update_metadata:
            metadata_update = {
                "word_count": len(new_content.raw_text.split()),
                "character_count": len(new_content.raw_text),
                "file_size": len(new_content.raw_text.encode('utf-8'))
            }
            document.update_metadata(metadata_update)
        
        # Save document
        updated_document = await self.document_repository.update(document)
        
        return updated_document

    async def publish_document(
        self,
        document_id: str,
        user_id: int
    ) -> DocumentEntity:
        """Publish a document (make it public and active).
        
        Args:
            document_id: ID of document to publish
            user_id: ID of user performing action
            
        Returns:
            DocumentEntity: Published document
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DocumentAccessDeniedError: If user cannot publish document
            BusinessRuleViolationError: If document cannot be published
        """
        # Get and validate document access
        document = await self._get_document_with_edit_access(document_id, user_id)
        
        # Validate document can be published
        await self._validate_document_publication(document)
        
        # Publish document
        document.publish()
        
        # Save document
        updated_document = await self.document_repository.update(document)
        
        return updated_document

    async def categorize_document(
        self,
        document_id: str,
        user_id: int,
        new_category: DocumentCategory,
        auto_tag: bool = True
    ) -> DocumentEntity:
        """Categorize a document and optionally add related tags.
        
        Args:
            document_id: ID of document to categorize
            user_id: ID of user performing action
            new_category: New category to assign
            auto_tag: Whether to automatically add category-related tags
            
        Returns:
            DocumentEntity: Updated document
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DocumentAccessDeniedError: If user cannot edit document
        """
        # Get and validate document access
        document = await self._get_document_with_edit_access(document_id, user_id)
        
        # Update category
        document.category = new_category
        document.updated_at = datetime.utcnow()
        
        # Add category-related tags if requested
        if auto_tag:
            category_tags = self._get_category_tags(new_category)
            for tag in category_tags:
                document.add_tag(tag)
        
        # Save document
        updated_document = await self.document_repository.update(document)
        
        return updated_document

    async def search_documents(
        self,
        query: str,
        user_id: int,
        filters: Optional[Dict] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentEntity]:
        """Search documents with user-specific access control.
        
        Args:
            query: Search query
            user_id: ID of user performing search
            filters: Optional search filters
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[DocumentEntity]: Documents matching search
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Validate user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Determine search scope based on user role
        include_public = True
        search_user_id = user_id
        
        # Admins can search all documents
        if user.role.value == "admin":
            search_user_id = None
        
        # Apply filters
        category = None
        if filters:
            category = filters.get("category")
        
        # Search documents
        documents = await self.document_repository.search_documents(
            query=query,
            user_id=search_user_id,
            include_public=include_public,
            limit=limit,
            offset=offset,
            category=category
        )
        
        # Filter results based on access permissions
        accessible_documents = []
        for doc in documents:
            if doc.can_be_accessed_by(user_id, user.role.value):
                accessible_documents.append(doc)
        
        return accessible_documents

    async def get_document_analytics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict:
        """Get document analytics and statistics.
        
        Args:
            user_id: Filter by specific user (optional)
            date_from: Start date for analytics
            date_to: End date for analytics
            
        Returns:
            Dict: Analytics data including counts, categories, trends
        """
        # Get basic statistics
        stats = await self.document_repository.get_document_statistics(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        
        # Add computed analytics
        analytics = {
            **stats,
            "storage_analysis": await self._get_storage_analysis(user_id),
            "category_distribution": await self._get_category_distribution(user_id),
            "tag_popularity": await self._get_tag_popularity(user_id),
            "content_health": self._calculate_content_health(stats),
        }
        
        return analytics

    async def detect_duplicate_documents(
        self,
        user_id: Optional[int] = None,
        similarity_threshold: float = 0.9
    ) -> List[List[DocumentEntity]]:
        """Detect duplicate documents based on content similarity.
        
        Args:
            user_id: Filter by specific user (optional)
            similarity_threshold: Similarity threshold for duplicates
            
        Returns:
            List[List[DocumentEntity]]: Groups of duplicate documents
        """
        # Get all documents (this would be optimized in production)
        if user_id:
            documents = await self.document_repository.get_user_documents(
                user_id=user_id,
                limit=10000
            )
        else:
            documents = await self.document_repository.get_public_documents(
                limit=10000
            )
        
        # Group documents by content hash
        hash_groups = {}
        for doc in documents:
            content_hash = doc.metadata.file_hash
            if content_hash:
                if content_hash not in hash_groups:
                    hash_groups[content_hash] = []
                hash_groups[content_hash].append(doc)
        
        # Return groups with more than one document
        duplicates = [group for group in hash_groups.values() if len(group) > 1]
        
        return duplicates

    async def archive_old_documents(
        self,
        days_old: int = 365,
        exclude_categories: Optional[List[DocumentCategory]] = None,
        exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Archive old documents to reduce active storage.
        
        Args:
            days_old: Age in days for archiving
            exclude_categories: Categories to exclude from archiving
            exclude_user_ids: User IDs to exclude from archiving
            
        Returns:
            int: Number of documents archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Archive old documents
        count = await self.document_repository.archive_old_documents(
            older_than=cutoff_date,
            exclude_user_ids=exclude_user_ids
        )
        
        return count

    async def bulk_document_operation(
        self,
        document_ids: List[str],
        operation: str,
        user_id: int,
        **kwargs
    ) -> Dict[str, int]:
        """Perform bulk operations on multiple documents.
        
        Args:
            document_ids: List of document IDs to operate on
            operation: Operation to perform (archive, delete, categorize, etc.)
            user_id: ID of user performing operation
            **kwargs: Additional parameters for operation
            
        Returns:
            Dict[str, int]: Results with success/failure counts
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for document_id in document_ids:
            try:
                document = await self.document_repository.get_by_id(document_id)
                if not document:
                    results["failed"] += 1
                    results["errors"].append(f"Document {document_id} not found")
                    continue
                
                # Check permissions
                if not document.can_be_edited_by(user_id, user.role.value):
                    results["failed"] += 1
                    results["errors"].append(f"No edit access to document {document_id}")
                    continue
                
                # Perform operation
                if operation == "archive":
                    document.archive()
                elif operation == "delete":
                    document.mark_deleted()
                elif operation == "activate":
                    document.activate()
                elif operation == "categorize":
                    category = kwargs.get("category")
                    if category:
                        document.category = category
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"No category provided for {document_id}")
                        continue
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Unknown operation: {operation}")
                    continue
                
                await self.document_repository.update(document)
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Document {document_id}: {str(e)}")
        
        return results

    async def _get_document_with_edit_access(
        self,
        document_id: str,
        user_id: int
    ) -> DocumentEntity:
        """Get document and validate user has edit access.
        
        Args:
            document_id: Document ID to get
            user_id: User ID to validate access for
            
        Returns:
            DocumentEntity: Document if access is valid
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DocumentAccessDeniedError: If user cannot edit document
            UserNotFoundError: If user doesn't exist
        """
        # Get document
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        # Get user to check role
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Check edit permissions
        if not document.can_be_edited_by(user_id, user.role.value):
            raise DocumentAccessDeniedError(document_id, user_id)
        
        return document

    async def _validate_document_size(
        self,
        content: DocumentContent,
        user_role: str
    ) -> None:
        """Validate document size based on user role.
        
        Args:
            content: Document content to validate
            user_role: User role for size limits
            
        Raises:
            DocumentTooLargeError: If document exceeds size limits
        """
        # Define size limits by role (in MB)
        size_limits = {
            "admin": 100.0,
            "editor": 50.0,
            "viewer": 10.0,
            "guest": 5.0
        }
        
        max_size_mb = size_limits.get(user_role, 5.0)
        content_size_mb = len(content.raw_text.encode('utf-8')) / (1024 * 1024)
        
        if content_size_mb > max_size_mb:
            raise DocumentTooLargeError(content_size_mb, max_size_mb)

    async def _validate_document_type(
        self,
        document_type: DocumentType,
        user_role: str
    ) -> None:
        """Validate document type based on user role.
        
        Args:
            document_type: Document type to validate
            user_role: User role for type restrictions
            
        Raises:
            UnsupportedDocumentTypeError: If type not allowed for user
        """
        # Define allowed types by role
        allowed_types = {
            "admin": list(DocumentType),
            "editor": [DocumentType.PDF, DocumentType.DOCX, DocumentType.TXT, 
                      DocumentType.MANUAL, DocumentType.UPLOAD],
            "viewer": [DocumentType.TXT, DocumentType.MANUAL],
            "guest": [DocumentType.TXT, DocumentType.MANUAL]
        }
        
        user_allowed_types = allowed_types.get(user_role, [DocumentType.MANUAL])
        
        if document_type not in user_allowed_types:
            raise UnsupportedDocumentTypeError(document_type.value)

    async def _check_document_quotas(self, user_id: int, user_role: str) -> None:
        """Check document quotas for user.
        
        Args:
            user_id: User ID to check quotas for
            user_role: User role for quota determination
            
        Raises:
            QuotaExceededError: If quota exceeded
        """
        # Define quotas by role
        quotas = {
            "admin": 10000,
            "editor": 1000,
            "viewer": 100,
            "guest": 10
        }
        
        max_documents = quotas.get(user_role, 10)
        
        # Count user's documents
        document_count = await self.document_repository.count_user_documents(
            user_id=user_id,
            status=DocumentStatus.ACTIVE
        )
        
        if document_count >= max_documents:
            raise QuotaExceededError(
                quota_type="user_documents",
                used=document_count,
                limit=max_documents
            )

    async def _check_duplicate_content(
        self,
        content: DocumentContent,
        user_id: int
    ) -> None:
        """Check for duplicate content in user's documents.
        
        Args:
            content: Content to check for duplicates
            user_id: User ID to check within
            
        Raises:
            BusinessRuleViolationError: If duplicate content found
        """
        # Calculate content hash
        content_hash = hashlib.sha256(content.raw_text.encode('utf-8')).hexdigest()
        
        # Check for documents with same hash
        duplicate_docs = await self.document_repository.get_documents_by_hash(content_hash)
        
        # Filter to user's documents
        user_duplicates = [doc for doc in duplicate_docs if doc.user_id == user_id]
        
        if user_duplicates:
            raise BusinessRuleViolationError(
                f"Document with identical content already exists: {user_duplicates[0].id}"
            )

    async def _validate_document_publication(
        self,
        document: DocumentEntity
    ) -> None:
        """Validate that document can be published.
        
        Args:
            document: Document to validate for publication
            
        Raises:
            BusinessRuleViolationError: If document cannot be published
        """
        # Check if document has content
        if not document.content.raw_text.strip():
            raise BusinessRuleViolationError(
                "Cannot publish document without content"
            )
        
        # Check if document has title
        if not document.title.strip():
            raise BusinessRuleViolationError(
                "Cannot publish document without title"
            )
        
        # Check if document is in valid status
        if document.status == DocumentStatus.ERROR:
            raise BusinessRuleViolationError(
                "Cannot publish document with errors"
            )

    def _get_category_tags(self, category: DocumentCategory) -> List[str]:
        """Get suggested tags for a document category.
        
        Args:
            category: Document category
            
        Returns:
            List[str]: Suggested tags for the category
        """
        category_tags = {
            DocumentCategory.LEI: ["legislação", "norma", "jurídico"],
            DocumentCategory.DECRETO: ["decreto", "regulamento", "executivo"],
            DocumentCategory.CONTRATO: ["contrato", "acordo", "negócio"],
            DocumentCategory.RELATORIO: ["relatório", "análise", "dados"],
            DocumentCategory.ATA: ["ata", "reunião", "registro"],
        }
        
        return category_tags.get(category, ["documento"])

    async def _get_storage_analysis(self, user_id: Optional[int]) -> Dict:
        """Get storage analysis for documents.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            Dict: Storage analysis data
        """
        # This would analyze storage usage patterns
        return {
            "total_size_mb": 1250.5,
            "average_document_size_mb": 2.1,
            "largest_documents": [],
            "storage_trend": "increasing"
        }

    async def _get_category_distribution(self, user_id: Optional[int]) -> Dict:
        """Get distribution of documents by category.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            Dict: Category distribution data
        """
        # This would query category distribution
        return {
            "lei": 45,
            "decreto": 23,
            "relatorio": 15,
            "other": 12
        }

    async def _get_tag_popularity(self, user_id: Optional[int]) -> List[Dict]:
        """Get popular tags by usage.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            List[Dict]: Popular tags with counts
        """
        # This would query tag popularity
        return [
            {"tag": "legislação", "count": 25},
            {"tag": "contrato", "count": 18},
            {"tag": "relatório", "count": 12},
        ]

    def _calculate_content_health(self, stats: Dict) -> str:
        """Calculate content health based on statistics.
        
        Args:
            stats: Document statistics
            
        Returns:
            str: Health status
        """
        total_docs = stats.get("total_documents", 0)
        error_docs = stats.get("error_documents", 0)
        
        if total_docs == 0:
            return "healthy"
        
        error_rate = error_docs / total_docs
        
        if error_rate < 0.01:
            return "healthy"
        elif error_rate < 0.05:
            return "warning"
        else:
            return "critical"