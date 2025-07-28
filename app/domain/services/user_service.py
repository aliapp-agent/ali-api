"""User domain service for Ali API.

This module contains business logic for user operations that involve
complex rules or multiple entities.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import secrets
import string

from app.domain.entities import UserEntity, UserRole, UserStatus
from app.domain.repositories import UserRepositoryInterface
from app.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidUserCredentialsError,
    UserNotActiveError,
    UserNotVerifiedError,
    InsufficientPermissionsError,
    BusinessRuleViolationError,
)


class UserDomainService:
    """Domain service for user-related business logic.
    
    This service encapsulates complex user operations that involve
    business rules, validations, and coordination between entities.
    """
    
    def __init__(self, user_repository: UserRepositoryInterface):
        """Initialize the user domain service.
        
        Args:
            user_repository: Repository for user data access
        """
        self.user_repository = user_repository

    async def register_user(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        auto_verify: bool = False,
        invited_by_user_id: Optional[int] = None
    ) -> UserEntity:
        """Register a new user with business rule validation.
        
        Args:
            email: User email address
            password: Plain text password
            role: User role to assign
            auto_verify: Whether to auto-verify the user
            invited_by_user_id: ID of user who invited this user
            
        Returns:
            UserEntity: Newly created user
            
        Raises:
            UserAlreadyExistsError: If user already exists
            BusinessRuleViolationError: If business rules are violated
        """
        # Check if user already exists
        if await self.user_repository.exists_by_email(email):
            raise UserAlreadyExistsError(email)
        
        # Validate business rules for registration
        await self._validate_registration_rules(role, invited_by_user_id)
        
        # Create user entity
        hashed_password = UserEntity.hash_password(password)
        user = UserEntity(
            email=email,
            hashed_password=hashed_password,
            role=role,
            status=UserStatus.ACTIVE if auto_verify else UserStatus.PENDING,
            is_verified=auto_verify,
        )
        
        # Save user
        created_user = await self.user_repository.create(user)
        
        return created_user

    async def authenticate_user(
        self,
        email: str,
        password: str,
        update_login_info: bool = True
    ) -> UserEntity:
        """Authenticate a user with credentials.
        
        Args:
            email: User email address
            password: Plain text password
            update_login_info: Whether to update last login info
            
        Returns:
            UserEntity: Authenticated user
            
        Raises:
            InvalidUserCredentialsError: If credentials are invalid
            UserNotActiveError: If user is not active
            UserNotVerifiedError: If user is not verified (optional check)
        """
        # Get user by email
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise InvalidUserCredentialsError()
        
        # Verify password
        if not user.verify_password(password):
            raise InvalidUserCredentialsError()
        
        # Check if user is active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise UserNotActiveError(user.id)
        
        # Update login information if requested
        if update_login_info:
            user.update_last_login()
            await self.user_repository.update(user)
        
        return user

    async def change_user_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password with current password verification.
        
        Args:
            user_id: ID of user to update
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidUserCredentialsError: If current password is wrong
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Verify current password
        if not user.verify_password(current_password):
            raise InvalidUserCredentialsError()
        
        # Set new password
        user.hashed_password = UserEntity.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # Save user
        await self.user_repository.update(user)
        
        return True

    async def reset_user_password(
        self,
        email: str
    ) -> Tuple[UserEntity, str]:
        """Reset user password and generate temporary password.
        
        Args:
            email: Email of user to reset password for
            
        Returns:
            Tuple[UserEntity, str]: User entity and temporary password
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Get user by email
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(email=email)
        
        # Generate temporary password
        temp_password = self._generate_temporary_password()
        
        # Set temporary password
        user.hashed_password = UserEntity.hash_password(temp_password)
        user.updated_at = datetime.utcnow()
        
        # Save user
        updated_user = await self.user_repository.update(user)
        
        return updated_user, temp_password

    async def promote_user_role(
        self,
        user_id: int,
        new_role: UserRole,
        promoted_by_user_id: int
    ) -> UserEntity:
        """Promote user to a higher role with authorization check.
        
        Args:
            user_id: ID of user to promote
            new_role: New role to assign
            promoted_by_user_id: ID of user performing the promotion
            
        Returns:
            UserEntity: Updated user
            
        Raises:
            UserNotFoundError: If user doesn't exist
            InsufficientPermissionsError: If promoter lacks permissions
            BusinessRuleViolationError: If promotion violates business rules
        """
        # Get user to promote
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Get promoter user
        promoter = await self.user_repository.get_by_id(promoted_by_user_id)
        if not promoter:
            raise UserNotFoundError(promoted_by_user_id)
        
        # Validate promotion authorization
        await self._validate_role_promotion(user, new_role, promoter)
        
        # Update user role
        user.change_role(new_role)
        
        # Save user
        updated_user = await self.user_repository.update(user)
        
        return updated_user

    async def deactivate_user(
        self,
        user_id: int,
        deactivated_by_user_id: int,
        reason: Optional[str] = None
    ) -> UserEntity:
        """Deactivate a user account.
        
        Args:
            user_id: ID of user to deactivate
            deactivated_by_user_id: ID of user performing the deactivation
            reason: Optional reason for deactivation
            
        Returns:
            UserEntity: Updated user
            
        Raises:
            UserNotFoundError: If user doesn't exist
            InsufficientPermissionsError: If deactivator lacks permissions
            BusinessRuleViolationError: If deactivation violates rules
        """
        # Get user to deactivate
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Get deactivator user
        deactivator = await self.user_repository.get_by_id(deactivated_by_user_id)
        if not deactivator:
            raise UserNotFoundError(deactivated_by_user_id)
        
        # Validate deactivation authorization
        await self._validate_user_deactivation(user, deactivator)
        
        # Deactivate user
        user.deactivate()
        
        # Save user
        updated_user = await self.user_repository.update(user)
        
        return updated_user

    async def verify_user_email(self, user_id: int) -> UserEntity:
        """Verify a user's email address.
        
        Args:
            user_id: ID of user to verify
            
        Returns:
            UserEntity: Updated user
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Verify email
        user.verify_email()
        
        # Save user
        updated_user = await self.user_repository.update(user)
        
        return updated_user

    async def cleanup_inactive_users(
        self,
        inactive_days: int = 90
    ) -> int:
        """Clean up users that have been inactive for too long.
        
        Args:
            inactive_days: Number of days of inactivity before cleanup
            
        Returns:
            int: Number of users cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
        
        # Get unverified users created before cutoff
        inactive_users = await self.user_repository.get_unverified_users(
            created_before=cutoff_date,
            limit=1000
        )
        
        # Deactivate inactive users
        user_ids = [user.id for user in inactive_users if user.id]
        count = await self.user_repository.bulk_update_status(
            user_ids, UserStatus.INACTIVE
        )
        
        return count

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get effective permissions for a user.
        
        Args:
            user_id: ID of user to get permissions for
            
        Returns:
            List[str]: List of permission strings
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Start with role-based permissions
        role_permissions = self._get_role_permissions(user.role)
        
        # Add explicit permissions
        all_permissions = set(role_permissions)
        all_permissions.update(user.permissions)
        
        return list(all_permissions)

    async def validate_user_action(
        self,
        user_id: int,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Validate if user can perform a specific action.
        
        Args:
            user_id: ID of user to check
            action: Action to validate
            resource_id: Optional resource ID for resource-specific checks
            
        Returns:
            bool: True if user can perform action
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Check if user can perform action
        return user.can_perform_action(action)

    def _generate_temporary_password(self, length: int = 12) -> str:
        """Generate a secure temporary password.
        
        Args:
            length: Length of password to generate
            
        Returns:
            str: Generated password
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for a role.
        
        Args:
            role: User role
            
        Returns:
            List[str]: List of permissions for the role
        """
        role_permissions = {
            UserRole.ADMIN: [
                "read", "write", "edit", "delete", "create_document",
                "manage_users", "manage_sessions", "manage_system",
                "chat", "upload", "export", "admin_dashboard"
            ],
            UserRole.EDITOR: [
                "read", "write", "edit", "create_document", 
                "delete_own", "chat", "upload", "export"
            ],
            UserRole.VIEWER: ["read", "chat"],
            UserRole.GUEST: ["read"]
        }
        
        return role_permissions.get(role, [])

    async def _validate_registration_rules(
        self,
        role: UserRole,
        invited_by_user_id: Optional[int]
    ) -> None:
        """Validate business rules for user registration.
        
        Args:
            role: Role being assigned
            invited_by_user_id: ID of inviting user
            
        Raises:
            BusinessRuleViolationError: If rules are violated
        """
        # Admin roles require invitation
        if role == UserRole.ADMIN and not invited_by_user_id:
            raise BusinessRuleViolationError(
                "Admin role requires invitation from existing admin"
            )
        
        # Check inviter permissions if provided
        if invited_by_user_id:
            inviter = await self.user_repository.get_by_id(invited_by_user_id)
            if not inviter or inviter.role != UserRole.ADMIN:
                raise BusinessRuleViolationError(
                    "Only admins can invite new users"
                )

    async def _validate_role_promotion(
        self,
        user: UserEntity,
        new_role: UserRole,
        promoter: UserEntity
    ) -> None:
        """Validate role promotion rules.
        
        Args:
            user: User being promoted
            new_role: New role being assigned
            promoter: User performing the promotion
            
        Raises:
            InsufficientPermissionsError: If promoter lacks permissions
            BusinessRuleViolationError: If promotion violates rules
        """
        # Only admins can promote users
        if promoter.role != UserRole.ADMIN:
            raise InsufficientPermissionsError("promote_user", promoter.id)
        
        # Cannot promote to same or lower role
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.VIEWER: 1, 
            UserRole.EDITOR: 2,
            UserRole.ADMIN: 3
        }
        
        current_level = role_hierarchy.get(user.role, 0)
        new_level = role_hierarchy.get(new_role, 0)
        
        if new_level <= current_level:
            raise BusinessRuleViolationError(
                f"Cannot promote from {user.role.value} to {new_role.value}"
            )

    async def _validate_user_deactivation(
        self,
        user: UserEntity,
        deactivator: UserEntity
    ) -> None:
        """Validate user deactivation rules.
        
        Args:
            user: User being deactivated
            deactivator: User performing the deactivation
            
        Raises:
            InsufficientPermissionsError: If deactivator lacks permissions
            BusinessRuleViolationError: If deactivation violates rules
        """
        # Only admins can deactivate other users
        if deactivator.role != UserRole.ADMIN and user.id != deactivator.id:
            raise InsufficientPermissionsError("deactivate_user", deactivator.id)
        
        # Cannot deactivate other admins
        if user.role == UserRole.ADMIN and user.id != deactivator.id:
            raise BusinessRuleViolationError(
                "Admins cannot deactivate other admins"
            )