"""Validation-related exceptions."""

from typing import Optional, List, Any


class ValidationError(Exception):
    """Base class for validation-related errors."""

    def __init__(self, message: str = "Validation failed", field: Optional[str] = None, value: Optional[Any] = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return self.message


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, field: str, value: Any, expected: str):
        self.expected = expected
        message = f"Invalid value '{value}' for field '{
            field}'. Expected: {expected}"
        super().__init__(message, field, value)


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""

    def __init__(self, email: str):
        message = f"Invalid email format: {email}"
        super().__init__(message, "email", email)


class InvalidPasswordError(ValidationError):
    """Raised when password doesn't meet requirements."""

    def __init__(self, reason: str):
        message = f"Password validation failed: {reason}"
        super().__init__(message, "password")


class InvalidSessionIdError(ValidationError):
    """Raised when session ID format is invalid."""

    def __init__(self, session_id: str):
        message = f"Invalid session ID format: {session_id}"
        super().__init__(message, "session_id", session_id)


class StringTooLongError(ValidationError):
    """Raised when string exceeds maximum length."""

    def __init__(self, field: str, actual_length: int, max_length: int):
        self.actual_length = actual_length
        self.max_length = max_length
        message = f"String too long: {
            actual_length} characters (max: {max_length})"
        super().__init__(message, field)


class StringTooShortError(ValidationError):
    """Raised when string is below minimum length."""

    def __init__(self, field: str, actual_length: int, min_length: int):
        self.actual_length = actual_length
        self.min_length = min_length
        message = f"String too short: {
            actual_length} characters (min: {min_length})"
        super().__init__(message, field)


class SecurityViolationError(ValidationError):
    """Raised when input contains potentially dangerous content."""

    def __init__(self, field: str, violation_type: str):
        self.violation_type = violation_type
        message = f"Security violation detected in field '{
            field}': {violation_type}"
        super().__init__(message, field)


class InvalidURLError(ValidationError):
    """Raised when URL format is invalid."""

    def __init__(self, url: str):
        message = f"Invalid URL format: {url}"
        super().__init__(message, "url", url)


class InvalidDateError(ValidationError):
    """Raised when date format is invalid."""

    def __init__(self, date_string: str, expected_format: str):
        self.expected_format = expected_format
        message = f"Invalid date format: {
            date_string}. Expected format: {expected_format}"
        super().__init__(message, "date", date_string)


class InvalidPhoneNumberError(ValidationError):
    """Raised when phone number format is invalid."""

    def __init__(self, phone: str):
        message = f"Invalid phone number format: {phone}"
        super().__init__(message, "phone", phone)


class InvalidUsernameError(ValidationError):
    """Raised when username format is invalid."""

    def __init__(self, username: str, reason: str):
        message = f"Invalid username '{username}': {reason}"
        super().__init__(message, "username", username)


class InvalidAPIKeyError(ValidationError):
    """Raised when API key format is invalid."""

    def __init__(self, reason: str):
        message = f"Invalid API key: {reason}"
        super().__init__(message, "api_key")


class InvalidTokenFormatError(ValidationError):
    """Raised when token format is invalid."""

    def __init__(self, token_type: str, reason: str):
        self.token_type = token_type
        message = f"Invalid {token_type} token format: {reason}"
        super().__init__(message, "token")


class InvalidFileError(ValidationError):
    """Raised when file validation fails."""

    def __init__(self, filename: str, reason: str):
        self.filename = filename
        message = f"Invalid file '{filename}': {reason}"
        super().__init__(message, "file", filename)


class FileTooLargeError(ValidationError):
    """Raised when file size exceeds limit."""

    def __init__(self, filename: str, actual_size: int, max_size: int):
        self.filename = filename
        self.actual_size = actual_size
        self.max_size = max_size
        message = f"File '{filename}' too large: {
            actual_size} bytes (max: {max_size} bytes)"
        super().__init__(message, "file", filename)


class UnsupportedFileTypeError(ValidationError):
    """Raised when file type is not supported."""

    def __init__(self, filename: str, file_type: str, supported_types: List[str]):
        self.filename = filename
        self.file_type = file_type
        self.supported_types = supported_types
        message = f"Unsupported file type '{file_type}' for file '{
            filename}'. Supported types: {', '.join(supported_types)}"
        super().__init__(message, "file", filename)


class InvalidRateLimitError(ValidationError):
    """Raised when rate limit format is invalid."""

    def __init__(self, rate_limit: str):
        message = f"Invalid rate limit format: {
            rate_limit}. Expected format: 'N per unit' (e.g., '100 per hour')"
        super().__init__(message, "rate_limit", rate_limit)


class ValidationErrorCollection(ValidationError):
    """Raised when multiple validation errors occur."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        error_messages = [str(error) for error in errors]
        message = f"Multiple validation errors: {'; '.join(error_messages)}"
        super().__init__(message)

    def get_field_errors(self) -> dict:
        """Get errors grouped by field."""
        field_errors = {}
        for error in self.errors:
            if error.field:
                if error.field not in field_errors:
                    field_errors[error.field] = []
                field_errors[error.field].append(error.message)
        return field_errors


class RequiredFieldMissingError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field: str):
        message = f"Required field missing: {field}"
        super().__init__(message, field)


class InvalidEnumValueError(ValidationError):
    """Raised when enum value is invalid."""

    def __init__(self, field: str, value: Any, valid_values: List[str]):
        self.valid_values = valid_values
        message = f"Invalid value '{value}' for field '{
            field}'. Valid values: {', '.join(map(str, valid_values))}"
        super().__init__(message, field, value)


class InvalidRangeError(ValidationError):
    """Raised when numeric value is outside valid range."""

    def __init__(self, field: str, value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.min_value = min_value
        self.max_value = max_value

        if min_value is not None and max_value is not None:
            message = f"Value '{value}' for field '{
                field}' must be between {min_value} and {max_value}"
        elif min_value is not None:
            message = f"Value '{value}' for field '{
                field}' must be at least {min_value}"
        elif max_value is not None:
            message = f"Value '{value}' for field '{
                field}' must be at most {max_value}"
        else:
            message = f"Value '{value}' for field '{
                field}' is outside valid range"

        super().__init__(message, field, value)


class InvalidRegexPatternError(ValidationError):
    """Raised when value doesn't match required regex pattern."""

    def __init__(self, field: str, value: Any, pattern: str):
        self.pattern = pattern
        message = f"Value '{value}' for field '{
            field}' doesn't match required pattern: {pattern}"
        super().__init__(message, field, value)
