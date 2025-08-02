"""Database-related exceptions."""

from typing import Optional


class DatabaseError(Exception):
    """Base class for database-related errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[str] = None,
    ):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Failed to connect to database",
        host: Optional[str] = None,
    ):
        self.host = host
        if host:
            message = f"{message} at {host}"
        super().__init__(message)


class DatabaseOperationError(DatabaseError):
    """Raised when a database operation fails."""

    def __init__(self, operation: str, message: Optional[str] = None):
        self.operation = operation
        if not message:
            message = f"Database operation failed: {operation}"
        super().__init__(message)


class RecordNotFoundError(DatabaseError):
    """Raised when a database record is not found."""

    def __init__(self, table: str, identifier: str, identifier_type: str = "ID"):
        self.table = table
        self.identifier = identifier
        self.identifier_type = identifier_type
        message = f"Record not found in {table} with {
            identifier_type.lower()}: {identifier}"
        super().__init__(message)


class DuplicateRecordError(DatabaseError):
    """Raised when trying to create a duplicate record."""

    def __init__(self, table: str, field: str, value: str):
        self.table = table
        self.field = field
        self.value = value
        message = f"Duplicate record in {table}: {
            field} '{value}' already exists"
        super().__init__(message)


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operation times out."""

    def __init__(self, operation: str, timeout: int):
        self.operation = operation
        self.timeout = timeout
        message = f"Database operation '{
            operation}' timed out after {timeout} seconds"
        super().__init__(message)


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated."""

    def __init__(self, constraint: str, message: Optional[str] = None):
        self.constraint = constraint
        if not message:
            message = f"Database integrity constraint violated: {constraint}"
        super().__init__(message)


class DatabaseMigrationError(DatabaseError):
    """Raised when database migration fails."""

    def __init__(self, migration: str, message: Optional[str] = None):
        self.migration = migration
        if not message:
            message = f"Database migration failed: {migration}"
        super().__init__(message)


class DatabaseTransactionError(DatabaseError):
    """Raised when database transaction fails."""

    def __init__(self, message: str = "Database transaction failed"):
        super().__init__(message)


class DatabasePoolExhaustedError(DatabaseError):
    """Raised when database connection pool is exhausted."""

    def __init__(self, pool_size: int):
        self.pool_size = pool_size
        message = f"Database connection pool exhausted (size: {pool_size})"
        super().__init__(message)


class DatabaseVersionError(DatabaseError):
    """Raised when database version is incompatible."""

    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        message = f"Database version mismatch: expected {
            expected}, got {actual}"
        super().__init__(message)


class DatabaseBackupError(DatabaseError):
    """Raised when database backup operation fails."""

    def __init__(self, message: str = "Database backup failed"):
        super().__init__(message)


class DatabaseRestoreError(DatabaseError):
    """Raised when database restore operation fails."""

    def __init__(self, message: str = "Database restore failed"):
        super().__init__(message)


class DatabaseConfigurationError(DatabaseError):
    """Raised when database configuration is invalid."""

    def __init__(self, parameter: str, message: Optional[str] = None):
        self.parameter = parameter
        if not message:
            message = f"Invalid database configuration: {parameter}"
        super().__init__(message)


class DatabaseLockError(DatabaseError):
    """Raised when database lock cannot be acquired."""

    def __init__(self, resource: str, timeout: Optional[int] = None):
        self.resource = resource
        self.timeout = timeout
        message = f"Could not acquire lock on {resource}"
        if timeout:
            message += f" within {timeout} seconds"
        super().__init__(message)
