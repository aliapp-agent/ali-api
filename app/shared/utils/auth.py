"""This file contains the authentication utilities for the application."""

import secrets
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from typing import Optional

from jose import (
    JWTError,
    jwt,
)

from app.constants.auth import (
    ACCESS_TOKEN_EXPIRE_DAYS_DEFAULT,
    JWT_ALGORITHM_DEFAULT,
    TOKEN_TYPE_BEARER,
)
from app.constants.validation import (
    JWT_TOKEN_MAX_LENGTH,
    JWT_TOKEN_MIN_LENGTH,
)
from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import Token
from app.utils.sanitization import (
    sanitize_string,
    validate_jwt_token,
)


def create_access_token(
    session_id: str, expires_delta: Optional[timedelta] = None
) -> Token:
    """Create a new access token for a session.

    Args:
        session_id: The unique session ID for the conversation.
        expires_delta: Optional expiration time delta.

    Returns:
        Token: The generated access token.

    Raises:
        ValueError: If session_id is invalid or JWT creation fails.
    """
    if not session_id or not isinstance(session_id, str):
        raise ValueError("Session ID must be a non-empty string")

    # Sanitize session ID
    session_id = sanitize_string(session_id, max_length=36, strict=True)

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire_days = getattr(
            settings,
            "JWT_ACCESS_TOKEN_EXPIRE_DAYS",
            ACCESS_TOKEN_EXPIRE_DAYS_DEFAULT,
        )
        expire = datetime.now(UTC) + timedelta(days=expire_days)

    # Get current time for issued at claim
    issued_at = datetime.now(UTC)

    # Generate unique token identifier
    jti = f"{session_id}-{issued_at.timestamp()}-{secrets.token_hex(8)}"

    # Prepare JWT payload
    to_encode = {
        "sub": session_id,
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "access_token",
    }

    try:
        # Get JWT configuration with fallbacks
        secret_key = getattr(settings, "JWT_SECRET_KEY", None)
        algorithm = getattr(settings, "JWT_ALGORITHM", JWT_ALGORITHM_DEFAULT)

        if not secret_key:
            raise ValueError("JWT secret key is not configured")

        # Encode the JWT token
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        logger.info(
            "token_created",
            session_id=session_id,
            expires_at=expire.isoformat(),
            algorithm=algorithm,
            jti=jti,
        )

        return Token(access_token=encoded_jwt, expires_at=expire)

    except Exception as e:
        logger.error(
            "token_creation_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True,
        )
        raise ValueError(f"Failed to create access token: {str(e)}")


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the session ID.

    Args:
        token: The JWT token to verify.

    Returns:
        Optional[str]: The session ID if token is valid, None otherwise.

    Raises:
        ValueError: If the token format is invalid
    """
    if not token or not isinstance(token, str):
        logger.warning(
            "token_invalid_format", token_length=len(token) if token else 0
        )
        raise ValueError("Token must be a non-empty string")

    # Validate token format and length
    try:
        validated_token = validate_jwt_token(token)
    except ValueError as e:
        logger.warning("token_format_validation_failed", error=str(e))
        raise

    try:
        # Get JWT configuration
        secret_key = getattr(settings, "JWT_SECRET_KEY", None)
        algorithm = getattr(settings, "JWT_ALGORITHM", JWT_ALGORITHM_DEFAULT)

        if not secret_key:
            logger.error("jwt_secret_key_not_configured")
            raise ValueError("JWT secret key is not configured")

        # Decode and verify the token
        payload = jwt.decode(
            validated_token,
            secret_key,
            algorithms=[algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require_exp": True,
                "require_iat": True,
            },
        )

        # Extract session ID from subject claim
        session_id: str = payload.get("sub")
        if not session_id:
            logger.warning(
                "token_missing_session_id", payload_keys=list(payload.keys())
            )
            return None

        # Verify token type if present
        token_type = payload.get("type")
        if token_type and token_type != "access_token":
            logger.warning("token_invalid_type", token_type=token_type)
            return None

        # Log successful verification
        jti = payload.get("jti", "unknown")
        logger.info(
            "token_verified",
            session_id=session_id,
            jti=jti,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )

        return session_id

    except jwt.ExpiredSignatureError:
        logger.warning("token_expired", token_part=token[:20] + "...")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(
            "token_invalid", error=str(e), token_part=token[:20] + "..."
        )
        return None
    except JWTError as e:
        logger.error("token_verification_failed", error=str(e), exc_info=True)
        return None
    except Exception as e:
        logger.error(
            "token_verification_unexpected_error", error=str(e), exc_info=True
        )
        return None


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: The length of the token in bytes (will be hex encoded, so output is 2x length)

    Returns:
        str: A secure random token

    Raises:
        ValueError: If length is invalid
    """
    if length < 16 or length > 128:
        raise ValueError("Token length must be between 16 and 128 bytes")

    return secrets.token_hex(length)


def validate_token_claims(payload: dict) -> bool:
    """Validate JWT token claims for security.

    Args:
        payload: The decoded JWT payload

    Returns:
        bool: True if claims are valid, False otherwise
    """
    required_claims = ["sub", "exp", "iat"]

    # Check required claims exist
    for claim in required_claims:
        if claim not in payload:
            logger.warning("token_missing_required_claim", claim=claim)
            return False

    # Validate expiration time
    exp = payload.get("exp")
    if exp and exp < datetime.now(UTC).timestamp():
        logger.warning("token_expired_in_validation", exp=exp)
        return False

    # Validate issued at time (not in future)
    iat = payload.get("iat")
    # Allow 60 second clock skew
    if iat and iat > datetime.now(UTC).timestamp() + 60:
        logger.warning("token_issued_in_future", iat=iat)
        return False

    return True


def create_refresh_token(user_id: int, expires_delta: Optional[timedelta] = None) -> Token:
    """Create a new refresh token for a user.
    
    Args:
        user_id: The user ID.
        expires_delta: Optional expiration time delta.
        
    Returns:
        Token: The generated refresh token.
        
    Raises:
        ValueError: If user_id is invalid or JWT creation fails.
    """
    if not user_id or not isinstance(user_id, int):
        raise ValueError("User ID must be a valid integer")
    
    # Calculate expiration time (refresh tokens live longer)
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=30)  # 30 days default
    
    # Get current time for issued at claim
    issued_at = datetime.now(UTC)
    
    # Generate unique token identifier
    jti = f"{user_id}-refresh-{issued_at.timestamp()}-{secrets.token_hex(8)}"
    
    # Prepare JWT payload
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "refresh_token",
    }
    
    try:
        secret_key = getattr(settings, "JWT_SECRET_KEY", None)
        algorithm = getattr(settings, "JWT_ALGORITHM", JWT_ALGORITHM_DEFAULT)
        
        if not secret_key:
            raise ValueError("JWT secret key is not configured")
        
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        
        logger.info(
            "refresh_token_created",
            user_id=user_id,
            expires_at=expire.isoformat(),
            jti=jti,
        )
        
        return Token(access_token=encoded_jwt, expires_at=expire)
        
    except Exception as e:
        logger.error(
            "refresh_token_creation_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise ValueError(f"Failed to create refresh token: {str(e)}")


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify a refresh token and return the user ID.
    
    Args:
        token: The refresh token to verify.
        
    Returns:
        Optional[str]: The user ID if token is valid, None otherwise.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string")
    
    try:
        validated_token = validate_jwt_token(token)
        secret_key = getattr(settings, "JWT_SECRET_KEY", None)
        algorithm = getattr(settings, "JWT_ALGORITHM", JWT_ALGORITHM_DEFAULT)
        
        if not secret_key:
            raise ValueError("JWT secret key is not configured")
        
        payload = jwt.decode(validated_token, secret_key, algorithms=[algorithm])
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh_token":
            logger.warning("invalid_refresh_token_type", token_type=token_type)
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        logger.warning("refresh_token_expired")
        return None
    except (jwt.InvalidTokenError, JWTError):
        logger.warning("refresh_token_invalid")
        return None
    except Exception as e:
        logger.error("refresh_token_verification_failed", error=str(e))
        return None


def create_password_reset_token(email: str) -> str:
    """Create a password reset token.
    
    Args:
        email: The user's email address.
        
    Returns:
        str: The password reset token.
    """
    # Generate a secure random token
    reset_token = generate_secure_token(32)
    
    # In a real implementation, you would store this token in the database
    # with an expiration time and associate it with the user's email
    logger.info("password_reset_token_created", email=email)
    
    return reset_token


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the associated email.
    
    Args:
        token: The password reset token.
        
    Returns:
        Optional[str]: The email if token is valid, None otherwise.
    """
    # In a real implementation, you would look up the token in the database
    # and check if it's still valid (not expired)
    # For now, we'll return None as this needs database integration
    logger.info("password_reset_token_verification_attempted", token_part=token[:10])
    return None
