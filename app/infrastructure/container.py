"""Dependency injection container for Ali API.

This module provides a dependency injection container to manage
dependencies between domain services, repositories, and other components.
"""

from typing import Dict, Any, Type, TypeVar, Optional
from functools import lru_cache
from sqlmodel import Session

from app.core.config import settings
from app.core.logging import logger

# Domain repositories (interfaces)
from app.domain.repositories import (
    UserRepositoryInterface,
    SessionRepositoryInterface,
    MessageRepositoryInterface,
    DocumentRepositoryInterface,
)

# Infrastructure repositories (concrete implementations)
from app.infrastructure.database import (
    PostgresUserRepository,
    PostgresSessionRepository,
    PostgresMessageRepository,
    PostgresDocumentRepository,
)

# Domain services
from app.domain.services import (
    UserDomainService,
    SessionDomainService,
    MessageDomainService,
    DocumentDomainService,
)

T = TypeVar('T')


class Container:
    """Dependency injection container for managing application dependencies."""
    
    def __init__(self):
        """Initialize the container."""
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._setup_dependencies()
    
    def _setup_dependencies(self) -> None:
        """Set up dependency bindings."""
        # Repository bindings (singletons within request scope)
        self.bind_factory(
            UserRepositoryInterface,
            lambda db: PostgresUserRepository(db)
        )
        
        self.bind_factory(
            SessionRepositoryInterface,
            lambda db: PostgresSessionRepository(db)
        )
        
        self.bind_factory(
            MessageRepositoryInterface,
            lambda db: PostgresMessageRepository(db)
        )
        
        self.bind_factory(
            DocumentRepositoryInterface,
            lambda db: PostgresDocumentRepository(db)
        )
        
        # Domain service bindings
        self.bind_factory(
            UserDomainService,
            self._create_user_service
        )
        
        self.bind_factory(
            SessionDomainService,
            self._create_session_service
        )
        
        self.bind_factory(
            MessageDomainService,
            self._create_message_service
        )
        
        self.bind_factory(
            DocumentDomainService,
            self._create_document_service
        )
    
    def bind_singleton(self, interface: Type[T], instance: T) -> None:
        """Bind a singleton instance to an interface.
        
        Args:
            interface: The interface type
            instance: The singleton instance
        """
        key = self._get_key(interface)
        self._singletons[key] = instance
        logger.debug(f"Bound singleton {key}")
    
    def bind_factory(self, interface: Type[T], factory: callable) -> None:
        """Bind a factory function to an interface.
        
        Args:
            interface: The interface type
            factory: Factory function that creates instances
        """
        key = self._get_key(interface)
        self._factories[key] = factory
        logger.debug(f"Bound factory {key}")
    
    def resolve(self, interface: Type[T], db_session: Optional[Session] = None) -> T:
        """Resolve an instance of the given interface.
        
        Args:
            interface: The interface type to resolve
            db_session: Database session for repository creation
            
        Returns:
            T: Instance of the requested type
            
        Raises:
            ValueError: If the interface is not registered
        """
        key = self._get_key(interface)
        
        # Check for singleton first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check for factory
        if key in self._factories:
            factory = self._factories[key]
            
            # Special handling for repositories that need db_session
            if interface in [
                UserRepositoryInterface,
                SessionRepositoryInterface,
                MessageRepositoryInterface,
                DocumentRepositoryInterface
            ]:
                if db_session is None:
                    raise ValueError(f"Database session required for {key}")
                return factory(db_session)
            
            # For services, resolve their dependencies
            return factory()
        
        raise ValueError(f"No binding found for {key}")
    
    def resolve_user_service(self, db_session: Session) -> UserDomainService:
        """Resolve user domain service with dependencies."""
        factory = self._create_user_service()
        return factory(db_session)
    
    def resolve_session_service(self, db_session: Session) -> SessionDomainService:
        """Resolve session domain service with dependencies."""
        factory = self._create_session_service()
        return factory(db_session)
    
    def resolve_message_service(self, db_session: Session) -> MessageDomainService:
        """Resolve message domain service with dependencies."""
        factory = self._create_message_service()
        return factory(db_session)
    
    def resolve_document_service(self, db_session: Session) -> DocumentDomainService:
        """Resolve document domain service with dependencies."""
        factory = self._create_document_service()
        return factory(db_session)
    
    def _create_user_service(self):
        """Create user service factory."""
        def factory(db_session: Session) -> UserDomainService:
            user_repo = PostgresUserRepository(db_session)
            return UserDomainService(user_repo)
        return factory
    
    def _create_session_service(self):
        """Create session service factory."""
        def factory(db_session: Session) -> SessionDomainService:
            session_repo = PostgresSessionRepository(db_session)
            user_repo = PostgresUserRepository(db_session)
            return SessionDomainService(session_repo, user_repo)
        return factory
    
    def _create_message_service(self):
        """Create message service factory."""
        def factory(db_session: Session) -> MessageDomainService:
            message_repo = PostgresMessageRepository(db_session)
            session_repo = PostgresSessionRepository(db_session)
            user_repo = PostgresUserRepository(db_session)
            return MessageDomainService(message_repo, session_repo, user_repo)
        return factory
    
    def _create_document_service(self):
        """Create document service factory."""
        def factory(db_session: Session) -> DocumentDomainService:
            document_repo = PostgresDocumentRepository(db_session)
            user_repo = PostgresUserRepository(db_session)
            return DocumentDomainService(document_repo, user_repo)
        return factory
    
    def _get_key(self, interface: Type) -> str:
        """Get string key for interface type.
        
        Args:
            interface: The interface type
            
        Returns:
            str: String key for the interface
        """
        return f"{interface.__module__}.{interface.__name__}"


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance.
    
    Returns:
        Container: The global container instance
    """
    global _container
    if _container is None:
        _container = Container()
        logger.info("Dependency injection container initialized")
    return _container


@lru_cache()
def get_cached_container() -> Container:
    """Get cached container instance for FastAPI dependencies.
    
    Returns:
        Container: Cached container instance
    """
    return get_container()


# Convenience functions for FastAPI dependency injection
def get_user_service(db_session: Session) -> UserDomainService:
    """Get user domain service for FastAPI dependency injection.
    
    Args:
        db_session: Database session
        
    Returns:
        UserDomainService: User service instance
    """
    container = get_cached_container()
    return container.resolve_user_service(db_session)


def get_session_service(db_session: Session) -> SessionDomainService:
    """Get session domain service for FastAPI dependency injection.
    
    Args:
        db_session: Database session
        
    Returns:
        SessionDomainService: Session service instance
    """
    container = get_cached_container()
    return container.resolve_session_service(db_session)


def get_message_service(db_session: Session) -> MessageDomainService:
    """Get message domain service for FastAPI dependency injection.
    
    Args:
        db_session: Database session
        
    Returns:
        MessageDomainService: Message service instance
    """
    container = get_cached_container()
    return container.resolve_message_service(db_session)


def get_document_service(db_session: Session) -> DocumentDomainService:
    """Get document domain service for FastAPI dependency injection.
    
    Args:
        db_session: Database session
        
    Returns:
        DocumentDomainService: Document service instance
    """
    container = get_cached_container()
    return container.resolve_document_service(db_session)


def setup_container() -> None:
    """Set up the dependency injection container."""
    container = get_container()
    logger.info("Dependency injection container setup completed")


def cleanup_container() -> None:
    """Clean up the dependency injection container."""
    global _container
    if _container:
        _container._services.clear()
        _container._singletons.clear()
        _container._factories.clear()
        _container = None
        logger.info("Dependency injection container cleaned up")