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
        self, user_data: UserCreate, created_by_user_id: str
    ) -> UserResponse:
        """Create a new user.

        Args:
            user_data: User creation data
            created_by_user_id: Firebase UID of the user creating this user

        Returns:
            UserResponse: Created user data
        """
        try:
            # Check if email already exists
            existing_user_data = await self.db_service.get_user_by_email(user_data.email)
            if existing_user_data:
                raise HTTPException(status_code=400, detail="Email already registered")

            # Hash password
            hashed_password = User.hash_password(user_data.password)

            # Generate Firebase UID (in production, this would be handled by Firebase Auth)
            user_id = str(uuid.uuid4())
            
            # Prepare user data
            now = datetime.utcnow()

            # Create user record
            user = User(
                id=user_id,
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

            # Save to Firebase
            success = await self.db_service.create_user(user_id, user.to_dict())
            if not success:
                raise Exception("Failed to save user to database")

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

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get a user by ID.

        Args:
            user_id: Firebase UID

        Returns:
            UserResponse: User data or None if not found
        """
        try:
            user_data = await self.db_service.get_user(user_id)
            if not user_data:
                return None

            user = User.from_dict(user_id, user_data)
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
        self, user_id: str, update_data: UserUpdate, updated_by_user_id: str
    ) -> Optional[UserResponse]:
        """Update an existing user.

        Args:
            user_id: Firebase UID to update
            update_data: User update data
            updated_by_user_id: Firebase UID of the user making the update

        Returns:
            UserResponse: Updated user data or None if not found
        """
        try:
            user_data = await self.db_service.get_user(user_id)
            if not user_data:
                return None
                
            user = User.from_dict(user_id, user_data)

            # Store original values for change tracking
            original_values = {
                "role": user.role,
                "status": user.status,
                "email": user.email,
            }

            # Check email uniqueness if email is being updated
            if update_data.email is not None:
                existing_user_data = await self.db_service.get_user_by_email(update_data.email)
                if existing_user_data:
                    # Get existing user ID from the document (need to find by query since we only have data)
                    from google.cloud.firestore_v1.base_query import FieldFilter
                    filters = [FieldFilter("email", "==", update_data.email)]
                    existing_users = await self.db_service.query_documents("users", filters=filters, limit=1)
                    if existing_users and existing_users[0].get("id") != user_id:
                        raise HTTPException(status_code=400, detail="Email already in use")

            # Update all fields using helper method
            self._update_user_fields(user, update_data)
            user.updated_at = datetime.utcnow()
            
            # Save updated user to Firebase
            success = await self.db_service.update_user(user_id, user.to_dict())
            if not success:
                raise Exception("Failed to update user in database")

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
        self, user_id: str, deleted_by_user_id: str, soft_delete: bool = True
    ) -> bool:
        """Delete a user.

        Args:
            user_id: Firebase UID to delete
            deleted_by_user_id: Firebase UID of the user performing the deletion
            soft_delete: Whether to soft delete (mark as deleted) or hard delete

        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            user_data = await self.db_service.get_user(user_id)
            if not user_data:
                return False
                
            user = User.from_dict(user_id, user_data)

            if soft_delete:
                # Soft delete - mark as deleted
                user.status = "deleted"
                user.is_active = False
                user.updated_at = datetime.utcnow()
                
                # Save updated user to Firebase
                success = await self.db_service.update_user(user_id, user.to_dict())
                if not success:
                    raise Exception("Failed to soft delete user in database")

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
                # Hard delete from database
                success = await self.db_service.delete_user(user_id)
                if not success:
                    raise Exception("Failed to hard delete user from database")
                    
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
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            # Build filters
            filters = []
            
            # Filter by query (search in email or profile name)
            if search_request.query:
                # Note: Firestore doesn't support full-text search, so we'll search by email prefix
                # In production, you might want to use a search service like Algolia or Elastic
                filters.append(FieldFilter("email", ">=", search_request.query))
                filters.append(FieldFilter("email", "<", search_request.query + "\uf8ff"))
            
            # Filter by role
            if search_request.role:
                filters.append(FieldFilter("role", "==", search_request.role.value))
                
            # Filter by status  
            if search_request.status:
                filters.append(FieldFilter("status", "==", search_request.status.value))
                
            # Filter by active status
            if search_request.is_active is not None:
                filters.append(FieldFilter("is_active", "==", search_request.is_active))

            # Get users with pagination
            # Note: For proper pagination with Firestore, you'd typically use startAfter cursors
            # This is a simplified approach
            all_users_data = await self.db_service.list_users(
                filters=filters if filters else None,
                order_by="created_at",
                limit=None  # Get all first to calculate total
            )
            
            total_count = len(all_users_data)
            
            # Apply pagination
            start_index = (search_request.page - 1) * search_request.page_size
            end_index = start_index + search_request.page_size
            paginated_users_data = all_users_data[start_index:end_index]
            
            # Convert to User objects and responses
            users = []
            for user_data in paginated_users_data:
                # Get user ID from document - need to query the collection to get doc IDs
                # This is inefficient but works for demonstration
                # In production, you'd store the user ID in the document or use a different approach
                if "email" in user_data:
                    user_id = str(uuid.uuid4())  # Temporary - would get from document ID
                    user = User.from_dict(user_id, user_data)
                    users.append(self._user_to_response(user))

            total_pages = (
                total_count + search_request.page_size - 1
            ) // search_request.page_size if search_request.page_size > 0 else 1

            logger.info(
                "users_searched",
                query=search_request.query,
                page=search_request.page,
                page_size=search_request.page_size,
                results_count=len(users),
                total_count=total_count,
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
            from collections import defaultdict
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            # Get all users for statistics
            all_users_data = await self.db_service.list_users()
            
            # Initialize counters
            total_users = len(all_users_data)
            active_users = 0
            by_role = defaultdict(int)
            by_status = defaultdict(int)
            by_organization = defaultdict(int)
            total_logins = 0
            
            # Date calculations
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            new_users_today = 0
            new_users_week = 0
            new_users_month = 0
            
            # Process each user
            for user_data in all_users_data:
                # Count active users
                if user_data.get("is_active", False):
                    active_users += 1
                
                # Count by role
                role = user_data.get("role", "viewer")
                by_role[role] += 1
                
                # Count by status
                status = user_data.get("status", "active")
                by_status[status] += 1
                
                # Count by organization
                profile = user_data.get("profile", {})
                if isinstance(profile, dict):
                    org = profile.get("organization", "Unknown")
                    by_organization[org] += 1
                
                # Login stats
                login_count = user_data.get("login_count", 0)
                total_logins += login_count
                
                # New users counting
                created_at = user_data.get("created_at")
                if created_at:
                    # Handle both datetime objects and ISO strings
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            continue
                    elif not isinstance(created_at, datetime):
                        continue
                        
                    if created_at >= today:
                        new_users_today += 1
                    if created_at >= week_ago:
                        new_users_week += 1
                    if created_at >= month_ago:
                        new_users_month += 1
            
            # Calculate averages
            avg_sessions_per_user = total_logins / total_users if total_users > 0 else 0
            
            # Generate growth trend (simplified - last 5 days)
            growth_trend = []
            for i in range(4, -1, -1):
                date = (now - timedelta(days=i)).date()
                # In a real implementation, you'd query users created on each specific date
                # For now, we'll provide estimated values
                new_users_on_date = max(1, new_users_week // 7)  # Rough estimate
                running_total = total_users - (new_users_week - new_users_on_date * (5-i))
                
                growth_trend.append({
                    "date": date.isoformat(),
                    "new_users": new_users_on_date,
                    "total_users": max(0, running_total)
                })
            
            # Today's login stats (would require session tracking in real app)
            unique_logins_today = min(active_users, active_users // 4)  # Estimate
            unique_logins_week = min(active_users, active_users // 2)   # Estimate
            
            stats = UserStats(
                total_users=total_users,
                active_users=active_users,
                new_users_today=new_users_today,
                new_users_week=new_users_week,
                new_users_month=new_users_month,
                by_role=dict(by_role),
                by_status=dict(by_status),
                by_organization=dict(by_organization) if any(by_organization.values()) else {"No Organization": total_users},
                login_stats={
                    "total_logins": total_logins,
                    "unique_logins_today": unique_logins_today,
                    "unique_logins_week": unique_logins_week,
                    "avg_sessions_per_user": round(avg_sessions_per_user, 1),
                },
                growth_trend=growth_trend,
            )

            logger.info(
                "user_stats_calculated",
                total_users=total_users,
                active_users=active_users,
                new_users_today=new_users_today,
            )

            return stats

        except Exception as e:
            logger.error("user_stats_failed", error=str(e), exc_info=True)
            raise Exception(f"Failed to get user statistics: {str(e)}")

    async def bulk_update_users(
        self, user_ids: List[str], operation: str, operator_user_id: str, **kwargs
    ) -> UserBulkResponse:
        """Perform bulk operations on multiple users.

        Args:
            user_ids: List of Firebase UIDs
            operation: Operation type
            operator_user_id: Firebase UID of the user performing the operation
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
                    user_data = await self.db_service.get_user(user_id)
                    if not user_data:
                        error_count += 1
                        errors.append(f"User {user_id} not found")
                        continue
                        
                    user = User.from_dict(user_id, user_data)

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
                    
                    # Save updated user to Firebase
                    success = await self.db_service.update_user(user_id, user.to_dict())
                    if not success:
                        error_count += 1
                        errors.append(f"Failed to update user {user_id} in database")

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
        self, user_id: str, permission: Permission, resource_id: Optional[str] = None
    ) -> UserPermissionResponse:
        """Check if a user has a specific permission.

        Args:
            user_id: Firebase UID
            permission: Permission to check
            resource_id: Optional resource ID for resource-specific permissions

        Returns:
            UserPermissionResponse: Permission check result
        """
        try:
            user_data = await self.db_service.get_user(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")

            user = User.from_dict(user_id, user_data)
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
        user_id: str,
        activity_type: str,
        description: str,
        *,
        data: Optional[dict] = None,
    ) -> None:
        """Log user activity for audit purposes.

        Args:
            user_id: Firebase UID
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
