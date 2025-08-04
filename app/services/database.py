"""Database service for Firebase Firestore integration."""

import asyncio
from typing import Any, Dict, List, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import settings
from app.core.firebase import get_firestore
from app.core.logging import logger


class DatabaseService:
    """Firebase Firestore database service."""
    
    def __init__(self):
        """Initialize the database service."""
        self.db = get_firestore()
        
    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            # Simple health check - attempt to read from a system collection
            doc_ref = self.db.collection("_health").document("check")
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.get
            )
            return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False
    
    async def create_document(
        self, 
        collection: str, 
        document_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Create a document in the specified collection.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.set, data
            )
            return True
        except Exception as e:
            logger.error(
                "database_create_document_failed",
                collection=collection,
                document_id=document_id,
                error=str(e)
            )
            return False
    
    async def get_document(
        self, 
        collection: str, 
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document from the specified collection.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data if found, None otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.get
            )
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(
                "database_get_document_failed",
                collection=collection,
                document_id=document_id,
                error=str(e)
            )
            return None
    
    async def update_document(
        self, 
        collection: str, 
        document_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Update a document in the specified collection.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Updated document data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.update, data
            )
            return True
        except Exception as e:
            logger.error(
                "database_update_document_failed",
                collection=collection,
                document_id=document_id,
                error=str(e)
            )
            return False
    
    async def delete_document(
        self, 
        collection: str, 
        document_id: str
    ) -> bool:
        """Delete a document from the specified collection.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.delete
            )
            return True
        except Exception as e:
            logger.error(
                "database_delete_document_failed",
                collection=collection,
                document_id=document_id,
                error=str(e)
            )
            return False
    
    async def query_documents(
        self, 
        collection: str, 
        filters: Optional[List[FieldFilter]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query documents from the specified collection.
        
        Args:
            collection: Collection name
            filters: List of field filters
            limit: Maximum number of documents to return
            order_by: Field to order by
            
        Returns:
            List of document data
        """
        try:
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for filter_obj in filters:
                    query = query.where(filter=filter_obj)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = await asyncio.get_event_loop().run_in_executor(
                None, query.stream
            )
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(
                "database_query_documents_failed",
                collection=collection,
                error=str(e)
            )
            return []


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance.
    
    Returns:
        DatabaseService: The database service instance
    """
    global _database_service
    
    if _database_service is None:
        _database_service = DatabaseService()
    
    return _database_service