"""Firestore Document Repository.

This module provides Firestore implementation for document data management,
including file storage integration with Google Cloud Storage.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from app.infrastructure.firestore.base_repository import BaseFirestoreRepository
from app.domain.entities.document_entity import DocumentEntity
from app.domain.repositories.document_repository import DocumentRepositoryInterface
from app.domain.entities import DocumentStatus, DocumentType, DocumentCategory


class FirestoreDocumentRepository(BaseFirestoreRepository, DocumentRepositoryInterface):
    """Firestore implementation of Document Repository."""
    
    def __init__(self):
        """Initialize Firestore Document Repository."""
        super().__init__('documents')
    
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document.
        
        Args:
            document: Document entity to create
            
        Returns:
            DocumentEntity: Created document entity
        """
        data = self.from_entity(document)
        doc_id = await super().create(data, document.id)
        
        # Return document with generated ID if not provided
        if not document.id:
            document.id = doc_id
        
        return document
    
    async def get_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[DocumentEntity]: Document entity or None if not found
        """
        data = await super().get_by_id(document_id)
        if data:
            return self.to_entity(data)
        return None
    
    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update document.
        
        Args:
            document: Document entity to update
            
        Returns:
            DocumentEntity: Updated document entity
        """
        data = self.from_entity(document)
        await super().update(document.id, data)
        return document
    
    async def delete(self, document_id: str) -> bool:
        """Delete document (soft delete).
        
        Args:
            document_id: Document ID
            
        Returns:
            bool: True if deleted successfully
        """
        return await super().update(document_id, {
            'status': DocumentStatus.DELETED.value,
            'deleted_at': datetime.utcnow()
        })
    
    async def get_user_documents(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        category: Optional[DocumentCategory] = None,
        is_public: Optional[bool] = None
    ) -> List[DocumentEntity]:
        """Get documents for a specific user."""
        query = self.collection.where('user_id', '==', str(user_id))
        
        # Apply filters
        if status:
            query = query.where('status', '==', status.value)
        if document_type:
            query = query.where('document_type', '==', document_type.value)
        if category:
            query = query.where('category', '==', category.value)
        if is_public is not None:
            query = query.where('is_public', '==', is_public)
        
        # Order by created_at descending
        query = query.order_by('created_at', direction='desc')
        
        # Apply pagination
        if offset > 0:
            docs = query.limit(offset + limit).stream()
            docs_list = list(docs)[offset:]
        else:
            docs_list = list(query.limit(limit).stream())
        
        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def count_user_documents(
        self,
        user_id: int,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        category: Optional[DocumentCategory] = None,
        is_public: Optional[bool] = None
    ) -> int:
        """Count documents for a specific user."""
        filters = {'user_id': str(user_id)}
        
        if status:
            filters['status'] = status.value
        if document_type:
            filters['document_type'] = document_type.value
        if category:
            filters['category'] = category.value
        if is_public is not None:
            filters['is_public'] = is_public
        
        return await self.count(filters)
    
    async def get_public_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None,
        document_type: Optional[DocumentType] = None
    ) -> List[DocumentEntity]:
        """Get public documents."""
        query = self.collection.where('is_public', '==', True)
        query = query.where('status', '==', DocumentStatus.PROCESSED.value)
        
        # Apply filters
        if category:
            query = query.where('category', '==', category.value)
        if document_type:
            query = query.where('document_type', '==', document_type.value)
        
        # Order by created_at descending
        query = query.order_by('created_at', direction='desc')
        
        # Apply pagination
        if offset > 0:
            docs = query.limit(offset + limit).stream()
            docs_list = list(docs)[offset:]
        else:
            docs_list = list(query.limit(limit).stream())
        
        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_documents_by_category(
        self,
        category: DocumentCategory,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> List[DocumentEntity]:
        """Get documents by category."""
        query = self.collection.where('category', '==', category.value)
        query = query.where('status', '==', DocumentStatus.PROCESSED.value)
        
        if user_id:
            query = query.where('user_id', '==', str(user_id))
        else:
            query = query.where('is_public', '==', True)
        
        query = query.order_by('created_at', direction='desc')
        
        # Apply pagination
        if offset > 0:
            docs = query.limit(offset + limit).stream()
            docs_list = list(docs)[offset:]
        else:
            docs_list = list(query.limit(limit).stream())
        
        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_documents_by_type(
        self,
        document_type: DocumentType,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> List[DocumentEntity]:
        """Get documents by type."""
        query = self.collection.where('document_type', '==', document_type.value)
        query = query.where('status', '==', DocumentStatus.PROCESSED.value)
        
        if user_id:
            query = query.where('user_id', '==', str(user_id))
        else:
            query = query.where('is_public', '==', True)
        
        query = query.order_by('created_at', direction='desc')
        
        # Apply pagination
        if offset > 0:
            docs = query.limit(offset + limit).stream()
            docs_list = list(docs)[offset:]
        else:
            docs_list = list(query.limit(limit).stream())
        
        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None
    ) -> List[DocumentEntity]:
        """Search documents by title, content, or tags."""
        # Note: Firestore doesn't support full-text search natively
        # This is a basic implementation that searches in title
        # For better search, integrate with Algolia or use Cloud Search API
        
        base_query = self.collection.where('status', '==', DocumentStatus.PROCESSED.value)
        
        # Search in title (basic approach)
        query_lower = query.lower()
        
        # This is a simplified search - in production, use proper search service
        docs = base_query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Check if user has access
            doc_user_id = data.get('user_id')
            if user_id and doc_user_id == str(user_id):
                # User's own document
                pass
            elif include_public and data.get('is_public'):
                # Public document
                pass
            else:
                continue
            
            # Apply category filter
            if category and data.get('category') != category.value:
                continue
            
            # Basic text search in title and description
            title = (data.get('title') or '').lower()
            description = (data.get('description') or '').lower()
            tags = data.get('tags', [])
            tag_text = ' '.join(tags).lower()
            
            if (query_lower in title or 
                query_lower in description or 
                query_lower in tag_text):
                results.append(self.to_entity(data))
                
                if len(results) >= limit + offset:
                    break
        
        # Apply offset and limit
        return results[offset:offset + limit]
    
    async def get_documents_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> List[DocumentEntity]:
        """Get documents by tags."""
        # Firestore array queries - using array-contains-any for OR, array-contains for AND
        query = self.collection.where('status', '==', DocumentStatus.PROCESSED.value)
        
        if match_all:
            # For match_all, we need to filter each tag separately (limited approach)
            for tag in tags:
                query = query.where('tags', 'array_contains', tag)
        else:
            # For match_any, use array-contains-any
            query = query.where('tags', 'array_contains_any', tags)
        
        if user_id:
            query = query.where('user_id', '==', str(user_id))
        else:
            query = query.where('is_public', '==', True)
        
        query = query.order_by('created_at', direction='desc')
        
        # Apply pagination
        if offset > 0:
            docs = query.limit(offset + limit).stream()
            docs_list = list(docs)[offset:]
        else:
            docs_list = list(query.limit(limit).stream())
        
        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_recent_documents(
        self,
        limit: int = 20,
        user_id: Optional[int] = None,
        include_public: bool = True
    ) -> List[DocumentEntity]:
        """Get recently created or updated documents."""
        if user_id:
            query = self.collection.where('user_id', '==', str(user_id))
        else:
            query = self.collection.where('is_public', '==', True)
        
        query = query.where('status', '==', DocumentStatus.PROCESSED.value)
        query = query.order_by('updated_at', direction='desc')
        query = query.limit(limit)
        
        docs = query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_popular_documents(
        self,
        limit: int = 10,
        time_period_days: int = 30,
        category: Optional[DocumentCategory] = None
    ) -> List[DocumentEntity]:
        """Get most accessed documents in a time period."""
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        query = self.collection.where('status', '==', DocumentStatus.PROCESSED.value)
        query = query.where('is_public', '==', True)
        query = query.where('updated_at', '>=', cutoff_date)
        
        if category:
            query = query.where('category', '==', category.value)
        
        # Order by access_count if available, otherwise by updated_at
        query = query.order_by('access_count', direction='desc')
        query = query.limit(limit)
        
        docs = query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_document_statistics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> dict:
        """Get document statistics."""
        base_query = self.collection
        
        if user_id:
            base_query = base_query.where('user_id', '==', str(user_id))
        
        if date_from:
            base_query = base_query.where('created_at', '>=', date_from)
        
        if date_to:
            base_query = base_query.where('created_at', '<=', date_to)
        
        docs = list(base_query.stream())
        
        stats = {
            'total_documents': len(docs),
            'by_status': {},
            'by_category': {},
            'by_type': {},
            'total_size_mb': 0,
            'public_documents': 0,
            'private_documents': 0
        }
        
        for doc in docs:
            data = doc.to_dict()
            
            # Count by status
            status = data.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Count by category
            category = data.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by type
            doc_type = data.get('document_type', 'unknown')
            stats['by_type'][doc_type] = stats['by_type'].get(doc_type, 0) + 1
            
            # Sum file sizes
            file_size = data.get('file_size_mb', 0)
            stats['total_size_mb'] += file_size
            
            # Count public vs private
            if data.get('is_public'):
                stats['public_documents'] += 1
            else:
                stats['private_documents'] += 1
        
        return stats
    
    async def get_documents_by_hash(self, file_hash: str) -> List[DocumentEntity]:
        """Get documents with matching content hash (duplicates)."""
        docs_data = await self.find_by_field('file_hash', file_hash)
        return [self.to_entity(data) for data in docs_data]
    
    async def bulk_update_status(
        self,
        document_ids: List[str],
        status: DocumentStatus
    ) -> int:
        """Bulk update document status."""
        updates = {}
        for doc_id in document_ids:
            updates[doc_id] = {'status': status.value}
        
        success = await self.batch_update(updates)
        return len(document_ids) if success else 0
    
    async def bulk_update_category(
        self,
        document_ids: List[str],
        category: DocumentCategory
    ) -> int:
        """Bulk update document category."""
        updates = {}
        for doc_id in document_ids:
            updates[doc_id] = {'category': category.value}
        
        success = await self.batch_update(updates)
        return len(document_ids) if success else 0
    
    async def archive_old_documents(
        self,
        older_than: datetime,
        exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Archive documents older than specified date."""
        query = self.collection.where('created_at', '<', older_than)
        query = query.where('status', '!=', DocumentStatus.ARCHIVED.value)
        
        docs = list(query.stream())
        archived_count = 0
        
        for doc in docs:
            data = doc.to_dict()
            user_id = data.get('user_id')
            
            # Skip excluded users
            if exclude_user_ids and user_id and int(user_id) in exclude_user_ids:
                continue
            
            # Archive the document
            await self.update(doc.id, {
                'status': DocumentStatus.ARCHIVED.value,
                'archived_at': datetime.utcnow()
            })
            archived_count += 1
        
        return archived_count
    
    async def cleanup_deleted_documents(self, deleted_before: datetime) -> int:
        """Permanently remove documents marked as deleted."""
        query = self.collection.where('status', '==', DocumentStatus.DELETED.value)
        query = query.where('deleted_at', '<', deleted_before)
        
        docs = list(query.stream())
        doc_ids = [doc.id for doc in docs]
        
        if doc_ids:
            success = await self.batch_delete(doc_ids)
            return len(doc_ids) if success else 0
        
        return 0
    
    async def get_large_documents(
        self,
        size_threshold_mb: float = 10.0,
        limit: int = 50
    ) -> List[DocumentEntity]:
        """Get documents larger than threshold."""
        query = self.collection.where('file_size_mb', '>=', size_threshold_mb)
        query = query.order_by('file_size_mb', direction='desc')
        query = query.limit(limit)
        
        docs = query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_processing_documents(
        self,
        older_than_minutes: int = 30
    ) -> List[DocumentEntity]:
        """Get documents stuck in processing state."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        
        query = self.collection.where('status', '==', DocumentStatus.PROCESSING.value)
        query = query.where('updated_at', '<', cutoff_time)
        
        docs = query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(self.to_entity(data))
        
        return results
    
    async def get_all_tags(
        self,
        user_id: Optional[int] = None,
        min_usage_count: int = 1
    ) -> List[Tuple[str, int]]:
        """Get all tags with usage counts."""
        query = self.collection.where('status', '==', DocumentStatus.PROCESSED.value)
        
        if user_id:
            query = query.where('user_id', '==', str(user_id))
        
        docs = list(query.stream())
        tag_counts = {}
        
        for doc in docs:
            data = doc.to_dict()
            tags = data.get('tags', [])
            
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Filter by minimum usage count and sort by count descending
        filtered_tags = [
            (tag, count) for tag, count in tag_counts.items() 
            if count >= min_usage_count
        ]
        
        return sorted(filtered_tags, key=lambda x: x[1], reverse=True)
    
    def to_entity(self, data: Dict[str, Any]) -> DocumentEntity:
        """Convert Firestore document to DocumentEntity."""
        return DocumentEntity(
            id=data.get('id'),
            title=data.get('title'),
            filename=data.get('filename'),
            file_path=data.get('file_path'),
            gcs_url=data.get('gcs_url'),
            user_id=int(data.get('user_id')) if data.get('user_id') else None,
            category=DocumentCategory(data.get('category', 'other')),
            document_type=DocumentType(data.get('document_type', 'pdf')),
            status=DocumentStatus(data.get('status', 'uploaded')),
            file_size_mb=data.get('file_size_mb', 0.0),
            file_hash=data.get('file_hash'),
            description=data.get('description'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            is_public=data.get('is_public', False),
            access_count=data.get('access_count', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            processed_at=data.get('processed_at'),
            archived_at=data.get('archived_at'),
            deleted_at=data.get('deleted_at')
        )
    
    def from_entity(self, entity: DocumentEntity) -> Dict[str, Any]:
        """Convert DocumentEntity to Firestore document."""
        data = {
            'title': entity.title,
            'filename': entity.filename,
            'file_path': entity.file_path,
            'user_id': str(entity.user_id) if entity.user_id else None,
            'category': entity.category.value if entity.category else 'other',
            'document_type': entity.document_type.value if entity.document_type else 'pdf',
            'status': entity.status.value if entity.status else 'uploaded',
            'file_size_mb': entity.file_size_mb or 0.0,
            'is_public': entity.is_public or False,
            'access_count': entity.access_count or 0,
            'tags': entity.tags or [],
            'metadata': entity.metadata or {}
        }
        
        # Add optional fields if they exist
        if entity.gcs_url:
            data['gcs_url'] = entity.gcs_url
        if entity.file_hash:
            data['file_hash'] = entity.file_hash
        if entity.description:
            data['description'] = entity.description
        if entity.created_at:
            data['created_at'] = entity.created_at
        if entity.updated_at:
            data['updated_at'] = entity.updated_at
        if entity.processed_at:
            data['processed_at'] = entity.processed_at
        if entity.archived_at:
            data['archived_at'] = entity.archived_at
        if entity.deleted_at:
            data['deleted_at'] = entity.deleted_at
        
        return data