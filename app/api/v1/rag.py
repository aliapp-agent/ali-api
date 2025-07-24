"""RAG API endpoints for legislative documents."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.rag import (
    DocumentoLegislativo,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUploadRequest,
    DocumentUploadResponse
)
from app.services.rag import rag_service
from app.api.v1.auth import get_current_session
from app.core.limiter import limiter
from app.core.config import settings

router = APIRouter()

@router.post("/search", response_model=List[DocumentSearchResult])
@limiter.limit("10/minute")
async def search_documents(
    request: Request,
    search_request: DocumentSearchRequest,
    session = Depends(get_current_session)
):
    """Buscar documentos legislativos."""
    try:
        results = await rag_service.search_legislative_documents(
            query=search_request.query,
            max_results=search_request.max_results,
            categoria=search_request.categoria,
            source_type=search_request.source_type,
            status=search_request.status,
            legislatura=search_request.legislatura
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")

@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    upload_request: DocumentUploadRequest,
    session = Depends(get_current_session)
):
    """Upload de documento legislativo."""
    try:
        document_id = await rag_service.add_legislative_document(upload_request.documento)
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            message="Documento adicionado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.get("/health")
async def rag_health():
    """Verificar saúde do serviço RAG."""
    try:
        # Verificar conexão com Elasticsearch
        health = await rag_service.health_check()
        return {"status": "healthy", "elasticsearch": health}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serviço indisponível: {str(e)}")