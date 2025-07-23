"""Database configuration constants."""

# Connection Pool Configuration
DEFAULT_POOL_SIZE = 20
DEFAULT_MAX_OVERFLOW = 10
CONNECTION_TIMEOUT = 30  # seconds
POOL_RECYCLE_TIME = 1800  # 30 minutes in seconds
POOL_PRE_PING = True

# Database Timeouts
QUERY_TIMEOUT = 30  # seconds
TRANSACTION_TIMEOUT = 60  # seconds
CONNECTION_RETRY_ATTEMPTS = 3
CONNECTION_RETRY_DELAY = 1  # seconds

# Table Names
USERS_TABLE = "users"
SESSIONS_TABLE = "sessions"
CHECKPOINT_TABLES = [
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoints"
]

# Database Limits
MAX_CONNECTIONS_PER_USER = 10
MAX_SESSIONS_PER_USER = 100
MAX_QUERY_RESULTS = 1000

# Migration Configuration
MIGRATION_TIMEOUT = 300  # 5 minutes
BACKUP_BEFORE_MIGRATION = True

# Health Check Configuration
HEALTH_CHECK_QUERY = "SELECT 1"
HEALTH_CHECK_TIMEOUT = 5  # seconds

# Environment Specific Settings
DATABASE_SETTINGS = {
    "development": {
        "pool_size": 5,
        "max_overflow": 5,
        "echo": True,
        "pool_pre_ping": True,
    },
    "staging": {
        "pool_size": 10,
        "max_overflow": 10,
        "echo": False,
        "pool_pre_ping": True,
    },
    "production": {
        "pool_size": 20,
        "max_overflow": 20,
        "echo": False,
        "pool_pre_ping": True,
    },
    "test": {
        "pool_size": 1,
        "max_overflow": 0,
        "echo": False,
        "pool_pre_ping": False,
    },
}

# Database URL Templates
DATABASE_URL_TEMPLATES = {
    "postgresql": "postgresql://{user}:{password}@{host}:{port}/{database}",
    "sqlite": "sqlite:///{database}.db",
}
