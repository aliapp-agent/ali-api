from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date as DateType

class DocumentoLegislativo(BaseModel):
    """Schema para documentos legislativos de Água Clara-MS"""
    id: str = Field(..., description="ID único do documento")
    source_type: str = Field(..., description="Tipo da fonte (projeto, lei, decreto, etc.)")
    title: str = Field(..., description="Título do documento")
    content: str = Field(..., description="Conteúdo completo do documento")
    summary: str = Field(..., description="Resumo do documento")
    tokens: Optional[List[float]] = Field(None, description="Embeddings do documento")
    date: DateType = Field(..., description="Data do documento")
    municipio: str = Field(default="Água Clara-MS", description="Município")
    legislatura: str = Field(..., description="Período da legislatura")
    autor: str = Field(..., description="Autor do documento")
    categoria: str = Field(..., description="Categoria (saúde, educação, etc.)")
    status: str = Field(..., description="Status atual do documento")
    tipo_documento: str = Field(..., description="Tipo específico do documento")
    file_path: Optional[str] = Field(None, description="Caminho do arquivo original")

class DocumentSearchRequest(BaseModel):
    """Request para busca de documentos"""
    query: str = Field(..., description="Texto da consulta")
    max_results: int = Field(default=5, description="Número máximo de resultados")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    source_type: Optional[str] = Field(None, description="Filtrar por tipo de fonte")
    status: Optional[str] = Field(None, description="Filtrar por status")
    legislatura: Optional[str] = Field(None, description="Filtrar por legislatura")

class DocumentSearchResult(BaseModel):
    """Resultado da busca de documentos"""
    id: str
    title: str
    summary: str
    content: str
    score: float
    categoria: str
    source_type: str
    status: str
    autor: str
    date: DateType
    legislatura: str
    tipo_documento: str

class DocumentUploadRequest(BaseModel):
    """Request para upload de documento"""
    documento: DocumentoLegislativo

class DocumentUploadResponse(BaseModel):
    """Response do upload de documento"""
    success: bool
    document_id: str
    message: str