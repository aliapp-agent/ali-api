"""Configuration for pytest tests.

This file contains fixtures and setup configuration for all tests.
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import Mock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.main import app as fastapi_app
from app.models.base import SQLModel
from app.services.database import DatabaseService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Test settings with overrides."""
    # Override settings for testing
    os.environ["APP_ENV"] = "test"
    os.environ["POSTGRES_URL"] = "sqlite:///test.db"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["LLM_API_KEY"] = "test-llm-key"

    return settings


@pytest.fixture
def test_db_engine():
    """Create a test database engine using SQLite in memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after test
    SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_database_service(test_db_session):
    """Mock DatabaseService for testing."""
    service = Mock(spec=DatabaseService)
    service.get_session.return_value = test_db_session
    return service


@pytest.fixture
def client(settings, mock_database_service) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    # Override dependencies
    # Settings already configured globally

    with TestClient(fastapi_app) as test_client:
        yield test_client

    # Clean up
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(settings) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    # Settings already configured globally

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from the LLM.",
                    "role": "assistant"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client for testing."""
    mock_es = Mock()
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_score": 0.9,
                    "_source": {
                        "content": "Test document 1",
                        "metadata": {"title": "Test Doc 1"}
                    }
                },
                {
                    "_score": 0.8,
                    "_source": {
                        "content": "Test document 2",
                        "metadata": {"title": "Test Doc 2"}
                    }
                }
            ]
        }
    }
    return mock_es


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        f.write("Test content for file processing")
        temp_file_path = f.name

    yield temp_file_path

    # Clean up
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    }


@pytest.fixture
def sample_rag_query():
    """Sample RAG query for testing."""
    return {
        "query": "What is the capital of Brazil?",
        "max_results": 5,
        "threshold": 0.7
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "content": "Hello, how can you help me?",
        "role": "user"
    }


# Mark all tests as asyncio
pytest_plugins = ("pytest_asyncio",)
