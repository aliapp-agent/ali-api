"""User model definitions."""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for Firebase authentication with extended functionality."""
    
    id: str = Field(..., description="Firebase UID")
    email: str = Field(..., description="User email")
    hashed_password: Optional[str] = Field(None, description="Hashed password")
    role: str = Field(default="viewer", description="User role")
    status: str = Field(default="active", description="User status")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Additional permissions")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    profile: Optional[Dict[str, Any]] = Field(None, description="User profile information")
    is_verified: bool = Field(False, description="Whether email is verified")
    is_active: bool = Field(True, description="Whether user is active")
    login_count: int = Field(default=0, description="Number of logins")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        # Get role-based permissions
        role_permissions = self.get_role_permissions()
        
        # Get additional permissions
        additional_permissions = []
        if self.permissions and "additional" in self.permissions:
            additional_permissions = self.permissions["additional"]
        
        return permission in role_permissions or permission in additional_permissions
    
    def get_role_permissions(self) -> List[str]:
        """Get permissions based on user role.
        
        Returns:
            List of permissions for the user's role
        """
        role_permission_mapping = {
            "admin": ["read", "write", "delete", "admin"],
            "editor": ["read", "write"],
            "viewer": ["read"],
            "guest": []
        }
        return role_permission_mapping.get(self.role, [])
    
    def get_all_permissions(self) -> List[str]:
        """Get all effective permissions for the user.
        
        Returns:
            List of all permissions
        """
        role_permissions = self.get_role_permissions()
        additional_permissions = []
        if self.permissions and "additional" in self.permissions:
            additional_permissions = self.permissions["additional"]
        
        return list(set(role_permissions + additional_permissions))
    
    def get_display_name(self) -> str:
        """Get user display name.
        
        Returns:
            Display name or email if profile not set
        """
        if self.profile:
            first_name = self.profile.get("first_name", "")
            last_name = self.profile.get("last_name", "")
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()
        return self.email
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for Firebase storage.
        
        Returns:
            Dictionary representation
        """
        data = {
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "login_count": self.login_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        if self.hashed_password:
            data["hashed_password"] = self.hashed_password
        if self.permissions:
            data["permissions"] = self.permissions
        if self.preferences:
            data["preferences"] = self.preferences
        if self.profile:
            data["profile"] = self.profile
        if self.last_login:
            data["last_login"] = self.last_login
            
        return data
    
    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]) -> "User":
        """Create User from dictionary (Firebase data).
        
        Args:
            user_id: Firebase UID
            data: User data dictionary
            
        Returns:
            User instance
        """
        return cls(
            id=user_id,
            email=data.get("email"),
            hashed_password=data.get("hashed_password"),
            role=data.get("role", "viewer"),
            status=data.get("status", "active"),
            permissions=data.get("permissions"),
            preferences=data.get("preferences"),
            profile=data.get("profile"),
            is_verified=data.get("is_verified", False),
            is_active=data.get("is_active", True),
            login_count=data.get("login_count", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            last_login=data.get("last_login")
        )