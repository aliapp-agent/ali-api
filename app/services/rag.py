from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from app.core.config import settings
from app.schemas.rag import DocumentoLegislativo, DocumentSearchResult

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self._initialize_client()
        self._initialize_embedding_model()
    
    def _initialize_client(self):
        """Initialize Elasticsearch client for Serverless"""
        try:
            self.client = Elasticsearch(
                settings.ELASTICSEARCH_URL,
                api_key=settings.ELASTICSEARCH_API_KEY,
                request_timeout=30,
                retry_on_timeout=True,
                max_retries=3
            )
            
            if self.client.ping():
                logger.info("Successfully connected to Elasticsearch Serverless")
                info = self.client.info()
                logger.info(f"Connected to cluster: {info['cluster_name']}")
            else:
                logger.error("Failed to connect to Elasticsearch Serverless")
                
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client: {e}")
            self.client = None
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model"""
        try:
            self.embedding_model = SentenceTransformer(settings.RAG_EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.RAG_EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
    
    def create_index(self) -> bool:
        """Create index with mapping for legislative documents"""
        try:
            if not self.client:
                return False
            
            index_mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "summary": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 384
                        },
                        "date": {"type": "date"},
                        "municipio": {"type": "keyword"},
                        "legislatura": {"type": "keyword"},
                        "autor": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "categoria": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "tipo_documento": {"type": "keyword"},
                        "file_path": {"type": "keyword"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            
            if not self.client.indices.exists(index=settings.RAG_INDEX_NAME):
                self.client.indices.create(
                    index=settings.RAG_INDEX_NAME,
                    body=index_mapping
                )
                logger.info(f"Created index: {settings.RAG_INDEX_NAME}")
            else:
                logger.info(f"Index {settings.RAG_INDEX_NAME} already exists")
            
            return True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def add_legislative_document(self, documento: DocumentoLegislativo) -> bool:
        """Add legislative document to index"""
        try:
            if not self.client or not self.embedding_model:
                return False
            
            # Generate embedding from content + summary
            text_for_embedding = f"{documento.title} {documento.summary} {documento.content}"
            embedding = self.embedding_model.encode(text_for_embedding).tolist()
            
            doc = {
                "id": documento.id,
                "source_type": documento.source_type,
                "title": documento.title,
                "content": documento.content,
                "summary": documento.summary,
                "embedding": embedding,
                "date": documento.date.isoformat(),
                "municipio": documento.municipio,
                "legislatura": documento.legislatura,
                "autor": documento.autor,
                "categoria": documento.categoria,
                "status": documento.status,
                "tipo_documento": documento.tipo_documento,
                "file_path": documento.file_path,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.client.index(
                index=settings.RAG_INDEX_NAME,
                id=documento.id,  # Use document ID as Elasticsearch ID
                body=doc
            )
            
            logger.info(f"Added legislative document: {documento.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding legislative document: {e}")
            return False
    
    def search_legislative_documents(
        self, 
        query: str, 
        max_results: int = None,
        categoria: Optional[str] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        legislatura: Optional[str] = None
    ) -> List[DocumentSearchResult]:
        """Search legislative documents with filters"""
        try:
            if not self.client or not self.embedding_model:
                return []
            
            max_results = max_results or settings.RAG_MAX_RESULTS
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build filters
            filters = []
            if categoria:
                filters.append({"term": {"categoria": categoria}})
            if source_type:
                filters.append({"term": {"source_type": source_type}})
            if status:
                filters.append({"term": {"status": status}})
            if legislatura:
                filters.append({"term": {"legislatura": legislatura}})
            
            # Build query
            base_query = {"match_all": {}}
            if filters:
                base_query = {
                    "bool": {
                        "must": filters
                    }
                }
            
            search_body = {
                "query": {
                    "script_score": {
                        "query": base_query,
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                },
                "size": max_results,
                "_source": [
                    "id", "title", "summary", "content", "categoria", 
                    "source_type", "status", "autor", "date", 
                    "legislatura", "tipo_documento"
                ]
            }
            
            response = self.client.search(
                index=settings.RAG_INDEX_NAME,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append(DocumentSearchResult(
                    id=source["id"],
                    title=source["title"],
                    summary=source["summary"],
                    content=source["content"],
                    score=hit["_score"],
                    categoria=source["categoria"],
                    source_type=source["source_type"],
                    status=source["status"],
                    autor=source["autor"],
                    date=source["date"],
                    legislatura=source["legislatura"],
                    tipo_documento=source["tipo_documento"]
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching legislative documents: {e}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get specific document by ID"""
        try:
            if not self.client:
                return None
            
            response = self.client.get(
                index=settings.RAG_INDEX_NAME,
                id=document_id
            )
            
            return response["_source"]
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {e}")
            return None
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        try:
            if not self.client:
                return []
            
            search_body = {
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {
                            "field": "categoria",
                            "size": 100
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=settings.RAG_INDEX_NAME,
                body=search_body
            )
            
            categories = []
            for bucket in response["aggregations"]["categories"]["buckets"]:
                categories.append(bucket["key"])
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    # Adicionar este método à classe RAGService
    
    async def health_check(self) -> dict:
    '''Verificar saúde do Elasticsearch.'''
    try:
        health = await self.es_client.cluster.health()
        return {
            "status": health["status"],
            "cluster_name": health["cluster_name"],
            "number_of_nodes": health["number_of_nodes"]
        }
    except Exception as e:
        raise Exception(f"Elasticsearch não disponível: {str(e)}")
        
        try:
            if not self.client:
                return {"status": "error", "message": "Client not initialized"}
            
            if self.client.ping():
                info = self.client.info()
                count_response = self.client.count(index=settings.RAG_INDEX_NAME)
                
                return {
                    "status": "healthy",
                    "cluster_name": info["cluster_name"],
                    "version": info["version"]["number"],
                    "index_name": settings.RAG_INDEX_NAME,
                    "total_documents": count_response["count"],
                    "mode": "serverless",
                    "municipio": "Água Clara-MS"
                }
            else:
                return {"status": "error", "message": "Connection failed"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global RAG service instance
rag_service = RAGService()