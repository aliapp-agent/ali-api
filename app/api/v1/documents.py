"""Comprehensive documents API endpoints.

This module provides full CRUD operations, advanced search, categorization,
file upload, and bulk operations for document management.
"""

from typing import List, Optional
import time
import asyncio

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

from app.api.v1.auth import get_current_session, get_current_user
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.session import Session
from app.models.user import User
from app.schemas.documents import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentBulkOperation,
    DocumentBulkUpdate,
    DocumentBulkResponse,
    DocumentStats,
    DocumentStatus,
    DocumentCategory,
    DocumentType,
    MessageResponse,
)
from app.services.documents_service import documents_service
from app.services.document_processor import DocumentProcessor
from app.services.rag import rag_service

router = APIRouter()
doc_processor = DocumentProcessor()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_document(
    request: Request,
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new document.
    
    Args:
        request: FastAPI request object for rate limiting
        document_data: Document creation data
        current_user: Authenticated user
        
    Returns:
        DocumentResponse: Created document data
    """
    try:
        document = await documents_service.create_document(document_data, current_user.id)
        return document
    except Exception as e:
        logger.error("document_creation_endpoint_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
@limiter.limit("100/minute")
async def get_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a document by ID.
    
    Args:
        request: FastAPI request object for rate limiting
        document_id: Document ID
        current_user: Authenticated user
        
    Returns:
        DocumentResponse: Document data
    """
    try:
        document = await documents_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_retrieval_endpoint_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.put("/{document_id}", response_model=DocumentResponse)
@limiter.limit("30/minute")
async def update_document(
    request: Request,
    document_id: str,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update an existing document.
    
    Args:
        request: FastAPI request object for rate limiting
        document_id: Document ID to update
        update_data: Document update data
        current_user: Authenticated user
        
    Returns:
        DocumentResponse: Updated document data
    """
    try:
        document = await documents_service.update_document(document_id, update_data, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_update_endpoint_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=MessageResponse)
@limiter.limit("20/minute")
async def delete_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a document.
    
    Args:
        request: FastAPI request object for rate limiting
        document_id: Document ID to delete
        current_user: Authenticated user
        
    Returns:
        MessageResponse: Deletion confirmation
    """
    try:
        success = await documents_service.delete_document(document_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return MessageResponse(
            message="Document deleted successfully",
            success=True,
            data={"document_id": document_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_deletion_endpoint_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search and Discovery
# ============================================================================

@router.post("/search", response_model=List[DocumentSearchResult])
@limiter.limit("50/minute")
async def search_documents(
    request: Request,
    search_request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search documents with advanced filtering and ranking.
    
    Args:
        request: FastAPI request object for rate limiting
        search_request: Search parameters
        current_user: Authenticated user
        
    Returns:
        List[DocumentSearchResult]: Search results
    """
    try:
        results = await documents_service.search_documents(search_request)
        return results
    except Exception as e:
        logger.error("document_search_endpoint_failed", query=search_request.query, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[DocumentSearchResult])
@limiter.limit("50/minute")
async def simple_search(
    request: Request,
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, description="Maximum results", ge=1, le=100),
    categoria: Optional[DocumentCategory] = Query(None, description="Filter by category"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    municipio: Optional[str] = Query(None, description="Filter by municipality"),
    current_user: User = Depends(get_current_user),
):
    """Simple search endpoint with query parameters.
    
    Args:
        request: FastAPI request object for rate limiting
        q: Search query
        limit: Maximum results
        categoria: Filter by category
        status: Filter by status
        municipio: Filter by municipality
        current_user: Authenticated user
        
    Returns:
        List[DocumentSearchResult]: Search results
    """
    try:
        search_request = DocumentSearchRequest(
            query=q,
            max_results=limit,
            categoria=categoria,
            status=status,
            municipio=municipio,
        )
        results = await documents_service.search_documents(search_request)
        return results
    except Exception as e:
        logger.error("simple_search_endpoint_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# File Upload and Processing
# ============================================================================

@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    categoria: DocumentCategory = Form(DocumentCategory.OUTROS),
    municipio: str = Form(""),
    legislatura: str = Form(""),
    autor: str = Form(""),
    auto_process: bool = Form(True),
    chunk_size: int = Form(1000),
    current_user: User = Depends(get_current_user),
):
    """Upload and process a document file.
    
    Args:
        request: FastAPI request object for rate limiting
        file: Uploaded file
        title: Document title (optional, will use filename if not provided)
        categoria: Document category
        municipio: Municipality
        legislatura: Legislature
        autor: Author
        auto_process: Whether to auto-process with OCR/text extraction
        chunk_size: Text chunk size for processing
        current_user: Authenticated user
        
    Returns:
        DocumentUploadResponse: Upload results
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Process file content
        content = await doc_processor.process_file(file)
        
        if not content:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Use filename as title if not provided
        document_title = title or file.filename
        
        # Split content into chunks if needed
        chunks = doc_processor.chunk_text(content, chunk_size) if auto_process else [content]
        
        document_ids = []
        for i, chunk in enumerate(chunks):
            chunk_title = f"{document_title}" if len(chunks) == 1 else f"{document_title} - Part {i+1}"
            
            document_data = DocumentCreate(
                title=chunk_title,
                content=chunk,
                summary="",
                categoria=categoria,
                tipo_documento=DocumentType.UPLOAD,
                status=DocumentStatus.ACTIVE,
                municipio=municipio,
                legislatura=legislatura,
                autor=autor,
                source_type="upload",
                file_path=file.filename,
                tokens=len(chunk.split()),
            )
            
            document = await documents_service.create_document(document_data, current_user.id)
            document_ids.append(document.id)
        
        processing_time = time.time() - start_time
        
        logger.info(
            "document_upload_completed",
            filename=file.filename,
            chunks_created=len(chunks),
            processing_time=processing_time,
            user_id=current_user.id
        )
        
        return DocumentUploadResponse(
            success=True,
            document_ids=document_ids,
            message=f"File processed successfully into {len(chunks)} document(s)",
            filename=file.filename,
            file_size=file.size or 0,
            chunks_created=len(chunks),
            processing_time=processing_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_upload_failed", filename=file.filename, error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk/delete", response_model=DocumentBulkResponse)
@limiter.limit("5/minute")
async def bulk_delete_documents(
    request: Request,
    operation_data: DocumentBulkOperation,
    current_user: User = Depends(get_current_user),
):
    """Bulk delete multiple documents.
    
    Args:
        request: FastAPI request object for rate limiting
        operation_data: Bulk operation data
        current_user: Authenticated user
        
    Returns:
        DocumentBulkResponse: Bulk operation results
    """
    try:
        result = await documents_service.bulk_update_documents(
            operation_data.document_ids,
            "delete",
            current_user.id
        )
        return result
    except Exception as e:
        logger.error("bulk_delete_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/update", response_model=DocumentBulkResponse)
@limiter.limit("5/minute")
async def bulk_update_documents(
    request: Request,
    update_data: DocumentBulkUpdate,
    current_user: User = Depends(get_current_user),
):
    """Bulk update multiple documents.
    
    Args:
        request: FastAPI request object for rate limiting
        update_data: Bulk update data
        current_user: Authenticated user
        
    Returns:
        DocumentBulkResponse: Bulk operation results
    """
    try:
        kwargs = {}
        if update_data.categoria:
            kwargs["categoria"] = update_data.categoria
        if update_data.status:
            kwargs["status"] = update_data.status
        if update_data.tags:
            kwargs["tags"] = update_data.tags
        
        result = await documents_service.bulk_update_documents(
            update_data.document_ids,
            update_data.operation,
            current_user.id,
            **kwargs
        )
        return result
    except Exception as e:
        logger.error("bulk_update_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics and Analytics
# ============================================================================

@router.get("/stats", response_model=DocumentStats)
@limiter.limit("20/minute")
async def get_document_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive document statistics.
    
    Args:
        request: FastAPI request object for rate limiting
        current_user: Authenticated user
        
    Returns:
        DocumentStats: Document statistics
    """
    try:
        stats = await documents_service.get_document_stats()
        return stats
    except Exception as e:
        logger.error("document_stats_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Legacy RAG Endpoints (for backward compatibility)
# ============================================================================

@router.post("/rag/search", response_model=List[DocumentSearchResult])
@limiter.limit("10/minute")
async def rag_search_documents(
    request: Request,
    search_request: DocumentSearchRequest,
    session: Session = Depends(get_current_session),
):
    """Legacy RAG search endpoint for backward compatibility.
    
    Args:
        request: FastAPI request object for rate limiting
        search_request: Search parameters
        session: Current session
        
    Returns:
        List[DocumentSearchResult]: Search results
    """
    try:
        # Use the RAG service for backward compatibility
        results = await rag_service.search_legislative_documents(
            query=search_request.query,
            max_results=search_request.max_results,
            categoria=getattr(search_request, "categoria", None),
            source_type=getattr(search_request, "source_type", None),
            status=getattr(search_request, "status", None),
            legislatura=getattr(search_request, "legislatura", None),
        )
        return results
    except Exception as e:
        logger.error("rag_search_failed", query=search_request.query, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def documents_health():
    """Health check for documents service.
    
    Returns:
        dict: Health status
    """
    try:
        # Check Elasticsearch connection
        health_status = await rag_service.health_check()
        
        # Add documents service specific checks
        stats = await documents_service.get_document_stats()
        
        return {
            "status": "healthy",
            "elasticsearch": health_status,
            "total_documents": stats.total_documents,
            "service": "documents",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("documents_health_check_failed", error=str(e))
        return {
            "status": "unhealthy", 
            "error": str(e),
            "service": "documents",
            "timestamp": time.time()
        }