"""Infrastructure layer for Ali API.

This package contains implementations of external dependencies
like databases, APIs, and messaging systems.
"""

from . import (
    external,
    messaging,
)
# Note: Container functionality not used in Firebase mode
# from .container import (
#     Container,
#     cleanup_container,
#     get_cached_container,
#     get_container,
#     get_document_service,
#     get_message_service,
#     get_session_service,
#     get_user_service,
#     setup_container,
# )

__all__ = [
    "external",
    "messaging",
    # Container functionality not used in Firebase mode
    # "Container",
    # "get_container",
    # "get_cached_container",
    # "get_user_service",
    # "get_session_service",
    # "get_message_service",
    # "get_document_service",
    # "setup_container",
    # "cleanup_container",
]
