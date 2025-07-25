"""Tests for health check endpoints.

This module contains tests for the health check functionality,
including API health, database connectivity, and component status.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.services.database import DatabaseService


class TestHealthCheck:
    """Test suite for health check endpoints."""

    def test_health_check_success(self, client: TestClient):
        """Test successful health check with all components healthy."""
        with patch("app.main.database_service") as mock_db_service:
            # Mock database health check as successful
            mock_db_service.health_check = AsyncMock(return_value=True)

            response = client.get("/health")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "environment" in data
            assert "timestamp" in data
            assert "components" in data

            # Check components
            components = data["components"]
            assert components["api"] == "healthy"
            assert components["database"] == "healthy"

    def test_health_check_database_unhealthy(self, client: TestClient):
        """Test health check when database is unhealthy."""
        with patch("app.main.database_service") as mock_db_service:
            # Mock database health check as failed
            mock_db_service.health_check = AsyncMock(return_value=False)

            response = client.get("/health")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            data = response.json()
            assert data["status"] == "degraded"

            # Check components
            components = data["components"]
            assert components["api"] == "healthy"
            assert components["database"] == "unhealthy"

    def test_health_check_exception(self, client: TestClient):
        """Test health check when an exception occurs."""
        with patch("app.main.database_service") as mock_db_service:
            # Mock database service to raise an exception
            mock_db_service.health_check = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = client.get("/health")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["error"] == "Health check failed"
            assert "error_id" in data
            assert "timestamp" in data

    def test_health_check_response_structure(self, client: TestClient):
        """Test that health check response has the correct structure."""
        with patch("app.main.database_service") as mock_db_service:
            mock_db_service.health_check = AsyncMock(return_value=True)

            response = client.get("/health")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()

            # Required fields
            required_fields = ["status", "version", "environment", "components", "timestamp"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Status should be a string
            assert isinstance(data["status"], str)
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

            # Components should be a dictionary
            assert isinstance(data["components"], dict)
            assert "api" in data["components"]
            assert "database" in data["components"]

    def test_health_check_security_headers(self, client: TestClient):
        """Test that health check response includes security headers."""
        with patch("app.main.database_service") as mock_db_service:
            mock_db_service.health_check = AsyncMock(return_value=True)

            response = client.get("/health")

            # Check for security headers
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection"
            ]

            for header in expected_headers:
                assert header in response.headers

    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client):
        """Test health check using async client."""
        with patch("app.main.database_service") as mock_db_service:
            mock_db_service.health_check = AsyncMock(return_value=True)

            response = await async_client.get("/health")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "healthy"

    def test_health_check_rate_limiting(self, client: TestClient):
        """Test that health check endpoint respects rate limiting."""
        # This test would need to make many requests quickly
        # For now, just ensure the endpoint is accessible
        with patch("app.main.database_service") as mock_db_service:
            mock_db_service.health_check = AsyncMock(return_value=True)

            # Make a few requests to ensure it works
            for _ in range(5):
                response = client.get("/health")
                assert response.status_code == status.HTTP_200_OK


class TestDatabaseHealthCheck:
    """Test suite for database health check functionality."""

    @pytest.mark.asyncio
    async def test_database_service_health_check_success(self, test_db_session):
        """Test successful database health check."""
        db_service = DatabaseService()

        # Mock the session creation
        with patch.object(db_service, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_session.execute.return_value = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = await db_service.health_check()

            assert result is True
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_health_check_failure(self):
        """Test database health check failure."""
        db_service = DatabaseService()

        # Mock the session creation to raise an exception
        with patch.object(db_service, 'get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Database connection failed")

            result = await db_service.health_check()

            assert result is False


class TestApiHealthCheck:
    """Test suite for API v1 health check endpoint."""

    def test_api_v1_health_check(self, client: TestClient):
        """Test API v1 health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestRAGHealthCheck:
    """Test suite for RAG service health check."""

    def test_rag_health_check_success(self, client: TestClient, mock_elasticsearch):
        """Test successful RAG health check."""
        with patch("app.services.rag.RAGService") as mock_rag_service:
            # Mock RAG service health check
            mock_instance = mock_rag_service.return_value
            mock_instance.health_check = AsyncMock(return_value={
                "status": "healthy",
                "elasticsearch": "connected",
                "index_exists": True
            })

            response = client.get("/api/v1/rag/health")

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "healthy"

    def test_rag_health_check_failure(self, client: TestClient):
        """Test RAG health check failure."""
        with patch("app.services.rag.RAGService") as mock_rag_service:
            # Mock RAG service health check to fail
            mock_instance = mock_rag_service.return_value
            mock_instance.health_check = AsyncMock(side_effect=Exception("ES connection failed"))

            response = client.get("/api/v1/rag/health")

            # The endpoint should handle the exception gracefully
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
