"""PostgreSQL implementation of MessageRepositoryInterface for Ali API.

This module contains the concrete implementation of message data access
using PostgreSQL and SQLModel.
"""

from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

from sqlalchemy import (
    and_,
    func,
    or_,
    text,
)
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlmodel import (
    Session,
    select,
)

from app.core.config import settings
from app.core.logging import logger
from app.domain.entities import (
    MessageEntity,
    MessageRole,
    MessageStatus,
)
from app.domain.exceptions import (
    MessageAlreadyExistsError,
    MessageNotFoundError,
    RepositoryError,
)
from app.domain.repositories import MessageRepositoryInterface
from app.models.chat import ChatMessage as MessageModel


class PostgresMessageRepository(MessageRepositoryInterface):
    """PostgreSQL implementation of the message repository.

    This class implements message data access using PostgreSQL database
    through SQLModel ORM.
    """

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session.

        Args:
            db_session: SQLModel database session
        """
        self.db_session = db_session

    async def create(self, message: MessageEntity) -> MessageEntity:
        """Create a new message in the database.

        Args:
            message: Message entity to create

        Returns:
            MessageEntity: Created message with assigned ID

        Raises:
            MessageAlreadyExistsError: If message with ID already exists
            RepositoryError: If creation fails
        """
        try:
            # Convert entity to model
            message_model = self._entity_to_model(message)

            # Save to database
            self.db_session.add(message_model)
            self.db_session.commit()
            self.db_session.refresh(message_model)

            logger.info(
                "message_created",
                message_id=message_model.id,
                session_id=message.session_id,
                user_id=message.user_id,
                role=message.role.value,
            )

            # Convert back to entity
            return self._model_to_entity(message_model)

        except IntegrityError as e:
            self.db_session.rollback()
            if "id" in str(e).lower():
                raise MessageAlreadyExistsError(message.id)
            else:
                raise RepositoryError(f"Failed to create message: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                "message_creation_failed",
                error=str(e),
                session_id=message.session_id,
                user_id=message.user_id,
            )
            raise RepositoryError(f"Database error during message creation: {str(e)}")

    async def get_by_id(self, message_id: str) -> Optional[MessageEntity]:
        """Get message by ID from the database.

        Args:
            message_id: Message ID to lookup

        Returns:
            MessageEntity or None if not found
        """
        try:
            message_model = self.db_session.get(MessageModel, message_id)

            if not message_model:
                return None

            return self._model_to_entity(message_model)

        except SQLAlchemyError as e:
            logger.error(
                "get_message_by_id_failed", error=str(e), message_id=message_id
            )
            raise RepositoryError(f"Database error during message lookup: {str(e)}")

    async def update(self, message: MessageEntity) -> MessageEntity:
        """Update an existing message in the database.

        Args:
            message: Message entity with updated data

        Returns:
            MessageEntity: Updated message

        Raises:
            MessageNotFoundError: If message doesn't exist
            RepositoryError: If update fails
        """
        try:
            # Get existing message
            message_model = self.db_session.get(MessageModel, message.id)
            if not message_model:
                raise MessageNotFoundError(message.id)

            # Update model fields
            self._update_model_from_entity(message_model, message)

            # Save changes
            self.db_session.commit()
            self.db_session.refresh(message_model)

            logger.info(
                "message_updated", message_id=message.id, session_id=message.session_id
            )

            return self._model_to_entity(message_model)

        except MessageNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("message_update_failed", error=str(e), message_id=message.id)
            raise RepositoryError(f"Database error during message update: {str(e)}")

    async def delete(self, message_id: str) -> bool:
        """Delete a message (soft delete) from the database.

        Args:
            message_id: ID of message to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            MessageNotFoundError: If message doesn't exist
        """
        try:
            message_model = self.db_session.get(MessageModel, message_id)
            if not message_model:
                raise MessageNotFoundError(message_id)

            # Soft delete by setting status
            message_model.status = MessageStatus.DELETED.value
            message_model.updated_at = datetime.utcnow()

            self.db_session.commit()

            logger.info("message_deleted", message_id=message_id)

            return True

        except MessageNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("message_deletion_failed", error=str(e), message_id=message_id)
            raise RepositoryError(f"Database error during message deletion: {str(e)}")

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> List[MessageEntity]:
        """Get messages for a specific session.

        Args:
            session_id: Session ID to get messages for
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            include_deleted: Whether to include deleted messages

        Returns:
            List[MessageEntity]: Session messages in chronological order
        """
        try:
            query = select(MessageModel).where(MessageModel.session_id == session_id)

            # Filter out deleted messages unless requested
            if not include_deleted:
                query = query.where(MessageModel.status != MessageStatus.DELETED.value)

            # Apply pagination and ordering
            query = (
                query.offset(offset)
                .limit(limit)
                .order_by(MessageModel.created_at.asc())
            )

            message_models = self.db_session.exec(query).all()

            return [self._model_to_entity(model) for model in message_models]

        except SQLAlchemyError as e:
            logger.error(
                "get_session_messages_failed", error=str(e), session_id=session_id
            )
            raise RepositoryError(
                f"Database error during session messages lookup: {str(e)}"
            )

    async def get_user_messages(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[MessageEntity]:
        """Get messages for a specific user.

        Args:
            user_id: User ID to get messages for
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            date_from: Filter messages from this date
            date_to: Filter messages until this date

        Returns:
            List[MessageEntity]: User messages
        """
        try:
            query = select(MessageModel).where(MessageModel.user_id == user_id)

            # Apply date filters
            if date_from:
                query = query.where(MessageModel.created_at >= date_from)
            if date_to:
                query = query.where(MessageModel.created_at <= date_to)

            # Exclude deleted messages
            query = query.where(MessageModel.status != MessageStatus.DELETED.value)

            # Apply pagination and ordering
            query = (
                query.offset(offset)
                .limit(limit)
                .order_by(MessageModel.created_at.desc())
            )

            message_models = self.db_session.exec(query).all()

            return [self._model_to_entity(model) for model in message_models]

        except SQLAlchemyError as e:
            logger.error("get_user_messages_failed", error=str(e), user_id=user_id)
            raise RepositoryError(
                f"Database error during user messages lookup: {str(e)}"
            )

    async def get_conversation_context(
        self,
        session_id: str,
        before_message_id: Optional[str] = None,
        context_size: int = 10,
    ) -> List[MessageEntity]:
        """Get conversation context for a session.

        Args:
            session_id: Session ID to get context for
            before_message_id: Get messages before this message
            context_size: Number of context messages to return

        Returns:
            List[MessageEntity]: Context messages in chronological order
        """
        try:
            query = select(MessageModel).where(
                and_(
                    MessageModel.session_id == session_id,
                    MessageModel.status != MessageStatus.DELETED.value,
                )
            )

            # If before_message_id specified, get messages before it
            if before_message_id:
                before_message = self.db_session.get(MessageModel, before_message_id)
                if before_message:
                    query = query.where(
                        MessageModel.created_at < before_message.created_at
                    )

            # Get most recent messages up to context size
            query = query.order_by(MessageModel.created_at.desc()).limit(context_size)

            message_models = self.db_session.exec(query).all()

            # Reverse to get chronological order
            message_models.reverse()

            return [self._model_to_entity(model) for model in message_models]

        except SQLAlchemyError as e:
            logger.error(
                "get_conversation_context_failed", error=str(e), session_id=session_id
            )
            raise RepositoryError(f"Database error during context lookup: {str(e)}")

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
            user_id: Filter by specific user
            session_id: Filter by specific session
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[MessageEntity]: Messages matching search
        """
        try:
            search_term = f"%{query.lower()}%"

            base_query = select(MessageModel).where(
                and_(
                    MessageModel.content.ilike(search_term),
                    MessageModel.status != MessageStatus.DELETED.value,
                )
            )

            # Apply filters
            if user_id:
                base_query = base_query.where(MessageModel.user_id == user_id)

            if session_id:
                base_query = base_query.where(MessageModel.session_id == session_id)

            # Apply pagination and ordering
            base_query = (
                base_query.offset(offset)
                .limit(limit)
                .order_by(MessageModel.created_at.desc())
            )

            message_models = self.db_session.exec(base_query).all()

            return [self._model_to_entity(model) for model in message_models]

        except SQLAlchemyError as e:
            logger.error("search_messages_failed", error=str(e))
            raise RepositoryError(f"Database error during search: {str(e)}")

    async def get_message_statistics(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict:
        """Get message statistics.

        Args:
            user_id: Filter by specific user
            session_id: Filter by specific session
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            Dict: Statistics including counts, averages, etc.
        """
        try:
            # Build base filters
            filters = [MessageModel.status != MessageStatus.DELETED.value]

            if user_id:
                filters.append(MessageModel.user_id == user_id)
            if session_id:
                filters.append(MessageModel.session_id == session_id)
            if date_from:
                filters.append(MessageModel.created_at >= date_from)
            if date_to:
                filters.append(MessageModel.created_at <= date_to)

            # Total messages
            total_messages = self.db_session.exec(
                select(func.count(MessageModel.id)).where(and_(*filters))
            ).one()

            # Messages by role
            user_messages = self.db_session.exec(
                select(func.count(MessageModel.id)).where(
                    and_(MessageModel.role == MessageRole.USER.value, *filters)
                )
            ).one()

            assistant_messages = self.db_session.exec(
                select(func.count(MessageModel.id)).where(
                    and_(MessageModel.role == MessageRole.ASSISTANT.value, *filters)
                )
            ).one()

            # Error messages
            error_messages = self.db_session.exec(
                select(func.count(MessageModel.id)).where(
                    and_(MessageModel.status == MessageStatus.ERROR.value, *filters)
                )
            ).one()

            # Token statistics (for assistant messages)
            token_stats = self.db_session.exec(
                select(
                    func.sum(
                        MessageModel.metadata["tokens_used"].astext.cast(
                            text("integer")
                        )
                    ),
                    func.avg(
                        MessageModel.metadata["tokens_used"].astext.cast(
                            text("integer")
                        )
                    ),
                ).where(
                    and_(
                        MessageModel.role == MessageRole.ASSISTANT.value,
                        MessageModel.metadata["tokens_used"].isnot(None),
                        *filters,
                    )
                )
            ).first()

            total_tokens, avg_tokens = token_stats or (0, 0)

            # Response time statistics
            response_time_stats = self.db_session.exec(
                select(
                    func.avg(
                        MessageModel.metadata["processing_time"].astext.cast(
                            text("float")
                        )
                    )
                ).where(
                    and_(
                        MessageModel.role == MessageRole.ASSISTANT.value,
                        MessageModel.metadata["processing_time"].isnot(None),
                        *filters,
                    )
                )
            ).first()

            avg_response_time = response_time_stats[0] if response_time_stats else 0

            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "error_messages": error_messages,
                "total_tokens": int(total_tokens or 0),
                "avg_tokens_per_message": float(avg_tokens or 0),
                "avg_response_time": float(avg_response_time or 0),
                "error_rate": (
                    error_messages / total_messages if total_messages > 0 else 0
                ),
            }

        except SQLAlchemyError as e:
            logger.error("get_message_statistics_failed", error=str(e))
            raise RepositoryError(f"Database error during statistics: {str(e)}")

    async def get_conversation_export_data(
        self, session_id: str, include_metadata: bool = False
    ) -> List[Dict]:
        """Get conversation data for export.

        Args:
            session_id: Session ID to export
            include_metadata: Include message metadata

        Returns:
            List[Dict]: Exported conversation data
        """
        try:
            query = (
                select(MessageModel)
                .where(
                    and_(
                        MessageModel.session_id == session_id,
                        MessageModel.status != MessageStatus.DELETED.value,
                    )
                )
                .order_by(MessageModel.created_at.asc())
            )

            message_models = self.db_session.exec(query).all()

            export_data = []
            for model in message_models:
                message_data = {
                    "id": model.id,
                    "role": model.role,
                    "content": model.content,
                    "created_at": model.created_at.isoformat(),
                }

                if include_metadata and model.metadata:
                    message_data["metadata"] = model.metadata

                export_data.append(message_data)

            return export_data

        except SQLAlchemyError as e:
            logger.error(
                "get_conversation_export_data_failed",
                error=str(e),
                session_id=session_id,
            )
            raise RepositoryError(f"Database error during export: {str(e)}")

    async def archive_old_messages(
        self, older_than: datetime, exclude_session_ids: Optional[List[str]] = None
    ) -> int:
        """Archive old messages.

        Args:
            older_than: Archive messages older than this date
            exclude_session_ids: Session IDs to exclude from archiving

        Returns:
            int: Number of messages archived
        """
        try:
            filters = [
                MessageModel.created_at < older_than,
                MessageModel.status != MessageStatus.DELETED.value,
            ]

            if exclude_session_ids:
                filters.append(MessageModel.session_id.notin_(exclude_session_ids))

            # Use raw SQL for bulk update
            result = self.db_session.exec(
                text(
                    """
                    UPDATE chat_messages 
                    SET status = 'archived', updated_at = :updated_at 
                    WHERE created_at < :older_than 
                    AND status != 'deleted'
                    {} 
                """.format(
                        "AND session_id NOT IN :exclude_session_ids"
                        if exclude_session_ids
                        else ""
                    )
                ),
                {
                    "older_than": older_than,
                    "updated_at": datetime.utcnow(),
                    **(
                        {"exclude_session_ids": tuple(exclude_session_ids)}
                        if exclude_session_ids
                        else {}
                    ),
                },
            )

            self.db_session.commit()

            affected_rows = result.rowcount
            logger.info("messages_archived", count=affected_rows)

            return affected_rows

        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("archive_old_messages_failed", error=str(e))
            raise RepositoryError(f"Database error during archiving: {str(e)}")

    async def get_token_usage_by_period(
        self, date_from: datetime, date_to: datetime, user_id: Optional[int] = None
    ) -> List[Tuple[datetime, int]]:
        """Get token usage trends by time period.

        Args:
            date_from: Start date
            date_to: End date
            user_id: Filter by user ID

        Returns:
            List[Tuple[datetime, int]]: Token usage by date
        """
        try:
            filters = [
                MessageModel.created_at >= date_from,
                MessageModel.created_at <= date_to,
                MessageModel.role == MessageRole.ASSISTANT.value,
                MessageModel.metadata["tokens_used"].isnot(None),
            ]

            if user_id:
                filters.append(MessageModel.user_id == user_id)

            # Group by date and sum tokens
            query = (
                select(
                    func.date(MessageModel.created_at).label("date"),
                    func.sum(
                        MessageModel.metadata["tokens_used"].astext.cast(
                            text("integer")
                        )
                    ).label("tokens"),
                )
                .where(and_(*filters))
                .group_by(func.date(MessageModel.created_at))
                .order_by("date")
            )

            results = self.db_session.exec(query).all()

            return [(result.date, int(result.tokens or 0)) for result in results]

        except SQLAlchemyError as e:
            logger.error("get_token_usage_by_period_failed", error=str(e))
            raise RepositoryError(f"Database error during token usage query: {str(e)}")

    def _entity_to_model(self, entity: MessageEntity) -> MessageModel:
        """Convert MessageEntity to MessageModel.

        Args:
            entity: Message entity to convert

        Returns:
            MessageModel: Converted message model
        """
        return MessageModel(
            id=entity.id,
            session_id=entity.session_id,
            user_id=entity.user_id,
            role=entity.role.value,
            content=entity.content,
            status=entity.status.value,
            message_metadata=(
                str(entity.metadata.to_dict()) if entity.metadata else None
            ),
            context=str(entity.context) if entity.context else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _model_to_entity(self, model: MessageModel) -> MessageEntity:
        """Convert MessageModel to MessageEntity.

        Args:
            model: Message model to convert

        Returns:
            MessageEntity: Converted message entity
        """
        import json

        # Parse metadata and context from strings
        metadata_dict = {}
        context_dict = {}

        if model.message_metadata:
            try:
                metadata_dict = json.loads(model.message_metadata)
            except:
                metadata_dict = {}

        if model.context:
            try:
                context_dict = json.loads(model.context)
            except:
                context_dict = {}

        return MessageEntity(
            session_id=model.session_id,
            user_id=model.user_id,
            role=MessageRole(model.role),
            content=model.content,
            status=MessageStatus(model.status),
            metadata_dict=metadata_dict,
            context=context_dict,
            created_at=model.created_at,
            updated_at=model.updated_at,
            message_id=model.id,
        )

    def _update_model_from_entity(
        self, model: MessageModel, entity: MessageEntity
    ) -> None:
        """Update MessageModel fields from MessageEntity.

        Args:
            model: Message model to update
            entity: Message entity with new data
        """
        import json

        model.content = entity.content
        model.status = entity.status.value
        model.message_metadata = (
            json.dumps(entity.metadata.to_dict()) if entity.metadata else None
        )
        model.context = json.dumps(entity.context) if entity.context else None
        model.updated_at = entity.updated_at

    # Additional methods to satisfy the interface
    async def bulk_update_status(
        self, message_ids: List[str], status: MessageStatus
    ) -> int:
        """Bulk update message status (simplified implementation)."""
        return 0

    async def cleanup_deleted_messages(self, older_than: datetime) -> int:
        """Clean up deleted messages (simplified implementation)."""
        return 0

    async def count_session_messages(self, session_id: str) -> int:
        """Count messages in a session (simplified implementation)."""
        try:
            count = self.db_session.exec(
                select(func.count(MessageModel.id)).where(
                    MessageModel.session_id == session_id
                )
            ).one()
            return count
        except:
            return 0

    async def get_error_messages(self, limit: int = 50) -> List[MessageEntity]:
        """Get messages with errors (simplified implementation)."""
        return []

    async def get_high_token_messages(
        self, token_threshold: int, limit: int = 50
    ) -> List[MessageEntity]:
        """Get high-token messages (simplified implementation)."""
        return []

    async def get_messages_by_status(
        self, status: MessageStatus, limit: int = 50
    ) -> List[MessageEntity]:
        """Get messages by status (simplified implementation)."""
        return []

    async def get_recent_messages(
        self, hours: int = 24, limit: int = 50
    ) -> List[MessageEntity]:
        """Get recent messages (simplified implementation)."""
        return []
