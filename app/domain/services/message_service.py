"""Message domain service for Ali API.

This module contains business logic for message operations that involve
complex rules or multiple entities.
"""

import uuid
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

from app.domain.entities import (
    MessageEntity,
    MessageRole,
    MessageStatus,
    SessionEntity,
    UserEntity,
)
from app.domain.exceptions import (
    BusinessRuleViolationError,
    MessageEditNotAllowedError,
    MessageNotFoundError,
    MessageProcessingError,
    QuotaExceededError,
    RateLimitExceededError,
    SessionAccessDeniedError,
    SessionNotFoundError,
    UserNotFoundError,
)
from app.domain.repositories import (
    MessageRepositoryInterface,
    SessionRepositoryInterface,
    UserRepositoryInterface,
)


class MessageDomainService:
    """Domain service for message-related business logic.

    This service encapsulates complex message operations that involve
    business rules, validations, and coordination between entities.
    """

    def __init__(
        self,
        message_repository: MessageRepositoryInterface,
        session_repository: SessionRepositoryInterface,
        user_repository: UserRepositoryInterface,
    ):
        """Initialize the message domain service.

        Args:
            message_repository: Repository for message data access
            session_repository: Repository for session data access
            user_repository: Repository for user data access
        """
        self.message_repository = message_repository
        self.session_repository = session_repository
        self.user_repository = user_repository

    async def create_user_message(
        self,
        session_id: str,
        user_id: int,
        content: str,
        context: Optional[Dict] = None,
    ) -> MessageEntity:
        """Create a new user message with validation.

        Args:
            session_id: ID of session to add message to
            user_id: ID of user sending the message
            content: Message content
            context: Optional message context

        Returns:
            MessageEntity: Created message

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
            UserNotFoundError: If user doesn't exist
            BusinessRuleViolationError: If business rules are violated
            RateLimitExceededError: If rate limits exceeded
        """
        # Validate session access
        session = await self._validate_session_access(session_id, user_id)

        # Validate user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Check rate limits
        await self._check_rate_limits(user_id, "message_creation")

        # Check message quotas
        await self._check_message_quotas(user_id, user.role.value)

        # Create message entity
        message = MessageEntity(
            session_id=session_id,
            user_id=user_id,
            role=MessageRole.USER,
            content=content,
            status=MessageStatus.COMPLETED,
        )

        # Set context if provided
        if context:
            message.update_context(context)

        # Save message
        created_message = await self.message_repository.create(message)

        # Update session activity
        await self.session_repository.record_session_message(
            session_id=session_id,
            tokens_used=0,  # User messages don't consume tokens
            response_time=0.0,
        )

        return created_message

    async def create_assistant_message(
        self,
        session_id: str,
        user_id: int,
        content: str,
        model_used: str,
        tokens_used: int,
        processing_time: float,
        confidence_score: Optional[float] = None,
        context_documents: Optional[List[str]] = None,
    ) -> MessageEntity:
        """Create a new assistant message with metadata.

        Args:
            session_id: ID of session to add message to
            user_id: ID of user who triggered this response
            content: Message content
            model_used: AI model that generated the response
            tokens_used: Number of tokens consumed
            processing_time: Time taken to generate response
            confidence_score: AI confidence score
            context_documents: Related document IDs

        Returns:
            MessageEntity: Created message

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
        """
        # Validate session access
        await self._validate_session_access(session_id, user_id)

        # Create assistant message
        message = MessageEntity(
            session_id=session_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=content,
            status=MessageStatus.COMPLETED,
        )

        # Set metadata
        metadata_update = {
            "model_used": model_used,
            "tokens_used": tokens_used,
            "processing_time": processing_time,
        }

        if confidence_score is not None:
            metadata_update["confidence_score"] = confidence_score

        if context_documents:
            metadata_update["context_documents"] = context_documents

        message.update_metadata(metadata_update)

        # Save message
        created_message = await self.message_repository.create(message)

        # Update session activity
        await self.session_repository.record_session_message(
            session_id=session_id,
            tokens_used=tokens_used,
            response_time=processing_time,
        )

        return created_message

    async def edit_user_message(
        self, message_id: str, user_id: int, new_content: str
    ) -> MessageEntity:
        """Edit a user message if allowed.

        Args:
            message_id: ID of message to edit
            user_id: ID of user attempting to edit
            new_content: New message content

        Returns:
            MessageEntity: Updated message

        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageEditNotAllowedError: If message cannot be edited
            SessionAccessDeniedError: If user cannot access session
        """
        # Get message
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(message_id)

        # Validate session access
        await self._validate_session_access(message.session_id, user_id)

        # Check if message can be edited
        if not message.can_be_edited():
            raise MessageEditNotAllowedError(
                message_id,
                f"Message status: {message.status.value}, role: {message.role.value}",
            )

        # Check if user owns the message
        if not message.belongs_to_user(user_id):
            raise MessageEditNotAllowedError(message_id, "Only message owner can edit")

        # Update content
        message.update_content(new_content)

        # Save message
        updated_message = await self.message_repository.update(message)

        return updated_message

    async def delete_message(
        self, message_id: str, user_id: int, force_delete: bool = False
    ) -> bool:
        """Delete a message if allowed.

        Args:
            message_id: ID of message to delete
            user_id: ID of user attempting to delete
            force_delete: Whether to force delete (admin only)

        Returns:
            bool: True if message was deleted

        Raises:
            MessageNotFoundError: If message doesn't exist
            SessionAccessDeniedError: If user cannot access session
            BusinessRuleViolationError: If deletion not allowed
        """
        # Get message
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(message_id)

        # Validate session access
        await self._validate_session_access(message.session_id, user_id)

        # Get user to check permissions
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Check deletion permissions
        can_delete = (
            message.belongs_to_user(user_id)
            or user.role.value == "admin"
            or force_delete
        )

        if not can_delete:
            raise BusinessRuleViolationError(
                "Insufficient permissions to delete message"
            )

        # Soft delete message
        message.mark_deleted()
        await self.message_repository.update(message)

        return True

    async def get_conversation_context(
        self,
        session_id: str,
        user_id: int,
        max_messages: int = 10,
        before_message_id: Optional[str] = None,
    ) -> List[MessageEntity]:
        """Get conversation context for a session.

        Args:
            session_id: Session ID to get context for
            user_id: User ID requesting context
            max_messages: Maximum number of messages to return
            before_message_id: Get messages before this message

        Returns:
            List[MessageEntity]: Context messages

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
        """
        # Validate session access
        await self._validate_session_access(session_id, user_id)

        # Get conversation context
        context_messages = await self.message_repository.get_conversation_context(
            session_id=session_id,
            before_message_id=before_message_id,
            context_size=max_messages,
        )

        return context_messages

    async def search_user_messages(
        self,
        user_id: int,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MessageEntity]:
        """Search messages for a user.

        Args:
            user_id: User ID to search messages for
            query: Search query
            session_id: Optional session ID to limit search
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[MessageEntity]: Messages matching search

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Validate user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # If session specified, validate access
        if session_id:
            await self._validate_session_access(session_id, user_id)

        # Search messages
        messages = await self.message_repository.search_messages(
            query=query,
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

        return messages

    async def get_message_analytics(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict:
        """Get message analytics and statistics.

        Args:
            user_id: Filter by specific user (optional)
            session_id: Filter by specific session (optional)
            date_from: Start date for analytics
            date_to: End date for analytics

        Returns:
            Dict: Analytics data including counts, trends, usage
        """
        # Get basic statistics
        stats = await self.message_repository.get_message_statistics(
            user_id=user_id, session_id=session_id, date_from=date_from, date_to=date_to
        )

        # Add computed analytics
        analytics = {
            **stats,
            "message_health": self._calculate_message_health(stats),
            "token_trends": await self._get_token_usage_trends(
                user_id, date_from, date_to
            ),
            "response_time_analysis": self._analyze_response_times(stats),
        }

        return analytics

    async def retry_failed_message(
        self, message_id: str, user_id: int
    ) -> MessageEntity:
        """Retry processing a failed message.

        Args:
            message_id: ID of message to retry
            user_id: ID of user requesting retry

        Returns:
            MessageEntity: Updated message

        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageProcessingError: If message cannot be retried
            SessionAccessDeniedError: If user cannot access session
        """
        # Get message
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(message_id)

        # Validate session access
        await self._validate_session_access(message.session_id, user_id)

        # Check if message can be retried
        if not message.can_be_retried():
            raise MessageProcessingError(
                message_id,
                f"Message cannot be retried. Status: {message.status.value}, "
                f"retry count: {message.metadata.retry_count}",
            )

        # Reset message status for retry
        message.status = MessageStatus.PENDING
        message.metadata.error_details = None
        message.updated_at = datetime.utcnow()

        # Save message
        updated_message = await self.message_repository.update(message)

        return updated_message

    async def export_conversation(
        self,
        session_id: str,
        user_id: int,
        include_metadata: bool = False,
        format_type: str = "json",
    ) -> List[Dict]:
        """Export conversation data for a session.

        Args:
            session_id: Session ID to export
            user_id: User ID requesting export
            include_metadata: Include message metadata
            format_type: Export format (json, csv, txt)

        Returns:
            List[Dict]: Exported conversation data

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
        """
        # Validate session access
        await self._validate_session_access(session_id, user_id)

        # Get conversation export data
        export_data = await self.message_repository.get_conversation_export_data(
            session_id=session_id, include_metadata=include_metadata
        )

        return export_data

    async def cleanup_old_messages(
        self, days_old: int = 365, exclude_session_ids: Optional[List[str]] = None
    ) -> int:
        """Clean up old messages to save storage.

        Args:
            days_old: Age in days for message cleanup
            exclude_session_ids: Session IDs to exclude from cleanup

        Returns:
            int: Number of messages cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Archive old messages
        count = await self.message_repository.archive_old_messages(
            older_than=cutoff_date, exclude_session_ids=exclude_session_ids
        )

        return count

    async def _validate_session_access(
        self, session_id: str, user_id: int
    ) -> SessionEntity:
        """Validate that user can access the session.

        Args:
            session_id: Session ID to check
            user_id: User ID to validate

        Returns:
            SessionEntity: Session if access is valid

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
            UserNotFoundError: If user doesn't exist
        """
        # Get session
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        # Get user to check role
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Check access permissions
        if not session.can_be_accessed_by(user_id, user.role.value):
            raise SessionAccessDeniedError(session_id, user_id)

        return session

    async def _check_rate_limits(self, user_id: int, operation: str) -> None:
        """Check rate limits for user operations.

        Args:
            user_id: User ID to check limits for
            operation: Operation being performed

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        # This would implement actual rate limiting logic
        # For now, just placeholder validation

        # Get recent messages count for user
        recent_messages = await self.message_repository.get_user_messages(
            user_id=user_id, limit=100, date_from=datetime.utcnow() - timedelta(hours=1)
        )

        # Simple rate limit: max 100 messages per hour
        if len(recent_messages) >= 100:
            raise RateLimitExceededError(
                limit_type="messages_per_hour", limit_value=100, reset_time=3600
            )

    async def _check_message_quotas(self, user_id: int, user_role: str) -> None:
        """Check message quotas for user.

        Args:
            user_id: User ID to check quotas for
            user_role: User role for quota determination

        Raises:
            QuotaExceededError: If quota exceeded
        """
        # Define quotas by role (daily limits)
        quotas = {"admin": 10000, "editor": 1000, "viewer": 100, "guest": 20}

        daily_limit = quotas.get(user_role, 20)

        # Count today's messages
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_messages = await self.message_repository.get_user_messages(
            user_id=user_id, limit=daily_limit + 1, date_from=today_start
        )

        if len(today_messages) >= daily_limit:
            raise QuotaExceededError(
                quota_type="daily_messages", used=len(today_messages), limit=daily_limit
            )

    def _calculate_message_health(self, stats: Dict) -> str:
        """Calculate message processing health.

        Args:
            stats: Message statistics

        Returns:
            str: Health status
        """
        total_messages = stats.get("total_messages", 0)
        error_messages = stats.get("error_messages", 0)

        if total_messages == 0:
            return "healthy"

        error_rate = error_messages / total_messages

        if error_rate < 0.01:  # Less than 1% errors
            return "healthy"
        elif error_rate < 0.05:  # Less than 5% errors
            return "warning"
        else:
            return "critical"

    async def _get_token_usage_trends(
        self,
        user_id: Optional[int],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> List[Tuple[datetime, int]]:
        """Get token usage trends over time.

        Args:
            user_id: Filter by user ID
            date_from: Start date
            date_to: End date

        Returns:
            List[Tuple[datetime, int]]: Token usage by date
        """
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()

        return await self.message_repository.get_token_usage_by_period(
            date_from=date_from, date_to=date_to, user_id=user_id
        )

    def _analyze_response_times(self, stats: Dict) -> Dict:
        """Analyze response time statistics.

        Args:
            stats: Message statistics

        Returns:
            Dict: Response time analysis
        """
        avg_response_time = stats.get("avg_response_time", 0)

        # Categorize response time performance
        if avg_response_time < 2.0:
            performance = "excellent"
        elif avg_response_time < 5.0:
            performance = "good"
        elif avg_response_time < 10.0:
            performance = "acceptable"
        else:
            performance = "poor"

        return {
            "average_seconds": avg_response_time,
            "performance_rating": performance,
            "target_seconds": 3.0,
            "meets_target": avg_response_time < 3.0,
        }
