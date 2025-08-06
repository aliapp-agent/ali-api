"""Message service for integrating domain and infrastructure layers.

This service acts as a bridge between the domain layer (business logic) and 
the infrastructure layer (Firebase repository), providing a clean interface
for message operations in the API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.core.logging import logger
from app.domain.entities.message_entity import MessageEntity, MessageRole, MessageStatus
from app.domain.services.message_service import MessageDomainService
from app.infrastructure.firestore.message_repository import FirestoreMessageRepository
from app.infrastructure.firestore.session_repository import FirestoreSessionRepository
from app.infrastructure.firestore.user_repository import FirestoreUserRepository


class MessageService:
    """Service for message operations integrating domain and infrastructure."""

    def __init__(self):
        """Initialize the message service with repositories and domain service."""
        # Initialize repositories
        self.message_repository = FirestoreMessageRepository()
        self.session_repository = FirestoreSessionRepository()
        self.user_repository = FirestoreUserRepository()
        
        # Initialize domain service
        self.domain_service = MessageDomainService(
            message_repository=self.message_repository,
            session_repository=self.session_repository,
            user_repository=self.user_repository,
        )

    async def create_user_message(
        self,
        session_id: str,
        user_id: int,
        content: str,
        context: Optional[Dict] = None,
    ) -> MessageEntity:
        """Create a new user message.

        Args:
            session_id: ID of the session
            user_id: ID of the user
            content: Message content
            context: Optional context data

        Returns:
            MessageEntity: Created message entity

        Raises:
            Various domain exceptions for validation failures
        """
        try:
            logger.info(
                "creating_user_message",
                session_id=session_id,
                user_id=user_id,
                content_length=len(content),
            )

            message = await self.domain_service.create_user_message(
                session_id=session_id,
                user_id=user_id,
                content=content,
                context=context,
            )

            logger.info(
                "user_message_created",
                message_id=message.id,
                session_id=session_id,
                user_id=user_id,
            )

            return message
        except Exception as e:
            logger.error(
                "create_user_message_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

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
        """Create a new assistant message.

        Args:
            session_id: ID of the session
            user_id: ID of the user who triggered this response
            content: Message content
            model_used: AI model that generated the response
            tokens_used: Number of tokens consumed
            processing_time: Time taken to generate response
            confidence_score: AI confidence score
            context_documents: Related document IDs

        Returns:
            MessageEntity: Created message entity
        """
        try:
            logger.info(
                "creating_assistant_message",
                session_id=session_id,
                user_id=user_id,
                model_used=model_used,
                tokens_used=tokens_used,
                processing_time=processing_time,
            )

            message = await self.domain_service.create_assistant_message(
                session_id=session_id,
                user_id=user_id,
                content=content,
                model_used=model_used,
                tokens_used=tokens_used,
                processing_time=processing_time,
                confidence_score=confidence_score,
                context_documents=context_documents,
            )

            logger.info(
                "assistant_message_created",
                message_id=message.id,
                session_id=session_id,
                tokens_used=tokens_used,
            )

            return message
        except Exception as e:
            logger.error(
                "create_assistant_message_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_session_messages(
        self,
        session_id: str,
        user_id: int,
        limit: int = 50,
        order_by: str = "timestamp",
        direction: str = "asc",
    ) -> List[MessageEntity]:
        """Get messages for a session.

        Args:
            session_id: Session ID
            user_id: User ID for access validation
            limit: Maximum number of messages to return
            order_by: Field to order by
            direction: Sort direction ('asc' or 'desc')

        Returns:
            List[MessageEntity]: List of messages
        """
        try:
            # Validate session access using domain service
            await self.domain_service._validate_session_access(session_id, user_id)

            # Get messages from repository
            messages = await self.message_repository.get_session_messages(
                session_id=session_id,
                limit=limit,
                order_by=order_by,
                direction=direction,
            )

            logger.info(
                "session_messages_retrieved",
                session_id=session_id,
                user_id=user_id,
                message_count=len(messages),
            )

            return messages
        except Exception as e:
            logger.error(
                "get_session_messages_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def clear_session_messages(
        self, session_id: str, user_id: int
    ) -> int:
        """Clear all messages for a session.

        Args:
            session_id: Session ID
            user_id: User ID for access validation

        Returns:
            int: Number of messages cleared
        """
        try:
            # Validate session access
            await self.domain_service._validate_session_access(session_id, user_id)

            # Get current message count for logging
            current_messages = await self.message_repository.get_session_messages(
                session_id=session_id, limit=1000
            )
            message_count = len(current_messages)

            # Delete all messages
            success = await self.message_repository.delete_session_messages(session_id)

            if success:
                logger.info(
                    "session_messages_cleared",
                    session_id=session_id,
                    user_id=user_id,
                    messages_cleared=message_count,
                )
                return message_count
            else:
                logger.error(
                    "clear_session_messages_failed",
                    session_id=session_id,
                    user_id=user_id,
                    error="Failed to delete messages from repository",
                )
                return 0
        except Exception as e:
            logger.error(
                "clear_session_messages_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_conversation_context(
        self,
        session_id: str,
        user_id: int,
        max_messages: int = 10,
    ) -> List[MessageEntity]:
        """Get recent conversation context for a session.

        Args:
            session_id: Session ID
            user_id: User ID for access validation
            max_messages: Maximum number of messages for context

        Returns:
            List[MessageEntity]: Recent messages for context
        """
        try:
            return await self.domain_service.get_conversation_context(
                session_id=session_id,
                user_id=user_id,
                max_messages=max_messages,
            )
        except Exception as e:
            logger.error(
                "get_conversation_context_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def search_messages(
        self,
        session_id: str,
        user_id: int,
        query: str,
        limit: int = 50,
    ) -> List[MessageEntity]:
        """Search messages in a session.

        Args:
            session_id: Session ID
            user_id: User ID for access validation
            query: Search query
            limit: Maximum number of results

        Returns:
            List[MessageEntity]: Search results
        """
        try:
            # Validate session access
            await self.domain_service._validate_session_access(session_id, user_id)

            # Search messages
            results = await self.message_repository.search_messages(
                session_id=session_id, query_text=query, limit=limit
            )

            logger.info(
                "messages_searched",
                session_id=session_id,
                user_id=user_id,
                query=query,
                results_count=len(results),
            )

            return results
        except Exception as e:
            logger.error(
                "search_messages_failed",
                session_id=session_id,
                user_id=user_id,
                query=query,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_message_count(self, session_id: str, user_id: int) -> int:
        """Get total message count for a session.

        Args:
            session_id: Session ID
            user_id: User ID for access validation

        Returns:
            int: Number of messages in the session
        """
        try:
            # Validate session access
            await self.domain_service._validate_session_access(session_id, user_id)

            count = await self.message_repository.get_message_count(session_id)

            logger.info(
                "message_count_retrieved",
                session_id=session_id,
                user_id=user_id,
                count=count,
            )

            return count
        except Exception as e:
            logger.error(
                "get_message_count_failed",
                session_id=session_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def health_check(self) -> Dict:
        """Check the health of the message service.

        Returns:
            Dict: Health status information
        """
        try:
            # Test repository connection
            test_session = "health_check_session"
            messages = await self.message_repository.get_session_messages(
                session_id=test_session, limit=1
            )

            return {
                "status": "healthy",
                "message_repository": "connected",
                "domain_service": "initialized",
                "test_query_successful": True,
            }
        except Exception as e:
            logger.error(
                "message_service_health_check_failed",
                error=str(e),
                exc_info=True,
            )
            return {
                "status": "unhealthy",
                "error": str(e),
                "message_repository": "error",
                "domain_service": "error",
                "test_query_successful": False,
            }

    def to_api_format(self, message: MessageEntity) -> Dict:
        """Convert MessageEntity to API response format.

        Args:
            message: Message entity

        Returns:
            Dict: Message in API format compatible with frontend
        """
        # Handle metadata properly based on whether it's a dataclass or dict
        metadata = message.metadata
        if hasattr(metadata, 'tokens_used'):
            # It's a MessageMetadata dataclass
            tokens = metadata.tokens_used
            processing_time = metadata.processing_time
            model_used = metadata.model_used
            context_documents = metadata.context_documents or []
            confidence_score = metadata.confidence_score
        else:
            # It's a dict or None
            tokens = metadata.get("tokens_used", 0) if metadata else 0
            processing_time = metadata.get("processing_time") if metadata else None
            model_used = metadata.get("model_used") if metadata else None
            context_documents = metadata.get("context_documents", []) if metadata else []
            confidence_score = metadata.get("confidence_score") if metadata else None

        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "session_id": message.session_id,
            "user_id": message.user_id,
            "status": message.status,
            "tokens": tokens,
            "processing_time": processing_time,
            "model_used": model_used,
            "context_documents": context_documents,
            "confidence_score": confidence_score,
        }

    def to_api_format_list(self, messages: List[MessageEntity]) -> List[Dict]:
        """Convert list of MessageEntity to API format.

        Args:
            messages: List of message entities

        Returns:
            List[Dict]: Messages in API format
        """
        return [self.to_api_format(message) for message in messages]


# Global service instance
_message_service: Optional[MessageService] = None


def get_message_service() -> MessageService:
    """Get the global message service instance.

    Returns:
        MessageService: The message service instance
    """
    global _message_service

    if _message_service is None:
        _message_service = MessageService()

    return _message_service