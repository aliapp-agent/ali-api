"""This file contains the user model for the application."""

from datetime import datetime
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

import bcrypt
from sqlmodel import (
    JSON,
    Column,
    Field,
    Relationship,
)
from sqlmodel import Session as SQLSession

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.session import Session


class User(BaseModel, table=True):
    """Enhanced user model for comprehensive user management.

    Attributes:
        id: The primary key
        email: User's email (unique)
        hashed_password: Bcrypt hashed password
        role: User role (admin, editor, viewer, guest)
        status: User status (active, inactive, suspended, pending, deleted)
        permissions: Additional permissions as JSON array
        preferences: User preferences as JSON object
        profile: Extended profile information as JSON object
        is_verified: Email verification status
        is_active: Active status
        last_login: Last login timestamp
        login_count: Total login count
        created_at: When the user was created
        updated_at: When the user was last updated
        sessions: Relationship to user's chat sessions
    """

    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

    # Role and permissions
    role: str = Field(default="viewer", index=True)  # admin, editor, viewer, guest
    status: str = Field(
        default="active", index=True
    )  # active, inactive, suspended, pending, deleted
    permissions: Optional[dict] = Field(
        default=None, sa_column=Column(JSON)
    )  # Additional permissions

    # User preferences and profile
    preferences: Optional[dict] = Field(
        default=None, sa_column=Column(JSON)
    )  # User preferences
    profile: Optional[dict] = Field(
        default=None, sa_column=Column(JSON)
    )  # Extended profile

    # Status flags
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)

    # Activity tracking
    last_login: Optional[datetime] = Field(default=None)
    login_count: int = Field(default=0)

    # Relationships
    sessions: List["Session"] = Relationship(back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Admin has all permissions
        if self.role == "admin":
            return True

        # Check role-based permissions
        role_permissions = self.get_role_permissions()
        if permission in role_permissions:
            return True

        # Check additional permissions
        if self.permissions and permission in self.permissions.get("additional", []):
            return True

        return False

    def get_role_permissions(self) -> List[str]:
        """Get permissions based on user role."""
        role_permission_map = {
            "admin": [
                "documents:read",
                "documents:write",
                "documents:delete",
                "documents:admin",
                "users:read",
                "users:write",
                "users:delete",
                "users:admin",
                "chat:read",
                "chat:write",
                "chat:admin",
                "system:read",
                "system:write",
                "system:admin",
                "analytics:read",
                "analytics:admin",
            ],
            "editor": [
                "documents:read",
                "documents:write",
                "documents:delete",
                "users:read",
                "chat:read",
                "chat:write",
                "analytics:read",
            ],
            "viewer": ["documents:read", "chat:read", "analytics:read"],
            "guest": ["documents:read"],
        }
        return role_permission_map.get(self.role, [])

    def get_all_permissions(self) -> List[str]:
        """Get all effective permissions for the user."""
        permissions = self.get_role_permissions()

        # Add additional permissions
        if self.permissions and "additional" in self.permissions:
            permissions.extend(self.permissions["additional"])

        return list(set(permissions))  # Remove duplicates

    def update_login_info(self) -> None:
        """Update login information when user logs in."""
        self.last_login = datetime.utcnow()
        self.login_count += 1

    def get_display_name(self) -> str:
        """Get display name for the user."""
        if self.profile:
            first_name = self.profile.get("first_name", "")
            last_name = self.profile.get("last_name", "")
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()

        return self.email.split("@")[0]

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin"

    def is_editor(self) -> bool:
        """Check if user is an editor."""
        return self.role in ["admin", "editor"]

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.has_permission("users:admin") or self.role == "admin"


# Avoid circular imports
from app.models.session import Session as ChatSession  # noqa: E402
