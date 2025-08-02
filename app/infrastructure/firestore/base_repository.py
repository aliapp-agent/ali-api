"""Base Firestore repository.

This module provides base functionality for Firestore repositories with common
CRUD operations and query patterns.
"""

from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from google.cloud.firestore import (
    Client,
    CollectionReference,
    DocumentReference,
    Query,
)

from app.core.firebase import get_firestore


class BaseFirestoreRepository(ABC):
    """Base class for Firestore repositories."""

    def __init__(self, collection_name: str):
        """Initialize base Firestore repository.

        Args:
            collection_name: Name of the Firestore collection
        """
        self.collection_name = collection_name
        self._db: Optional[Client] = None
        self._collection: Optional[CollectionReference] = None

    @property
    def db(self) -> Client:
        """Get Firestore client."""
        if self._db is None:
            self._db = get_firestore()
        return self._db

    @property
    def collection(self) -> CollectionReference:
        """Get collection reference."""
        if self._collection is None:
            self._collection = self.db.collection(self.collection_name)
        return self._collection

    async def create(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """Create a new document.

        Args:
            data: Document data
            doc_id: Optional document ID (auto-generated if not provided)

        Returns:
            str: Document ID
        """
        # Add timestamps
        now = datetime.utcnow()
        data.update({"created_at": now, "updated_at": now})

        if doc_id:
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(data)
            return doc_id
        else:
            doc_ref = self.collection.add(data)[1]
            return doc_ref.id

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found
        """
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    async def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update document.

        Args:
            doc_id: Document ID
            data: Update data

        Returns:
            bool: True if updated successfully
        """
        try:
            # Add update timestamp
            data["updated_at"] = datetime.utcnow()

            doc_ref = self.collection.document(doc_id)
            doc_ref.update(data)
            return True
        except Exception:
            return False

    async def delete(self, doc_id: str) -> bool:
        """Delete document.

        Args:
            doc_id: Document ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.delete()
            return True
        except Exception:
            return False

    async def list_all(
        self,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        direction: str = "asc",
    ) -> List[Dict[str, Any]]:
        """List all documents in collection.

        Args:
            limit: Maximum number of documents to return
            order_by: Field to order by
            direction: Sort direction ('asc' or 'desc')

        Returns:
            List[Dict[str, Any]]: List of documents
        """
        query = self.collection

        if order_by:
            query = query.order_by(
                order_by,
                direction=Query.ASCENDING if direction == "asc" else Query.DESCENDING,
            )

        if limit:
            query = query.limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        return results

    async def find_by_field(
        self, field: str, value: Any, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find documents by field value.

        Args:
            field: Field name
            value: Field value
            limit: Maximum number of documents to return

        Returns:
            List[Dict[str, Any]]: List of matching documents
        """
        query = self.collection.where(field, "==", value)

        if limit:
            query = query.limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)

        return results

    async def find_by_user_id(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find documents by user ID.

        Args:
            user_id: User ID
            limit: Maximum number of documents to return

        Returns:
            List[Dict[str, Any]]: List of user's documents
        """
        return await self.find_by_field("user_id", user_id, limit)

    async def exists(self, doc_id: str) -> bool:
        """Check if document exists.

        Args:
            doc_id: Document ID

        Returns:
            bool: True if document exists
        """
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        return doc.exists

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection.

        Args:
            filters: Optional filters to apply

        Returns:
            int: Number of documents
        """
        query = self.collection

        if filters:
            for field, value in filters.items():
                query = query.where(field, "==", value)

        docs = query.stream()
        return len(list(docs))

    async def batch_create(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Create multiple documents in batch.

        Args:
            documents: List of document data

        Returns:
            List[str]: List of created document IDs
        """
        batch = self.db.batch()
        doc_ids = []
        now = datetime.utcnow()

        for data in documents:
            # Add timestamps
            data.update({"created_at": now, "updated_at": now})

            doc_ref = self.collection.document()
            batch.set(doc_ref, data)
            doc_ids.append(doc_ref.id)

        batch.commit()
        return doc_ids

    async def batch_update(self, updates: Dict[str, Dict[str, Any]]) -> bool:
        """Update multiple documents in batch.

        Args:
            updates: Dictionary mapping doc_id to update data

        Returns:
            bool: True if all updates successful
        """
        try:
            batch = self.db.batch()
            now = datetime.utcnow()

            for doc_id, data in updates.items():
                # Add update timestamp
                data["updated_at"] = now

                doc_ref = self.collection.document(doc_id)
                batch.update(doc_ref, data)

            batch.commit()
            return True
        except Exception:
            return False

    async def batch_delete(self, doc_ids: List[str]) -> bool:
        """Delete multiple documents in batch.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            bool: True if all deletions successful
        """
        try:
            batch = self.db.batch()

            for doc_id in doc_ids:
                doc_ref = self.collection.document(doc_id)
                batch.delete(doc_ref)

            batch.commit()
            return True
        except Exception:
            return False

    @abstractmethod
    def to_entity(self, data: Dict[str, Any]) -> Any:
        """Convert Firestore document to domain entity.

        Args:
            data: Document data from Firestore

        Returns:
            Any: Domain entity instance
        """
        pass

    @abstractmethod
    def from_entity(self, entity: Any) -> Dict[str, Any]:
        """Convert domain entity to Firestore document.

        Args:
            entity: Domain entity instance

        Returns:
            Dict[str, Any]: Document data for Firestore
        """
        pass
