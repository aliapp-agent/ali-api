"""Simple dependency injection for Ali API.

This module provides minimal dependency injection for FastAPI,
focusing only on essential domain services where business logic is complex.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.services.database import DatabaseService
from app.infrastructure.container import get_container
from app.domain.services import (
    MessageDomainService,
    SessionDomainService,
    UserDomainService,
    DocumentDomainService,
)

# Singleton database service (keep existing simple approach)
_db_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """Get the database service singleton.
    
    Returns:
        DatabaseService: The database service instance
    """
    return _db_service


def get_db_session() -> Session:
    """Get database session for domain services.
    
    Returns:
        Session: SQLModel database session
    """
    return _db_service.get_session_maker()


# Simple domain service dependencies
def get_message_service(
    db_session: Session = Depends(get_db_session)
) -> MessageDomainService:
    """Get message domain service.
    
    Args:
        db_session: Database session
        
    Returns:
        MessageDomainService: Message service instance
    """
    container = get_container()
    return container.resolve_message_service(db_session)


def get_session_service(
    db_session: Session = Depends(get_db_session)
) -> SessionDomainService:
    """Get session domain service.
    
    Args:
        db_session: Database session
        
    Returns:
        SessionDomainService: Session service instance
    """
    container = get_container()
    return container.resolve_session_service(db_session)


def get_user_service(
    db_session: Session = Depends(get_db_session)
) -> UserDomainService:
    """Get user domain service.
    
    Args:
        db_session: Database session
        
    Returns:
        UserDomainService: User service instance
    """
    container = get_container()
    return container.resolve_user_service(db_session)


def get_document_service(
    db_session: Session = Depends(get_db_session)
) -> DocumentDomainService:
    """Get document domain service.
    
    Args:
        db_session: Database session
        
    Returns:
        DocumentDomainService: Document service instance
    """
    container = get_container()
    return container.resolve_document_service(db_session)


# Type aliases for cleaner endpoint signatures
DatabaseServiceDep = Annotated[DatabaseService, Depends(get_database_service)]
DbSessionDep = Annotated[Session, Depends(get_db_session)]
MessageServiceDep = Annotated[MessageDomainService, Depends(get_message_service)]
SessionServiceDep = Annotated[SessionDomainService, Depends(get_session_service)]
UserServiceDep = Annotated[UserDomainService, Depends(get_user_service)]
DocumentServiceDep = Annotated[DocumentDomainService, Depends(get_document_service)]