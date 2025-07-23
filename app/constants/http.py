"""HTTP and API constants."""

# HTTP Status Codes (commonly used)
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503

# CORS Configuration
CORS_MAX_AGE = 86400  # 24 hours in seconds
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "X-API-Key",
]

# Request/Response Configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Rate Limiting
DEFAULT_RATE_LIMIT = ["200 per day", "50 per hour"]
RATE_LIMIT_STORAGE_URL = "memory://"

# API Rate Limits by Endpoint Type
API_RATE_LIMITS = {
    "auth": ["20 per minute", "100 per hour"],
    "chat": ["30 per minute", "500 per hour"],
    "chat_stream": ["20 per minute", "300 per hour"],
    "messages": ["50 per minute", "1000 per hour"],
    "health": ["100 per minute"],
    "root": ["50 per minute"],
}

# Content Types
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_HTML = "text/html"
CONTENT_TYPE_SSE = "text/event-stream"

# Headers
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_AUTHORIZATION = "Authorization"
HEADER_USER_AGENT = "User-Agent"
HEADER_X_FORWARDED_FOR = "X-Forwarded-For"
HEADER_X_REAL_IP = "X-Real-IP"
HEADER_X_REQUEST_ID = "X-Request-ID"

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
}

# API Versioning
API_VERSION_HEADER = "X-API-Version"
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"

# Environment Specific Timeouts
ENVIRONMENT_TIMEOUTS = {
    "development": {
        "request_timeout": 60,
        "response_timeout": 60,
        "keepalive_timeout": 5,
    },
    "staging": {
        "request_timeout": 30,
        "response_timeout": 30,
        "keepalive_timeout": 5,
    },
    "production": {
        "request_timeout": 15,
        "response_timeout": 15,
        "keepalive_timeout": 5,
    },
    "test": {
        "request_timeout": 10,
        "response_timeout": 10,
        "keepalive_timeout": 1,
    },
}

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL = 30  # seconds
WS_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
WS_CONNECTION_TIMEOUT = 60  # seconds

# Cache Headers
CACHE_CONTROL_NO_CACHE = "no-cache, no-store, must-revalidate"
CACHE_CONTROL_PUBLIC = "public, max-age=3600"
CACHE_CONTROL_PRIVATE = "private, max-age=300"

# Error Response Format
ERROR_RESPONSE_FORMAT = {
    "detail": "string",
    "errors": "array",
    "timestamp": "string",
    "path": "string",
    "status_code": "integer",
}
