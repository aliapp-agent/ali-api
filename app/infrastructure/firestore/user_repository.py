"""Firestore User Repository.

This module provides Firestore implementation for user data management,
integrating with Firebase Auth for authentication data.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from app.domain.entities.user_entity import UserEntity
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.firestore.base_repository import BaseFirestoreRepository


class FirestoreUserRepository(BaseFirestoreRepository, UserRepositoryInterface):
    """Firestore implementation of User Repository."""

    def __init__(self):
        """Initialize Firestore User Repository."""
        super().__init__("users")

    async def create_user(self, user: UserEntity) -> UserEntity:
        """Create a new user.

        Args:
            user: User entity to create

        Returns:
            UserEntity: Created user entity
        """
        data = self.from_entity(user)
        doc_id = await self.create(data, user.id)

        # Return user with generated ID if not provided
        if not user.id:
            user.id = doc_id

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UserEntity]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[UserEntity]: User entity or None if not found
        """
        data = await self.get_by_id(user_id)
        if data:
            return self.to_entity(data)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            Optional[UserEntity]: User entity or None if not found
        """
        users = await self.find_by_field("email", email, limit=1)
        if users:
            return self.to_entity(users[0])
        return None

    async def update_user(self, user: UserEntity) -> UserEntity:
        """Update user.

        Args:
            user: User entity to update

        Returns:
            UserEntity: Updated user entity
        """
        data = self.from_entity(user)
        await self.update(user.id, data)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete user.

        Args:
            user_id: User ID

        Returns:
            bool: True if deleted successfully
        """
        return await self.delete(user_id)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[UserEntity]:
        """List users with optional filtering.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            role: Filter by role
            status: Filter by status

        Returns:
            List[UserEntity]: List of user entities
        """
        query = self.collection.order_by("created_at", direction="desc")

        # Apply filters
        if role:
            query = query.where("role", "==", role)
        if status:
            query = query.where("status", "==", status)

        # Apply pagination
        if skip > 0:
            # For Firestore, we need to use cursor-based pagination
            # This is a simplified approach
            docs = query.limit(skip + limit).stream()
            docs_list = list(docs)
            docs_list = docs_list[skip:]
        else:
            query = query.limit(limit)
            docs_list = list(query.stream())

        results = []
        for doc in docs_list:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def count_users(
        self, role: Optional[str] = None, status: Optional[str] = None
    ) -> int:
        """Count users with optional filtering.

        Args:
            role: Filter by role
            status: Filter by status

        Returns:
            int: Number of users
        """
        filters = {}
        if role:
            filters["role"] = role
        if status:
            filters["status"] = status

        return await self.count(filters)

    async def user_exists(self, user_id: str) -> bool:
        """Check if user exists.

        Args:
            user_id: User ID

        Returns:
            bool: True if user exists
        """
        return await self.exists(user_id)

    async def email_exists(self, email: str) -> bool:
        """Check if email exists.

        Args:
            email: Email address

        Returns:
            bool: True if email exists
        """
        users = await self.find_by_field("email", email, limit=1)
        return len(users) > 0

    async def get_users_by_role(self, role: str, limit: int = 100) -> List[UserEntity]:
        """Get users by role.

        Args:
            role: User role
            limit: Maximum number of users to return

        Returns:
            List[UserEntity]: List of users with specified role
        """
        users_data = await self.find_by_field("role", role, limit)
        return [self.to_entity(data) for data in users_data]

    async def get_active_users(self, limit: int = 100) -> List[UserEntity]:
        """Get active users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List[UserEntity]: List of active users
        """
        users_data = await self.find_by_field("status", "active", limit)
        return [self.to_entity(data) for data in users_data]

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            bool: True if updated successfully
        """
        from google.cloud import firestore

        return await self.update(
            user_id,
            {"last_login": datetime.utcnow(), "login_count": firestore.Increment(1)},
        )

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user.

        Args:
            user_id: User ID

        Returns:
            bool: True if deactivated successfully
        """
        return await self.update(user_id, {"status": "inactive", "is_active": False})

    async def activate_user(self, user_id: str) -> bool:
        """Activate user.

        Args:
            user_id: User ID

        Returns:
            bool: True if activated successfully
        """
        return await self.update(user_id, {"status": "active", "is_active": True})

    def to_entity(self, data: Dict[str, Any]) -> UserEntity:
        """Convert Firestore document to UserEntity.

        Args:
            data: Document data from Firestore

        Returns:
            UserEntity: User entity instance
        """
        return UserEntity(
            id=data.get("id"),
            email=data.get("email"),
            role=data.get("role", "viewer"),
            status=data.get("status", "active"),
            permissions=data.get("permissions"),
            preferences=data.get("preferences"),
            profile=data.get("profile"),
            is_verified=data.get("is_verified", False),
            is_active=data.get("is_active", True),
            last_login=data.get("last_login"),
            login_count=data.get("login_count", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def from_entity(self, entity: UserEntity) -> Dict[str, Any]:
        """Convert UserEntity to Firestore document.

        Args:
            entity: User entity instance

        Returns:
            Dict[str, Any]: Document data for Firestore
        """
        data = {
            "email": entity.email,
            "role": entity.role,
            "status": entity.status,
            "is_verified": entity.is_verified,
            "is_active": entity.is_active,
            "login_count": entity.login_count,
        }

        # Add optional fields if they exist
        if entity.permissions is not None:
            data["permissions"] = entity.permissions
        if entity.preferences is not None:
            data["preferences"] = entity.preferences
        if entity.profile is not None:
            data["profile"] = entity.profile
        if entity.last_login is not None:
            data["last_login"] = entity.last_login
        if entity.created_at is not None:
            data["created_at"] = entity.created_at
        if entity.updated_at is not None:
            data["updated_at"] = entity.updated_at

        return data

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            Optional[UserEntity]: User entity or None if not found
        """
        return await self.get_user_by_email(email)

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: User email address

        Returns:
            bool: True if user exists
        """
        return await self.email_exists(email)

    async def search_users(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> List[UserEntity]:
        """Search users by email or name.

        Args:
            query: Search query
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List[UserEntity]: List of matching users
        """
        # Simple search by email prefix (Firestore limitation)
        # For better search, integrate with Algolia or Cloud Search API
        query_lower = query.lower()

        # Search by email prefix
        users_query = (
            self.collection.where("email", ">=", query_lower)
            .where("email", "<", query_lower + "\uf8ff")
            .order_by("email")
            .limit(limit + offset)
        )

        docs = list(users_query.stream())

        # Apply offset manually
        if offset > 0:
            docs = docs[offset:]
        else:
            docs = docs[:limit]

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_unverified_users(
        self, limit: int = 50, older_than_days: int = 7
    ) -> List[UserEntity]:
        """Get unverified users older than specified days.

        Args:
            limit: Maximum number of users to return
            older_than_days: Number of days to consider as old

        Returns:
            List[UserEntity]: List of unverified users
        """
        from datetime import (
            datetime,
            timedelta,
        )

        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        query = (
            self.collection.where("is_verified", "==", False)
            .where("created_at", "<", cutoff_date)
            .order_by("created_at")
            .limit(limit)
        )

        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.to_entity(data))

        return results

    async def get_user_statistics(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> dict:
        """Get user statistics.

        Args:
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            dict: User statistics
        """
        query = self.collection

        if date_from:
            query = query.where("created_at", ">=", date_from)
        if date_to:
            query = query.where("created_at", "<=", date_to)

        docs = list(query.stream())

        stats = {
            "total_users": len(docs),
            "verified_users": 0,
            "unverified_users": 0,
            "active_users": 0,
            "inactive_users": 0,
            "by_role": {},
            "total_logins": 0,
            "users_with_logins": 0,
        }

        for doc in docs:
            data = doc.to_dict()

            # Count verified/unverified
            if data.get("is_verified", False):
                stats["verified_users"] += 1
            else:
                stats["unverified_users"] += 1

            # Count active/inactive
            if data.get("is_active", True):
                stats["active_users"] += 1
            else:
                stats["inactive_users"] += 1

            # Count by role
            role = data.get("role", "viewer")
            stats["by_role"][role] = stats["by_role"].get(role, 0) + 1

            # Login statistics
            login_count = data.get("login_count", 0)
            stats["total_logins"] += login_count
            if login_count > 0:
                stats["users_with_logins"] += 1

        return stats

    async def increment_login_count(self, user_id: str) -> bool:
        """Increment user's login count.

        Args:
            user_id: User ID

        Returns:
            bool: True if updated successfully
        """
        return await self.update_last_login(user_id)

    async def bulk_update_status(
        self, user_ids: List[str], status: str, is_active: bool
    ) -> int:
        """Bulk update user status.

        Args:
            user_ids: List of user IDs
            status: New status
            is_active: New active state

        Returns:
            int: Number of users updated
        """
        updates = {}
        for user_id in user_ids:
            updates[user_id] = {"status": status, "is_active": is_active}

        success = await self.batch_update(updates)
        return len(user_ids) if success else 0
