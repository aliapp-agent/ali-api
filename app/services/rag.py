from datetime import (
    datetime,
    timezone,
)
from typing import (
    Dict,
    List,
    Optional,
)

from elasticsearch import Elasticsearch
# from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import (
    DocumentoLegislativo,
    DocumentSearchResult,
)


class RAGService:
    def __init__(self):
        # Configurar Elasticsearch com autenticação se necessário
        es_config = {
            "hosts": [settings.ELASTICSEARCH_URL],
            "request_timeout": settings.ELASTICSEARCH_TIMEOUT,
            "retry_on_timeout": True,
        }

        # Adicionar API key se fornecida
        if settings.ELASTICSEARCH_API_KEY:
            es_config["api_key"] = settings.ELASTICSEARCH_API_KEY

        self.es_client = Elasticsearch(**es_config)
        # self.embedding_model = SentenceTransformer(settings.RAG_EMBEDDING_MODEL)
        self.embedding_model = None  # Temporarily disabled
        self.index_name = settings.RAG_INDEX_NAME

    async def initialize_index(self):
        """Cria o índice do Elasticsearch se não existir."""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "title": {"type": "text"},
                        "source_type": {"type": "keyword"},
                        "summary": {"type": "text"},
                        "municipio": {"type": "keyword"},
                        "legislatura": {"type": "keyword"},
                        "autor": {"type": "keyword"},
                        "categoria": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "tipo_documento": {"type": "keyword"},
                        "embedding": {"type": "dense_vector", "dims": 384},
                        "date": {"type": "date"},
                        "tokens": {"type": "integer"},
                        "file_path": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Índice {self.index_name} criado com sucesso")

    async def add_legislative_document(self, document: DocumentoLegislativo) -> str:
        """Adiciona um documento legislativo ao índice."""
        # Temporarily use empty embedding when model is disabled
        if self.embedding_model is not None:
            embedding = self.embedding_model.encode(document.content).tolist()
        else:
            embedding = [0.0] * 384  # Default embedding size for sentence-transformers

        doc = {
            "content": document.content,
            "title": document.title,
            "source_type": document.source_type,
            "summary": document.summary,
            "municipio": document.municipio,
            "legislatura": document.legislatura,
            "autor": document.autor,
            "categoria": document.categoria,
            "status": document.status,
            "tipo_documento": document.tipo_documento,
            "embedding": embedding,
            "date": document.date,
            "tokens": document.tokens,
            "file_path": document.file_path,
            "timestamp": datetime.now(timezone.utc),
        }

        result = self.es_client.index(index=self.index_name, body=doc)
        logger.info(f"Documento adicionado com ID: {result['_id']}")
        return result["_id"]

    async def search_legislative_documents(
        self,
        query: str,
        max_results: int = 5,
        categoria: Optional[str] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        legislatura: Optional[str] = None,
    ) -> List[DocumentSearchResult]:
        """Busca documentos legislativos usando busca semântica e filtros."""
        # Gerar embedding da query
        if self.embedding_model is not None:
            query_embedding = self.embedding_model.encode(query).tolist()
        else:
            query_embedding = [0.0] * 384  # Default embedding size for sentence-transformers

        # Construir filtros
        filters = []
        if categoria:
            filters.append({"term": {"categoria": categoria}})
        if source_type:
            filters.append({"term": {"source_type": source_type}})
        if status:
            filters.append({"term": {"status": status}})
        if legislatura:
            filters.append({"term": {"legislatura": legislatura}})

        # Query híbrida: busca semântica + busca textual
        search_body = {
            "size": max_results,
            "query": {
                "bool": {
                    "should": [
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                    "params": {"query_vector": query_embedding},
                                },
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^2",
                                    "content",
                                    "summary^1.5",
                                ],
                                "type": "best_fields",
                            }
                        },
                    ],
                    "filter": filters if filters else [],
                }
            },
        }

        response = self.es_client.search(index=self.index_name, body=search_body)

        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            result = DocumentSearchResult(
                id=hit["_id"],
                title=source["title"],
                content=source["content"],
                source_type=source["source_type"],
                summary=source.get("summary", ""),
                municipio=source.get("municipio", ""),
                legislatura=source.get("legislatura", ""),
                autor=source.get("autor", ""),
                categoria=source.get("categoria", ""),
                status=source.get("status", ""),
                tipo_documento=source.get("tipo_documento", ""),
                date=source.get("date"),
                tokens=source.get("tokens", 0),
                file_path=source.get("file_path", ""),
                score=hit["_score"],
            )
            results.append(result)

        return results

    async def health_check(self) -> Dict[str, str]:
        """Verifica a saúde do serviço RAG."""
        try:
            # Verificar conexão com Elasticsearch
            es_health = self.es_client.ping()

            # Verificar se o índice existe
            index_exists = self.es_client.indices.exists(index=self.index_name)

            return {
                "status": "healthy" if es_health and index_exists else "unhealthy",
                "elasticsearch": "connected" if es_health else "disconnected",
                "index": "exists" if index_exists else "missing",
                "embedding_model": settings.RAG_EMBEDDING_MODEL,
            }
        except Exception as e:
            logger.error(f"RAG health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}


# Criar instância global do serviço
rag_service = RAGService()
