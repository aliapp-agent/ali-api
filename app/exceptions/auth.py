"""Authentication and authorization exceptions."""

from typing import Optional


class AuthenticationError(Exception):
    """Base class for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed", details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class AuthorizationError(AuthenticationError):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Access denied", resource: Optional[str] = None):
        self.resource = resource
        if resource:
            message = f"{message}: insufficient permissions for {resource}"
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token", reason: Optional[str] = None):
        if reason:
            message = f"{message}: {reason}"
        super().__init__(message)


class SessionNotFoundError(AuthenticationError):
    """Raised when a session is not found."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        message = f"Session not found: {session_id}"
        super().__init__(message)


class UserNotFoundError(AuthenticationError):
    """Raised when a user is not found."""

    def __init__(self, identifier: str, identifier_type: str = "ID"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        message = f"User not found with {identifier_type.lower()}: {
            identifier}"
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class AccountLockedError(AuthenticationError):
    """Raised when user account is locked."""

    def __init__(self, message: str = "Account is locked", unlock_time: Optional[str] = None):
        if unlock_time:
            message = f"{message}. Try again after {unlock_time}"
        super().__init__(message)


class PasswordResetRequiredError(AuthenticationError):
    """Raised when password reset is required."""

    def __init__(self, message: str = "Password reset required"):
        super().__init__(message)


class TwoFactorRequiredError(AuthenticationError):
    """Raised when two-factor authentication is required."""

    def __init__(self, message: str = "Two-factor authentication required"):
        super().__init__(message)


class SessionExpiredError(AuthenticationError):
    """Raised when a session has expired."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        message = f"Session expired: {session_id}"
        super().__init__(message)


class MaxSessionsExceededError(AuthenticationError):
    """Raised when user has exceeded maximum number of sessions."""

    def __init__(self, max_sessions: int):
        self.max_sessions = max_sessions
        message = f"Maximum number of sessions exceeded: {max_sessions}"
        super().__init__(message)


class RefreshTokenInvalidError(AuthenticationError):
    """Raised when refresh token is invalid."""

    def __init__(self, message: str = "Invalid refresh token"):
        super().__init__(message)


class TokenRevokededError(AuthenticationError):
    """Raised when a token has been revoked."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message)
