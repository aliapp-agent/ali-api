"""Firestore Session Repository.

This module provides Firestore implementation for chat session management
with subcollections for messages.
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

from app.domain.entities.session_entity import SessionEntity
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.infrastructure.firestore.base_repository import BaseFirestoreRepository


class FirestoreSessionRepository(BaseFirestoreRepository, SessionRepositoryInterface):
    """Firestore implementation of Session Repository."""

    def __init__(self):
        """Initialize Firestore Session Repository."""
        super().__init__("sessions")

    async def create_session(self, session: SessionEntity) -> SessionEntity:
        """Create a new chat session.

        Args:
            session: Session entity to create

        Returns:
            SessionEntity: Created session entity
        """
        data = self.from_entity(session)
        doc_id = await self.create(data, session.id)

        # Return session with generated ID if not provided
        if not session.id:
            session.id = doc_id

        return session

    async def get_by_id(self, session_id: str) -> Optional[SessionEntity]:
        """Get session by ID (interface method).

        Args:
            session_id: Session ID

        Returns:
            Optional[SessionEntity]: Session entity or None if not found
        """
        # Call BaseFirestoreRepository.get_by_id() directly (not the current method)
        data = await super().get_by_id(session_id)
        if data:
            print(f"DEBUG: Raw session data from Firestore: {data}")
            entity = self.to_entity(data)
            print(f"DEBUG: Converted SessionEntity: {entity}")
            print(f"DEBUG: Entity type: {type(entity)}")
            return entity
        return None

    async def get_session_by_id(self, session_id: str) -> Optional[SessionEntity]:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Optional[SessionEntity]: Session entity or None if not found
        """
        return await self.get_by_id(session_id)

    async def update_session(self, session: SessionEntity) -> SessionEntity:
        """Update session.

        Args:
            session: Session entity to update

        Returns:
            SessionEntity: Updated session entity
        """
        data = self.from_entity(session)
        await self.update(session.id, data)
        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete session and all its messages.

        Args:
            session_id: Session ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            # Delete all messages in the session first
            messages_ref = self.collection.document(session_id).collection("messages")
            messages = messages_ref.stream()

            batch = self.db.batch()
            for message in messages:
                batch.delete(message.reference)

            # Delete the session document
            session_ref = self.collection.document(session_id)
            batch.delete(session_ref)

            batch.commit()
            return True
        except Exception:
            return False

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        order_by: str = "created_at",
        direction: str = "desc",
    ) -> List[SessionEntity]:
        """Get sessions for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            order_by: Field to order by
            direction: Sort direction ('asc' or 'desc')

        Returns:
            List[SessionEntity]: List of user's sessions
        """
        sessions_data = await self.find_by_user_id(user_id, limit)
        return [self.to_entity(data) for data in sessions_data]

    async def search_sessions(
        self,
        user_id: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 50,
    ) -> List[SessionEntity]:
        """Search sessions with optional filters.

        Args:
            user_id: Filter by user ID
            name_contains: Filter by session name containing text
            limit: Maximum number of sessions to return

        Returns:
            List[SessionEntity]: List of matching sessions
        """
        query = self.collection

        if user_id:
            query = query.where("user_id", "==", user_id)

        query = query.order_by("created_at", direction="desc").limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id

            # Filter by name if specified (Firestore doesn't support contains)
            if (
                name_contains
                and name_contains.lower() not in data.get("name", "").lower()
            ):
                continue

            results.append(self.to_entity(data))

        return results

    async def count_user_sessions(self, user_id: str) -> int:
        """Count sessions for a specific user.

        Args:
            user_id: User ID

        Returns:
            int: Number of sessions
        """
        return await self.count({"user_id": user_id})

    async def get_recent_sessions(
        self, user_id: Optional[str] = None, days: int = 7, limit: int = 20
    ) -> List[SessionEntity]:
        """Get recent sessions.

        Args:
            user_id: Optional user ID filter
            days: Number of days to look back
            limit: Maximum number of sessions to return

        Returns:
            List[SessionEntity]: List of recent sessions
        """
        query = self.collection

        # Filter by date
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.where("created_at", ">=", since_date)

        if user_id:
            query = query.where("user_id", "==", user_id)

        query = query.order_by("created_at", direction="desc").limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def update_session_stats(
        self,
        session_id: str,
        message_count: Optional[int] = None,
        total_tokens: Optional[int] = None,
        total_response_time: Optional[float] = None,
    ) -> bool:
        """Update session statistics.

        Args:
            session_id: Session ID
            message_count: New message count
            total_tokens: New total tokens
            total_response_time: New total response time

        Returns:
            bool: True if updated successfully
        """
        update_data = {}

        if message_count is not None:
            update_data["message_count"] = message_count
        if total_tokens is not None:
            update_data["total_tokens"] = total_tokens
        if total_response_time is not None:
            update_data["total_response_time"] = total_response_time

        if update_data:
            return await self.update(session_id, update_data)

        return True

    async def archive_session(self, session_id: str) -> bool:
        """Archive a session.

        Args:
            session_id: Session ID

        Returns:
            bool: True if archived successfully
        """
        return await self.update(
            session_id, {"status": "archived", "archived_at": datetime.utcnow()}
        )

    async def restore_session(self, session_id: str) -> bool:
        """Restore an archived session.

        Args:
            session_id: Session ID

        Returns:
            bool: True if restored successfully
        """
        return await self.update(session_id, {"status": "active", "archived_at": None})

    def to_entity(self, data: Dict[str, Any]) -> SessionEntity:
        """Convert Firestore document to SessionEntity.

        Args:
            data: Document data from Firestore

        Returns:
            SessionEntity: Session entity instance
        """
        # Handle both old domain format and new auth format
        session_id = data.get("id")  # This comes from BaseFirestoreRepository.get_by_id()
        
        if "metadata" in data and isinstance(data.get("metadata"), dict):
            # Auth system format - has metadata structure
            name = data.get("metadata", {}).get("name", "")
            status = "active" if data.get("is_active", True) else "inactive"
        else:
            # Original domain format
            name = data.get("name", "")
            status = data.get("status", "active")
            
        # Convert DatetimeWithNanoseconds to datetime
        def convert_datetime(dt):
            if hasattr(dt, 'timestamp'):
                from datetime import datetime
                return datetime.fromtimestamp(dt.timestamp())
            return dt
            
        return SessionEntity(
            id=session_id,
            user_id=data.get("user_id"),
            name=name,
            session_type=data.get("session_type", "chat"),
            status=status,
            context=data.get("context"),
            message_count=data.get("message_count", 0),
            total_tokens=data.get("total_tokens", 0),
            total_response_time=data.get("total_response_time", 0.0),
            created_at=convert_datetime(data.get("created_at")),
            updated_at=convert_datetime(data.get("updated_at")),
        )

    def from_entity(self, entity: SessionEntity) -> Dict[str, Any]:
        """Convert SessionEntity to Firestore document.

        Args:
            entity: Session entity instance

        Returns:
            Dict[str, Any]: Document data for Firestore
        """
        data = {
            "user_id": entity.user_id,
            "name": entity.name,
            "session_type": entity.session_type,
            "status": entity.status,
            "message_count": entity.message_count,
            "total_tokens": entity.total_tokens,
            "total_response_time": entity.total_response_time,
        }

        # Add optional fields if they exist
        if entity.context is not None:
            data["context"] = entity.context
        if entity.created_at is not None:
            data["created_at"] = entity.created_at
        if entity.updated_at is not None:
            data["updated_at"] = entity.updated_at

        return data

    async def get_active_sessions(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> List[SessionEntity]:
        """Get active sessions.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of sessions to return

        Returns:
            List[SessionEntity]: List of active sessions
        """
        query = self.collection.where("status", "==", "active")

        if user_id:
            query = query.where("user_id", "==", user_id)

        query = query.order_by("updated_at", direction="desc").limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_inactive_sessions(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> List[SessionEntity]:
        """Get inactive sessions.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of sessions to return

        Returns:
            List[SessionEntity]: List of inactive sessions
        """
        query = self.collection.where("status", "==", "inactive")

        if user_id:
            query = query.where("user_id", "==", user_id)

        query = query.order_by("updated_at", direction="desc").limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_sessions_by_type(
        self, session_type: str, user_id: Optional[str] = None, limit: int = 50
    ) -> List[SessionEntity]:
        """Get sessions by type.

        Args:
            session_type: Session type to filter by
            user_id: Filter by user ID (optional)
            limit: Maximum number of sessions to return

        Returns:
            List[SessionEntity]: List of sessions with specified type
        """
        query = self.collection.where("session_type", "==", session_type)

        if user_id:
            query = query.where("user_id", "==", user_id)

        query = query.order_by("created_at", direction="desc").limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_popular_sessions(
        self, limit: int = 10, time_period_days: int = 30
    ) -> List[SessionEntity]:
        """Get most popular sessions (by message count).

        Args:
            limit: Maximum number of sessions to return
            time_period_days: Time period in days to consider

        Returns:
            List[SessionEntity]: List of popular sessions
        """
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

        query = (
            self.collection.where("updated_at", ">=", cutoff_date)
            .order_by("message_count", direction="desc")
            .limit(limit)
        )

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_session_statistics(
        self,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get session statistics.

        Args:
            user_id: Filter by user ID (optional)
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            dict: Session statistics
        """
        query = self.collection

        if user_id:
            query = query.where("user_id", "==", user_id)
        if date_from:
            query = query.where("created_at", ">=", date_from)
        if date_to:
            query = query.where("created_at", "<=", date_to)

        docs = list(query.stream())

        stats = {
            "total_sessions": len(docs),
            "by_status": {},
            "by_type": {},
            "total_messages": 0,
            "total_tokens": 0,
            "average_messages_per_session": 0,
            "average_response_time": 0,
        }

        total_response_time = 0
        sessions_with_response_time = 0

        for doc in docs:
            data = doc.to_dict()

            # Count by status
            status = data.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Count by type
            session_type = data.get("session_type", "unknown")
            stats["by_type"][session_type] = stats["by_type"].get(session_type, 0) + 1

            # Sum totals
            stats["total_messages"] += data.get("message_count", 0)
            stats["total_tokens"] += data.get("total_tokens", 0)

            # Response time
            response_time = data.get("total_response_time", 0)
            if response_time > 0:
                total_response_time += response_time
                sessions_with_response_time += 1

        # Calculate averages
        if len(docs) > 0:
            stats["average_messages_per_session"] = round(
                stats["total_messages"] / len(docs), 2
            )

        if sessions_with_response_time > 0:
            stats["average_response_time"] = round(
                total_response_time / sessions_with_response_time, 2
            )

        return stats

    async def record_session_message(
        self, session_id: str, message_tokens: int = 0, response_time: float = 0.0
    ) -> bool:
        """Record a message in session statistics.

        Args:
            session_id: Session ID
            message_tokens: Number of tokens in the message
            response_time: Response time for the message

        Returns:
            bool: True if recorded successfully
        """
        from google.cloud import firestore

        return await self.update(
            session_id,
            {
                "message_count": firestore.Increment(1),
                "total_tokens": firestore.Increment(message_tokens),
                "total_response_time": firestore.Increment(response_time),
                "updated_at": datetime.utcnow(),
            },
        )

    async def update_session_activity(self, session_id: str) -> bool:
        """Update session's last activity timestamp.

        Args:
            session_id: Session ID

        Returns:
            bool: True if updated successfully
        """
        return await self.update(session_id, {"updated_at": datetime.utcnow()})

    async def bulk_update_status(self, session_ids: List[str], status: str) -> int:
        """Bulk update session status.

        Args:
            session_ids: List of session IDs
            status: New status

        Returns:
            int: Number of sessions updated
        """
        updates = {}
        for session_id in session_ids:
            updates[session_id] = {"status": status}

        success = await self.batch_update(updates)
        return len(session_ids) if success else 0

    async def archive_old_sessions(
        self, older_than_days: int = 30, exclude_user_ids: Optional[List[str]] = None
    ) -> int:
        """Archive sessions older than specified days.

        Args:
            older_than_days: Number of days to consider as old
            exclude_user_ids: User IDs to exclude from archiving

        Returns:
            int: Number of sessions archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        query = self.collection.where("updated_at", "<", cutoff_date).where(
            "status", "!=", "archived"
        )

        docs = list(query.stream())
        archived_count = 0

        for doc in docs:
            data = doc.to_dict()
            user_id = data.get("user_id")

            # Skip excluded users
            if exclude_user_ids and user_id in exclude_user_ids:
                continue

            # Archive the session
            await self.update(
                doc.id, {"status": "archived", "archived_at": datetime.utcnow()}
            )
            archived_count += 1

        return archived_count

    async def cleanup_deleted_sessions(self, deleted_before: datetime) -> int:
        """Permanently remove sessions marked as deleted.

        Args:
            deleted_before: Remove sessions deleted before this date

        Returns:
            int: Number of sessions permanently removed
        """
        query = self.collection.where("status", "==", "deleted").where(
            "updated_at", "<", deleted_before
        )

        docs = list(query.stream())
        doc_ids = [doc.id for doc in docs]

        if doc_ids:
            success = await self.batch_delete(doc_ids)
            return len(doc_ids) if success else 0

        return 0
