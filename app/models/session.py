"""Session model definitions."""

from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field


class Session(BaseModel):
    """Session model for user sessions."""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Firebase user UID")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last session update")
    expires_at: Optional[datetime] = Field(None, description="Session expiration timestamp")
    is_active: bool = Field(True, description="Whether session is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    
    @property
    def id(self) -> str:
        """Return session_id as id for compatibility."""
        return self.session_id
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }