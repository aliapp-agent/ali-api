# agno_state.py

import re
import uuid

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class AgnoState(BaseModel):
    """State definition for the Agno Agent."""

    messages: list = Field(
        default_factory=list, description="The messages in the conversation"
    )
    session_id: str = Field(
        ..., description="The unique identifier for the conversation session"
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            if not re.match(r"^[a-zA-Z0-9_\\-]+$", v):
                raise ValueError(
                    "Session ID must contain only alphanumeric characters, underscores, and hyphens"
                )
            return v
