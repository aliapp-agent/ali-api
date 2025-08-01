"""User activity tracking model."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, JSON, Column

from app.models.base import BaseModel


class UserActivity(BaseModel, table=True):
    """Model for tracking user activities and audit logs.
    
    Attributes:
        id: Primary key
        user_id: ID of the user who performed the activity
        activity_type: Type of activity (login, logout, document_create, etc.)
        description: Human-readable description of the activity
        activity_metadata: Additional metadata as JSON object
        ip_address: IP address from which the activity was performed
        user_agent: User agent string
        session_id: Session ID if applicable
        resource_type: Type of resource affected (user, document, etc.)
        resource_id: ID of the affected resource
        success: Whether the activity was successful
        created_at: Timestamp when the activity occurred
    """
    
    __tablename__ = "user_activities"
    
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="User who performed the activity")
    activity_type: str = Field(index=True, description="Type of activity")
    description: str = Field(description="Human-readable description")
    
    # Additional data
    activity_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 support
    user_agent: Optional[str] = Field(default=None, max_length=500)
    session_id: Optional[str] = Field(default=None, index=True)
    
    # Resource information
    resource_type: Optional[str] = Field(default=None, index=True)
    resource_id: Optional[str] = Field(default=None, index=True)
    
    # Status
    success: bool = Field(default=True, index=True)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class UserInvitation(BaseModel, table=True):
    """Model for user invitations.
    
    Attributes:
        id: Primary key (UUID string)
        email: Email address of the invited user
        role: Role to assign to the invited user
        permissions: Additional permissions as JSON array
        message: Optional invitation message
        status: Invitation status (pending, accepted, expired, revoked)
        invited_by: ID of the user who sent the invitation
        invited_at: Timestamp when invitation was sent
        expires_at: Timestamp when invitation expires
        accepted_at: Timestamp when invitation was accepted
        accepted_by: ID of the user who accepted (for tracking)
        token: Unique token for accepting the invitation
    """
    
    __tablename__ = "user_invitations"
    
    id: str = Field(primary_key=True, description="Invitation UUID")
    email: str = Field(index=True, description="Invited email address")
    role: str = Field(default="viewer", description="Role to assign")
    permissions: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    message: Optional[str] = Field(default=None, max_length=500)
    
    # Status tracking
    status: str = Field(default="pending", index=True)  # pending, accepted, expired, revoked
    
    # User relationships
    invited_by: int = Field(index=True, description="User who sent invitation")
    accepted_by: Optional[int] = Field(default=None, description="User who accepted")
    
    # Timestamps
    invited_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: datetime = Field(index=True, description="Expiration timestamp")
    accepted_at: Optional[datetime] = Field(default=None, description="Acceptance timestamp")
    
    # Security
    token: str = Field(unique=True, index=True, description="Unique acceptance token")
    
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_pending(self) -> bool:
        """Check if the invitation is still pending."""
        return self.status == "pending" and not self.is_expired()
    
    def can_be_accepted(self) -> bool:
        """Check if the invitation can be accepted."""
        return self.status == "pending" and not self.is_expired()


class UserSession(BaseModel, table=True):
    """Model for tracking user sessions (web sessions, not chat sessions).
    
    Attributes:
        id: Primary key
        user_id: ID of the user
        session_token: Unique session token
        ip_address: IP address
        user_agent: User agent string
        created_at: Session creation time
        last_activity: Last activity timestamp
        expires_at: Session expiration time
        is_active: Whether session is active
        device_info: Device information as JSON
    """
    
    __tablename__ = "user_sessions"
    
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="Session owner")
    session_token: str = Field(unique=True, index=True, description="Unique session token")
    
    # Connection info
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_activity: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: datetime = Field(index=True, description="Session expiration")
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Additional info
    device_info: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the session is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()