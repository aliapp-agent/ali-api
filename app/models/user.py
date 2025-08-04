"""User model definitions."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for Firebase authentication."""
    
    uid: str = Field(..., description="Firebase UID")
    email: str = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="User display name")
    photo_url: Optional[str] = Field(None, description="User photo URL")
    phone_number: Optional[str] = Field(None, description="User phone number")
    disabled: bool = Field(False, description="Whether user is disabled")
    email_verified: bool = Field(False, description="Whether email is verified")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }