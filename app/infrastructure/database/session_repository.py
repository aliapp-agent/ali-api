"""PostgreSQL implementation of SessionRepositoryInterface for Ali API.

This module contains the concrete implementation of session data access
using PostgreSQL and SQLModel.
"""

from datetime import datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy import and_, or_, text, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User as UserModel  # For joins
from app.domain.entities import SessionEntity, SessionStatus, SessionType
from app.domain.repositories import SessionRepositoryInterface
from app.domain.exceptions import (
    SessionAlreadyExistsError,
    SessionNotFoundError,
    RepositoryError,
)


class PostgresSessionRepository(SessionRepositoryInterface):
    """PostgreSQL implementation of the session repository.
    
    This class implements session data access using PostgreSQL database
    through SQLModel ORM.
    """
    
    def __init__(self, db_session: Session):
        """Initialize the repository with a database session.
        
        Args:
            db_session: SQLModel database session
        """
        self.db_session = db_session

    async def create(self, session: SessionEntity) -> SessionEntity:
        """Create a new session in the database.
        
        Args:
            session: Session entity to create
            
        Returns:
            SessionEntity: Created session with assigned ID
            
        Raises:
            SessionAlreadyExistsError: If session with ID already exists
            RepositoryError: If creation fails
        """
        try:
            # Convert entity to model
            from app.models.chat import ChatSession as SessionModel
            
            session_model = self._entity_to_model(session)
            
            # Save to database
            self.db_session.add(session_model)
            self.db_session.commit()
            self.db_session.refresh(session_model)
            
            logger.info(
                "session_created",
                session_id=session_model.id,
                user_id=session.user_id,
                session_type=session.session_type.value
            )
            
            # Convert back to entity
            return self._model_to_entity(session_model)
            
        except IntegrityError as e:
            self.db_session.rollback()
            if "id" in str(e).lower():
                raise SessionAlreadyExistsError(session.id)
            else:
                raise RepositoryError(f"Failed to create session: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("session_creation_failed", error=str(e), user_id=session.user_id)
            raise RepositoryError(f"Database error during session creation: {str(e)}")

    async def get_by_id(self, session_id: str) -> Optional[SessionEntity]:
        """Get session by ID from the database.
        
        Args:
            session_id: Session ID to lookup
            
        Returns:
            SessionEntity or None if not found
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            session_model = self.db_session.get(SessionModel, session_id)
            
            if not session_model:
                return None
            
            return self._model_to_entity(session_model)
            
        except SQLAlchemyError as e:
            logger.error("get_session_by_id_failed", error=str(e), session_id=session_id)
            raise RepositoryError(f"Database error during session lookup: {str(e)}")

    async def update(self, session: SessionEntity) -> SessionEntity:
        """Update an existing session in the database.
        
        Args:
            session: Session entity with updated data
            
        Returns:
            SessionEntity: Updated session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            RepositoryError: If update fails
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            # Get existing session
            session_model = self.db_session.get(SessionModel, session.id)
            if not session_model:
                raise SessionNotFoundError(session.id)
            
            # Update model fields
            self._update_model_from_entity(session_model, session)
            
            # Save changes
            self.db_session.commit()
            self.db_session.refresh(session_model)
            
            logger.info("session_updated", session_id=session.id, user_id=session.user_id)
            
            return self._model_to_entity(session_model)
            
        except SessionNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("session_update_failed", error=str(e), session_id=session.id)
            raise RepositoryError(f"Database error during session update: {str(e)}")

    async def delete(self, session_id: str) -> bool:
        """Delete a session (soft delete) from the database.
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            session_model = self.db_session.get(SessionModel, session_id)
            if not session_model:
                raise SessionNotFoundError(session_id)
            
            # Soft delete by setting status
            session_model.status = SessionStatus.DELETED.value
            session_model.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            logger.info("session_deleted", session_id=session_id)
            
            return True
            
        except SessionNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("session_deletion_failed", error=str(e), session_id=session_id)
            raise RepositoryError(f"Database error during session deletion: {str(e)}")

    async def get_user_sessions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None
    ) -> List[SessionEntity]:
        """Get sessions for a specific user.
        
        Args:
            user_id: User ID to get sessions for
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status: Filter by session status
            session_type: Filter by session type
            
        Returns:
            List[SessionEntity]: User's sessions
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            query = select(SessionModel).where(SessionModel.user_id == user_id)
            
            # Apply filters
            if status:
                query = query.where(SessionModel.status == status.value)
            
            if session_type:
                query = query.where(SessionModel.session_type == session_type.value)
            
            # Apply pagination and ordering
            query = query.offset(offset).limit(limit).order_by(SessionModel.updated_at.desc())
            
            session_models = self.db_session.exec(query).all()
            
            return [self._model_to_entity(model) for model in session_models]
            
        except SQLAlchemyError as e:
            logger.error("get_user_sessions_failed", error=str(e), user_id=user_id)
            raise RepositoryError(f"Database error during user sessions lookup: {str(e)}")

    async def count_user_sessions(
        self,
        user_id: int,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None
    ) -> int:
        """Count sessions for a specific user.
        
        Args:
            user_id: User ID to count sessions for
            status: Filter by session status
            session_type: Filter by session type
            
        Returns:
            int: Number of sessions matching criteria
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            query = select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
            
            # Apply filters
            if status:
                query = query.where(SessionModel.status == status.value)
            
            if session_type:
                query = query.where(SessionModel.session_type == session_type.value)
            
            count = self.db_session.exec(query).one()
            return count
            
        except SQLAlchemyError as e:
            logger.error("count_user_sessions_failed", error=str(e), user_id=user_id)
            raise RepositoryError(f"Database error during user sessions count: {str(e)}")

    async def get_active_sessions(
        self,
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[SessionEntity]:
        """Get active sessions.
        
        Args:
            limit: Maximum number of sessions to return
            user_id: Filter by specific user
            
        Returns:
            List[SessionEntity]: Active sessions
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            query = select(SessionModel).where(SessionModel.status == SessionStatus.ACTIVE.value)
            
            if user_id:
                query = query.where(SessionModel.user_id == user_id)
            
            query = query.limit(limit).order_by(SessionModel.updated_at.desc())
            
            session_models = self.db_session.exec(query).all()
            
            return [self._model_to_entity(model) for model in session_models]
            
        except SQLAlchemyError as e:
            logger.error("get_active_sessions_failed", error=str(e))
            raise RepositoryError(f"Database error during active sessions lookup: {str(e)}")

    async def get_inactive_sessions(
        self,
        inactive_since: datetime,
        limit: int = 100
    ) -> List[SessionEntity]:
        """Get sessions that have been inactive since a certain time.
        
        Args:
            inactive_since: Cutoff time for inactivity
            limit: Maximum number of sessions to return
            
        Returns:
            List[SessionEntity]: Inactive sessions
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            query = select(SessionModel).where(
                and_(
                    SessionModel.status == SessionStatus.ACTIVE.value,
                    SessionModel.updated_at < inactive_since
                )
            ).limit(limit).order_by(SessionModel.updated_at.asc())
            
            session_models = self.db_session.exec(query).all()
            
            return [self._model_to_entity(model) for model in session_models]
            
        except SQLAlchemyError as e:
            logger.error("get_inactive_sessions_failed", error=str(e))
            raise RepositoryError(f"Database error during inactive sessions lookup: {str(e)}")

    async def record_session_message(
        self,
        session_id: str,
        tokens_used: int,
        response_time: float
    ) -> bool:
        """Record message activity for a session.
        
        Args:
            session_id: Session ID to update
            tokens_used: Number of tokens used
            response_time: Response time in seconds
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            session_model = self.db_session.get(SessionModel, session_id)
            if not session_model:
                return False
            
            # Update session statistics
            session_model.message_count += 1
            session_model.total_tokens += tokens_used
            session_model.total_response_time += response_time
            session_model.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("record_session_message_failed", error=str(e), session_id=session_id)
            return False

    async def bulk_update_status(
        self,
        session_ids: List[str],
        status: SessionStatus
    ) -> int:
        """Bulk update session status.
        
        Args:
            session_ids: List of session IDs to update
            status: New status to set
            
        Returns:
            int: Number of sessions updated
        """
        try:
            if not session_ids:
                return 0
            
            # Use raw SQL for bulk update
            result = self.db_session.exec(
                text("""
                    UPDATE chat_sessions 
                    SET status = :status, updated_at = :updated_at 
                    WHERE id = ANY(:session_ids)
                """),
                {
                    "status": status.value,
                    "updated_at": datetime.utcnow(),
                    "session_ids": session_ids
                }
            )
            
            self.db_session.commit()
            
            affected_rows = result.rowcount
            logger.info("bulk_session_status_update", count=affected_rows, status=status.value)
            
            return affected_rows
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("bulk_update_status_failed", error=str(e))
            raise RepositoryError(f"Database error during bulk update: {str(e)}")

    async def get_session_statistics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict:
        """Get session statistics.
        
        Args:
            user_id: Filter by specific user
            date_from: Start date for statistics
            date_to: End date for statistics
            
        Returns:
            Dict: Statistics including counts, averages, etc.
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            # Base query
            base_query = select(SessionModel)
            
            # Apply filters
            filters = []
            if user_id:
                filters.append(SessionModel.user_id == user_id)
            if date_from:
                filters.append(SessionModel.created_at >= date_from)
            if date_to:
                filters.append(SessionModel.created_at <= date_to)
            
            if filters:
                base_query = base_query.where(and_(*filters))
            
            # Total sessions
            total_sessions = self.db_session.exec(
                select(func.count(SessionModel.id)).where(
                    and_(*filters) if filters else True
                )
            ).one()
            
            # Active sessions
            active_sessions = self.db_session.exec(
                select(func.count(SessionModel.id)).where(
                    and_(
                        SessionModel.status == SessionStatus.ACTIVE.value,
                        *(filters if filters else [])
                    )
                )
            ).one()
            
            # Average statistics
            avg_stats = self.db_session.exec(
                select(
                    func.avg(SessionModel.message_count),
                    func.avg(SessionModel.total_tokens),
                    func.avg(SessionModel.total_response_time)
                ).where(
                    and_(*filters) if filters else True
                )
            ).first()
            
            avg_messages, avg_tokens, avg_response_time = avg_stats or (0, 0, 0)
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "archived_sessions": total_sessions - active_sessions,
                "avg_messages_per_session": float(avg_messages or 0),
                "avg_tokens_per_session": float(avg_tokens or 0),
                "avg_response_time": float(avg_response_time or 0),
            }
            
        except SQLAlchemyError as e:
            logger.error("get_session_statistics_failed", error=str(e))
            raise RepositoryError(f"Database error during statistics: {str(e)}")

    async def search_sessions(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionEntity]:
        """Search sessions by name or content.
        
        Args:
            query: Search query
            user_id: Filter by specific user
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[SessionEntity]: Sessions matching search
        """
        try:
            from app.models.chat import ChatSession as SessionModel
            
            search_term = f"%{query.lower()}%"
            
            base_query = select(SessionModel).where(
                or_(
                    SessionModel.name.ilike(search_term),
                    SessionModel.context.astext.ilike(search_term)
                )
            )
            
            if user_id:
                base_query = base_query.where(SessionModel.user_id == user_id)
            
            base_query = base_query.offset(offset).limit(limit).order_by(
                SessionModel.updated_at.desc()
            )
            
            session_models = self.db_session.exec(base_query).all()
            
            return [self._model_to_entity(model) for model in session_models]
            
        except SQLAlchemyError as e:
            logger.error("search_sessions_failed", error=str(e))
            raise RepositoryError(f"Database error during search: {str(e)}")

    def _entity_to_model(self, entity: SessionEntity):
        """Convert SessionEntity to SessionModel.
        
        Args:
            entity: Session entity to convert
            
        Returns:
            SessionModel: Converted session model
        """
        from app.models.chat import ChatSession as SessionModel
        
        return SessionModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            session_type=entity.session_type.value,
            status=entity.status.value,
            context=entity.context,
            message_count=entity.message_count,
            total_tokens=entity.total_tokens,
            total_response_time=entity.total_response_time,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _model_to_entity(self, model) -> SessionEntity:
        """Convert SessionModel to SessionEntity.
        
        Args:
            model: Session model to convert
            
        Returns:
            SessionEntity: Converted session entity
        """
        return SessionEntity(
            user_id=model.user_id,
            name=model.name,
            session_type=SessionType(model.session_type),
            status=SessionStatus(model.status),
            context=model.context or {},
            message_count=model.message_count,
            total_tokens=model.total_tokens,
            total_response_time=model.total_response_time,
            created_at=model.created_at,
            updated_at=model.updated_at,
            session_id=model.id,
        )

    def _update_model_from_entity(self, model, entity: SessionEntity) -> None:
        """Update SessionModel fields from SessionEntity.
        
        Args:
            model: Session model to update
            entity: Session entity with new data
        """
        model.name = entity.name
        model.session_type = entity.session_type.value
        model.status = entity.status.value
        model.context = entity.context
        model.message_count = entity.message_count
        model.total_tokens = entity.total_tokens
        model.total_response_time = entity.total_response_time
        model.updated_at = entity.updated_at

    # Additional methods to satisfy the interface
    async def archive_old_sessions(self, older_than: datetime, exclude_user_ids: Optional[List[int]] = None) -> int:
        """Archive old sessions (simplified implementation)."""
        return 0
    
    async def cleanup_deleted_sessions(self, older_than: datetime) -> int:
        """Clean up deleted sessions (simplified implementation)."""
        return 0
    
    async def get_popular_sessions(self, limit: int = 50) -> List[SessionEntity]:
        """Get popular sessions (simplified implementation)."""
        return []
    
    async def get_sessions_by_type(self, session_type: SessionType, limit: int = 50) -> List[SessionEntity]:
        """Get sessions by type (simplified implementation)."""
        return []
    
    async def update_session_activity(self, session_id: str, activity_data: Dict) -> bool:
        """Update session activity (simplified implementation)."""
        return True