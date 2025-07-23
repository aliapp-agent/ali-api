"""Authentication and authorization constants."""

# JWT Configuration
JWT_ALGORITHM_DEFAULT = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS_DEFAULT = 30
TOKEN_TYPE_BEARER = "bearer"

# Password Configuration
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Password strength requirements
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True

# Special characters allowed in passwords
PASSWORD_SPECIAL_CHARS = r'!@#$%^&*(),.?":{}|<>'

# Session Configuration
SESSION_ID_LENGTH = 36  # UUID4 length
SESSION_NAME_MAX_LENGTH = 100
SESSION_NAME_DEFAULT = "New Chat"

# Rate limiting for auth endpoints
AUTH_RATE_LIMITS = {
    "register": ["10 per hour", "3 per minute"],
    "login": ["20 per minute", "100 per hour"],
    "session_create": ["30 per minute"],
    "session_update": ["60 per minute"],
    "session_delete": ["30 per minute"],
}

# Token validation
TOKEN_MIN_LENGTH = 10
TOKEN_MAX_LENGTH = 2048

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
}
