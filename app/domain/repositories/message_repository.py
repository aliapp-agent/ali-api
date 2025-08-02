"""Message repository interface for Ali API.

This module defines the contract for message data access operations
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
    MessageEntity,
    MessageRole,
    MessageStatus,
)


class MessageRepositoryInterface(ABC):
    """Abstract repository interface for Message operations.

    This interface defines all the operations that can be performed
    on message data without coupling to any specific database implementation.
    """

    @abstractmethod
    async def create(self, message: MessageEntity) -> MessageEntity:
        """Create a new message.

        Args:
            message: Message entity to create

        Returns:
            MessageEntity: Created message with assigned ID

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, message_id: str) -> Optional[MessageEntity]:
        """Get message by ID.

        Args:
            message_id: Message ID to lookup

        Returns:
            MessageEntity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, message: MessageEntity) -> MessageEntity:
        """Update an existing message.

        Args:
            message: Message entity with updated data

        Returns:
            MessageEntity: Updated message

        Raises:
            MessageNotFoundError: If message doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, message_id: str) -> bool:
        """Delete a message (soft delete).

        Args:
            message_id: ID of message to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            MessageNotFoundError: If message doesn't exist
        """
        pass

    @abstractmethod
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
        role: Optional[MessageRole] = None,
        status: Optional[MessageStatus] = None,
        order_desc: bool = False,
    ) -> List[MessageEntity]:
        """Get messages for a specific session.

        Args:
            session_id: Session ID to get messages for
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            role: Filter by message role
            status: Filter by message status
            order_desc: Order by creation time descending

        Returns:
            List[MessageEntity]: List of session messages
        """
        pass

    @abstractmethod
    async def count_session_messages(
        self,
        session_id: str,
        role: Optional[MessageRole] = None,
        status: Optional[MessageStatus] = None,
    ) -> int:
        """Count messages for a specific session.

        Args:
            session_id: Session ID to count messages for
            role: Filter by message role
            status: Filter by message status

        Returns:
            int: Number of messages matching criteria
        """
        pass

    @abstractmethod
    async def get_user_messages(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[MessageEntity]:
        """Get messages for a specific user across all sessions.

        Args:
            user_id: User ID to get messages for
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            date_from: Start date filter
            date_to: End date filter

        Returns:
            List[MessageEntity]: List of user messages
        """
        pass

    @abstractmethod
    async def get_recent_messages(
        self,
        limit: int = 50,
        role: Optional[MessageRole] = None,
        user_id: Optional[int] = None,
    ) -> List[MessageEntity]:
        """Get recent messages across all sessions.

        Args:
            limit: Maximum number of messages to return
            role: Filter by message role
            user_id: Filter by specific user

        Returns:
            List[MessageEntity]: List of recent messages
        """
        pass

    @abstractmethod
    async def get_messages_by_status(
        self,
        status: MessageStatus,
        limit: int = 100,
        created_before: Optional[datetime] = None,
    ) -> List[MessageEntity]:
        """Get messages by status.

        Args:
            status: Message status to filter by
            limit: Maximum number of messages to return
            created_before: Only return messages created before this time

        Returns:
            List[MessageEntity]: List of messages with specified status
        """
        pass

    @abstractmethod
    async def search_messages(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MessageEntity]:
        """Search messages by content.

        Args:
            query: Search query
            user_id: Filter by specific user (optional)
            session_id: Filter by specific session (optional)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[MessageEntity]: List of messages matching search
        """
        pass

    @abstractmethod
    async def get_conversation_context(
        self,
        session_id: str,
        before_message_id: Optional[str] = None,
        context_size: int = 10,
    ) -> List[MessageEntity]:
        """Get conversation context for a session.

        Args:
            session_id: Session ID to get context for
            before_message_id: Get messages before this message ID
            context_size: Number of messages to include in context

        Returns:
            List[MessageEntity]: List of context messages
        """
        pass

    @abstractmethod
    async def get_message_statistics(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get message statistics.

        Args:
            user_id: Filter by specific user (optional)
            session_id: Filter by specific session (optional)
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            dict: Statistics including message counts, tokens, etc.
        """
        pass

    @abstractmethod
    async def get_error_messages(
        self, limit: int = 50, retry_count_threshold: int = 0
    ) -> List[MessageEntity]:
        """Get messages with errors.

        Args:
            limit: Maximum number of messages to return
            retry_count_threshold: Minimum retry count to include

        Returns:
            List[MessageEntity]: List of error messages
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self, message_ids: List[str], status: MessageStatus
    ) -> int:
        """Bulk update message status.

        Args:
            message_ids: List of message IDs to update
            status: New status to set

        Returns:
            int: Number of messages updated
        """
        pass

    @abstractmethod
    async def get_token_usage_by_period(
        self, date_from: datetime, date_to: datetime, user_id: Optional[int] = None
    ) -> List[Tuple[datetime, int]]:
        """Get token usage aggregated by time period.

        Args:
            date_from: Start date
            date_to: End date
            user_id: Filter by specific user (optional)

        Returns:
            List[Tuple[datetime, int]]: List of (date, token_count) tuples
        """
        pass

    @abstractmethod
    async def archive_old_messages(
        self, older_than: datetime, exclude_session_ids: Optional[List[str]] = None
    ) -> int:
        """Archive messages older than specified date.

        Args:
            older_than: Cutoff date for archiving
            exclude_session_ids: Session IDs to exclude from archiving

        Returns:
            int: Number of messages archived
        """
        pass

    @abstractmethod
    async def cleanup_deleted_messages(self, deleted_before: datetime) -> int:
        """Permanently remove messages marked as deleted.

        Args:
            deleted_before: Remove messages deleted before this date

        Returns:
            int: Number of messages permanently removed
        """
        pass

    @abstractmethod
    async def get_high_token_messages(
        self, token_threshold: int = 1000, limit: int = 50
    ) -> List[MessageEntity]:
        """Get messages with high token usage.

        Args:
            token_threshold: Minimum token count
            limit: Maximum number of messages to return

        Returns:
            List[MessageEntity]: List of high-token messages
        """
        pass

    @abstractmethod
    async def get_conversation_export_data(
        self, session_id: str, include_metadata: bool = False
    ) -> List[dict]:
        """Get conversation data formatted for export.

        Args:
            session_id: Session ID to export
            include_metadata: Include message metadata

        Returns:
            List[dict]: List of message data for export
        """
        pass
