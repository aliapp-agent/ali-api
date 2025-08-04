"""User activity model definitions."""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """User activity types."""
    
    LOGIN = "login"
    LOGOUT = "logout"
    CHAT = "chat"
    DOCUMENT_UPLOAD = "document_upload"
    SEARCH = "search"
    API_CALL = "api_call"


class UserActivity(BaseModel):
    """User activity tracking model."""
    
    activity_id: str = Field(..., description="Unique activity identifier")
    user_id: str = Field(..., description="Firebase user UID")
    activity_type: ActivityType = Field(..., description="Type of activity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Activity timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional activity data")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserSession(BaseModel):
    """User session activity model."""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="Firebase user UID")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    duration_seconds: Optional[int] = Field(None, description="Session duration in seconds")
    activities_count: int = Field(0, description="Number of activities in session")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }