"""Schemas for RAG (Retrieval-Augmented Generation) functionality."""

from datetime import date as DateType
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)


class DocumentoLegislativo(BaseModel):
    """Schema para documento legislativo."""

    id: Optional[str] = Field(None, description="ID único do documento")
    source_type: str = Field(..., description="Tipo da fonte (lei, decreto, etc.)")
    title: str = Field(..., description="Título do documento")
    content: str = Field(..., description="Conteúdo completo do documento")
    summary: str = Field(default="", description="Resumo do documento")
    tokens: int = Field(default=0, description="Número de tokens")
    date: Optional[DateType] = Field(None, description="Data do documento")
    municipio: str = Field(default="", description="Município de origem")
    legislatura: str = Field(default="", description="Legislatura")
    autor: str = Field(default="", description="Autor do documento")
    categoria: str = Field(default="", description="Categoria do documento")
    status: str = Field(default="ativo", description="Status do documento")
    tipo_documento: str = Field(default="", description="Tipo específico do documento")
    file_path: str = Field(default="", description="Caminho do arquivo original")


class DocumentSearchRequest(BaseModel):
    """Schema para requisição de busca de documentos."""

    query: str = Field(..., description="Texto da consulta")
    max_results: int = Field(default=5, description="Número máximo de resultados")
    categoria: Optional[str] = Field(None, description="Filtro por categoria")
    source_type: Optional[str] = Field(None, description="Filtro por tipo de fonte")
    status: Optional[str] = Field(None, description="Filtro por status")
    legislatura: Optional[str] = Field(None, description="Filtro por legislatura")


class DocumentSearchResult(BaseModel):
    """Schema para resultado de busca de documentos."""

    id: str = Field(..., description="ID único do documento")
    title: str = Field(..., description="Título do documento")
    content: str = Field(..., description="Conteúdo do documento")
    source_type: str = Field(..., description="Tipo da fonte")
    summary: str = Field(default="", description="Resumo do documento")
    municipio: str = Field(default="", description="Município")
    legislatura: str = Field(default="", description="Legislatura")
    autor: str = Field(default="", description="Autor")
    categoria: str = Field(default="", description="Categoria")
    status: str = Field(default="", description="Status")
    tipo_documento: str = Field(default="", description="Tipo do documento")
    date: Optional[DateType] = Field(None, description="Data do documento")
    tokens: int = Field(default=0, description="Número de tokens")
    file_path: str = Field(default="", description="Caminho do arquivo")
    score: float = Field(..., description="Score de relevância da busca")


class DocumentUploadRequest(BaseModel):
    """Schema para requisição de upload de documento."""

    documento: DocumentoLegislativo = Field(..., description="Dados do documento")


class DocumentUploadResponse(BaseModel):
    """Schema para resposta de upload de documento."""

    success: bool = Field(..., description="Indica se o upload foi bem-sucedido")
    document_id: str = Field(..., description="ID do documento criado")
    message: str = Field(..., description="Mensagem de status")
