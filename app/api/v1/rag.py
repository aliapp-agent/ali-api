"""RAG API endpoints for legislative documents."""

from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from app.api.v1.auth import get_current_session
from app.core.limiter import limiter
from app.core.logging import logger
from app.schemas.rag import (
    DocumentoLegislativo,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services.document_processor import DocumentProcessor
from app.services import get_rag_service

router = APIRouter()
doc_processor = DocumentProcessor()


@router.post("/search", response_model=List[DocumentSearchResult])
@limiter.limit("10/minute")
async def search_documents(
    request: Request,
    search_request: DocumentSearchRequest,
    session=Depends(get_current_session),
):
    """Buscar documentos legislativos."""
    try:
        rag_service = get_rag_service()
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
        logger.error(f"Erro na busca de documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    upload_request: DocumentUploadRequest,
    session=Depends(get_current_session),
):
    """Upload de documento legislativo."""
    try:
        rag_service = get_rag_service()
        document_id = await rag_service.add_legislative_document(
            upload_request.documento
        )
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            message="Documento adicionado com sucesso",
        )
    except Exception as e:
        logger.error(f"Erro no upload de documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@router.post("/documents/upload")
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session=Depends(get_current_session),
):
    """Upload de arquivo para processamento."""
    try:
        # Processar arquivo
        content = await doc_processor.process_file(file)

        # Dividir em chunks se necessário
        chunks = doc_processor.chunk_text(content)

        document_ids = []
        for i, chunk in enumerate(chunks):
            # Criar documento para cada chunk
            documento = DocumentoLegislativo(
                title=f"{file.filename} - Parte {i+1}",
                content=chunk,
                source_type="upload",
                summary="",
                municipio="",
                legislatura="",
                autor="",
                categoria="documento",
                status="ativo",
                tipo_documento="upload",
                tokens=len(chunk.split()),
                file_path=file.filename,
            )

            rag_service = get_rag_service()
            doc_id = await rag_service.add_legislative_document(documento)
            document_ids.append(doc_id)

        return {
            "success": True,
            "message": f"Arquivo processado em {len(chunks)} chunks",
            "document_ids": document_ids,
            "filename": file.filename,
        }
    except Exception as e:
        logger.error(f"Erro no upload de arquivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


@router.get("/search")
@limiter.limit("20/minute")
async def search_knowledge_base(
    request: Request,
    query: str,
    top_k: int = 5,
    session=Depends(get_current_session),
):
    """Busca simples na base de conhecimento."""
    try:
        search_request = DocumentSearchRequest(query=query, max_results=top_k)
        rag_service = get_rag_service()
        results = await rag_service.search_legislative_documents(
            query=search_request.query, max_results=search_request.max_results
        )
        return {"query": query, "results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health():
    """Health check do serviço RAG."""
    try:
        rag_service = get_rag_service()
        health_status = await rag_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Erro no health check RAG: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
