"""Base response models for Ali API.

This module contains standardized response models used across
the API to ensure consistent response formats.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from pydantic import (
    BaseModel,
    Field,
)

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses."""

    success: bool = Field(description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[T] = Field(None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = Field(False, description="Always false for errors")
    error: str = Field(description="Error type or code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class ValidationErrorResponse(ErrorResponse):
    """Response model for validation errors."""

    error: str = Field("validation_error", description="Error type")
    field_errors: Optional[Dict[str, List[str]]] = Field(
        None, description="Field-specific validation errors"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    success: bool = Field(True, description="Whether the operation was successful")
    data: List[T] = Field(description="List of items")
    pagination: "PaginationInfo" = Field(description="Pagination information")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class PaginationInfo(BaseModel):
    """Pagination information model."""

    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class SuccessResponse(BaseModel):
    """Simple success response model."""

    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(description="Success message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class StatusResponse(BaseModel):
    """Status response model for health checks and status endpoints."""

    status: str = Field(description="Service status")
    version: Optional[str] = Field(None, description="API version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    checks: Optional[Dict[str, Any]] = Field(None, description="Health check results")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""

    success: bool = Field(description="Whether the overall operation was successful")
    processed: int = Field(description="Number of items processed")
    succeeded: int = Field(description="Number of items that succeeded")
    failed: int = Field(description="Number of items that failed")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class AnalyticsResponse(BaseModel):
    """Response model for analytics and statistics."""

    success: bool = Field(True, description="Whether the operation was successful")
    period: Optional[str] = Field(None, description="Analytics period")
    metrics: Dict[str, Any] = Field(description="Analytics metrics")
    trends: Optional[Dict[str, Any]] = Field(None, description="Trend data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


# Update forward references
PaginatedResponse.model_rebuild()
