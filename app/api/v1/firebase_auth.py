"""Firebase Authentication endpoints.

This module provides Firebase Authentication integration endpoints for user
registration, login, token verification, and profile management.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, EmailStr

from app.core.limiter import limiter
from app.core.logging import logger
from app.core.config import settings
from app.services.firebase_auth import firebase_auth_service
from app.infrastructure.firestore.user_repository import FirestoreUserRepository
from app.shared.middleware.firebase_auth import (
    firebase_auth_required,
    get_current_user,
    get_current_user_id
)
from app.shared.exceptions.auth import AuthenticationError

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize repositories
user_repo = FirestoreUserRepository()


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    role: str = "viewer"


class LoginResponse(BaseModel):
    """Login response with user info."""
    message: str
    instructions: str


class UserProfileResponse(BaseModel):
    """User profile response."""
    uid: str
    email: str
    display_name: Optional[str]
    email_verified: bool
    role: str
    permissions: Dict[str, Any]
    profile: Optional[Dict[str, Any]]
    created_at: Optional[str]


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    display_name: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


@router.post("/register", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(request: Request, user_data: RegisterRequest):
    """Register a new user with Firebase Auth.
    
    This endpoint creates a user in Firebase Auth and creates their
    profile in Firestore.
    """
    try:
        logger.info(f"Registering new user: {user_data.email}")
        
        # Create user in Firebase Auth
        firebase_uid = await firebase_auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name,
            role=user_data.role
        )
        
        # Create user profile in Firestore
        user_profile = {
            'id': firebase_uid,
            'email': user_data.email,
            'role': user_data.role,
            'status': 'active',
            'is_verified': False,
            'is_active': True,
            'permissions': {},
            'preferences': {},
            'profile': {'display_name': user_data.display_name} if user_data.display_name else {},
            'login_count': 0
        }
        
        await user_repo.create(user_profile, firebase_uid)
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return MessageResponse(
            message="User registered successfully. Please verify your email address."
        )
        
    except Exception as e:
        logger.error(f"Registration failed for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request):
    """Login endpoint - Firebase Auth handles authentication.
    
    Since Firebase Auth is handled client-side, this endpoint provides
    instructions for frontend authentication.
    """
    return LoginResponse(
        message="Use Firebase Auth client SDK for authentication",
        instructions=(
            "1. Use Firebase Auth signInWithEmailAndPassword() on frontend\n"
            "2. Get ID token from Firebase\n" 
            "3. Send token in Authorization header: 'Bearer <id-token>'\n"
            "4. Use /auth/verify to validate token server-side"
        )
    )


@router.post("/verify", response_model=UserProfileResponse)
@limiter.limit("100 per minute")
async def verify_token(request: Request, user: dict = Depends(firebase_auth_required)):
    """Verify Firebase ID token and return user profile.
    
    This endpoint verifies the Firebase ID token and returns the user's
    profile information from Firestore.
    """
    try:
        user_id = user.get('uid')
        
        # Get user profile from Firestore
        user_profile = await user_repo.get_by_id(user_id)
        
        if not user_profile:
            # Create profile if it doesn't exist (for existing Firebase users)
            user_profile = {
                'id': user_id,
                'email': user.get('email'),
                'role': user.get('custom_claims', {}).get('role', 'viewer'),
                'status': 'active',
                'is_verified': user.get('email_verified', False),
                'is_active': True,
                'permissions': user.get('custom_claims', {}).get('permissions', {}),
                'preferences': {},
                'profile': {},
                'login_count': 0
            }
            await user_repo.create(user_profile, user_id)
        
        # Update last login
        await user_repo.update_last_login(user_id)
        
        return UserProfileResponse(
            uid=user_id,
            email=user.get('email'),
            display_name=user_profile.get('profile', {}).get('display_name'),
            email_verified=user.get('email_verified', False),
            role=user_profile.get('role', 'viewer'),
            permissions=user_profile.get('permissions', {}),
            profile=user_profile.get('profile'),
            created_at=user_profile.get('created_at').isoformat() if user_profile.get('created_at') else None
        )
        
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(request: Request, user: dict = Depends(firebase_auth_required)):
    """Get current user's profile."""
    try:
        user_id = user.get('uid')
        user_profile = await user_repo.get_by_id(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfileResponse(
            uid=user_id,
            email=user.get('email'),
            display_name=user_profile.get('profile', {}).get('display_name'),
            email_verified=user.get('email_verified', False),
            role=user_profile.get('role', 'viewer'),
            permissions=user_profile.get('permissions', {}),
            profile=user_profile.get('profile'),
            created_at=user_profile.get('created_at').isoformat() if user_profile.get('created_at') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.put("/profile", response_model=MessageResponse)
async def update_profile(
    request: Request,
    profile_data: UpdateProfileRequest,
    user: dict = Depends(firebase_auth_required)
):
    """Update current user's profile."""
    try:
        user_id = user.get('uid')
        
        # Prepare update data
        update_data = {}
        
        if profile_data.profile is not None:
            update_data['profile'] = profile_data.profile
        if profile_data.preferences is not None:
            update_data['preferences'] = profile_data.preferences
        
        # Update display name in Firebase Auth if provided
        if profile_data.display_name is not None:
            await firebase_auth_service.update_user(
                user_id,
                display_name=profile_data.display_name
            )
            
            # Also update in profile
            if 'profile' not in update_data:
                update_data['profile'] = {}
            update_data['profile']['display_name'] = profile_data.display_name
        
        # Update profile in Firestore
        if update_data:
            await user_repo.update(user_id, update_data)
        
        logger.info(f"Profile updated for user: {user_id}")
        
        return MessageResponse(message="Profile updated successfully")
        
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/password-reset", response_model=MessageResponse)
@limiter.limit("5 per hour")
async def request_password_reset(request: Request, reset_request: PasswordResetRequest):
    """Request password reset email via Firebase Auth."""
    try:
        # Generate password reset link
        reset_link = await firebase_auth_service.generate_password_reset_link(
            reset_request.email
        )
        
        logger.info(f"Password reset requested for: {reset_request.email}")
        
        # In production, you would send this link via email
        # For now, we'll just log it
        logger.info(f"Password reset link: {reset_link}")
        
        return MessageResponse(
            message="Password reset email sent if the email address is registered"
        )
        
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        # Don't reveal whether email exists
        return MessageResponse(
            message="Password reset email sent if the email address is registered"
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    request: Request,
    user: dict = Depends(firebase_auth_required)
):
    """Resend email verification."""
    try:
        email = user.get('email')
        
        # Generate email verification link
        verification_link = await firebase_auth_service.generate_email_verification_link(email)
        
        logger.info(f"Email verification resent for: {email}")
        logger.info(f"Verification link: {verification_link}")
        
        return MessageResponse(
            message="Verification email sent"
        )
        
    except Exception as e:
        logger.error(f"Failed to resend verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    request: Request,
    user: dict = Depends(firebase_auth_required)
):
    """Delete current user's account."""
    try:
        user_id = user.get('uid')
        
        # Delete user profile from Firestore
        await user_repo.delete(user_id)
        
        # Delete user from Firebase Auth
        await firebase_auth_service.delete_user(user_id)
        
        logger.info(f"Account deleted for user: {user_id}")
        
        return MessageResponse(message="Account deleted successfully")
        
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request):
    """Logout endpoint - Firebase Auth handles token invalidation client-side."""
    return MessageResponse(
        message="Use Firebase Auth signOut() on frontend to invalidate tokens"
    )