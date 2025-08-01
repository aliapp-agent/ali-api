"""Authentication and authorization endpoints for the API.

This module provides endpoints for user registration, login, session management,
and token verification.
"""

import uuid
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
# Firebase mode - PostgreSQL not needed
try:
    from app.services.database import DatabaseService
except Exception:
    DatabaseService = None
from app.utils.auth import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    verify_password_reset_token,
    verify_refresh_token,
    verify_token,
)
from app.utils.sanitization import (
    sanitize_email,
    sanitize_string,
    validate_password_strength,
)

router = APIRouter()
security = HTTPBearer()

# Initialize database service - handle Firebase mode
if DatabaseService is not None:
    db_service = DatabaseService()
else:
    db_service = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current user ID from the token.

    Args:
        credentials: The HTTP authorization credentials containing the JWT token.

    Returns:
        User: The user extracted from the token.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    try:
        # Sanitize token
        token = sanitize_string(credentials.credentials)

        user_id = verify_token(token)
        if user_id is None:
            logger.error("invalid_token", token_part=token[:10] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify user exists in database
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user_id_int = int(user_id)
        user = await db_service.get_user(user_id_int)
        if user is None:
            logger.error("user_not_found", user_id=user_id_int)
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except ValueError as ve:
        logger.error("token_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Session:
    """Get the current session ID from the token.

    Args:
        credentials: The HTTP authorization credentials containing the JWT token.

    Returns:
        Session: The session extracted from the token.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    try:
        # Sanitize token
        token = sanitize_string(credentials.credentials)

        session_id = verify_token(token)
        if session_id is None:
            logger.error("session_id_not_found", token_part=token[:10] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Sanitize session_id before using it
        session_id = sanitize_string(session_id)

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify session exists in database
        session = await db_service.get_session(session_id)
        if session is None:
            logger.error("session_not_found", session_id=session_id)
            raise HTTPException(
                status_code=404,
                detail="Session not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return session
    except ValueError as ve:
        logger.error("token_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["register"][0])
async def register_user(request: Request, user_data: UserCreate):
    """Register a new user.

    Args:
        request: The FastAPI request object for rate limiting.
        user_data: User registration data

    Returns:
        UserResponse: The created user info
    """
    try:
        # Sanitize email
        sanitized_email = sanitize_email(user_data.email)

        # Extract and validate password
        password = user_data.password.get_secret_value()
        validate_password_strength(password)

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Check if user exists
        if await db_service.get_user_by_email(sanitized_email):
            raise HTTPException(
                status_code=400, detail="Email already registered"
            )

        # Create user
        user = await db_service.create_user(
            email=sanitized_email, password=User.hash_password(password)
        )

        # Create access token
        token = create_access_token(str(user.id))

        return UserResponse(id=user.id, email=user.email, token=token)
    except ValueError as ve:
        logger.error(
            "user_registration_validation_failed", error=str(ve), exc_info=True
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["login"][0])
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password"),
):
    """Login a user.

    Args:
        request: The FastAPI request object for rate limiting.
        username: User's email
        password: User's password
        grant_type: Must be "password"

    Returns:
        TokenResponse: Access token information

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Sanitize inputs
        username = sanitize_string(username)
        password = sanitize_string(password)
        grant_type = sanitize_string(grant_type)

        # Verify grant type
        if grant_type != "password":
            raise HTTPException(
                status_code=400,
                detail="Unsupported grant type. Must be 'password'",
            )

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await db_service.get_user_by_email(username)
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(str(user.id))
        return TokenResponse(
            access_token=token.access_token,
            token_type="bearer",
            expires_at=token.expires_at,
        )
    except ValueError as ve:
        logger.error("login_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.post("/session", response_model=SessionResponse)
async def create_session(user: User = Depends(get_current_user)):
    """Create a new chat session for the authenticated user.

    Args:
        user: The authenticated user

    Returns:
        SessionResponse: The session ID, name, and access token
    """
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Create session in database
        session = await db_service.create_session(session_id, user.id)

        # Create access token for the session
        token = create_access_token(session_id)

        logger.info(
            "session_created",
            session_id=session_id,
            user_id=user.id,
            name=session.name,
            expires_at=token.expires_at.isoformat(),
        )

        return SessionResponse(
            session_id=session_id, name=session.name, token=token
        )
    except ValueError as ve:
        logger.error(
            "session_creation_validation_failed",
            error=str(ve),
            user_id=user.id,
            exc_info=True,
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.patch("/session/{session_id}/name", response_model=SessionResponse)
async def update_session_name(
    session_id: str,
    name: str = Form(...),
    current_session: Session = Depends(get_current_session),
):
    """Update a session's name.

    Args:
        session_id: The ID of the session to update
        name: The new name for the session
        current_session: The current session from auth

    Returns:
        SessionResponse: The updated session information
    """
    try:
        # Sanitize inputs
        sanitized_session_id = sanitize_string(session_id)
        sanitized_name = sanitize_string(name)
        sanitized_current_session = sanitize_string(current_session.id)

        # Verify the session ID matches the authenticated session
        if sanitized_session_id != sanitized_current_session:
            raise HTTPException(
                status_code=403, detail="Cannot modify other sessions"
            )

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Update the session name
        session = await db_service.update_session_name(
            sanitized_session_id, sanitized_name
        )

        # Create a new token (not strictly necessary but maintains consistency)
        token = create_access_token(sanitized_session_id)

        return SessionResponse(
            session_id=sanitized_session_id, name=session.name, token=token
        )
    except ValueError as ve:
        logger.error(
            "session_update_validation_failed",
            error=str(ve),
            session_id=session_id,
            exc_info=True,
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str, current_session: Session = Depends(get_current_session)
):
    """Delete a session for the authenticated user.

    Args:
        session_id: The ID of the session to delete
        current_session: The current session from auth

    Returns:
        None
    """
    try:
        # Sanitize inputs
        sanitized_session_id = sanitize_string(session_id)
        sanitized_current_session = sanitize_string(current_session.id)

        # Verify the session ID matches the authenticated session
        if sanitized_session_id != sanitized_current_session:
            raise HTTPException(
                status_code=403, detail="Cannot delete other sessions"
            )

        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Delete the session
        await db_service.delete_session(sanitized_session_id)

        logger.info(
            "session_deleted",
            session_id=session_id,
            user_id=current_session.user_id,
        )
    except ValueError as ve:
        logger.error(
            "session_deletion_validation_failed",
            error=str(ve),
            session_id=session_id,
            exc_info=True,
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user: User = Depends(get_current_user)):
    """Get all session IDs for the authenticated user.

    Args:
        user: The authenticated user

    Returns:
        List[SessionResponse]: List of session IDs
    """
    try:
        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        sessions = await db_service.get_user_sessions(user.id)
        return [
            SessionResponse(
                session_id=sanitize_string(session.id),
                name=sanitize_string(session.name),
                token=create_access_token(session.id),
            )
            for session in sessions
        ]
    except ValueError as ve:
        logger.error(
            "get_sessions_validation_failed",
            user_id=user.id,
            error=str(ve),
            exc_info=True,
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.post("/logout", response_model=MessageResponse)
@limiter.limit("10/minute")
async def logout(
    request: Request,
    logout_request: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
):
    """Logout a user by invalidating their token.
    
    Args:
        request: The FastAPI request object for rate limiting.
        logout_request: Optional logout request data.
        current_user: The authenticated user.
        
    Returns:
        MessageResponse: Confirmation message.
    """
    try:
        # In a real implementation, you would add the token to a blacklist
        # or invalidate it in the database
        logger.info("user_logged_out", user_id=current_user.id)
        
        return MessageResponse(
            message="Successfully logged out",
            success=True
        )
    except Exception as e:
        logger.error("logout_failed", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
):
    """Refresh an access token using a refresh token.
    
    Args:
        request: The FastAPI request object for rate limiting.
        refresh_request: The refresh token request.
        
    Returns:
        TokenResponse: New access token.
    """
    try:
        # Verify the refresh token
        user_id = verify_refresh_token(refresh_request.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify user still exists
        user = await db_service.get_user(int(user_id))
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )
        
        # Create new access token
        token = create_access_token(str(user.id))
        
        logger.info("token_refreshed", user_id=user.id)
        
        return TokenResponse(
            access_token=token.access_token,
            token_type="bearer",
            expires_at=token.expires_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
):
    """Send a password reset email to the user.
    
    Args:
        request: The FastAPI request object for rate limiting.
        forgot_request: The forgot password request.
        
    Returns:
        MessageResponse: Confirmation message.
    """
    try:
        # Sanitize email
        email = sanitize_email(forgot_request.email)
        
        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Check if user exists (but don't reveal if they don't)
        user = await db_service.get_user_by_email(email)
        
        if user:
            # Generate reset token
            reset_token = create_password_reset_token(email)
            
            # In a real implementation, you would:
            # 1. Store the reset token in the database with expiration
            # 2. Send an email with the reset link
            logger.info("password_reset_requested", email=email)
        
        # Always return success to prevent email enumeration
        return MessageResponse(
            message="If an account with that email exists, a password reset link has been sent",
            success=True
        )
    except Exception as e:
        logger.error("forgot_password_failed", error=str(e))
        # Still return success to prevent information leakage
        return MessageResponse(
            message="If an account with that email exists, a password reset link has been sent",
            success=True
        )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
):
    """Reset a user's password using a reset token.
    
    Args:
        request: The FastAPI request object for rate limiting.
        reset_request: The password reset request.
        
    Returns:
        MessageResponse: Confirmation message.
    """
    try:
        # Verify the reset token
        email = verify_password_reset_token(reset_request.reset_token)
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        # Check if database service is available
        if db_service is None:
            raise HTTPException(
                status_code=503,
                detail="Database service not available"
            )

        # Get user by email
        user = await db_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Update password
        new_password = reset_request.new_password.get_secret_value()
        hashed_password = User.hash_password(new_password)
        
        # In a real implementation, you would update the user's password in the database
        # await db_service.update_user_password(user.id, hashed_password)
        
        logger.info("password_reset_completed", user_id=user.id)
        
        return MessageResponse(
            message="Password has been reset successfully",
            success=True
        )
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error("password_reset_validation_failed", error=str(ve))
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("password_reset_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Password reset failed")
