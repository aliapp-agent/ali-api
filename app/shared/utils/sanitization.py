"""This file contains the sanitization utilities for the application."""

import html
import re
from typing import (
    Any,
    Dict,
    List,
)

from app.constants.validation import (
    DANGEROUS_PATTERNS,
    EMAIL_REGEX,
    PASSWORD_REGEX,
    SQL_INJECTION_PATTERNS,
    VALIDATION_MESSAGES,
)


def sanitize_string(
    value: str, max_length: int = 1000, strict: bool = False
) -> str:
    """Sanitize a string to prevent XSS and other injection attacks.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length for the string
        strict: If True, apply stricter sanitization rules

    Returns:
        str: The sanitized string

    Raises:
        ValueError: If the string is too long or contains dangerous patterns
    """
    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)

    # Check length limits
    if len(value) > max_length:
        raise ValueError(f"String too long. Maximum length is {
                         max_length} characters")

    # Remove null bytes and control characters
    value = value.replace("\0", "").replace("\r", "").replace("\x1a", "")

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(value):
            if strict:
                raise ValueError(
                    "String contains potentially dangerous content"
                )
            else:
                value = pattern.sub("", value)

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            if strict:
                raise ValueError(
                    "String contains potentially harmful SQL patterns"
                )
            else:
                value = pattern.sub("", value)

    # HTML escape to prevent XSS (only if not already escaped)
    if not strict:
        value = html.escape(value)

    # Strip leading/trailing whitespace
    value = value.strip()

    return value


def sanitize_email(email: str) -> str:
    """Sanitize an email address.

    Args:
        email: The email address to sanitize

    Returns:
        str: The sanitized email address

    Raises:
        ValueError: If the email format is invalid
    """
    # Basic sanitization with strict mode for emails
    email = sanitize_string(email, max_length=254, strict=True)

    # Convert to lowercase for consistency
    email = email.lower()

    # Validate email format using regex from constants
    if not EMAIL_REGEX.match(email):
        raise ValueError(VALIDATION_MESSAGES["email_invalid"])

    return email


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize all string values in a dictionary.

    Args:
        data: The dictionary to sanitize

    Returns:
        Dict[str, Any]: The sanitized dictionary
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value)
        else:
            sanitized[key] = value
    return sanitized


def sanitize_list(data: List[Any]) -> List[Any]:
    """Recursively sanitize all string values in a list.

    Args:
        data: The list to sanitize

    Returns:
        List[Any]: The sanitized list
    """
    sanitized = []
    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item))
        else:
            sanitized.append(item)
    return sanitized


def validate_password_strength(password: str) -> bool:
    """Validate password strength using comprehensive rules.

    Args:
        password: The password to validate

    Returns:
        bool: Whether the password is strong enough

    Raises:
        ValueError: If the password is not strong enough with detailed reason
    """
    from app.constants.validation import (
        PASSWORD_DIGIT_REGEX,
        PASSWORD_LOWERCASE_REGEX,
        PASSWORD_MAX_LENGTH,
        PASSWORD_MIN_LENGTH,
        PASSWORD_SPECIAL_CHAR_REGEX,
        PASSWORD_UPPERCASE_REGEX,
    )

    # Check length constraints
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(VALIDATION_MESSAGES["password_too_short"])

    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(VALIDATION_MESSAGES["password_too_long"])

    # Check for required character types
    if not PASSWORD_UPPERCASE_REGEX.search(password):
        raise ValueError(VALIDATION_MESSAGES["password_no_uppercase"])

    if not PASSWORD_LOWERCASE_REGEX.search(password):
        raise ValueError(VALIDATION_MESSAGES["password_no_lowercase"])

    if not PASSWORD_DIGIT_REGEX.search(password):
        raise ValueError(VALIDATION_MESSAGES["password_no_digit"])

    if not PASSWORD_SPECIAL_CHAR_REGEX.search(password):
        raise ValueError(VALIDATION_MESSAGES["password_no_special"])

    # Check against common weak passwords
    common_weak_passwords = {
        "password",
        "123456",
        "password123",
        "admin",
        "qwerty",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
    }

    if password.lower() in common_weak_passwords:
        raise ValueError(
            "Password is too common. Please choose a stronger password"
        )

    return True


def validate_session_id(session_id: str) -> str:
    """Validate and sanitize a session ID.

    Args:
        session_id: The session ID to validate

    Returns:
        str: The validated session ID

    Raises:
        ValueError: If the session ID format is invalid
    """
    from app.constants.validation import SESSION_ID_REGEX

    # Sanitize the session ID
    session_id = sanitize_string(session_id, max_length=36, strict=True)

    # Validate UUID format
    if not SESSION_ID_REGEX.match(session_id):
        raise ValueError(VALIDATION_MESSAGES["session_id_invalid"])

    return session_id


def validate_jwt_token(token: str) -> str:
    """Validate and sanitize a JWT token.

    Args:
        token: The JWT token to validate

    Returns:
        str: The validated token

    Raises:
        ValueError: If the token format is invalid
    """
    from app.constants.validation import (
        JWT_TOKEN_MAX_LENGTH,
        JWT_TOKEN_MIN_LENGTH,
        JWT_TOKEN_REGEX,
    )

    # Basic length validation
    if len(token) < JWT_TOKEN_MIN_LENGTH:
        raise ValueError("Token is too short")

    if len(token) > JWT_TOKEN_MAX_LENGTH:
        raise ValueError("Token is too long")

    # Sanitize without HTML escaping (tokens shouldn't contain HTML)
    token = token.strip().replace("\0", "")

    # Validate JWT format
    if not JWT_TOKEN_REGEX.match(token):
        raise ValueError(VALIDATION_MESSAGES["token_invalid"])

    return token
