"""User management schemas for the API.

This module provides schemas for comprehensive user management including
CRUD operations, role-based access control, profile management, and user analytics.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator, HttpUrl


class UserRole(str, Enum):
    """User role enumeration for RBAC."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class Permission(str, Enum):
    """Permission enumeration for fine-grained access control."""
    # Document permissions
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_WRITE = "documents:write"
    DOCUMENTS_DELETE = "documents:delete"
    DOCUMENTS_ADMIN = "documents:admin"
    
    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    USERS_ADMIN = "users:admin"
    
    # Chat permissions
    CHAT_READ = "chat:read"
    CHAT_WRITE = "chat:write"
    CHAT_ADMIN = "chat:admin"
    
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_ADMIN = "analytics:admin"


class UserPreferences(BaseModel):
    """User preferences and settings."""
    
    language: str = Field("pt-BR", description="Preferred language")
    timezone: str = Field("America/Sao_Paulo", description="User timezone")
    theme: str = Field("light", description="UI theme preference")
    notifications_email: bool = Field(True, description="Enable email notifications")
    notifications_browser: bool = Field(True, description="Enable browser notifications")
    default_document_view: str = Field("list", description="Default document view mode")
    items_per_page: int = Field(20, description="Items per page", ge=10, le=100)


class UserProfile(BaseModel):
    """Extended user profile information."""
    
    first_name: Optional[str] = Field(None, description="First name", max_length=50)
    last_name: Optional[str] = Field(None, description="Last name", max_length=50)
    phone: Optional[str] = Field(None, description="Phone number", max_length=20)
    organization: Optional[str] = Field(None, description="Organization", max_length=100)
    department: Optional[str] = Field(None, description="Department", max_length=100)
    job_title: Optional[str] = Field(None, description="Job title", max_length=100)
    bio: Optional[str] = Field(None, description="Biography", max_length=500)
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar image URL")
    website: Optional[HttpUrl] = Field(None, description="Personal website")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile", max_length=100)
    location: Optional[str] = Field(None, description="Location", max_length=100)
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        
        # Remove common formatting characters
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        
        # Basic validation - should be 8-15 digits possibly with + prefix
        if not (8 <= len(cleaned.replace('+', '')) <= 15):
            raise ValueError("Phone number must be between 8 and 15 digits")
        
        return cleaned


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(UserRole.VIEWER, description="User role")
    status: UserStatus = Field(UserStatus.ACTIVE, description="User status")
    permissions: List[Permission] = Field(default_factory=list, description="Additional permissions")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    profile: UserProfile = Field(default_factory=UserProfile, description="User profile")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., description="User password", min_length=8, max_length=128)
    send_welcome_email: bool = Field(True, description="Send welcome email to user")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase, lowercase, digit, and special character
        import re
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    role: Optional[UserRole] = Field(None, description="User role")
    status: Optional[UserStatus] = Field(None, description="User status")
    permissions: Optional[List[Permission]] = Field(None, description="Additional permissions")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")
    profile: Optional[UserProfile] = Field(None, description="User profile")


class UserResponse(UserBase):
    """Schema for user responses."""
    
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(0, description="Total login count")
    is_verified: bool = Field(False, description="Email verification status")
    is_active: bool = Field(True, description="Active status")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar URL")
    full_name: Optional[str] = Field(None, description="Full name")
    
    # Computed fields
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        if self.profile.first_name or self.profile.last_name:
            return f"{self.profile.first_name or ''} {self.profile.last_name or ''}".strip()
        return self.email.split('@')[0]


class UserListResponse(BaseModel):
    """Schema for paginated user list responses."""
    
    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total user count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class UserSearchRequest(BaseModel):
    """Schema for user search requests."""
    
    query: Optional[str] = Field(None, description="Search query", max_length=100)
    role: Optional[UserRole] = Field(None, description="Filter by role")
    status: Optional[UserStatus] = Field(None, description="Filter by status")
    organization: Optional[str] = Field(None, description="Filter by organization")
    department: Optional[str] = Field(None, description="Filter by department")
    date_from: Optional[datetime] = Field(None, description="Filter from creation date")
    date_to: Optional[datetime] = Field(None, description="Filter to creation date")
    last_login_from: Optional[datetime] = Field(None, description="Filter by last login from")
    last_login_to: Optional[datetime] = Field(None, description="Filter by last login to")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(20, description="Page size", ge=1, le=100)
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort field."""
        allowed_fields = [
            "id", "email", "created_at", "updated_at", "last_login", 
            "login_count", "role", "status", "first_name", "last_name"
        ]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class UserBulkOperation(BaseModel):
    """Schema for bulk user operations."""
    
    user_ids: List[int] = Field(..., description="User IDs", min_items=1, max_items=100)
    operation: str = Field(..., description="Operation type")
    
    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        allowed_operations = [
            "activate", "deactivate", "suspend", "delete", 
            "change_role", "add_permissions", "remove_permissions",
            "send_welcome_email", "reset_password"
        ]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v


class UserBulkUpdate(UserBulkOperation):
    """Schema for bulk user updates."""
    
    role: Optional[UserRole] = Field(None, description="New role for change_role operation")
    permissions: Optional[List[Permission]] = Field(None, description="Permissions for add/remove operations")
    send_email: bool = Field(False, description="Send notification email")


class UserBulkResponse(BaseModel):
    """Schema for bulk operation responses."""
    
    success: bool = Field(..., description="Overall operation success")
    processed_count: int = Field(..., description="Number of users processed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    message: str = Field(..., description="Response message")


class UserStats(BaseModel):
    """Schema for user statistics."""
    
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    new_users_today: int = Field(..., description="New users today")
    new_users_week: int = Field(..., description="New users this week")
    new_users_month: int = Field(..., description="New users this month")
    by_role: dict = Field(..., description="Users count by role")
    by_status: dict = Field(..., description="Users count by status")
    by_organization: dict = Field(..., description="Users count by organization")
    login_stats: dict = Field(..., description="Login statistics")
    growth_trend: List[dict] = Field(..., description="User growth trend")


class UserActivity(BaseModel):
    """Schema for user activity tracking."""
    
    id: int = Field(..., description="Activity ID")
    user_id: int = Field(..., description="User ID")
    activity_type: str = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(..., description="Activity timestamp")


class UserActivityResponse(BaseModel):
    """Schema for user activity responses."""
    
    activities: List[UserActivity] = Field(..., description="List of activities")
    total_count: int = Field(..., description="Total activity count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_more: bool = Field(..., description="Whether there are more activities")


class UserPermissionCheck(BaseModel):
    """Schema for permission check requests."""
    
    permission: Permission = Field(..., description="Permission to check")
    resource_id: Optional[str] = Field(None, description="Resource ID (optional)")


class UserPermissionResponse(BaseModel):
    """Schema for permission check responses."""
    
    has_permission: bool = Field(..., description="Whether user has permission")
    effective_permissions: List[Permission] = Field(..., description="All effective permissions")
    role_permissions: List[Permission] = Field(..., description="Permissions from role")
    additional_permissions: List[Permission] = Field(..., description="Additional permissions")


class UserInvitation(BaseModel):
    """Schema for user invitations."""
    
    email: EmailStr = Field(..., description="Invitation email")
    role: UserRole = Field(UserRole.VIEWER, description="Invited user role")
    permissions: List[Permission] = Field(default_factory=list, description="Additional permissions")
    message: Optional[str] = Field(None, description="Invitation message", max_length=500)
    expires_at: Optional[datetime] = Field(None, description="Invitation expiry")


class UserInvitationResponse(BaseModel):
    """Schema for user invitation responses."""
    
    id: str = Field(..., description="Invitation ID")
    email: EmailStr = Field(..., description="Invitation email")
    role: UserRole = Field(..., description="Invited role")
    status: str = Field(..., description="Invitation status")
    invited_by: int = Field(..., description="ID of user who sent invitation")
    invited_at: datetime = Field(..., description="Invitation timestamp")
    expires_at: datetime = Field(..., description="Invitation expiry")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=8, max_length=128)
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        import re
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v


class MessageResponse(BaseModel):
    """Generic response schema for simple operations."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")
    data: Optional[dict] = Field(None, description="Additional response data")