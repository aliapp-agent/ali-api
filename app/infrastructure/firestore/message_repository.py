"""Firestore Message Repository.

This module provides Firestore implementation for chat message management
using subcollections within chat sessions.
"""

from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from app.domain.entities.message_entity import MessageEntity
from app.domain.repositories.message_repository import MessageRepositoryInterface
from app.infrastructure.firestore.base_repository import BaseFirestoreRepository


class FirestoreMessageRepository(BaseFirestoreRepository, MessageRepositoryInterface):
    """Firestore implementation of Message Repository using subcollections."""

    def __init__(self):
        """Initialize Firestore Message Repository."""
        super().__init__("chat_sessions")  # Parent collection

    def get_messages_collection(self, session_id: str):
        """Get messages subcollection for a session.

        Args:
            session_id: Session ID

        Returns:
            CollectionReference: Messages subcollection
        """
        return self.collection.document(session_id).collection("messages")

    async def create_message(self, message: MessageEntity) -> MessageEntity:
        """Create a new message in a session.

        Args:
            message: Message entity to create

        Returns:
            MessageEntity: Created message entity
        """
        data = self.from_entity(message)
        messages_collection = self.get_messages_collection(message.session_id)

        # Add timestamps
        now = datetime.utcnow()
        data.update({"timestamp": now, "created_at": now, "updated_at": now})

        if message.id:
            doc_ref = messages_collection.document(message.id)
            doc_ref.set(data)
            doc_id = message.id
        else:
            doc_ref = messages_collection.add(data)[1]
            doc_id = doc_ref.id

        # Return message with generated ID if not provided
        if not message.id:
            message.id = doc_id

        return message

    async def get_message_by_id(
        self, session_id: str, message_id: str
    ) -> Optional[MessageEntity]:
        """Get message by ID within a session.

        Args:
            session_id: Session ID
            message_id: Message ID

        Returns:
            Optional[MessageEntity]: Message entity or None if not found
        """
        messages_collection = self.get_messages_collection(session_id)
        doc_ref = messages_collection.document(message_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            data["session_id"] = session_id
            return self.to_entity(data)
        return None

    async def update_message(self, message: MessageEntity) -> MessageEntity:
        """Update message.

        Args:
            message: Message entity to update

        Returns:
            MessageEntity: Updated message entity
        """
        data = self.from_entity(message)
        data["updated_at"] = datetime.utcnow()

        messages_collection = self.get_messages_collection(message.session_id)
        doc_ref = messages_collection.document(message.id)
        doc_ref.update(data)

        return message

    async def delete_message(self, session_id: str, message_id: str) -> bool:
        """Delete message.

        Args:
            session_id: Session ID
            message_id: Message ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            messages_collection = self.get_messages_collection(session_id)
            doc_ref = messages_collection.document(message_id)
            doc_ref.delete()
            return True
        except Exception:
            return False

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        order_by: str = "timestamp",
        direction: str = "asc",
    ) -> List[MessageEntity]:
        """Get all messages for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            order_by: Field to order by
            direction: Sort direction ('asc' or 'desc')

        Returns:
            List[MessageEntity]: List of messages in the session
        """
        messages_collection = self.get_messages_collection(session_id)

        from google.cloud.firestore import Query
        
        firestore_direction = Query.ASCENDING if direction.lower() == "asc" else Query.DESCENDING
        query = messages_collection.order_by(order_by, direction=firestore_direction).limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["session_id"] = session_id
            results.append(self.to_entity(data))

        return results

    async def get_recent_messages(
        self, session_id: str, count: int = 10
    ) -> List[MessageEntity]:
        """Get recent messages for a session.

        Args:
            session_id: Session ID
            count: Number of recent messages to return

        Returns:
            List[MessageEntity]: List of recent messages
        """
        return await self.get_session_messages(
            session_id=session_id, limit=count, order_by="timestamp", direction="desc"
        )

    async def search_messages(
        self, session_id: str, query_text: str, limit: int = 50
    ) -> List[MessageEntity]:
        """Search messages by content (simplified - Firestore doesn't support full text search).

        Args:
            session_id: Session ID
            query_text: Text to search for
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of matching messages
        """
        # Note: This is a simplified search. For better search capabilities,
        # consider using Cloud Search API or Algolia

        messages_collection = self.get_messages_collection(session_id)
        docs = messages_collection.order_by("timestamp").limit(limit).stream()

        results = []
        query_lower = query_text.lower()

        for doc in docs:
            data = doc.to_dict()
            content = data.get("content", "").lower()

            if query_lower in content:
                data["id"] = doc.id
                data["session_id"] = session_id
                results.append(self.to_entity(data))

        return results

    async def get_messages_by_role(
        self, session_id: str, role: str, limit: int = 100
    ) -> List[MessageEntity]:
        """Get messages by role (user/assistant).

        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of messages with specified role
        """
        messages_collection = self.get_messages_collection(session_id)

        query = (
            messages_collection.where("role", "==", role)
            .order_by("timestamp")
            .limit(limit)
        )
        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["session_id"] = session_id
            results.append(self.to_entity(data))

        return results

    async def get_message_count(self, session_id: str) -> int:
        """Get total message count for a session.

        Args:
            session_id: Session ID

        Returns:
            int: Number of messages in the session
        """
        messages_collection = self.get_messages_collection(session_id)
        docs = messages_collection.stream()
        return len(list(docs))

    async def delete_session_messages(self, session_id: str) -> bool:
        """Delete all messages in a session.

        Args:
            session_id: Session ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            messages_collection = self.get_messages_collection(session_id)
            docs = messages_collection.stream()

            batch = self.db.batch()
            for doc in docs:
                batch.delete(doc.reference)

            batch.commit()
            return True
        except Exception:
            return False

    async def get_messages_since(
        self, session_id: str, since: datetime, limit: int = 100
    ) -> List[MessageEntity]:
        """Get messages since a specific timestamp.

        Args:
            session_id: Session ID
            since: Timestamp to get messages after
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of messages since timestamp
        """
        messages_collection = self.get_messages_collection(session_id)

        query = (
            messages_collection.where("timestamp", ">=", since)
            .order_by("timestamp")
            .limit(limit)
        )
        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["session_id"] = session_id
            results.append(self.to_entity(data))

        return results

    async def batch_create_messages(
        self, session_id: str, messages: List[MessageEntity]
    ) -> List[str]:
        """Create multiple messages in batch.

        Args:
            session_id: Session ID
            messages: List of message entities

        Returns:
            List[str]: List of created message IDs
        """
        messages_collection = self.get_messages_collection(session_id)
        batch = self.db.batch()
        doc_ids = []
        now = datetime.utcnow()

        for message in messages:
            data = self.from_entity(message)
            data.update({"timestamp": now, "created_at": now, "updated_at": now})

            if message.id:
                doc_ref = messages_collection.document(message.id)
                doc_ids.append(message.id)
            else:
                doc_ref = messages_collection.document()
                doc_ids.append(doc_ref.id)

            batch.set(doc_ref, data)

        batch.commit()
        return doc_ids

    def to_entity(self, data: Dict[str, Any]) -> MessageEntity:
        """Convert Firestore document to MessageEntity.

        Args:
            data: Document data from Firestore

        Returns:
            MessageEntity: Message entity instance
        """
        return MessageEntity(
            id=data.get("id"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            role=data.get("role"),
            content=data.get("content"),
            status=data.get("status", "completed"),
            metadata=data.get("metadata"),
            context=data.get("context"),
            timestamp=data.get("timestamp"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def from_entity(self, entity: MessageEntity) -> Dict[str, Any]:
        """Convert MessageEntity to Firestore document.

        Args:
            entity: Message entity instance

        Returns:
            Dict[str, Any]: Document data for Firestore
        """
        data = {
            "user_id": entity.user_id,
            "role": entity.role,
            "content": entity.content,
            "status": entity.status,
        }

        # Add optional fields if they exist
        if entity.metadata is not None:
            data["metadata"] = entity.metadata
        if entity.context is not None:
            data["context"] = entity.context
        if entity.timestamp is not None:
            data["timestamp"] = entity.timestamp
        if entity.created_at is not None:
            data["created_at"] = entity.created_at
        if entity.updated_at is not None:
            data["updated_at"] = entity.updated_at

        return data

    async def get_user_messages(
        self, user_id: str, limit: int = 100, session_ids: Optional[List[str]] = None
    ) -> List[MessageEntity]:
        """Get messages by user across sessions.

        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            session_ids: Filter by specific session IDs (optional)

        Returns:
            List[MessageEntity]: List of user messages
        """
        results = []

        # If specific sessions provided, search in those
        if session_ids:
            sessions_to_search = session_ids
        else:
            # Get all user sessions first
            sessions_query = self.collection.where("user_id", "==", user_id)
            sessions_docs = list(sessions_query.stream())
            sessions_to_search = [doc.id for doc in sessions_docs]

        # Search messages in each session
        for session_id in sessions_to_search:
            messages_collection = self.get_messages_collection(session_id)
            query = (
                messages_collection.where("user_id", "==", user_id)
                .order_by("timestamp", direction="desc")
                .limit(limit)
            )

            docs = query.stream()
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                data["session_id"] = session_id
                results.append(self.to_entity(data))

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        return results

    async def get_messages_by_status(
        self, session_id: str, status: str, limit: int = 100
    ) -> List[MessageEntity]:
        """Get messages by status.

        Args:
            session_id: Session ID
            status: Message status
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of messages with specified status
        """
        messages_collection = self.get_messages_collection(session_id)

        query = (
            messages_collection.where("status", "==", status)
            .order_by("timestamp")
            .limit(limit)
        )

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["session_id"] = session_id
            results.append(self.to_entity(data))

        return results

    async def count_session_messages(
        self, session_id: str, role: Optional[str] = None, status: Optional[str] = None
    ) -> int:
        """Count messages in a session with optional filters.

        Args:
            session_id: Session ID
            role: Filter by role (optional)
            status: Filter by status (optional)

        Returns:
            int: Number of messages
        """
        messages_collection = self.get_messages_collection(session_id)
        query = messages_collection

        if role:
            query = query.where("role", "==", role)
        if status:
            query = query.where("status", "==", status)

        docs = list(query.stream())
        return len(docs)

    async def get_conversation_context(
        self, session_id: str, limit: int = 10
    ) -> List[MessageEntity]:
        """Get recent conversation context for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages for context

        Returns:
            List[MessageEntity]: List of recent messages
        """
        return await self.get_recent_messages(session_id, limit)

    async def get_error_messages(
        self, session_id: Optional[str] = None, limit: int = 50
    ) -> List[MessageEntity]:
        """Get messages with error status.

        Args:
            session_id: Filter by session ID (optional)
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of error messages
        """
        if session_id:
            return await self.get_messages_by_status(session_id, "error", limit)
        else:
            # Search across all sessions - simplified approach
            # In production, consider maintaining an error messages index
            results = []
            sessions_query = self.collection.limit(100)  # Limit session search
            sessions_docs = list(sessions_query.stream())

            for session_doc in sessions_docs:
                session_errors = await self.get_messages_by_status(
                    session_doc.id, "error", limit
                )
                results.extend(session_errors)

                if len(results) >= limit:
                    break

            return results[:limit]

    async def get_high_token_messages(
        self,
        session_id: Optional[str] = None,
        token_threshold: int = 1000,
        limit: int = 50,
    ) -> List[MessageEntity]:
        """Get messages with high token count.

        Args:
            session_id: Filter by session ID (optional)
            token_threshold: Minimum token count
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of high token messages
        """
        results = []

        if session_id:
            sessions_to_search = [session_id]
        else:
            # Get recent sessions to search
            sessions_query = self.collection.order_by(
                "updated_at", direction="desc"
            ).limit(50)
            sessions_docs = list(sessions_query.stream())
            sessions_to_search = [doc.id for doc in sessions_docs]

        for session_id in sessions_to_search:
            messages_collection = self.get_messages_collection(session_id)

            # Note: This is a simplified approach since Firestore doesn't support
            # direct numeric comparisons on nested fields easily
            docs = list(
                messages_collection.order_by("timestamp", direction="desc")
                .limit(100)
                .stream()
            )

            for doc in docs:
                data = doc.to_dict()
                metadata = data.get("metadata", {})
                token_count = metadata.get("token_count", 0)

                if token_count >= token_threshold:
                    data["id"] = doc.id
                    data["session_id"] = session_id
                    results.append(self.to_entity(data))

                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        return results

    async def get_message_statistics(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get message statistics.

        Args:
            session_id: Filter by session ID (optional)
            user_id: Filter by user ID (optional)
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            dict: Message statistics
        """
        stats = {
            "total_messages": 0,
            "by_role": {},
            "by_status": {},
            "total_tokens": 0,
            "average_tokens_per_message": 0,
        }

        total_token_count = 0
        messages_with_tokens = 0

        if session_id:
            sessions_to_analyze = [session_id]
        else:
            # Get sessions to analyze
            sessions_query = self.collection
            if user_id:
                sessions_query = sessions_query.where("user_id", "==", user_id)
            if date_from:
                sessions_query = sessions_query.where("created_at", ">=", date_from)
            if date_to:
                sessions_query = sessions_query.where("created_at", "<=", date_to)

            sessions_docs = list(sessions_query.limit(100).stream())
            sessions_to_analyze = [doc.id for doc in sessions_docs]

        for session_id in sessions_to_analyze:
            messages_collection = self.get_messages_collection(session_id)
            query = messages_collection

            if date_from:
                query = query.where("timestamp", ">=", date_from)
            if date_to:
                query = query.where("timestamp", "<=", date_to)

            docs = list(query.stream())

            for doc in docs:
                data = doc.to_dict()
                stats["total_messages"] += 1

                # Count by role
                role = data.get("role", "unknown")
                stats["by_role"][role] = stats["by_role"].get(role, 0) + 1

                # Count by status
                status = data.get("status", "unknown")
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

                # Token statistics
                metadata = data.get("metadata", {})
                token_count = metadata.get("token_count", 0)
                if token_count > 0:
                    total_token_count += token_count
                    messages_with_tokens += 1

        stats["total_tokens"] = total_token_count
        if messages_with_tokens > 0:
            stats["average_tokens_per_message"] = round(
                total_token_count / messages_with_tokens, 2
            )

        return stats

    async def get_token_usage_by_period(
        self, user_id: Optional[str] = None, period_days: int = 30
    ) -> dict:
        """Get token usage statistics by time period.

        Args:
            user_id: Filter by user ID (optional)
            period_days: Number of days to analyze

        Returns:
            dict: Token usage by period
        """
        from datetime import (
            datetime,
            timedelta,
        )

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        stats = await self.get_message_statistics(
            user_id=user_id, date_from=start_date, date_to=end_date
        )

        return {
            "period_days": period_days,
            "start_date": start_date,
            "end_date": end_date,
            "total_tokens": stats["total_tokens"],
            "total_messages": stats["total_messages"],
            "average_tokens_per_day": round(stats["total_tokens"] / period_days, 2),
            "average_messages_per_day": round(stats["total_messages"] / period_days, 2),
        }

    async def get_conversation_export_data(self, session_id: str) -> dict:
        """Get conversation data for export.

        Args:
            session_id: Session ID

        Returns:
            dict: Export data with session and messages
        """
        # Get session data
        session_doc = self.collection.document(session_id).get()
        if not session_doc.exists:
            return {}

        session_data = session_doc.to_dict()
        session_data["id"] = session_doc.id

        # Get all messages
        messages = await self.get_session_messages(
            session_id, limit=10000, order_by="timestamp", direction="asc"
        )

        return {
            "session": session_data,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "status": msg.status,
                    "metadata": msg.metadata,
                }
                for msg in messages
            ],
            "export_timestamp": datetime.utcnow(),
            "total_messages": len(messages),
        }

    async def bulk_update_status(
        self, session_id: str, message_ids: List[str], status: str
    ) -> int:
        """Bulk update message status.

        Args:
            session_id: Session ID
            message_ids: List of message IDs
            status: New status

        Returns:
            int: Number of messages updated
        """
        messages_collection = self.get_messages_collection(session_id)
        batch = self.db.batch()

        for message_id in message_ids:
            doc_ref = messages_collection.document(message_id)
            batch.update(doc_ref, {"status": status, "updated_at": datetime.utcnow()})

        try:
            batch.commit()
            return len(message_ids)
        except Exception:
            return 0

    async def archive_old_messages(
        self, older_than_days: int = 90, session_id: Optional[str] = None
    ) -> int:
        """Archive messages older than specified days.

        Args:
            older_than_days: Number of days to consider as old
            session_id: Filter by session ID (optional)

        Returns:
            int: Number of messages archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        archived_count = 0

        if session_id:
            sessions_to_process = [session_id]
        else:
            # Get old sessions
            sessions_query = self.collection.where("updated_at", "<", cutoff_date)
            sessions_docs = list(sessions_query.limit(100).stream())
            sessions_to_process = [doc.id for doc in sessions_docs]

        for session_id in sessions_to_process:
            messages_collection = self.get_messages_collection(session_id)

            query = messages_collection.where("timestamp", "<", cutoff_date).where(
                "status", "!=", "archived"
            )

            docs = list(query.stream())

            for doc in docs:
                await self.update_message(
                    MessageEntity(
                        id=doc.id,
                        session_id=session_id,
                        user_id=doc.to_dict().get("user_id"),
                        role=doc.to_dict().get("role"),
                        content=doc.to_dict().get("content"),
                        status="archived",
                    )
                )
                archived_count += 1

        return archived_count

    async def cleanup_deleted_messages(
        self, deleted_before: datetime, session_id: Optional[str] = None
    ) -> int:
        """Permanently remove messages marked as deleted.

        Args:
            deleted_before: Remove messages deleted before this date
            session_id: Filter by session ID (optional)

        Returns:
            int: Number of messages permanently removed
        """
        deleted_count = 0

        if session_id:
            sessions_to_process = [session_id]
        else:
            # Get sessions with old deleted messages
            sessions_query = self.collection.where("updated_at", "<", deleted_before)
            sessions_docs = list(sessions_query.limit(100).stream())
            sessions_to_process = [doc.id for doc in sessions_docs]

        for session_id in sessions_to_process:
            messages_collection = self.get_messages_collection(session_id)

            query = messages_collection.where("status", "==", "deleted").where(
                "updated_at", "<", deleted_before
            )

            docs = list(query.stream())

            batch = self.db.batch()
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1

            if docs:
                batch.commit()

        return deleted_count
