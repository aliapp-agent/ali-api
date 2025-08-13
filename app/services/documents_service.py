"""Documents service for comprehensive document management.

This service provides full CRUD operations, search functionality,
categorization, and cloud storage integration for documents.
"""

import asyncio
import hashlib
import os
import uuid
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

from elasticsearch import Elasticsearch
# from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.schemas.documents import (
    DocumentBulkResponse,
    DocumentCreate,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentStats,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
    DocumentUploadResponse,
    MessageResponse,
)
from app.schemas.documents import DocumentCategory as DocumentCategoryEnum
from app.services import get_rag_service


class DocumentsService:
    """Service for comprehensive document management."""

    def __init__(self):
        """Initialize the documents service."""
        self.rag_service = get_rag_service()
        # RAG service now uses Qdrant instead of Elasticsearch
        self.qdrant_client = self.rag_service.qdrant_client
        self.embedding_model = self.rag_service.embedding_model
        self.collection_name = self.rag_service.collection_name

    async def create_document(
        self, document_data: DocumentCreate, user_id: int
    ) -> DocumentResponse:
        """Create a new document.

        Args:
            document_data: Document creation data
            user_id: ID of the user creating the document

        Returns:
            DocumentResponse: Created document data
        """
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())

            # Calculate tokens if not provided
            if document_data.tokens == 0:
                document_data.tokens = len(document_data.content.split())

            # Generate content embedding
            if self.embedding_model is not None:
                embedding = self.embedding_model.encode(
                    f"{document_data.title} {document_data.content}"
                ).tolist()
            else:
                # Temporary empty embedding when model is disabled
                embedding = [0.0] * 384

            # Prepare document for Elasticsearch
            now = datetime.now(timezone.utc)
            doc_dict = {
                "id": document_id,
                "title": document_data.title,
                "content": document_data.content,
                "summary": document_data.summary,
                "categoria": document_data.categoria.value,
                "tipo_documento": document_data.tipo_documento.value,
                "status": document_data.status.value,
                "municipio": document_data.municipio,
                "legislatura": document_data.legislatura,
                "autor": document_data.autor,
                "source_type": document_data.source_type,
                "file_path": document_data.file_path,
                "tokens": document_data.tokens,
                "tags": document_data.tags,
                "embedding": embedding,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "created_by": user_id,
                "updated_by": user_id,
                "date": now.isoformat(),
            }

            # Index document in Elasticsearch
            response = self.es_client.index(
                index=self.index_name, id=document_id, document=doc_dict
            )

            if response.get("result") != "created":
                raise Exception(f"Failed to create document: {response}")

            logger.info(
                "document_created",
                document_id=document_id,
                user_id=user_id,
                title=document_data.title[:100],
            )

            return DocumentResponse(
                id=document_id,
                title=document_data.title,
                content=document_data.content,
                summary=document_data.summary,
                categoria=document_data.categoria,
                tipo_documento=document_data.tipo_documento,
                status=document_data.status,
                municipio=document_data.municipio,
                legislatura=document_data.legislatura,
                autor=document_data.autor,
                source_type=document_data.source_type,
                file_path=document_data.file_path,
                tokens=document_data.tokens,
                tags=document_data.tags,
                created_at=now,
                updated_at=now,
                created_by=user_id,
                updated_by=user_id,
            )

        except Exception as e:
            logger.error(
                "document_creation_failed", error=str(e), user_id=user_id, exc_info=True
            )
            raise Exception(f"Failed to create document: {str(e)}")

    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            DocumentResponse: Document data or None if not found
        """
        try:
            response = self.es_client.get(index=self.index_name, id=document_id)

            if not response.get("found"):
                return None

            source = response["_source"]

            return DocumentResponse(
                id=source["id"],
                title=source["title"],
                content=source["content"],
                summary=source.get("summary", ""),
                categoria=DocumentCategoryEnum(source.get("categoria", "outros")),
                tipo_documento=DocumentType(source.get("tipo_documento", "manual")),
                status=DocumentStatus(source.get("status", "active")),
                municipio=source.get("municipio", ""),
                legislatura=source.get("legislatura", ""),
                autor=source.get("autor", ""),
                source_type=source.get("source_type", "manual"),
                file_path=source.get("file_path"),
                tokens=source.get("tokens", 0),
                tags=source.get("tags", []),
                created_at=datetime.fromisoformat(
                    source["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    source["updated_at"].replace("Z", "+00:00")
                ),
                created_by=source["created_by"],
                updated_by=source.get("updated_by"),
            )

        except Exception as e:
            logger.error(
                "document_retrieval_failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            return None

    async def update_document(
        self, document_id: str, update_data: DocumentUpdate, user_id: int
    ) -> Optional[DocumentResponse]:
        """Update an existing document.

        Args:
            document_id: Document ID to update
            update_data: Document update data
            user_id: ID of the user updating the document

        Returns:
            DocumentResponse: Updated document data or None if not found
        """
        try:
            # Get existing document
            existing_doc = await self.get_document(document_id)
            if not existing_doc:
                return None

            # Prepare update document
            update_dict = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": user_id,
            }

            # Update fields that are provided
            if update_data.title is not None:
                update_dict["title"] = update_data.title
            if update_data.content is not None:
                update_dict["content"] = update_data.content
                # Recalculate tokens
                update_dict["tokens"] = len(update_data.content.split())
            if update_data.summary is not None:
                update_dict["summary"] = update_data.summary
            if update_data.categoria is not None:
                update_dict["categoria"] = update_data.categoria.value
            if update_data.tipo_documento is not None:
                update_dict["tipo_documento"] = update_data.tipo_documento.value
            if update_data.status is not None:
                update_dict["status"] = update_data.status.value
            if update_data.municipio is not None:
                update_dict["municipio"] = update_data.municipio
            if update_data.legislatura is not None:
                update_dict["legislatura"] = update_data.legislatura
            if update_data.autor is not None:
                update_dict["autor"] = update_data.autor
            if update_data.source_type is not None:
                update_dict["source_type"] = update_data.source_type
            if update_data.file_path is not None:
                update_dict["file_path"] = update_data.file_path
            if update_data.tags is not None:
                update_dict["tags"] = update_data.tags

            # Regenerate embedding if content or title changed
            if "title" in update_dict or "content" in update_dict:
                current_title = update_dict.get("title", existing_doc.title)
                current_content = update_dict.get("content", existing_doc.content)
                if self.embedding_model is not None:
                    embedding = self.embedding_model.encode(
                        f"{current_title} {current_content}"
                    ).tolist()
                else:
                    # Temporary empty embedding when model is disabled
                    embedding = [0.0] * 384
                update_dict["embedding"] = embedding

            # Update document in Elasticsearch
            response = self.es_client.update(
                index=self.index_name, id=document_id, doc=update_dict
            )

            if response.get("result") not in ["updated", "noop"]:
                raise Exception(f"Failed to update document: {response}")

            logger.info(
                "document_updated",
                document_id=document_id,
                user_id=user_id,
                updated_fields=list(update_dict.keys()),
            )

            # Return updated document
            return await self.get_document(document_id)

        except Exception as e:
            logger.error(
                "document_update_failed",
                document_id=document_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to update document: {str(e)}")

    async def delete_document(self, document_id: str, user_id: int) -> bool:
        """Delete a document.

        Args:
            document_id: Document ID to delete
            user_id: ID of the user deleting the document

        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            response = self.es_client.delete(index=self.index_name, id=document_id)

            if response.get("result") == "deleted":
                logger.info(
                    "document_deleted", document_id=document_id, user_id=user_id
                )
                return True
            elif response.get("result") == "not_found":
                return False
            else:
                raise Exception(f"Unexpected delete response: {response}")

        except Exception as e:
            logger.error(
                "document_deletion_failed",
                document_id=document_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Failed to delete document: {str(e)}")

    async def search_documents(
        self, search_request: DocumentSearchRequest
    ) -> List[DocumentSearchResult]:
        """Search documents with advanced filtering and ranking.

        Args:
            search_request: Search parameters

        Returns:
            List[DocumentSearchResult]: Search results
        """
        try:
            # Build Elasticsearch query
            query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": search_request.query,
                                "fields": [
                                    "title^3",
                                    "content^2",
                                    "summary^2",
                                    "autor",
                                    "tags^1.5",
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                            }
                        }
                    ],
                    "filter": [],
                }
            }

            # Add filters
            if search_request.categoria:
                query["bool"]["filter"].append(
                    {"term": {"categoria": search_request.categoria.value}}
                )

            if search_request.status:
                query["bool"]["filter"].append(
                    {"term": {"status": search_request.status.value}}
                )

            if search_request.tipo_documento:
                query["bool"]["filter"].append(
                    {"term": {"tipo_documento": search_request.tipo_documento.value}}
                )

            if search_request.municipio:
                query["bool"]["filter"].append(
                    {"term": {"municipio": search_request.municipio}}
                )

            if search_request.legislatura:
                query["bool"]["filter"].append(
                    {"term": {"legislatura": search_request.legislatura}}
                )

            if search_request.autor:
                query["bool"]["filter"].append(
                    {"term": {"autor": search_request.autor}}
                )

            if search_request.source_type:
                query["bool"]["filter"].append(
                    {"term": {"source_type": search_request.source_type}}
                )

            if search_request.tags:
                query["bool"]["filter"].append({"terms": {"tags": search_request.tags}})

            # Date range filter
            if search_request.date_from or search_request.date_to:
                date_filter = {"range": {"created_at": {}}}
                if search_request.date_from:
                    date_filter["range"]["created_at"][
                        "gte"
                    ] = search_request.date_from.isoformat()
                if search_request.date_to:
                    date_filter["range"]["created_at"][
                        "lte"
                    ] = search_request.date_to.isoformat()
                query["bool"]["filter"].append(date_filter)

            # Execute search
            response = self.es_client.search(
                index=self.index_name,
                query=query,
                size=search_request.max_results,
                highlight={
                    "fields": {
                        "content": {"fragment_size": 150, "number_of_fragments": 1},
                        "title": {"fragment_size": 100, "number_of_fragments": 1},
                    }
                },
                _source_excludes=(
                    ["embedding"]
                    if not search_request.include_content
                    else ["embedding"]
                ),
            )

            # Process results
            results = []
            max_score = response.get("hits", {}).get("max_score", 1.0) or 1.0

            for hit in response["hits"]["hits"]:
                source = hit["_source"]

                # Calculate relevance score
                relevance_score = (hit["_score"] / max_score) if max_score > 0 else 0.0

                # Get content snippet from highlights
                content_snippet = None
                if "highlight" in hit:
                    if "content" in hit["highlight"]:
                        content_snippet = hit["highlight"]["content"][0]
                    elif "title" in hit["highlight"]:
                        content_snippet = hit["highlight"]["title"][0]

                if not content_snippet and search_request.include_content:
                    # Fallback to truncated content
                    content = source.get("content", "")
                    if len(content) > 200:
                        content_snippet = content[:200] + "..."
                    else:
                        content_snippet = content

                result = DocumentSearchResult(
                    id=source["id"],
                    title=source["title"],
                    summary=source.get("summary", ""),
                    categoria=DocumentCategoryEnum(source.get("categoria", "outros")),
                    tipo_documento=DocumentType(source.get("tipo_documento", "manual")),
                    status=DocumentStatus(source.get("status", "active")),
                    municipio=source.get("municipio", ""),
                    autor=source.get("autor", ""),
                    created_at=datetime.fromisoformat(
                        source["created_at"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        source["updated_at"].replace("Z", "+00:00")
                    ),
                    relevance_score=relevance_score,
                    content_snippet=content_snippet,
                    tags=source.get("tags", []),
                )

                results.append(result)

            logger.info(
                "documents_searched",
                query=search_request.query,
                results_count=len(results),
                max_results=search_request.max_results,
            )

            return results

        except Exception as e:
            logger.error(
                "document_search_failed",
                query=search_request.query,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Document search failed: {str(e)}")

    async def get_document_stats(self) -> DocumentStats:
        """Get comprehensive document statistics.

        Returns:
            DocumentStats: Document statistics
        """
        try:
            # Get total count
            total_response = self.es_client.count(index=self.index_name)
            total_documents = total_response["count"]

            # Get aggregations
            agg_response = self.es_client.search(
                index=self.index_name,
                size=0,
                aggs={
                    "by_category": {"terms": {"field": "categoria", "size": 50}},
                    "by_status": {"terms": {"field": "status", "size": 10}},
                    "by_type": {"terms": {"field": "tipo_documento", "size": 20}},
                    "by_municipality": {"terms": {"field": "municipio", "size": 100}},
                    "recent_documents": {
                        "date_range": {
                            "field": "created_at",
                            "ranges": [{"from": "now-30d", "to": "now"}],
                        }
                    },
                    "updated_today": {
                        "date_range": {
                            "field": "updated_at",
                            "ranges": [{"from": "now/d", "to": "now"}],
                        }
                    },
                },
            )

            aggregations = agg_response["aggregations"]

            return DocumentStats(
                total_documents=total_documents,
                by_category={
                    bucket["key"]: bucket["doc_count"]
                    for bucket in aggregations["by_category"]["buckets"]
                },
                by_status={
                    bucket["key"]: bucket["doc_count"]
                    for bucket in aggregations["by_status"]["buckets"]
                },
                by_type={
                    bucket["key"]: bucket["doc_count"]
                    for bucket in aggregations["by_type"]["buckets"]
                },
                by_municipality={
                    bucket["key"]: bucket["doc_count"]
                    for bucket in aggregations["by_municipality"]["buckets"]
                },
                total_storage_size=0,  # Would need to calculate from file sizes
                recent_documents=aggregations["recent_documents"]["buckets"][0][
                    "doc_count"
                ],
                updated_today=aggregations["updated_today"]["buckets"][0]["doc_count"],
            )

        except Exception as e:
            logger.error("document_stats_failed", error=str(e), exc_info=True)
            raise Exception(f"Failed to get document statistics: {str(e)}")

    async def bulk_update_documents(
        self, document_ids: List[str], operation: str, user_id: int, **kwargs
    ) -> DocumentBulkResponse:
        """Perform bulk operations on multiple documents.

        Args:
            document_ids: List of document IDs
            operation: Operation type (delete, archive, activate, etc.)
            user_id: ID of the user performing the operation
            **kwargs: Additional operation parameters

        Returns:
            DocumentBulkResponse: Bulk operation results
        """
        try:
            success_count = 0
            error_count = 0
            errors = []

            for doc_id in document_ids:
                try:
                    if operation == "delete":
                        success = await self.delete_document(doc_id, user_id)
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Document {doc_id} not found")

                    elif operation == "archive":
                        update_data = DocumentUpdate(status=DocumentStatus.ARCHIVED)
                        result = await self.update_document(
                            doc_id, update_data, user_id
                        )
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Document {doc_id} not found")

                    elif operation == "activate":
                        update_data = DocumentUpdate(status=DocumentStatus.ACTIVE)
                        result = await self.update_document(
                            doc_id, update_data, user_id
                        )
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Document {doc_id} not found")

                    elif operation == "change_category":
                        if "categoria" not in kwargs:
                            error_count += 1
                            errors.append(
                                f"Category not specified for document {doc_id}"
                            )
                            continue

                        update_data = DocumentUpdate(categoria=kwargs["categoria"])
                        result = await self.update_document(
                            doc_id, update_data, user_id
                        )
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Document {doc_id} not found")

                    else:
                        error_count += 1
                        errors.append(f"Unknown operation: {operation}")

                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing document {doc_id}: {str(e)}")

            success = error_count == 0
            message = f"Processed {len(document_ids)} documents. {success_count} successful, {error_count} failed."

            logger.info(
                "bulk_operation_completed",
                operation=operation,
                user_id=user_id,
                total_docs=len(document_ids),
                success_count=success_count,
                error_count=error_count,
            )

            return DocumentBulkResponse(
                success=success,
                processed_count=len(document_ids),
                success_count=success_count,
                error_count=error_count,
                errors=errors,
                message=message,
            )

        except Exception as e:
            logger.error(
                "bulk_operation_failed",
                operation=operation,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Bulk operation failed: {str(e)}")


# Create global instance
documents_service = DocumentsService()
