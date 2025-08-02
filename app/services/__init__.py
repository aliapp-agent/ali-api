"""This file contains the services for the application."""

from app.services.rag import rag_service

# Database service uses lazy initialization to avoid connection issues during imports
try:
    from app.services.database import get_database_service
    _database_available = True
    __all__ = ["get_database_service", "rag_service"]
except Exception:
    # Firebase-only mode - PostgreSQL not available
    _database_available = False
    get_database_service = None
    __all__ = ["rag_service"]
