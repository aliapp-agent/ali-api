"""Domain-specific exceptions for Ali API.

This module contains exceptions that represent domain business rule violations
and error conditions within the domain layer.
"""


class DomainError(Exception):
    """Base exception for all domain-related errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class DomainException(DomainError):
    """Alias for DomainError for backward compatibility."""
    pass


class RepositoryError(DomainError):
    """Base exception for repository-related errors."""
    pass


# User-related exceptions
class UserError(DomainError):
    """Base exception for user-related errors."""
    pass


class UserNotFoundError(UserError):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: int = None, email: str = None):
        if user_id:
            message = f"User with ID {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        else:
            message = "User not found"
        super().__init__(message, "USER_NOT_FOUND")
        self.user_id = user_id
        self.email = email


class UserAlreadyExistsError(UserError):
    """Raised when trying to create a user that already exists."""
    
    def __init__(self, email: str):
        message = f"User with email {email} already exists"
        super().__init__(message, "USER_ALREADY_EXISTS")
        self.email = email


class InvalidUserCredentialsError(UserError):
    """Raised when user credentials are invalid."""
    
    def __init__(self):
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS")


class UserNotActiveError(UserError):
    """Raised when trying to authenticate an inactive user."""
    
    def __init__(self, user_id: int):
        message = f"User {user_id} is not active"
        super().__init__(message, "USER_NOT_ACTIVE")
        self.user_id = user_id


class UserNotVerifiedError(UserError):
    """Raised when trying to perform an action requiring verification."""
    
    def __init__(self, user_id: int):
        message = f"User {user_id} email is not verified"
        super().__init__(message, "USER_NOT_VERIFIED")
        self.user_id = user_id


class InsufficientPermissionsError(UserError):
    """Raised when user lacks required permissions."""
    
    def __init__(self, action: str, user_id: int = None):
        message = f"Insufficient permissions to perform action: {action}"
        if user_id:
            message += f" (user: {user_id})"
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")
        self.action = action
        self.user_id = user_id


# Session-related exceptions
class SessionError(DomainError):
    """Base exception for session-related errors."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""
    
    def __init__(self, session_id: str):
        message = f"Session with ID {session_id} not found"
        super().__init__(message, "SESSION_NOT_FOUND")
        self.session_id = session_id


class SessionNotActiveError(SessionError):
    """Raised when trying to use an inactive session."""
    
    def __init__(self, session_id: str):
        message = f"Session {session_id} is not active"
        super().__init__(message, "SESSION_NOT_ACTIVE")
        self.session_id = session_id


class SessionAccessDeniedError(SessionError):
    """Raised when user cannot access a session."""
    
    def __init__(self, session_id: str, user_id: int):
        message = f"User {user_id} cannot access session {session_id}"
        super().__init__(message, "SESSION_ACCESS_DENIED")
        self.session_id = session_id
        self.user_id = user_id


class SessionAlreadyExistsError(SessionError):
    """Raised when trying to create a session that already exists."""
    
    def __init__(self, session_id: str):
        message = f"Session with ID {session_id} already exists"
        super().__init__(message, "SESSION_ALREADY_EXISTS")
        self.session_id = session_id


# Message-related exceptions
class MessageError(DomainError):
    """Base exception for message-related errors."""
    pass


class MessageNotFoundError(MessageError):
    """Raised when a message is not found."""
    
    def __init__(self, message_id: str):
        message = f"Message with ID {message_id} not found"
        super().__init__(message, "MESSAGE_NOT_FOUND")
        self.message_id = message_id


class MessageContentError(MessageError):
    """Raised when message content is invalid."""
    
    def __init__(self, reason: str):
        message = f"Invalid message content: {reason}"
        super().__init__(message, "INVALID_MESSAGE_CONTENT")
        self.reason = reason


class MessageProcessingError(MessageError):
    """Raised when message processing fails."""
    
    def __init__(self, message_id: str, reason: str):
        message = f"Failed to process message {message_id}: {reason}"
        super().__init__(message, "MESSAGE_PROCESSING_ERROR")
        self.message_id = message_id
        self.reason = reason


class MessageEditNotAllowedError(MessageError):
    """Raised when trying to edit a message that cannot be edited."""
    
    def __init__(self, message_id: str, reason: str):
        message = f"Cannot edit message {message_id}: {reason}"
        super().__init__(message, "MESSAGE_EDIT_NOT_ALLOWED")
        self.message_id = message_id
        self.reason = reason


class MessageAlreadyExistsError(MessageError):
    """Raised when trying to create a message that already exists."""
    
    def __init__(self, message_id: str):
        message = f"Message with ID {message_id} already exists"
        super().__init__(message, "MESSAGE_ALREADY_EXISTS")
        self.message_id = message_id


# Document-related exceptions
class DocumentError(DomainError):
    """Base exception for document-related errors."""
    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""
    
    def __init__(self, document_id: str):
        message = f"Document with ID {document_id} not found"
        super().__init__(message, "DOCUMENT_NOT_FOUND")
        self.document_id = document_id


class DocumentAccessDeniedError(DocumentError):
    """Raised when user cannot access a document."""
    
    def __init__(self, document_id: str, user_id: int):
        message = f"User {user_id} cannot access document {document_id}"
        super().__init__(message, "DOCUMENT_ACCESS_DENIED")
        self.document_id = document_id
        self.user_id = user_id


class DocumentProcessingError(DocumentError):
    """Raised when document processing fails."""
    
    def __init__(self, document_id: str, reason: str):
        message = f"Failed to process document {document_id}: {reason}"
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")
        self.document_id = document_id
        self.reason = reason


class DocumentTooLargeError(DocumentError):
    """Raised when document exceeds size limits."""
    
    def __init__(self, size_mb: float, max_size_mb: float):
        message = f"Document size {size_mb}MB exceeds limit of {max_size_mb}MB"
        super().__init__(message, "DOCUMENT_TOO_LARGE")
        self.size_mb = size_mb
        self.max_size_mb = max_size_mb


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when document type is not supported."""
    
    def __init__(self, file_type: str):
        message = f"Document type {file_type} is not supported"
        super().__init__(message, "UNSUPPORTED_DOCUMENT_TYPE")
        self.file_type = file_type


class DocumentAlreadyExistsError(DocumentError):
    """Raised when trying to create a document that already exists."""
    
    def __init__(self, document_id: str):
        message = f"Document with ID {document_id} already exists"
        super().__init__(message, "DOCUMENT_ALREADY_EXISTS")
        self.document_id = document_id


# Business rule violations
class BusinessRuleViolationError(DomainError):
    """Raised when a business rule is violated."""
    
    def __init__(self, rule: str, details: str = None):
        message = f"Business rule violation: {rule}"
        if details:
            message += f" - {details}"
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        self.rule = rule
        self.details = details


class RateLimitExceededError(DomainError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, limit_type: str, limit_value: int, reset_time: int = None):
        message = f"Rate limit exceeded for {limit_type}: {limit_value}"
        if reset_time:
            message += f" (resets in {reset_time}s)"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.reset_time = reset_time


class QuotaExceededError(DomainError):
    """Raised when quotas are exceeded."""
    
    def __init__(self, quota_type: str, used: int, limit: int):
        message = f"Quota exceeded for {quota_type}: {used}/{limit}"
        super().__init__(message, "QUOTA_EXCEEDED")
        self.quota_type = quota_type
        self.used = used
        self.limit = limit


class ConcurrencyError(DomainError):
    """Raised when concurrent operations conflict."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"Concurrent modification detected for {resource_type} {resource_id}"
        super().__init__(message, "CONCURRENCY_ERROR")
        self.resource_type = resource_type
        self.resource_id = resource_id


# Authentication and Authorization exceptions
class AuthenticationError(DomainError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Authentication failed"):
        super().__init__(reason, "AUTHENTICATION_ERROR")
        self.reason = reason


class AuthorizationError(DomainError):
    """Raised when authorization fails."""
    
    def __init__(self, action: str, reason: str = None):
        message = f"Authorization failed for action: {action}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.action = action
        self.reason = reason


class ValidationError(DomainError):
    """Raised when validation fails."""
    
    def __init__(self, field: str, reason: str):
        message = f"Validation failed for {field}: {reason}"
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.reason = reason


class ResourceNotFoundError(DomainError):
    """Raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(DomainError):
    """Raised when there's a conflict with the current state."""
    
    def __init__(self, reason: str):
        super().__init__(f"Conflict: {reason}", "CONFLICT_ERROR")
        self.reason = reason