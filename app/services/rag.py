from datetime import (
    datetime,
    timezone,
)
from typing import (
    Dict,
    List,
    Optional,
)

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import (
    DocumentoLegislativo,
    DocumentSearchResult,
)


class RAGService:
    def __init__(self):
        # Configurar Qdrant Client
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
            timeout=120
        )
        
        # Inicializar modelo de embedding
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Mesmo modelo usado nos embeddings
        
        # Nome da collection no Qdrant
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    async def initialize_index(self):
        """Verifica se a collection do Qdrant existe."""
        try:
            # Verificar se a collection existe
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if collection_exists:
                logger.info(f"Collection '{self.collection_name}' já existe no Qdrant")
            else:
                logger.warning(f"Collection '{self.collection_name}' não existe no Qdrant")
                
        except Exception as e:
            logger.error(f"Erro ao verificar collection no Qdrant: {e}")

    async def add_legislative_document(self, document: DocumentoLegislativo) -> str:
        """Adiciona um documento legislativo ao Qdrant."""
        try:
            # Gerar embedding do documento
            embedding = self.embedding_model.encode(document.content).tolist()

            # Preparar payload do documento
            payload = {
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
                "date": document.date.isoformat() if document.date else None,
                "tokens": document.tokens,
                "file_path": document.file_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Adicionar ponto ao Qdrant
            from qdrant_client.models import PointStruct
            import uuid
            
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )

            result = self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Documento adicionado ao Qdrant com ID: {point_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documento ao Qdrant: {e}")
            raise

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        categoria: Optional[str] = None,
        municipio: Optional[str] = None,
    ) -> List[Dict]:
        """Busca documentos similares usando Qdrant."""
        try:
            # Gerar embedding da query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Construir filtros se necessário
            filter_conditions = []
            if categoria:
                filter_conditions.append(
                    FieldCondition(key="categoria", match=MatchValue(value=categoria))
                )
            if municipio:
                filter_conditions.append(
                    FieldCondition(key="municipio", match=MatchValue(value=municipio))
                )
            
            # Criar filtro se houver condições
            search_filter = None
            if filter_conditions:
                search_filter = Filter(must=filter_conditions)
            
            # Fazer a busca no Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter,
                with_payload=True,
                score_threshold=0.3  # Threshold mínimo de similaridade
            )
            
            # Formatar resultados
            results = []
            for result in search_results:
                payload = result.payload
                results.append({
                    'id': result.id,
                    'score': float(result.score),
                    'title': payload.get('title', 'Sem título'),
                    'content': payload.get('content', ''),
                    'municipio': payload.get('municipio', ''),
                    'categoria': payload.get('categoria', ''),
                    'source_type': payload.get('source_type', ''),
                    'timestamp': payload.get('timestamp'),
                })
            
            logger.info(f"Busca RAG executada: '{query}' - {len(results)} resultados encontrados")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca Qdrant: {e}")
            return []

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
        # Usar o novo mét-odo search_similar
        results = await self.search_similar(
            query=query,
            top_k=max_results,
            categoria=categoria,
            municipio=None  # Pode ser mapeado de outro parâmetro se necessário
        )
        
        # Converter para DocumentSearchResult se necessário
        document_results = []
        for result in results:
            doc_result = DocumentSearchResult(
                id=str(result['id']),
                score=result['score'],
                title=result['title'],
                content=result['content'],
                source_type=result['source_type'],
                municipio=result['municipio'],
                timestamp=result['timestamp']
            )
            document_results.append(doc_result)
        
        return document_results

    async def health_check(self) -> Dict[str, str]:
        """Verifica a saúde do serviço RAG."""
        try:
            # Verificar conexão com Qdrant
            collections = self.qdrant_client.get_collections()
            
            # Verificar se a collection existe
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if collection_exists:
                # Verificar quantidade de vetores na collection
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                vector_count = collection_info.points_count
                
                return {
                    "status": "healthy",
                    "qdrant_connection": "ok",
                    "collection": self.collection_name,
                    "collection_exists": "yes",
                    "vector_count": str(vector_count),
                    "embedding_model": "all-MiniLM-L6-v2"
                }
            else:
                return {
                    "status": "unhealthy",
                    "qdrant_connection": "ok",
                    "collection": self.collection_name,
                    "collection_exists": "no",
                    "error": f"Collection '{self.collection_name}' não encontrada"
                }
                
        except Exception as e:
            logger.error(f"RAG health check failed: {e}")
            return {
                "status": "unhealthy",
                "qdrant_connection": "error",
                "error": str(e)
            }


# Removido instância global para evitar inicialização durante import
# Use get_rag_service() from app.services para obter a instância
