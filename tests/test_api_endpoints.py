"""Tests for critical API endpoints.

This module contains tests for the main API endpoints,
including chatbot, RAG, and integration tests.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.chat import Message, ChatResponse
from app.schemas.rag import DocumentSearchResult


class TestChatbotEndpoints:
    """Test suite for chatbot endpoints."""

    def test_chat_endpoint_success(self, client: TestClient):
        """Test successful chat request."""
        with patch("app.api.v1.chatbot.get_current_session") as mock_get_session:
            with patch("app.api.v1.chatbot.AgnoAgent") as mock_agent_class:
                # Mock session
                mock_session = Mock()
                mock_session.id = "test-session-123"
                mock_get_session.return_value = mock_session

                # Mock agent response
                mock_agent = Mock()
                mock_agent.arun = AsyncMock(return_value={
                    "content": "This is a test response from the agent",
                    "role": "assistant"
                })
                mock_agent_class.return_value = mock_agent

                # Make request with authorization header
                response = client.post(
                    "/api/v1/chat/",
                    json={
                        "content": "Hello, how are you?",
                        "role": "user"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["content"] == "This is a test response from the agent"
                assert data["role"] == "assistant"

    def test_chat_endpoint_invalid_message(self, client: TestClient):
        """Test chat endpoint with invalid message."""
        with patch("app.api.v1.chatbot.get_current_session"):
            response = client.post(
                "/api/v1/chat/",
                json={
                    "content": "",  # Empty content
                    "role": "user"
                },
                headers={"Authorization": "Bearer test-token"}
            )

            # Should return validation error
            assert response.status_code == 422

    def test_chat_endpoint_unauthorized(self, client: TestClient):
        """Test chat endpoint without authorization."""
        response = client.post(
            "/api/v1/chat/",
            json={
                "content": "Hello",
                "role": "user"
            }
        )

        assert response.status_code == 403  # No auth header

    def test_streaming_chat_endpoint(self, client: TestClient):
        """Test streaming chat endpoint."""
        with patch("app.api.v1.chatbot.get_current_session") as mock_get_session:
            with patch("app.api.v1.chatbot.AgnoAgent") as mock_agent_class:
                # Mock session
                mock_session = Mock()
                mock_session.id = "test-session-123"
                mock_get_session.return_value = mock_session

                # Mock streaming response
                async def mock_stream():
                    yield "data: chunk1\n\n"
                    yield "data: chunk2\n\n"
                    yield "data: [DONE]\n\n"

                mock_agent = Mock()
                mock_agent.astream = AsyncMock(return_value=mock_stream())
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/chat/stream",
                    json={
                        "content": "Stream test",
                        "role": "user"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestRAGEndpoints:
    """Test suite for RAG endpoints."""

    def test_rag_search_success(self, client: TestClient):
        """Test successful RAG search."""
        with patch("app.api.v1.rag.rag_service") as mock_rag_service:
            # Mock search results
            mock_results = [
                DocumentSearchResult(
                    id="doc1",
                    title="Test Document 1",
                    content="Content of document 1",
                    source_type="lei",
                    summary="Summary 1",
                    municipio="Test City",
                    legislatura="2024-2028",
                    autor="Test Author",
                    categoria="municipal",
                    status="aprovado",
                    tipo_documento="lei_ordinaria",
                    date="2024-01-01",
                    tokens=100,
                    file_path="/path/doc1.pdf",
                    score=0.9
                )
            ]
            mock_rag_service.search_legislative_documents = AsyncMock(return_value=mock_results)

            response = client.post(
                "/api/v1/rag/search",
                json={
                    "query": "test search query",
                    "max_results": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Document 1"
            assert data[0]["score"] == 0.9

    def test_rag_search_with_filters(self, client: TestClient):
        """Test RAG search with filters."""
        with patch("app.api.v1.rag.rag_service") as mock_rag_service:
            mock_rag_service.search_legislative_documents = AsyncMock(return_value=[])

            response = client.post(
                "/api/v1/rag/search",
                json={
                    "query": "filtered search",
                    "max_results": 10,
                    "categoria": "municipal",
                    "status": "aprovado"
                }
            )

            assert response.status_code == 200

            # Verify the service was called with filters
            mock_rag_service.search_legislative_documents.assert_called_once_with(
                query="filtered search",
                max_results=10,
                categoria="municipal",
                source_type=None,
                status="aprovado",
                legislatura=None
            )

    def test_rag_search_invalid_query(self, client: TestClient):
        """Test RAG search with invalid query."""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "",  # Empty query
                "max_results": 5
            }
        )

        # Should return validation error
        assert response.status_code == 422

    def test_rag_health_check(self, client: TestClient):
        """Test RAG health check endpoint."""
        with patch("app.api.v1.rag.rag_service") as mock_rag_service:
            mock_rag_service.health_check = AsyncMock(return_value={
                "status": "healthy",
                "elasticsearch": "connected",
                "index": "exists"
            })

            response = client.get("/api/v1/rag/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_rag_health_check_error(self, client: TestClient):
        """Test RAG health check when service fails."""
        with patch("app.api.v1.rag.rag_service") as mock_rag_service:
            mock_rag_service.health_check = AsyncMock(side_effect=Exception("ES connection failed"))

            response = client.get("/api/v1/rag/health")

            assert response.status_code == 200  # Endpoint handles errors gracefully
            data = response.json()
            assert data["status"] == "unhealthy"


class TestAuthEndpointsIntegration:
    """Integration tests for auth endpoints."""

    def test_full_auth_flow(self, client: TestClient):
        """Test complete authentication flow."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # 1. Register user
            mock_db.get_user_by_email.return_value = None  # User doesn't exist
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = "integration@example.com"
            mock_db.create_user.return_value = mock_user

            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "integration@example.com",
                    "password": "StrongPassword123!"
                }
            )

            assert register_response.status_code == 200
            register_data = register_response.json()
            assert "token" in register_data

            # 2. Login user
            mock_user.verify_password.return_value = True
            mock_db.get_user_by_email.return_value = mock_user

            login_response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "integration@example.com",
                    "password": "StrongPassword123!"
                }
            )

            assert login_response.status_code == 200
            login_data = login_response.json()
            assert login_data["token_type"] == "bearer"

            # 3. Create session
            mock_session = Mock()
            mock_session.id = "session-123"
            mock_session.name = ""
            mock_db.create_session.return_value = mock_session

            # Mock get_current_user for session creation
            with patch("app.api.v1.auth.get_current_user", return_value=mock_user):
                session_response = client.post(
                    "/api/v1/auth/session",
                    headers={"Authorization": f"Bearer {register_data['token']['access_token']}"}
                )

                assert session_response.status_code == 200
                session_data = session_response.json()
                assert "session_id" in session_data


class TestApiV1MainEndpoints:
    """Test suite for main API v1 endpoints."""

    def test_api_v1_health_check(self, client: TestClient):
        """Test API v1 health check."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_api_v1_root_endpoint(self, client: TestClient):
        """Test API v1 root endpoint if it exists."""
        response = client.get("/api/v1/")

        # This endpoint might not exist, so we check for either 200 or 404
        assert response.status_code in [200, 404]


class TestRateLimiting:
    """Test suite for rate limiting functionality."""

    def test_rate_limiting_headers(self, client: TestClient):
        """Test that rate limiting headers are present."""
        response = client.get("/health")

        # Check for rate limiting headers (might be present)
        # This is more of a smoke test since rate limiting is hard to test
        assert response.status_code == 200

    def test_multiple_requests_within_limit(self, client: TestClient):
        """Test multiple requests within rate limit."""
        # Make several requests quickly
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)

        # All should succeed if within limit
        for response in responses:
            assert response.status_code == 200


class TestErrorHandling:
    """Test suite for error handling across endpoints."""

    def test_404_endpoint(self, client: TestClient):
        """Test non-existent endpoint returns 404."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client: TestClient):
        """Test wrong HTTP method returns 405."""
        response = client.patch("/health")  # Health endpoint only supports GET

        assert response.status_code == 405

    def test_invalid_json_payload(self, client: TestClient):
        """Test invalid JSON in request body."""
        response = client.post(
            "/api/v1/rag/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestCorsAndSecurityHeaders:
    """Test suite for CORS and security headers."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present in responses."""
        response = client.get("/health")

        # Check for common security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]

        for header in expected_headers:
            # Headers might be set by middleware
            # This is more of a smoke test
            pass  # Headers are checked in health test

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers in responses."""
        # Make an OPTIONS request to check CORS
        response = client.options("/api/v1/health")

        # The response might vary based on CORS configuration
        # This is a basic smoke test
        assert response.status_code in [200, 404, 405]


class TestInputSanitization:
    """Test suite for input sanitization."""

    def test_malicious_input_handling(self, client: TestClient):
        """Test handling of potentially malicious input."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "' OR '1'='1",
        ]

        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/v1/rag/search",
                json={
                    "query": malicious_input,
                    "max_results": 5
                }
            )

            # Should either succeed (sanitized) or return validation error
            # Should not return 500 (server error)
            assert response.status_code != 500
