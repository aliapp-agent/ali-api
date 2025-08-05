"""Configuration for pytest tests.

This file contains fixtures and setup configuration for all tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"

# Import app after setting environment
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set required environment variables for tests
    test_env_vars = {
        "APP_ENV": "test",
        "TESTING": "true",
        "JWT_SECRET_KEY": "test-secret-key",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000",
        "RATE_LIMIT_REQUESTS": "100",
        "RATE_LIMIT_WINDOW": "60",
    }
    
    # Set environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    yield
    
    # Cleanup is handled automatically by pytest
