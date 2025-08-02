"""Elasticsearch integration tests.

This module contains integration tests for Elasticsearch
functionality, including RAG service integration.
"""

from datetime import datetime
from unittest.mock import (
    Mock,
    patch,
)

import pytest

from app.schemas.rag import DocumentoLegislativo
from app.services.rag import RAGService
class TestElasticsearchIntegration:
    """Integration tests for Elasticsearch functionality."""

    @pytest.fixture
    def mock_es_client(self):
        """Create a mock Elasticsearch client for integration testing."""
        mock_client = Mock()

        # Mock successful ping
        mock_client.ping.return_value = True

        # Mock index operations
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}

        # Mock document indexing
        mock_client.index.return_value = {"_id": "test_doc_id", "result": "created"}

        # Mock search results
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "test_doc_id",
                        "_score": 0.95,
                        "_source": {
                            "content": "Test legislative content",
                            "title": "Test Law Document",
                            "source_type": "lei",
                            "summary": "This is a test document",
                            "municipio": "Test City",
                            "legislatura": "2024-2028",
                            "autor": "Test Author",
                            "categoria": "municipal",
                            "status": "aprovado",
                            "tipo_documento": "lei_ordinaria",
                            "date": "2024-01-01T00:00:00Z",
                            "tokens": 150,
                            "file_path": "/test/documents/law.pdf",
                        },
                    }
                ],
            }
        }

        return mock_client

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_service_full_workflow(self, mock_es_client):
        """Test complete RAG service workflow."""
        with patch("app.services.rag.Elasticsearch", return_value=mock_es_client):                # Mock sentence transformer
                mock_model = Mock()
                mock_model.encode.return_value = [0.1, 0.2, 0.3] * 128  # 384 dimensions
                mock_st.return_value = mock_model

                # Initialize RAG service
                rag_service = RAGService()

                # 1. Initialize index
                await rag_service.initialize_index()
                mock_es_client.indices.create.assert_called_once()

                # 2. Add document
                test_document = DocumentoLegislativo(
                    content="This is a test legislative document about municipal regulations.",
                    title="Municipal Regulation Test",
                    source_type="lei",
                    summary="Test document for integration testing",
                    municipio="Integration City",
                    legislatura="2024-2028",
                    autor="Integration Tester",
                    categoria="municipal",
                    status="aprovado",
                    tipo_documento="lei_ordinaria",
                    date=datetime.now(),
                    tokens=200,
                    file_path="/integration/test/doc.pdf",
                )

                document_id = await rag_service.add_legislative_document(test_document)
                assert document_id == "test_doc_id"
                mock_es_client.index.assert_called_once()

                # 3. Search documents
                results = await rag_service.search_legislative_documents(
                    query="municipal regulations", max_results=5
                )

                assert len(results) == 1
                assert results[0].title == "Test Law Document"
                assert results[0].score == 0.95
                mock_es_client.search.assert_called_once()

                # 4. Health check
                health = await rag_service.health_check()
                assert health["status"] == "healthy"
                assert health["elasticsearch"] == "connected"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_search_with_multiple_filters(self, mock_es_client):
        """Test RAG search with complex filtering."""
        with patch("app.services.rag.Elasticsearch", return_value=mock_es_client):                mock_model = Mock()
                mock_model.encode.return_value = [0.1] * 384
                mock_st.return_value = mock_model

                rag_service = RAGService()

                # Search with multiple filters
                await rag_service.search_legislative_documents(
                    query="urban planning",
                    max_results=10,
                    categoria="municipal",
                    source_type="lei",
                    status="aprovado",
                    legislatura="2024-2028",
                )

                # Verify search was called with correct parameters
                search_call = mock_es_client.search.call_args
                search_body = search_call[1]["body"]

                # Check filters were applied
                filters = search_body["query"]["bool"]["filter"]
                assert len(filters) == 4

                # Verify specific filter values
                filter_values = {}
                for filter_item in filters:
                    term_key = list(filter_item["term"].keys())[0]
                    filter_values[term_key] = filter_item["term"][term_key]

                assert filter_values["categoria"] == "municipal"
                assert filter_values["source_type"] == "lei"
                assert filter_values["status"] == "aprovado"
                assert filter_values["legislatura"] == "2024-2028"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rag_service_error_scenarios(self, mock_es_client):
        """Test RAG service behavior in error scenarios."""
        with patch("app.services.rag.Elasticsearch", return_value=mock_es_client):                mock_model = Mock()
                mock_model.encode.return_value = [0.1] * 384
                mock_st.return_value = mock_model

                rag_service = RAGService()

                # Test Elasticsearch connection failure
                mock_es_client.ping.return_value = False
                health = await rag_service.health_check()
                assert health["status"] == "unhealthy"
                assert health["elasticsearch"] == "disconnected"

                # Test search failure
                mock_es_client.search.side_effect = Exception("Search failed")

                try:
                    await rag_service.search_legislative_documents("test query")
                    assert False, "Expected exception was not raised"
                except Exception as e:
                    assert "Search failed" in str(e)

                # Test document indexing failure
                mock_es_client.index.side_effect = Exception("Index failed")

                test_document = DocumentoLegislativo(
                    content="Test content",
                    title="Test Title",
                    source_type="lei",
                    summary="Test summary",
                    municipio="Test City",
                    legislatura="2024-2028",
                    autor="Test Author",
                    categoria="municipal",
                    status="aprovado",
                    tipo_documento="lei_ordinaria",
                    date=datetime.now(),
                    tokens=100,
                    file_path="/test/path.pdf",
                )

                try:
                    await rag_service.add_legislative_document(test_document)
                    assert False, "Expected exception was not raised"
                except Exception as e:
                    assert "Index failed" in str(e)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_embedding_model_integration(self):
        """Test sentence transformer integration."""
        with patch("app.services.rag.Elasticsearch") as mock_es_class:                # Create a more realistic mock for sentence transformer
                mock_model = Mock()

                # Test different text inputs produce different embeddings
                def mock_encode(text):
                    # Simple hash-based mock embedding
                    hash_val = hash(text) % 1000
                    return [float(hash_val % 10) / 10.0] * 384

                mock_model.encode = mock_encode
                mock_st_class.return_value = mock_model

                # Mock ES client
                mock_es_client = Mock()
                mock_es_client.ping.return_value = True
                mock_es_client.indices.exists.return_value = True
                mock_es_class.return_value = mock_es_client

                rag_service = RAGService()

                # Test that different queries produce different embeddings
                with patch.object(rag_service, "es_client") as mock_es:
                    mock_es.search.return_value = {"hits": {"hits": []}}

                    # Search with different queries
                    await rag_service.search_legislative_documents("urban planning")
                    first_call_embedding = mock_es.search.call_args[1]["body"]["query"][
                        "bool"
                    ]["should"][0]["script_score"]["script"]["params"]["query_vector"]

                    await rag_service.search_legislative_documents("environmental law")
                    second_call_embedding = mock_es.search.call_args[1]["body"][
                        "query"
                    ]["bool"]["should"][0]["script_score"]["script"]["params"][
                        "query_vector"
                    ]

                    # Embeddings should be different for different texts
                    assert first_call_embedding != second_call_embedding

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_large_document_handling(self, mock_es_client):
        """Test handling of large documents."""
        with patch("app.services.rag.Elasticsearch", return_value=mock_es_client):                mock_model = Mock()
                mock_model.encode.return_value = [0.1] * 384
                mock_st.return_value = mock_model

                rag_service = RAGService()

                # Create a large document
                large_content = "This is a test document. " * 1000  # ~25KB of text

                large_document = DocumentoLegislativo(
                    content=large_content,
                    title="Large Test Document",
                    source_type="lei",
                    summary="A very large test document for testing",
                    municipio="Test City",
                    legislatura="2024-2028",
                    autor="Test Author",
                    categoria="municipal",
                    status="aprovado",
                    tipo_documento="lei_ordinaria",
                    date=datetime.now(),
                    tokens=5000,
                    file_path="/test/large_doc.pdf",
                )

                # Should handle large documents without issues
                document_id = await rag_service.add_legislative_document(large_document)
                assert document_id == "test_doc_id"

                # Verify the model was called with the large content
                mock_model.encode.assert_called_with(large_content)
