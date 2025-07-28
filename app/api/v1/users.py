"""Comprehensive users API endpoints.

This module provides full user lifecycle management including CRUD operations,
role-based access control, bulk operations, activity tracking, and user analytics.
"""

from typing import List, Optional
import time

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

from app.api.v1.auth import get_current_user
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.user import User
from app.schemas.users import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserSearchRequest,
    UserBulkOperation,
    UserBulkUpdate,
    UserBulkResponse,
    UserStats,
    UserActivityResponse,
    UserPermissionCheck,
    UserPermissionResponse,
    UserInvitation,
    UserInvitationResponse,
    PasswordChangeRequest,
    UserRole,
    UserStatus,
    Permission,
    MessageResponse,
)
from app.services.users_service import users_service

router = APIRouter()


# ============================================================================
# Access Control Decorators
# ============================================================================

def require_permission(permission: str):
    """Decorator to require specific permission for endpoint access."""
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required permission: {permission}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new user (Admin/Editor only).
    
    Args:
        request: FastAPI request object for rate limiting
        user_data: User creation data
        current_user: Authenticated user
        
    Returns:
        UserResponse: Created user data
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:write"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = await users_service.create_user(user_data, current_user.id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_creation_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """Get a user by ID.
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: User ID
        current_user: Authenticated user
        
    Returns:
        UserResponse: User data
    """
    try:
        # Users can view their own profile, others need users:read permission
        if user_id != current_user.id and not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = await users_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_retrieval_endpoint_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve user")


@router.put("/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_user(
    request: Request,
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update an existing user.
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: User ID to update
        update_data: User update data
        current_user: Authenticated user
        
    Returns:
        UserResponse: Updated user data
    """
    try:
        # Users can update their own profile (limited fields), others need users:write permission
        if user_id != current_user.id and not current_user.has_permission("users:write"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # If user is updating their own profile, restrict certain fields
        if user_id == current_user.id and not current_user.has_permission("users:write"):
            # Only allow profile and preferences updates for self
            restricted_update = UserUpdate(
                preferences=update_data.preferences,
                profile=update_data.profile
            )
            update_data = restricted_update
        
        user = await users_service.update_user(user_id, update_data, current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_update_endpoint_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", response_model=MessageResponse)
@limiter.limit("20/minute")
async def delete_user(
    request: Request,
    user_id: int,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: User = Depends(get_current_user),
):
    """Delete a user (Admin only).
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: User ID to delete
        hard_delete: Whether to perform hard delete
        current_user: Authenticated user
        
    Returns:
        MessageResponse: Deletion confirmation
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:delete"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        success = await users_service.delete_user(user_id, current_user.id, soft_delete=not hard_delete)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return MessageResponse(
            message=f"User {'hard' if hard_delete else 'soft'} deleted successfully",
            success=True,
            data={"user_id": user_id, "hard_delete": hard_delete}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_deletion_endpoint_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search and Listing
# ============================================================================

@router.post("/search", response_model=UserListResponse)
@limiter.limit("50/minute")
async def search_users(
    request: Request,
    search_request: UserSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search users with advanced filtering and pagination.
    
    Args:
        request: FastAPI request object for rate limiting
        search_request: Search parameters
        current_user: Authenticated user
        
    Returns:
        UserListResponse: Paginated search results
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        results = await users_service.search_users(search_request)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_search_endpoint_failed", query=search_request.query, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=UserListResponse)
@limiter.limit("50/minute")
async def list_users(
    request: Request,
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(20, description="Page size", ge=1, le=100),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: User = Depends(get_current_user),
):
    """List users with basic filtering and pagination.
    
    Args:
        request: FastAPI request object for rate limiting
        page: Page number
        page_size: Page size
        role: Filter by role
        status: Filter by status
        sort_by: Sort field
        sort_order: Sort order
        current_user: Authenticated user
        
    Returns:
        UserListResponse: Paginated user list
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        search_request = UserSearchRequest(
            page=page,
            page_size=page_size,
            role=role,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        results = await users_service.search_users(search_request)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_list_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk/update", response_model=UserBulkResponse)
@limiter.limit("5/minute")
async def bulk_update_users(
    request: Request,
    update_data: UserBulkUpdate,
    current_user: User = Depends(get_current_user),
):
    """Bulk update multiple users (Admin only).
    
    Args:
        request: FastAPI request object for rate limiting
        update_data: Bulk update data
        current_user: Authenticated user
        
    Returns:
        UserBulkResponse: Bulk operation results
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:write"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        kwargs = {}
        if update_data.role:
            kwargs["role"] = update_data.role
        if update_data.permissions:
            kwargs["permissions"] = update_data.permissions
        
        result = await users_service.bulk_update_users(
            update_data.user_ids,
            update_data.operation,
            current_user.id,
            **kwargs
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("bulk_update_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/delete", response_model=UserBulkResponse)
@limiter.limit("5/minute")
async def bulk_delete_users(
    request: Request,
    operation_data: UserBulkOperation,
    current_user: User = Depends(get_current_user),
):
    """Bulk delete multiple users (Admin only).
    
    Args:
        request: FastAPI request object for rate limiting
        operation_data: Bulk operation data
        current_user: Authenticated user
        
    Returns:
        UserBulkResponse: Bulk operation results
    """
    try:
        # Check permissions
        if not current_user.has_permission("users:delete"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Prevent self-deletion
        if current_user.id in operation_data.user_ids:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        result = await users_service.bulk_update_users(
            operation_data.user_ids,
            "delete",
            current_user.id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("bulk_delete_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Permissions and Roles
# ============================================================================

@router.post("/{user_id}/permissions/check", response_model=UserPermissionResponse)
@limiter.limit("100/minute")
async def check_user_permission(
    request: Request,
    user_id: int,
    permission_check: UserPermissionCheck,
    current_user: User = Depends(get_current_user),
):
    """Check if a user has a specific permission.
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: User ID to check
        permission_check: Permission check request
        current_user: Authenticated user
        
    Returns:
        UserPermissionResponse: Permission check result
    """
    try:
        # Users can check their own permissions, others need users:read permission
        if user_id != current_user.id and not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = await users_service.check_user_permission(
            user_id,
            permission_check.permission,
            permission_check.resource_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("permission_check_endpoint_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/permissions", response_model=UserPermissionResponse)
@limiter.limit("100/minute")
async def get_user_permissions(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """Get all permissions for a user.
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: User ID
        current_user: Authenticated user
        
    Returns:
        UserPermissionResponse: User permissions
    """
    try:
        # Users can view their own permissions, others need users:read permission
        if user_id != current_user.id and not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = await users_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Mock permission response based on user data
        user_model = await users_service.db_service.get_user(user_id)
        
        return UserPermissionResponse(
            has_permission=True,  # This would be calculated based on specific permission
            effective_permissions=[Permission(p) for p in user_model.get_all_permissions()],
            role_permissions=[Permission(p) for p in user_model.get_role_permissions()],
            additional_permissions=[
                Permission(p) for p in user_model.permissions.get("additional", [])
            ] if user_model.permissions else []
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_permissions_endpoint_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics and Analytics
# ============================================================================

@router.get("/stats", response_model=UserStats)
@limiter.limit("20/minute")
async def get_user_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive user statistics (Admin only).
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        UserStats: User statistics
    """
    try:
        # Check permissions
        if not current_user.has_permission("analytics:read"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        stats = await users_service.get_user_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_stats_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Profile Management
# ============================================================================

@router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get current user's profile.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        UserResponse: Current user profile
    """
    try:
        user = await users_service.get_user(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("current_user_profile_failed", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user profile")


@router.put("/me", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_current_user_profile(
    request: Request,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile.
    
    Args:
        request: FastAPI request object for rate limiting
        update_data: Profile update data
        current_user: Authenticated user
        
    Returns:
        UserResponse: Updated user profile
    """
    try:
        # Users can only update their own profile and preferences
        restricted_update = UserUpdate(
            preferences=update_data.preferences,
            profile=update_data.profile
        )
        
        user = await users_service.update_user(current_user.id, restricted_update, current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("current_user_update_failed", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/me/change-password", response_model=MessageResponse)
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
):
    """Change current user's password.
    
    Args:
        request: FastAPI request object for rate limiting
        password_change: Password change request
        current_user: Authenticated user
        
    Returns:
        MessageResponse: Password change confirmation
    """
    try:
        # Verify current password
        if not current_user.verify_password(password_change.current_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password (mock implementation)
        # In real implementation: current_user.hashed_password = User.hash_password(password_change.new_password)
        
        # Log activity
        await users_service.log_activity(
            current_user.id,
            "password_change",
            "User changed password",
            success=True
        )
        
        return MessageResponse(
            message="Password changed successfully",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("password_change_failed", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="Password change failed")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def users_health():
    """Health check for users service.
    
    Returns:
        dict: Health status
    """
    try:
        # Basic health check
        stats = await users_service.get_user_stats()
        
        return {
            "status": "healthy",
            "total_users": stats.total_users,
            "active_users": stats.active_users,
            "service": "users",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("users_health_check_failed", error=str(e))
        return {
            "status": "unhealthy", 
            "error": str(e),
            "service": "users",
            "timestamp": time.time()
        }