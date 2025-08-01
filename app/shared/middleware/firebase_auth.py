"""Firebase Authentication middleware.

This module provides middleware for Firebase token verification and user context
management in FastAPI requests.
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.firebase_auth import firebase_auth_service
from app.shared.exceptions.auth import AuthenticationError


class FirebaseAuthMiddleware:
    """Firebase authentication middleware."""
    
    def __init__(self, auto_error: bool = True):
        """Initialize Firebase auth middleware.
        
        Args:
            auto_error: Whether to automatically raise HTTP errors
        """
        self.auto_error = auto_error
        self.bearer = HTTPBearer(auto_error=auto_error)
    
    async def __call__(
        self, 
        request: Request, 
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Optional[dict]:
        """Verify Firebase token and set user context.
        
        Args:
            request: FastAPI request object
            credentials: HTTP authorization credentials
            
        Returns:
            Optional[dict]: Decoded token with user claims
            
        Raises:
            HTTPException: If authentication fails and auto_error is True
        """
        if credentials is None:
            credentials = await self.bearer(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        try:
            # Verify the Firebase token
            decoded_token = await firebase_auth_service.verify_token(
                credentials.credentials
            )
            
            # Add user context to request state
            request.state.user = decoded_token
            request.state.user_id = decoded_token.get('uid')
            request.state.user_email = decoded_token.get('email')
            
            return decoded_token
            
        except AuthenticationError as e:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None


# Global middleware instances
firebase_auth_required = FirebaseAuthMiddleware(auto_error=True)
firebase_auth_optional = FirebaseAuthMiddleware(auto_error=False)


async def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Current user data
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.user


async def get_current_user_id(request: Request) -> str:
    """Get current authenticated user ID from request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Current user ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = await get_current_user(request)
    return user.get('uid')


async def get_current_user_email(request: Request) -> str:
    """Get current authenticated user email from request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Current user email
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = await get_current_user(request)
    return user.get('email')


def require_role(required_role: str):
    """Decorator to require specific role for endpoint access.
    
    Args:
        required_role: Required user role
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            user_role = user.get('custom_claims', {}).get('role', 'viewer')
            
            # Admin has access to everything
            if user_role == 'admin':
                return await func(request, *args, **kwargs)
            
            # Check specific role
            if user_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(required_permission: str):
    """Decorator to require specific permission for endpoint access.
    
    Args:
        required_permission: Required permission
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            custom_claims = user.get('custom_claims', {})
            
            # Admin has all permissions
            if custom_claims.get('role') == 'admin':
                return await func(request, *args, **kwargs)
            
            # Check specific permission
            permissions = custom_claims.get('permissions', [])
            if required_permission not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission}' required"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator