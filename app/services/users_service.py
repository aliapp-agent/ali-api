"""Users service for comprehensive user management.

This service provides full user lifecycle management including CRUD operations,
role-based access control, activity tracking, and user analytics.
"""

import hashlib
import secrets
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

from fastapi import HTTPException
from sqlmodel import (
    Session,
    and_,
    func,
    or_,
    select,
)

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.models.user_activity import (
    UserActivity,
    UserInvitation,
    UserSession,
)
from app.schemas.users import (
    MessageResponse,
    Permission,
    UserActivityResponse,
    UserBulkResponse,
    UserCreate,
    UserInvitationResponse,
    UserListResponse,
    UserPermissionResponse,
    UserResponse,
    UserRole,
    UserSearchRequest,
    UserStats,
    UserStatus,
    UserUpdate,
)
from app.services.database import DatabaseService


class UsersService:
    """Service for comprehensive user management."""

    def __init__(self):
        """Initialize the users service."""
        self.db_service = DatabaseService()

    async def create_user(
        self, user_data: UserCreate, created_by_user_id: int
    ) -> UserResponse:
        """Create a new user.

        Args:
            user_data: User creation data
            created_by_user_id: ID of the user creating this user

        Returns:
            UserResponse: Created user data
        """
        try:
            # Check if email already exists
            existing_user = await self.db_service.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")

            # Hash password
            hashed_password = User.hash_password(user_data.password)

            # Prepare user data
            now = datetime.utcnow()

            # Create user record
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                role=user_data.role.value,
                status=user_data.status.value,
                permissions=(
                    {"additional": [p.value for p in user_data.permissions]}
                    if user_data.permissions
                    else None
                ),
                preferences=(
                    user_data.preferences.dict() if user_data.preferences else None
                ),
                profile=user_data.profile.dict() if user_data.profile else None,
                is_verified=False,
                is_active=user_data.status == UserStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

            # TODO: Implement actual database save
            user.id = hash(user.email) % 1000000  # TODO: Use proper ID generation

            # Log activity
            await self.log_activity(
                created_by_user_id,
                "user_create",
                f"Created user {user.email}",
                data={
                    "metadata": {
                        "created_user_id": user.id,
                        "role": user.role,
                        "status": user.status,
                    },
                    "success": True,
                },
            )

            # Send welcome email if requested
            if user_data.send_welcome_email:
                await self._send_welcome_email(user)

            logger.info(
                "user_created",
                user_id=user.id,
                email=user.email,
                role=user.role,
                created_by=created_by_user_id,
            )

            return self._user_to_response(user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "user_creation_failed",
                email=user_data.email,
                created_by=created_by_user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to create user: {str(e)}")

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            UserResponse: User data or None if not found
        """
        try:
            user = await self.db_service.get_user(user_id)
            if not user:
                return None

            return self._user_to_response(user)

        except Exception as e:
            logger.error(
                "user_retrieval_failed", user_id=user_id, error=str(e), exc_info=True
            )
            return None

    def _update_user_fields(self, user, update_data):
        """Helper method to update user fields."""
        field_updates = [
            ("email", update_data.email),
            ("role", update_data.role.value if update_data.role else None),
            ("status", update_data.status.value if update_data.status else None),
            ("permissions", {"additional": [p.value for p in update_data.permissions]} if update_data.permissions else None),
            ("preferences", update_data.preferences.dict() if update_data.preferences else None),
            ("profile", update_data.profile.dict() if update_data.profile else None),
        ]

        for field, value in field_updates:
            if value is not None:
                setattr(user, field, value)
                if field == "status":
                    user.is_active = update_data.status == UserStatus.ACTIVE

    async def update_user(
        self, user_id: int, update_data: UserUpdate, updated_by_user_id: int
    ) -> Optional[UserResponse]:
        """Update an existing user.

        Args:
            user_id: User ID to update
            update_data: User update data
            updated_by_user_id: ID of the user making the update

        Returns:
            UserResponse: Updated user data or None if not found
        """
        try:
            user = await self.db_service.get_user(user_id)
            if not user:
                return None

            # Store original values for change tracking
            original_values = {
                "role": user.role,
                "status": user.status,
                "email": user.email,
            }

            # Check email uniqueness if email is being updated
            if update_data.email is not None:
                existing_user = await self.db_service.get_user_by_email(update_data.email)
                if existing_user and existing_user.id != user_id:
                    raise HTTPException(status_code=400, detail="Email already in use")

            # Update all fields using helper method
            self._update_user_fields(user, update_data)
            user.updated_at = datetime.utcnow()

            # Log significant changes
            changes = [
                f"{field}: {original_value} -> {getattr(user, field)}"
                for field, original_value in original_values.items()
                if original_value != getattr(user, field)
            ]

            if changes:
                await self.log_activity(
                    updated_by_user_id,
                    "user_update",
                    f"Updated user {user.email}: {', '.join(changes)}",
                    data={
                        "metadata": {"updated_user_id": user_id, "changes": changes},
                        "success": True,
                    },
                )

            logger.info(
                "user_updated",
                user_id=user_id,
                updated_by=updated_by_user_id,
                changes=changes,
            )

            return self._user_to_response(user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "user_update_failed",
                user_id=user_id,
                updated_by=updated_by_user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to update user: {str(e)}")

    async def delete_user(
        self, user_id: int, deleted_by_user_id: int, soft_delete: bool = True
    ) -> bool:
        """Delete a user.

        Args:
            user_id: User ID to delete
            deleted_by_user_id: ID of the user performing the deletion
            soft_delete: Whether to soft delete (mark as deleted) or hard delete

        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            user = await self.db_service.get_user(user_id)
            if not user:
                return False

            if soft_delete:
                # Soft delete - mark as deleted
                user.status = "deleted"
                user.is_active = False
                user.updated_at = datetime.utcnow()

                await self.log_activity(
                    deleted_by_user_id,
                    "user_soft_delete",
                    f"Soft deleted user {user.email}",
                    data={
                        "metadata": {"deleted_user_id": user_id},
                        "success": True,
                    },
                )

                logger.info(
                    "user_soft_deleted",
                    user_id=user_id,
                    email=user.email,
                    deleted_by=deleted_by_user_id,
                )
            else:
                # TODO: Implement hard delete from database
                await self.log_activity(
                    deleted_by_user_id,
                    "user_hard_delete",
                    f"Hard deleted user {user.email}",
                    data={
                        "metadata": {"deleted_user_id": user_id},
                        "success": True,
                    },
                )

                logger.info(
                    "user_hard_deleted",
                    user_id=user_id,
                    email=user.email,
                    deleted_by=deleted_by_user_id,
                )

            return True

        except Exception as e:
            logger.error(
                "user_deletion_failed",
                user_id=user_id,
                deleted_by=deleted_by_user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to delete user: {str(e)}")

    async def search_users(self, search_request: UserSearchRequest) -> UserListResponse:
        """Search users with advanced filtering and pagination.

        Args:
            search_request: Search parameters

        Returns:
            UserListResponse: Paginated search results
        """
        try:
            # TODO: Implement actual database query
            total_count = 150  # TODO: Get actual count from database

            # TODO: Generate actual users from database for the page
            users = []
            start_index = (search_request.page - 1) * search_request.page_size

            for i in range(search_request.page_size):
                user_id = start_index + i + 1
                if user_id > total_count:
                    break

                # TODO: Create actual user from database
                user = User(
                    id=user_id,
                    email=f"user{user_id}@example.com",
                    hashed_password="placeholder_hash",
                    role=(
                        "viewer" if i % 3 == 0 else "editor" if i % 3 == 1 else "admin"
                    ),
                    status="active",
                    is_verified=i % 2 == 0,
                    is_active=True,
                    login_count=i * 5,
                    created_at=datetime.utcnow() - timedelta(days=i),
                    updated_at=datetime.utcnow() - timedelta(hours=i),
                    last_login=(
                        datetime.utcnow() - timedelta(hours=i * 2)
                        if i % 2 == 0
                        else None
                    ),
                    profile={
                        "first_name": "User",
                        "last_name": f"{user_id}",
                        "organization": (
                            "Example Corp" if i % 2 == 0 else "Another Corp"
                        ),
                    },
                )

                users.append(self._user_to_response(user))

            total_pages = (
                total_count + search_request.page_size - 1
            ) // search_request.page_size

            logger.info(
                "users_searched",
                query=search_request.query,
                page=search_request.page,
                page_size=search_request.page_size,
                results_count=len(users),
            )

            return UserListResponse(
                users=users,
                total_count=total_count,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=total_pages,
                has_next=search_request.page < total_pages,
                has_previous=search_request.page > 1,
            )

        except Exception as e:
            logger.error(
                "user_search_failed",
                query=search_request.query,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"User search failed: {str(e)}")

    async def get_user_stats(self) -> UserStats:
        """Get comprehensive user statistics.

        Returns:
            UserStats: User statistics
        """
        try:
            # TODO: Implement actual statistics aggregation from database
            stats = UserStats(
                total_users=245,
                active_users=198,
                new_users_today=3,
                new_users_week=18,
                new_users_month=67,
                by_role={"admin": 5, "editor": 45, "viewer": 180, "guest": 15},
                by_status={
                    "active": 198,
                    "inactive": 25,
                    "suspended": 8,
                    "pending": 12,
                    "deleted": 2,
                },
                by_organization={
                    "Example Corp": 120,
                    "Another Corp": 85,
                    "Small Co": 25,
                    "Big Enterprise": 15,
                },
                login_stats={
                    "total_logins": 15670,
                    "unique_logins_today": 45,
                    "unique_logins_week": 156,
                    "avg_sessions_per_user": 8.2,
                },
                growth_trend=[
                    {"date": "2025-01-15", "new_users": 12, "total_users": 238},
                    {"date": "2025-01-16", "new_users": 8, "total_users": 246},
                    {"date": "2025-01-17", "new_users": 15, "total_users": 261},
                    {"date": "2025-01-18", "new_users": 6, "total_users": 267},
                    {"date": "2025-01-19", "new_users": 9, "total_users": 276},
                ],
            )

            return stats

        except Exception as e:
            logger.error("user_stats_failed", error=str(e), exc_info=True)
            raise Exception(f"Failed to get user statistics: {str(e)}")

    async def bulk_update_users(
        self, user_ids: List[int], operation: str, operator_user_id: int, **kwargs
    ) -> UserBulkResponse:
        """Perform bulk operations on multiple users.

        Args:
            user_ids: List of user IDs
            operation: Operation type
            operator_user_id: ID of the user performing the operation
            **kwargs: Additional operation parameters

        Returns:
            UserBulkResponse: Bulk operation results
        """
        try:
            success_count = 0
            error_count = 0
            errors = []

            for user_id in user_ids:
                try:
                    user = await self.db_service.get_user(user_id)
                    if not user:
                        error_count += 1
                        errors.append(f"User {user_id} not found")
                        continue

                    if operation == "activate":
                        user.status = "active"
                        user.is_active = True
                        success_count += 1

                    elif operation == "deactivate":
                        user.status = "inactive"
                        user.is_active = False
                        success_count += 1

                    elif operation == "suspend":
                        user.status = "suspended"
                        user.is_active = False
                        success_count += 1

                    elif operation == "delete":
                        await self.delete_user(
                            user_id, operator_user_id, soft_delete=True
                        )
                        success_count += 1

                    elif operation == "change_role":
                        if "role" not in kwargs:
                            error_count += 1
                            errors.append(f"Role not specified for user {user_id}")
                            continue

                        user.role = kwargs["role"].value
                        success_count += 1

                    else:
                        error_count += 1
                        errors.append(f"Unknown operation: {operation}")
                        continue

                    user.updated_at = datetime.utcnow()

                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing user {user_id}: {str(e)}")

            # Log bulk operation
            await self.log_activity(
                operator_user_id,
                f"bulk_{operation}",
                f"Bulk {operation} on {len(user_ids)} users",
                data={
                    "metadata": {
                        "user_ids": user_ids,
                        "success_count": success_count,
                        "error_count": error_count,
                    },
                    "success": error_count == 0,
                },
            )

            success = error_count == 0
            message = f"Processed {len(user_ids)} users. {success_count} successful, {error_count} failed."

            logger.info(
                "bulk_user_operation_completed",
                operation=operation,
                operator_id=operator_user_id,
                total_users=len(user_ids),
                success_count=success_count,
                error_count=error_count,
            )

            return UserBulkResponse(
                success=success,
                processed_count=len(user_ids),
                success_count=success_count,
                error_count=error_count,
                errors=errors,
                message=message,
            )

        except Exception as e:
            logger.error(
                "bulk_user_operation_failed",
                operation=operation,
                operator_id=operator_user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Bulk operation failed: {str(e)}")

    async def check_user_permission(
        self, user_id: int, permission: Permission, resource_id: Optional[str] = None
    ) -> UserPermissionResponse:
        """Check if a user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission to check
            resource_id: Optional resource ID for resource-specific permissions

        Returns:
            UserPermissionResponse: Permission check result
        """
        try:
            user = await self.db_service.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            has_permission = user.has_permission(permission.value)

            return UserPermissionResponse(
                has_permission=has_permission,
                effective_permissions=[
                    Permission(p) for p in user.get_all_permissions()
                ],
                role_permissions=[Permission(p) for p in user.get_role_permissions()],
                additional_permissions=(
                    [Permission(p) for p in user.permissions.get("additional", [])]
                    if user.permissions
                    else []
                ),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "permission_check_failed",
                user_id=user_id,
                permission=permission.value,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Permission check failed: {str(e)}")

    async def log_activity(
        self,
        user_id: int,
        activity_type: str,
        description: str,
        *,
        data: Optional[dict] = None,
    ) -> None:
        """Log user activity for audit purposes.

        Args:
            user_id: User ID
            activity_type: Type of activity
            description: Human-readable description
            data: Additional data including metadata, context, and success status
        """
        try:
            # In real implementation, save to database
            success = data.get("success", True) if data else True
            metadata = data.get("metadata") if data else None
            logger.info(
                "user_activity_logged",
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                success=success,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(
                "activity_logging_failed",
                user_id=user_id,
                activity_type=activity_type,
                error=str(e),
                exc_info=True,
            )

    def _user_to_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse schema.

        Args:
            user: User model instance

        Returns:
            UserResponse: User response schema
        """
        from app.schemas.users import (
            UserPreferences,
            UserProfile,
            UserStatus,
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            role=UserRole(user.role),
            status=UserStatus(user.status),
            permissions=(
                [Permission(p) for p in user.permissions.get("additional", [])]
                if user.permissions
                else []
            ),
            preferences=(
                UserPreferences(**user.preferences)
                if user.preferences
                else UserPreferences()
            ),
            profile=UserProfile(**user.profile) if user.profile else UserProfile(),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            login_count=user.login_count,
            is_verified=user.is_verified,
            is_active=user.is_active,
            avatar_url=user.profile.get("avatar_url") if user.profile else None,
            full_name=user.get_display_name(),
        )

    async def _send_welcome_email(self, user: User) -> None:
        """Send welcome email to new user.

        Args:
            user: User to send welcome email to
        """
        # TODO: Implement actual email sending
        logger.info("welcome_email_sent", user_id=user.id, email=user.email)


# Create global instance
users_service = UsersService()
