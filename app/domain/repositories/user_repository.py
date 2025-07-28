"""User repository interface for Ali API.

This module defines the contract for user data access operations
without specifying implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities import UserEntity, UserRole, UserStatus


class UserRepositoryInterface(ABC):
    """Abstract repository interface for User operations.
    
    This interface defines all the operations that can be performed
    on user data without coupling to any specific database implementation.
    """

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            UserEntity: Created user with assigned ID
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Get user by ID.
        
        Args:
            user_id: User ID to lookup
            
        Returns:
            UserEntity or None if not found
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email address.
        
        Args:
            email: Email address to lookup
            
        Returns:
            UserEntity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """Update an existing user.
        
        Args:
            user: User entity with updated data
            
        Returns:
            UserEntity: Updated user
            
        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete a user (soft delete).
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> List[UserEntity]:
        """List users with optional filtering.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            status: Filter by user status
            role: Filter by user role
            is_verified: Filter by verification status
            search_query: Search in email or name
            
        Returns:
            List[UserEntity]: List of users matching criteria
        """
        pass

    @abstractmethod
    async def count_users(
        self,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Count users with optional filtering.
        
        Args:
            status: Filter by user status
            role: Filter by user role
            is_verified: Filter by verification status
            search_query: Search in email or name
            
        Returns:
            int: Number of users matching criteria
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if user exists
        """
        pass

    @abstractmethod
    async def get_active_users(self, limit: int = 100) -> List[UserEntity]:
        """Get active users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List[UserEntity]: List of active users
        """
        pass

    @abstractmethod
    async def get_users_by_role(self, role: UserRole) -> List[UserEntity]:
        """Get users by role.
        
        Args:
            role: User role to filter by
            
        Returns:
            List[UserEntity]: List of users with specified role
        """
        pass

    @abstractmethod
    async def get_unverified_users(
        self, 
        created_before: datetime,
        limit: int = 100
    ) -> List[UserEntity]:
        """Get unverified users created before a certain date.
        
        Args:
            created_before: Cutoff date for user creation
            limit: Maximum number of users to return
            
        Returns:
            List[UserEntity]: List of unverified users
        """
        pass

    @abstractmethod
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def increment_login_count(self, user_id: int) -> bool:
        """Increment user's login count.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self, 
        user_ids: List[int], 
        status: UserStatus
    ) -> int:
        """Bulk update user status.
        
        Args:
            user_ids: List of user IDs to update
            status: New status to set
            
        Returns:
            int: Number of users updated
        """
        pass

    @abstractmethod
    async def get_user_statistics(self) -> dict:
        """Get user statistics.
        
        Returns:
            dict: Statistics including total users, by status, by role, etc.
        """
        pass

    @abstractmethod
    async def search_users(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserEntity]:
        """Search users by various fields.
        
        Args:
            query: Search query (email, name, etc.)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[UserEntity]: List of users matching search
        """
        pass