"""User domain entity for Ali API.

This module contains the pure domain model for User,
independent of any external dependencies or frameworks.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

import bcrypt


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User status in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


@dataclass
class UserProfile:
    """User profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "pt-BR"


@dataclass
class UserPreferences:
    """User preferences configuration."""
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    auto_save: bool = True
    default_language: str = "pt-BR"


class UserEntity:
    """Pure domain entity for User.
    
    This class contains the core business logic for users
    without any external dependencies.
    """
    
    def __init__(
        self,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.VIEWER,
        status: UserStatus = UserStatus.PENDING,
        permissions: Optional[List[str]] = None,
        preferences: Optional[UserPreferences] = None,
        profile: Optional[UserProfile] = None,
        is_verified: bool = False,
        is_active: bool = True,
        last_login: Optional[datetime] = None,
        login_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ):
        """Initialize a User entity.
        
        Args:
            email: User's email address
            hashed_password: Bcrypt hashed password
            role: User role in the system
            status: Current user status
            permissions: Additional permissions list
            preferences: User preferences
            profile: User profile information
            is_verified: Email verification status
            is_active: Whether user is active
            last_login: Last login timestamp
            login_count: Total number of logins
            created_at: Creation timestamp
            updated_at: Last update timestamp
            user_id: Unique identifier
        """
        self.id = user_id
        self.email = self._validate_email(email)
        self.hashed_password = hashed_password
        self.role = role
        self.status = status
        self.permissions = permissions or []
        self.preferences = preferences or UserPreferences()
        self.profile = profile or UserProfile()
        self.is_verified = is_verified
        self.is_active = is_active
        self.last_login = last_login
        self.login_count = login_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email format."""
        email = email.lower().strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError(f"Invalid email format: {email}")
        return email

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not password:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    def can_perform_action(self, action: str) -> bool:
        """Check if user can perform a specific action."""
        if not self.is_active or self.status != UserStatus.ACTIVE:
            return False
        
        # Admin can do everything
        if self.role == UserRole.ADMIN:
            return True
        
        # Role-based permissions
        role_permissions = {
            UserRole.EDITOR: [
                "read", "write", "edit", "create_document", 
                "delete_own", "chat", "upload"
            ],
            UserRole.VIEWER: ["read", "chat"],
            UserRole.GUEST: ["read"]
        }
        
        allowed_actions = role_permissions.get(self.role, [])
        
        # Check explicit permissions
        if action in self.permissions:
            return True
        
        # Check role-based permissions
        return action in allowed_actions

    def update_last_login(self) -> None:
        """Update last login information."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend the user account."""
        self.is_active = False
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.is_verified = True
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def update_profile(self, profile_data: Dict) -> None:
        """Update user profile information."""
        if 'first_name' in profile_data:
            self.profile.first_name = profile_data['first_name']
        if 'last_name' in profile_data:
            self.profile.last_name = profile_data['last_name']
        if 'avatar_url' in profile_data:
            self.profile.avatar_url = profile_data['avatar_url']
        if 'bio' in profile_data:
            self.profile.bio = profile_data['bio']
        if 'phone' in profile_data:
            self.profile.phone = profile_data['phone']
        if 'timezone' in profile_data:
            self.profile.timezone = profile_data['timezone']
        if 'language' in profile_data:
            self.profile.language = profile_data['language']
        
        self.updated_at = datetime.utcnow()

    def update_preferences(self, preferences_data: Dict) -> None:
        """Update user preferences."""
        if 'theme' in preferences_data:
            self.preferences.theme = preferences_data['theme']
        if 'notifications_enabled' in preferences_data:
            self.preferences.notifications_enabled = preferences_data['notifications_enabled']
        if 'email_notifications' in preferences_data:
            self.preferences.email_notifications = preferences_data['email_notifications']
        if 'auto_save' in preferences_data:
            self.preferences.auto_save = preferences_data['auto_save']
        if 'default_language' in preferences_data:
            self.preferences.default_language = preferences_data['default_language']
        
        self.updated_at = datetime.utcnow()

    def add_permission(self, permission: str) -> None:
        """Add a permission to the user."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()

    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()

    def change_role(self, new_role: UserRole) -> None:
        """Change user role."""
        self.role = new_role
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(id={self.id}, email={self.email}, role={self.role.value})"

    def __repr__(self) -> str:
        """Detailed representation of the user."""
        return (
            f"UserEntity(id={self.id}, email='{self.email}', "
            f"role={self.role.value}, status={self.status.value})"
        )