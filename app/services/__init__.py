"""This file contains the services for the application."""

from app.services.rag import rag_service

# Database service is only imported when explicitly needed
# to avoid PostgreSQL connection during Firebase-only usage
try:
    from app.services.database import database_service

    __all__ = ["database_service", "rag_service"]
except Exception:
    # Firebase-only mode - PostgreSQL not available
    database_service = None
    __all__ = ["rag_service"]
