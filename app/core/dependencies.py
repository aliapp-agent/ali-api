"""Simple dependency injection for Ali API - Firebase Mode.

This module provides minimal dependency injection for FastAPI,
using Firebase Firestore as the primary database.
"""

from typing import Annotated

from fastapi import Depends

from app.services.database import DatabaseService, get_database_service as _get_database_service
from app.services.message_service import MessageService, get_message_service as _get_message_service


def get_database_service() -> DatabaseService:
    """Get the Firebase database service singleton.

    Returns:
        DatabaseService: The Firebase database service instance
    """
    return _get_database_service()


def get_message_service() -> MessageService:
    """Get the message service singleton.

    Returns:
        MessageService: The message service instance
    """
    return _get_message_service()


# Type aliases for cleaner endpoint signatures
DatabaseServiceDep = Annotated[DatabaseService, Depends(get_database_service)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]