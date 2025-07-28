"""Session domain service for Ali API.

This module contains business logic for session operations that involve
complex rules or multiple entities.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import uuid

from app.domain.entities import SessionEntity, SessionStatus, SessionType, UserEntity
from app.domain.repositories import SessionRepositoryInterface, UserRepositoryInterface
from app.domain.exceptions import (
    SessionNotFoundError,
    SessionAccessDeniedError,
    UserNotFoundError,
    BusinessRuleViolationError,
    InsufficientPermissionsError,
)


class SessionDomainService:
    """Domain service for session-related business logic.
    
    This service encapsulates complex session operations that involve
    business rules, validations, and coordination between entities.
    """
    
    def __init__(
        self,
        session_repository: SessionRepositoryInterface,
        user_repository: UserRepositoryInterface
    ):
        """Initialize the session domain service.
        
        Args:
            session_repository: Repository for session data access
            user_repository: Repository for user data access
        """
        self.session_repository = session_repository
        self.user_repository = user_repository

    async def create_session(
        self,
        user_id: int,
        name: Optional[str] = None,
        session_type: SessionType = SessionType.CHAT,
        initial_context: Optional[Dict] = None
    ) -> SessionEntity:
        """Create a new session with business rule validation.
        
        Args:
            user_id: ID of user creating the session
            name: Optional session name
            session_type: Type of session to create
            initial_context: Optional initial context data
            
        Returns:
            SessionEntity: Newly created session
            
        Raises:
            UserNotFoundError: If user doesn't exist
            BusinessRuleViolationError: If business rules are violated
        """
        # Validate user exists and is active
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        if not user.is_active:
            raise BusinessRuleViolationError(
                "Inactive users cannot create sessions"
            )
        
        # Check session limits for user
        await self._validate_session_limits(user_id, user.role.value)
        
        # Create session entity
        session = SessionEntity(
            user_id=user_id,
            name=name,
            session_type=session_type,
            status=SessionStatus.ACTIVE
        )
        
        # Set initial context if provided
        if initial_context:
            session.update_context({"session_context": initial_context})
        
        # Save session
        created_session = await self.session_repository.create(session)
        
        return created_session

    async def get_user_session(
        self,
        session_id: str,
        user_id: int,
        require_active: bool = True
    ) -> SessionEntity:
        """Get a session ensuring user has access.
        
        Args:
            session_id: ID of session to retrieve
            user_id: ID of user requesting access
            require_active: Whether to require session to be active
            
        Returns:
            SessionEntity: Session if user has access
            
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
        
        # Check if session needs to be active
        if require_active and not session.is_active():
            raise BusinessRuleViolationError(
                f"Session {session_id} is not active"
            )
        
        return session

    async def update_session_activity(
        self,
        session_id: str,
        user_id: int,
        tokens_used: int = 0,
        response_time: float = 0.0
    ) -> SessionEntity:
        """Update session activity and statistics.
        
        Args:
            session_id: ID of session to update
            user_id: ID of user performing the action
            tokens_used: Number of tokens used in this interaction
            response_time: Response time for this interaction
            
        Returns:
            SessionEntity: Updated session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
        """
        # Get and validate session access
        session = await self.get_user_session(session_id, user_id)
        
        # Record message activity
        session.record_message(tokens_used, response_time)
        
        # Save session
        updated_session = await self.session_repository.update(session)
        
        return updated_session

    async def archive_session(
        self,
        session_id: str,
        user_id: int
    ) -> SessionEntity:
        """Archive a session.
        
        Args:
            session_id: ID of session to archive
            user_id: ID of user performing the action
            
        Returns:
            SessionEntity: Archived session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot access session
        """
        # Get and validate session access
        session = await self.get_user_session(session_id, user_id, require_active=False)
        
        # Archive session
        session.archive()
        
        # Save session
        updated_session = await self.session_repository.update(session)
        
        return updated_session

    async def delete_session(
        self,
        session_id: str,
        user_id: int,
        force_delete: bool = False
    ) -> bool:
        """Delete a session (soft delete).
        
        Args:
            session_id: ID of session to delete
            user_id: ID of user performing the action
            force_delete: Whether to force delete even if not owner
            
        Returns:
            bool: True if session was deleted
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionAccessDeniedError: If user cannot delete session
            InsufficientPermissionsError: If user lacks delete permissions
        """
        # Get session and user
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Check delete permissions
        can_delete = (
            session.is_owned_by(user_id) or
            user.role.value == "admin" or
            force_delete
        )
        
        if not can_delete:
            raise InsufficientPermissionsError("delete_session", user_id)
        
        # Soft delete session
        session.mark_deleted()
        await self.session_repository.update(session)
        
        return True

    async def cleanup_inactive_sessions(
        self,
        inactive_hours: int = 24,
        exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Clean up sessions that have been inactive for too long.
        
        Args:
            inactive_hours: Hours of inactivity before cleanup
            exclude_user_ids: User IDs to exclude from cleanup
            
        Returns:
            int: Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=inactive_hours)
        
        # Get inactive sessions
        inactive_sessions = await self.session_repository.get_inactive_sessions(
            inactive_since=cutoff_time,
            limit=1000
        )
        
        # Filter out excluded users
        if exclude_user_ids:
            inactive_sessions = [
                s for s in inactive_sessions 
                if s.user_id not in exclude_user_ids
            ]
        
        # Archive inactive sessions
        session_ids = [s.id for s in inactive_sessions]
        count = await self.session_repository.bulk_update_status(
            session_ids, SessionStatus.ARCHIVED
        )
        
        return count

    async def get_session_analytics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict:
        """Get session analytics and statistics.
        
        Args:
            user_id: Filter by specific user (optional)
            date_from: Start date for analytics
            date_to: End date for analytics
            
        Returns:
            Dict: Analytics data including counts, averages, trends
        """
        # Get basic statistics
        stats = await self.session_repository.get_session_statistics(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        
        # Add computed analytics
        analytics = {
            **stats,
            "session_health": self._calculate_session_health(stats),
            "usage_trends": await self._get_usage_trends(user_id, date_from, date_to),
            "popular_types": await self._get_popular_session_types(user_id),
        }
        
        return analytics

    async def transfer_session_ownership(
        self,
        session_id: str,
        current_owner_id: int,
        new_owner_id: int,
        transferred_by_user_id: int
    ) -> SessionEntity:
        """Transfer session ownership to another user.
        
        Args:
            session_id: ID of session to transfer
            current_owner_id: Current owner user ID
            new_owner_id: New owner user ID
            transferred_by_user_id: ID of user performing transfer
            
        Returns:
            SessionEntity: Updated session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            UserNotFoundError: If any user doesn't exist
            InsufficientPermissionsError: If transfer not authorized
        """
        # Get session
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        
        # Validate users exist
        current_owner = await self.user_repository.get_by_id(current_owner_id)
        new_owner = await self.user_repository.get_by_id(new_owner_id)
        transferrer = await self.user_repository.get_by_id(transferred_by_user_id)
        
        if not current_owner:
            raise UserNotFoundError(current_owner_id)
        if not new_owner:
            raise UserNotFoundError(new_owner_id)
        if not transferrer:
            raise UserNotFoundError(transferred_by_user_id)
        
        # Validate transfer authorization
        can_transfer = (
            session.is_owned_by(transferred_by_user_id) or
            transferrer.role.value == "admin"
        )
        
        if not can_transfer:
            raise InsufficientPermissionsError("transfer_session", transferred_by_user_id)
        
        # Transfer ownership
        session.user_id = new_owner_id
        session.updated_at = datetime.utcnow()
        
        # Save session
        updated_session = await self.session_repository.update(session)
        
        return updated_session

    async def bulk_session_operation(
        self,
        session_ids: List[str],
        operation: str,
        user_id: int,
        **kwargs
    ) -> Dict[str, int]:
        """Perform bulk operations on multiple sessions.
        
        Args:
            session_ids: List of session IDs to operate on
            operation: Operation to perform (archive, delete, activate)
            user_id: ID of user performing operation
            **kwargs: Additional parameters for operation
            
        Returns:
            Dict[str, int]: Results with success/failure counts
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for session_id in session_ids:
            try:
                session = await self.session_repository.get_by_id(session_id)
                if not session:
                    results["failed"] += 1
                    results["errors"].append(f"Session {session_id} not found")
                    continue
                
                # Check permissions
                if not session.can_be_accessed_by(user_id, user.role.value):
                    results["failed"] += 1
                    results["errors"].append(f"No access to session {session_id}")
                    continue
                
                # Perform operation
                if operation == "archive":
                    session.archive()
                elif operation == "delete":
                    session.mark_deleted()
                elif operation == "activate":
                    session.activate()
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Unknown operation: {operation}")
                    continue
                
                await self.session_repository.update(session)
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Session {session_id}: {str(e)}")
        
        return results

    async def _validate_session_limits(self, user_id: int, user_role: str) -> None:
        """Validate session creation limits for user.
        
        Args:
            user_id: User ID to check limits for
            user_role: User role for limit determination
            
        Raises:
            BusinessRuleViolationError: If limits exceeded
        """
        # Define limits by role
        limits = {
            "admin": 1000,
            "editor": 100,
            "viewer": 20,
            "guest": 5
        }
        
        max_sessions = limits.get(user_role, 5)
        
        # Count active sessions for user
        active_count = await self.session_repository.count_user_sessions(
            user_id=user_id,
            status=SessionStatus.ACTIVE
        )
        
        if active_count >= max_sessions:
            raise BusinessRuleViolationError(
                f"User has reached maximum active sessions limit: {max_sessions}"
            )

    def _calculate_session_health(self, stats: Dict) -> str:
        """Calculate overall session health based on statistics.
        
        Args:
            stats: Session statistics
            
        Returns:
            str: Health status (healthy, warning, critical)
        """
        total_sessions = stats.get("total_sessions", 0)
        active_sessions = stats.get("active_sessions", 0)
        
        if total_sessions == 0:
            return "healthy"
        
        active_ratio = active_sessions / total_sessions
        
        if active_ratio > 0.7:
            return "healthy"
        elif active_ratio > 0.4:
            return "warning"
        else:
            return "critical"

    async def _get_usage_trends(
        self,
        user_id: Optional[int],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[Dict]:
        """Get session usage trends over time.
        
        Args:
            user_id: Filter by user ID
            date_from: Start date
            date_to: End date
            
        Returns:
            List[Dict]: Trend data points
        """
        # This would typically involve time-series queries
        # For now, return placeholder structure
        return [
            {"date": "2024-01-01", "sessions_created": 10, "messages_sent": 150},
            {"date": "2024-01-02", "sessions_created": 15, "messages_sent": 220},
        ]

    async def _get_popular_session_types(
        self,
        user_id: Optional[int]
    ) -> List[Dict]:
        """Get popular session types by usage.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            List[Dict]: Popular session types with counts
        """
        # This would query session type popularity
        # For now, return placeholder structure
        return [
            {"type": "chat", "count": 45, "percentage": 60},
            {"type": "document_analysis", "count": 20, "percentage": 27},
            {"type": "rag_query", "count": 10, "percentage": 13},
        ]