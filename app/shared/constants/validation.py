"""Validation constants and regex patterns."""

import re

# Email Validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
EMAIL_MAX_LENGTH = 254
EMAIL_MIN_LENGTH = 5

# Password Validation
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).{8,}$"
)
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Password Component Regexes
PASSWORD_UPPERCASE_REGEX = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE_REGEX = re.compile(r"[a-z]")
PASSWORD_DIGIT_REGEX = re.compile(r"\d")
PASSWORD_SPECIAL_CHAR_REGEX = re.compile(r'[!@#$%^&*(),.?":{}|<>]')

# Session ID Validation
SESSION_ID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
SESSION_ID_LENGTH = 36

# JWT Token Validation
JWT_TOKEN_REGEX = re.compile(r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$")
JWT_TOKEN_MIN_LENGTH = 10
JWT_TOKEN_MAX_LENGTH = 2048

# String Validation
MAX_STRING_LENGTH = 1000
MAX_TEXT_LENGTH = 10000
MAX_MESSAGE_LENGTH = 5000
MAX_SESSION_NAME_LENGTH = 100

# URL Validation
URL_REGEX = re.compile(
    r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
)

# Numeric Validation
MIN_USER_ID = 1
MAX_USER_ID = 2147483647  # Max 32-bit integer
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 1000
DEFAULT_PAGE_SIZE = 50

# File Validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md"],
    "data": [".json", ".csv", ".xml", ".yaml", ".yml"],
}

# Input Sanitization
DANGEROUS_PATTERNS = [
    re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe.*?>.*?</iframe>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<object.*?>.*?</object>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<embed.*?>.*?</embed>", re.IGNORECASE | re.DOTALL),
]

# SQL Injection Prevention
SQL_INJECTION_PATTERNS = [
    re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        re.IGNORECASE,
    ),
    re.compile(r"(\b(OR|AND)\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(--|\#|\/\*|\*\/)", re.IGNORECASE),
    re.compile(r"(\b(CHAR|CONCAT|SUBSTRING|ASCII|HEX)\s*\()", re.IGNORECASE),
]

# Date/Time Validation
ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})$"
)

# Phone Number Validation (International format)
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")

# Username Validation
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30

# API Key Validation
API_KEY_REGEX = re.compile(r"^[a-zA-Z0-9]{32,}$")
API_KEY_MIN_LENGTH = 32
API_KEY_MAX_LENGTH = 128

# Rate Limit Format Validation
RATE_LIMIT_REGEX = re.compile(r"^\d+\s+per\s+(second|minute|hour|day)$")

# Common Validation Messages
VALIDATION_MESSAGES = {
    "email_invalid": "Please enter a valid email address",
    "email_too_long": f"Email must be less than {EMAIL_MAX_LENGTH} characters",
    "password_too_short": f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
    "password_too_long": f"Password must be less than {PASSWORD_MAX_LENGTH} characters",
    "password_no_uppercase": "Password must contain at least one uppercase letter",
    "password_no_lowercase": "Password must contain at least one lowercase letter",
    "password_no_digit": "Password must contain at least one number",
    "password_no_special": "Password must contain at least one special character",
    "session_id_invalid": "Invalid session ID format",
    "token_invalid": "Invalid token format",
    "string_too_long": f"Text must be less than {MAX_STRING_LENGTH} characters",
    "message_too_long": f"Message must be less than {MAX_MESSAGE_LENGTH} characters",
    "url_invalid": "Please enter a valid URL",
    "file_too_large": f"File size must be less than {MAX_FILE_SIZE // (1024*1024)}MB",
    "file_type_not_allowed": "File type not allowed",
}

# Environment-specific validation settings
VALIDATION_SETTINGS = {
    "development": {
        "strict_validation": False,
        "allow_test_data": True,
        "log_validation_errors": True,
    },
    "staging": {
        "strict_validation": True,
        "allow_test_data": True,
        "log_validation_errors": True,
    },
    "production": {
        "strict_validation": True,
        "allow_test_data": False,
        "log_validation_errors": False,
    },
    "test": {
        "strict_validation": False,
        "allow_test_data": True,
        "log_validation_errors": False,
    },
}
