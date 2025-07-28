"""This file contains the chat schema for the application."""

import re
from datetime import datetime
from typing import (
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class Message(BaseModel):
    """Message model for chat endpoint.

    Attributes:
        role: The role of the message sender (user or assistant).
        content: The content of the message.
    """

    model_config = {"extra": "ignore"}

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="The role of the message sender"
    )
    content: str = Field(
        ...,
        description="The content of the message",
        min_length=1,
        max_length=3000,
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate the message content.

        Args:
            v: The content to validate

        Returns:
            str: The validated content

        Raises:
            ValueError: If the content contains disallowed patterns
        """
        # Check for potentially harmful content
        if re.search(r"<script.*?>.*?</script>", v, re.IGNORECASE | re.DOTALL):
            raise ValueError(
                "Content contains potentially harmful script tags"
            )

        # Check for null bytes
        if "\0" in v:
            raise ValueError("Content contains null bytes")

        return v


class ChatRequest(BaseModel):
    """Request model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
    """

    messages: List[Message] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
    """

    messages: List[Message] = Field(
        ..., description="List of messages in the conversation"
    )


class StreamResponse(BaseModel):
    """Response model for streaming chat endpoint.

    Attributes:
        content: The content of the current chunk.
        done: Whether the stream is complete.
    """

    content: str = Field(
        default="", description="The content of the current chunk"
    )
    done: bool = Field(
        default=False, description="Whether the stream is complete"
    )


class DetailedMessage(BaseModel):
    """Enhanced message model with metadata and metrics.
    
    Attributes:
        id: Message ID
        role: Message role
        content: Message content
        timestamp: Message timestamp
        session_id: Session ID
        user_id: User ID
        tokens: Token count
        processing_time: Processing time in seconds
        model_used: AI model used
        context_documents: Related documents used
        confidence_score: AI confidence score
    """
    
    id: str = Field(..., description="Message ID")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    session_id: str = Field(..., description="Session ID")
    user_id: int = Field(..., description="User ID")
    tokens: int = Field(0, description="Token count")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    model_used: Optional[str] = Field(None, description="AI model used")
    context_documents: List[str] = Field(default_factory=list, description="Related document IDs")
    confidence_score: Optional[float] = Field(None, description="AI confidence score", ge=0.0, le=1.0)


class ChatHistoryRequest(BaseModel):
    """Request model for chat history retrieval.
    
    Attributes:
        limit: Maximum number of messages
        offset: Message offset for pagination
        date_from: Filter from date
        date_to: Filter to date
        include_metadata: Include message metadata
    """
    
    limit: int = Field(50, description="Maximum messages", ge=1, le=500)
    offset: int = Field(0, description="Message offset", ge=0)
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    include_metadata: bool = Field(False, description="Include message metadata")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history.
    
    Attributes:
        messages: List of messages
        total_count: Total message count
        has_more: Whether there are more messages
        session_info: Session information
    """
    
    messages: List[DetailedMessage] = Field(..., description="Messages")
    total_count: int = Field(..., description="Total message count")
    has_more: bool = Field(..., description="Whether there are more messages")
    session_info: dict = Field(..., description="Session information")


class ChatSearchRequest(BaseModel):
    """Request model for searching chat history.
    
    Attributes:
        query: Search query
        session_ids: Filter by session IDs
        user_id: Filter by user ID
        date_from: Filter from date
        date_to: Filter to date
        limit: Maximum results
        include_content: Include message content in results
    """
    
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    session_ids: Optional[List[str]] = Field(None, description="Filter by session IDs")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: int = Field(20, description="Maximum results", ge=1, le=100)
    include_content: bool = Field(True, description="Include message content")


class ChatSearchResult(BaseModel):
    """Search result for chat messages.
    
    Attributes:
        message: Message data
        relevance_score: Search relevance score
        context_snippet: Content snippet with highlights
        session_name: Session name
    """
    
    message: DetailedMessage = Field(..., description="Message data")
    relevance_score: float = Field(..., description="Search relevance score", ge=0.0, le=1.0)
    context_snippet: str = Field(..., description="Content snippet with highlights")
    session_name: str = Field(..., description="Session name")


class ChatMetrics(BaseModel):
    """Chat metrics and analytics.
    
    Attributes:
        total_messages: Total message count
        total_sessions: Total session count
        avg_messages_per_session: Average messages per session
        avg_response_time: Average AI response time
        most_active_users: Most active user IDs
        popular_topics: Popular conversation topics
        model_usage: Usage by AI model
        daily_stats: Daily message statistics
        token_usage: Token consumption statistics
    """
    
    total_messages: int = Field(..., description="Total message count")
    total_sessions: int = Field(..., description="Total session count")
    avg_messages_per_session: float = Field(..., description="Average messages per session")
    avg_response_time: float = Field(..., description="Average AI response time in seconds")
    most_active_users: List[dict] = Field(..., description="Most active users")
    popular_topics: List[dict] = Field(..., description="Popular conversation topics")
    model_usage: dict = Field(..., description="Usage by AI model")
    daily_stats: List[dict] = Field(..., description="Daily message statistics")
    token_usage: dict = Field(..., description="Token consumption statistics")


class ChatExportRequest(BaseModel):
    """Request model for chat export.
    
    Attributes:
        format: Export format (json, csv, txt)
        session_ids: Filter by session IDs
        user_id: Filter by user ID
        date_from: Filter from date
        date_to: Filter to date
        include_metadata: Include message metadata
        include_system_messages: Include system messages
    """
    
    format: Literal["json", "csv", "txt"] = Field("json", description="Export format")
    session_ids: Optional[List[str]] = Field(None, description="Filter by session IDs")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    include_metadata: bool = Field(True, description="Include message metadata")
    include_system_messages: bool = Field(False, description="Include system messages")


class ChatExportResponse(BaseModel):
    """Response model for chat export.
    
    Attributes:
        success: Export success status
        file_url: Download URL for exported file
        file_size: File size in bytes
        message_count: Number of exported messages
        export_format: Export format used
        expires_at: File expiration timestamp
    """
    
    success: bool = Field(..., description="Export success status")
    file_url: str = Field(..., description="Download URL")
    file_size: int = Field(..., description="File size in bytes")
    message_count: int = Field(..., description="Number of exported messages")
    export_format: str = Field(..., description="Export format used")
    expires_at: datetime = Field(..., description="File expiration timestamp")


class AIInsight(BaseModel):
    """AI-generated insights about chat patterns.
    
    Attributes:
        insight_type: Type of insight
        title: Insight title
        description: Insight description
        confidence: Confidence score
        data: Supporting data
        generated_at: Generation timestamp
    """
    
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    data: dict = Field(..., description="Supporting data")
    generated_at: datetime = Field(..., description="Generation timestamp")


class ChatInsightsResponse(BaseModel):
    """Response model for chat insights.
    
    Attributes:
        insights: List of AI insights
        summary: Overall summary
        recommendations: AI recommendations
        generated_at: Analysis timestamp
    """
    
    insights: List[AIInsight] = Field(..., description="List of AI insights")
    summary: str = Field(..., description="Overall summary")
    recommendations: List[str] = Field(..., description="AI recommendations")
    generated_at: datetime = Field(..., description="Analysis timestamp")
