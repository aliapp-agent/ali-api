"""Session repository interface for Ali API.

This module defines the contract for session data access operations
without specifying implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities import SessionEntity, SessionStatus, SessionType


class SessionRepositoryInterface(ABC):
    """Abstract repository interface for Session operations.
    
    This interface defines all the operations that can be performed
    on session data without coupling to any specific database implementation.
    """

    @abstractmethod
    async def create(self, session: SessionEntity) -> SessionEntity:
        """Create a new session.
        
        Args:
            session: Session entity to create
            
        Returns:
            SessionEntity: Created session with assigned ID
            
        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[SessionEntity]:
        """Get session by ID.
        
        Args:
            session_id: Session ID to lookup
            
        Returns:
            SessionEntity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, session: SessionEntity) -> SessionEntity:
        """Update an existing session.
        
        Args:
            session: Session entity with updated data
            
        Returns:
            SessionEntity: Updated session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session (soft delete).
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        pass

    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None,
    ) -> List[SessionEntity]:
        """Get sessions for a specific user.
        
        Args:
            user_id: User ID to get sessions for
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status: Filter by session status
            session_type: Filter by session type
            
        Returns:
            List[SessionEntity]: List of user sessions
        """
        pass

    @abstractmethod
    async def count_user_sessions(
        self,
        user_id: int,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None,
    ) -> int:
        """Count sessions for a specific user.
        
        Args:
            user_id: User ID to count sessions for
            status: Filter by session status
            session_type: Filter by session type
            
        Returns:
            int: Number of sessions matching criteria
        """
        pass

    @abstractmethod
    async def get_active_sessions(
        self,
        limit: int = 100,
        older_than: Optional[datetime] = None
    ) -> List[SessionEntity]:
        """Get active sessions.
        
        Args:
            limit: Maximum number of sessions to return
            older_than: Only return sessions older than this timestamp
            
        Returns:
            List[SessionEntity]: List of active sessions
        """
        pass

    @abstractmethod
    async def get_sessions_by_type(
        self,
        session_type: SessionType,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionEntity]:
        """Get sessions by type.
        
        Args:
            session_type: Session type to filter by
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List[SessionEntity]: List of sessions of specified type
        """
        pass

    @abstractmethod
    async def get_inactive_sessions(
        self,
        inactive_since: datetime,
        limit: int = 100
    ) -> List[SessionEntity]:
        """Get sessions that have been inactive since a certain time.
        
        Args:
            inactive_since: Cutoff time for last activity
            limit: Maximum number of sessions to return
            
        Returns:
            List[SessionEntity]: List of inactive sessions
        """
        pass

    @abstractmethod
    async def archive_old_sessions(
        self,
        older_than: datetime,
        exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Archive sessions older than specified date.
        
        Args:
            older_than: Cutoff date for archiving
            exclude_user_ids: User IDs to exclude from archiving
            
        Returns:
            int: Number of sessions archived
        """
        pass

    @abstractmethod
    async def update_session_activity(
        self,
        session_id: str,
        last_activity: Optional[datetime] = None
    ) -> bool:
        """Update session's last activity timestamp.
        
        Args:
            session_id: ID of session to update
            last_activity: New last activity time (defaults to now)
            
        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def record_session_message(
        self,
        session_id: str,
        tokens_used: int = 0,
        response_time: float = 0.0
    ) -> bool:
        """Record a message in the session (update stats).
        
        Args:
            session_id: ID of session to update
            tokens_used: Number of tokens used
            response_time: Response time in seconds
            
        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def get_session_statistics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> dict:
        """Get session statistics.
        
        Args:
            user_id: Filter by specific user (optional)
            date_from: Start date for statistics
            date_to: End date for statistics
            
        Returns:
            dict: Statistics including session counts, types, etc.
        """
        pass

    @abstractmethod
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
            user_id: Filter by specific user (optional)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[SessionEntity]: List of sessions matching search
        """
        pass

    @abstractmethod
    async def get_popular_sessions(
        self,
        limit: int = 10,
        time_period_days: int = 30
    ) -> List[SessionEntity]:
        """Get most active sessions in a time period.
        
        Args:
            limit: Maximum number of sessions to return
            time_period_days: Time period in days to consider
            
        Returns:
            List[SessionEntity]: List of popular sessions
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def cleanup_deleted_sessions(
        self,
        deleted_before: datetime
    ) -> int:
        """Permanently remove sessions marked as deleted.
        
        Args:
            deleted_before: Remove sessions deleted before this date
            
        Returns:
            int: Number of sessions permanently removed
        """
        pass