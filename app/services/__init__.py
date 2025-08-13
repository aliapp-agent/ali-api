"""This file contains the services for the application."""

# Lazy imports to avoid connection issues during imports
_rag_service_instance = None

def get_rag_service():
    """Get RAG service instance (lazy initialization)."""
    global _rag_service_instance
    if _rag_service_instance is None:
        from app.services.rag import RAGService
        _rag_service_instance = RAGService()
    return _rag_service_instance

# Database service uses lazy initialization to avoid connection issues during imports
try:
    from app.services.database import get_database_service
    _database_available = True
    __all__ = ["get_database_service", "get_rag_service"]
except Exception:
    # Firebase-only mode - PostgreSQL not available
    _database_available = False
    get_database_service = None
    __all__ = ["get_rag_service"]
