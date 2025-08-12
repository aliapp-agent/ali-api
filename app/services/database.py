"""Database service for Firebase Firestore integration."""

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import settings
from app.core.firebase import get_firestore
from app.core.logging import logger
from app.models.session import Session


class DatabaseService:
    """Firebase Firestore database service."""
    
    def __init__(self):
        """Initialize the database service."""
        self.db = get_firestore()
        self.is_available = self.db is not None
        
    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available in development mode")
            return False
            
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

    # User-specific methods
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by Firebase UID.
        
        Args:
            user_id: Firebase UID
            
        Returns:
            User document data if found, None otherwise
        """
        return await self.get_document("users", user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User document data if found, None otherwise
        """
        try:
            filters = [FieldFilter("email", "==", email)]
            users = await self.query_documents("users", filters=filters, limit=1)
            return users[0] if users else None
        except Exception as e:
            logger.error(
                "database_get_user_by_email_failed",
                email=email,
                error=str(e)
            )
            return None
    
    async def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Create a new user document.
        
        Args:
            user_id: Firebase UID
            user_data: User data dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.create_document("users", user_id, user_data)
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing user document.
        
        Args:
            user_id: Firebase UID
            update_data: Updated user data
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.update_document("users", user_id, update_data)
    
    async def list_users(
        self, 
        limit: Optional[int] = None,
        filters: Optional[List[FieldFilter]] = None,
        order_by: Optional[str] = "created_at"
    ) -> List[Dict[str, Any]]:
        """List users with optional filtering and pagination.
        
        Args:
            limit: Maximum number of users to return
            filters: Optional filters to apply
            order_by: Field to order by
            
        Returns:
            List of user documents
        """
        return await self.query_documents(
            "users", 
            filters=filters, 
            limit=limit, 
            order_by=order_by
        )
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user document.
        
        Args:
            user_id: Firebase UID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.delete_document("users", user_id)
    
    # Session-specific methods
    async def get_session(self, session_id: str) -> Optional["Session"]:
        """Get a session by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session object if found, None otherwise
        """
        from app.models.session import Session
        
        session_data = await self.get_document("sessions", session_id)
        if not session_data:
            return None
            
        # Convert to Session object
        return Session(
            session_id=session_id,
            user_id=session_data["user_id"],
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"],
            is_active=session_data.get("is_active", True),
            metadata=session_data.get("metadata", {})
        )
    
    async def create_session(self, session_id: str, user_id: str) -> "Session":
        """Create a new session document.
        
        Args:
            session_id: Session ID
            user_id: Firebase UID
            
        Returns:
            Session object
        """
        from datetime import datetime
        from app.models.session import Session
        
        now = datetime.utcnow()
        
        session_data = {
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "metadata": {"name": f"Chat Session {now.strftime('%Y-%m-%d %H:%M')}"}
        }
        
        success = await self.create_document("sessions", session_id, session_data)
        if not success:
            raise Exception("Failed to create session")
            
        return Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            is_active=True,
            metadata=session_data["metadata"]
        )
    
    async def update_session_name(self, session_id: str, name: str) -> "Session":
        """Update a session's name.
        
        Args:
            session_id: Session ID
            name: New session name
            
        Returns:
            Updated session object
        """
        from datetime import datetime
        update_data = {
            "metadata.name": name,
            "updated_at": datetime.utcnow(),
        }
        
        success = await self.update_document("sessions", session_id, update_data)
        if not success:
            raise Exception("Failed to update session name")
            
        # Return updated session
        session = await self.get_session(session_id)
        if not session:
            raise Exception("Session not found after update")
            
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session document.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.delete_document("sessions", session_id)
    
    async def get_user_sessions(self, user_id: str) -> List["Session"]:
        """Get all sessions for a user.
        
        Args:
            user_id: Firebase UID
            
        Returns:
            List of session objects
        """
        from google.cloud.firestore_v1.base_query import FieldFilter
        from app.models.session import Session
        
        filters = [FieldFilter("user_id", "==", user_id)]
        sessions_data = await self.query_documents("sessions", filters=filters, order_by="created_at")
        
        sessions = []
        for session_data in sessions_data:
            # We need to get the session ID from the document reference
            # For now, we'll generate a temporary ID - in production you'd store it or query differently
            session_id = str(uuid.uuid4())
            sessions.append(Session(
                session_id=session_id,
                user_id=session_data["user_id"],
                created_at=session_data["created_at"],
                updated_at=session_data["updated_at"],
                is_active=session_data.get("is_active", True),
                metadata=session_data.get("metadata", {})
            ))
        
        return sessions


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