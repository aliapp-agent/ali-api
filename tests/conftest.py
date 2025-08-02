"""Configuration for pytest tests.

This file contains fixtures and setup configuration for all tests.
Firebase-enabled testing configuration with integrated Firebase mocks.
"""

import asyncio
import json
import os
import sys
import tempfile
from typing import (
    AsyncGenerator,
    Generator,
)
from unittest.mock import (
    AsyncMock,
    Mock,
    patch,
)

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import our mock services
from tests.mocks import (
    create_mock_firebase_credentials,
    mock_firebase_auth,
    mock_firestore,
    mock_qdrant_client,
)

# ============================================================================
# FIREBASE MOCKS - Integrated into conftest.py
# ============================================================================


class MockFirebaseAdmin:
    """Mock Firebase Admin SDK."""

    def __init__(self):
        self.auth = mock_firebase_auth
        self.firestore = mock_firestore
        self.storage = MockFirebaseStorage()

    def initialize_app(self, *args, **kwargs):
        return Mock()

    def credentials(self):
        class Certificate:
            def __init__(self, *args, **kwargs):
                pass

        return Certificate


class MockFirebaseAuth:
    """Mock Firebase Auth."""

    def create_user(self, *args, **kwargs):
        return Mock(uid="test-uid")

    def get_user(self, uid):
        return Mock(uid=uid, email="test@example.com")

    def verify_id_token(self, token):
        return {"uid": "test-uid", "email": "test@example.com"}

    def update_user(self, uid, **kwargs):
        return True

    def delete_user(self, uid):
        return True


class MockFirestore:
    """Mock Firestore client."""

    def client(self):
        return MockFirestoreClient()


class MockFirestoreClient:
    """Mock Firestore client."""

    def collection(self, name):
        return MockCollection()

    def document(self, path):
        return MockDocument()


class MockCollection:
    """Mock Firestore collection."""

    def document(self, doc_id):
        return MockDocument()

    def add(self, data):
        return Mock(), Mock()

    def get(self):
        return []

    def where(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, *args):
        return self


class MockDocument:
    """Mock Firestore document."""

    def get(self):
        return Mock(exists=True, to_dict=lambda: {"test": "data"})

    def set(self, data):
        return Mock()

    def update(self, data):
        return Mock()

    def delete(self):
        return Mock()


class MockFirebaseStorage:
    """Mock Firebase Storage."""

    def bucket(self, name=None):
        return MockBucket()


class MockBucket:
    """Mock Storage bucket."""

    def blob(self, name):
        return MockBlob()


class MockBlob:
    """Mock Storage blob."""

    def upload_from_string(self, data):
        return Mock()

    def download_as_text(self):
        return "mock file content"

    def delete(self):
        return Mock()


def patch_firebase_imports():
    """Patch Firebase imports by injecting mocks into sys.modules."""
    mock_admin = MockFirebaseAdmin()

    # Create mock modules and inject them into sys.modules
    mock_modules = {
        "firebase_admin": Mock(
            initialize_app=mock_admin.initialize_app,
            credentials=Mock(Certificate=Mock),
            auth=mock_admin.auth,
            firestore=mock_admin.firestore,
            storage=mock_admin.storage,
        ),
        "firebase_admin.auth": mock_admin.auth,
        "firebase_admin.firestore": mock_admin.firestore,
        "firebase_admin.storage": mock_admin.storage,
        "firebase_admin.credentials": Mock(Certificate=Mock),
        "google.cloud.firestore": mock_admin.firestore,
        "google.cloud.storage": mock_admin.storage,
        "google.cloud.logging": Mock(),
    }

    # Inject mocks into sys.modules
    original_modules = {}
    for module_name, mock_module in mock_modules.items():
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = mock_module

    return original_modules


def setup_test_environment():
    """Setup test environment with Firebase mocks."""
    # Set test environment variables
    os.environ.update(
        {
            "APP_ENV": "test",
            "FIREBASE_PROJECT_ID": "test-project",
            "FIREBASE_CREDENTIALS_PATH": "/tmp/test-firebase-credentials.json",
            "FIREBASE_STORAGE_BUCKET": "test-project.appspot.com",
            "FIREBASE_REGION": "us-central1",
            "QDRANT_URL": "http://localhost:6333",
            "JWT_SECRET_KEY": "test-secret-key",
            "LLM_API_KEY": "test-llm-key",
            "POSTGRES_URL": "postgresql://postgres:postgres@localhost:5432/test_db",
        }
    )

    # Patch Firebase imports
    return patch_firebase_imports()


# Apply patches immediately when this module is imported
# Only if we're in a test environment
if "pytest" in sys.modules or os.environ.get("APP_ENV") == "test":
    # Set environment variables first
    os.environ.update(
        {
            "APP_ENV": "test",
            "FIREBASE_PROJECT_ID": "test-project",
            "FIREBASE_CREDENTIALS_PATH": "/tmp/test-firebase-credentials.json",
            "FIREBASE_STORAGE_BUCKET": "test-project.appspot.com",
            "FIREBASE_REGION": "us-central1",
            "QDRANT_URL": "http://localhost:6333",
            "JWT_SECRET_KEY": "test-secret-key",
            "LLM_API_KEY": "test-llm-key",
            "POSTGRES_URL": "postgresql://postgres:postgres@localhost:5432/test_db",
        }
    )

    # Apply Firebase mocks to sys.modules
    patch_firebase_imports()
    
    # Mock DatabaseService to avoid PostgreSQL connection during tests
    from unittest.mock import Mock, AsyncMock, patch
    
    # Create a mock DatabaseService
    mock_db_service = Mock()
    mock_db_service.health_check = AsyncMock(return_value=True)
    mock_db_service.get_user_by_email = AsyncMock(return_value=None)
    mock_db_service.create_user = AsyncMock()
    mock_db_service.get_user_sessions = AsyncMock(return_value=[])
    mock_db_service.create_session = AsyncMock()
    mock_db_service.get_session = AsyncMock(return_value=None)
    mock_db_service.update_session = AsyncMock()
    mock_db_service.delete_session = AsyncMock()
    
    # Patch the get_database_service function before any imports
    def mock_get_database_service():
        return mock_db_service
    
    # Apply the patch globally
    patch('app.services.database.get_database_service', mock_get_database_service).start()
    patch('app.core.dependencies.get_database_service', mock_get_database_service).start()

# ============================================================================
# END FIREBASE MOCKS
# ============================================================================

# Import app components - Firebase mocks already applied above
from app.core.config import settings


# Mock Firebase services before importing the app
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with mocked services."""
    # Create temporary Firebase credentials file
    temp_dir = tempfile.mkdtemp()
    credentials_path = os.path.join(temp_dir, "test-firebase-credentials.json")

    with open(credentials_path, "w") as f:
        json.dump(create_mock_firebase_credentials(), f)

    # Set environment variables
    os.environ["FIREBASE_CREDENTIALS_PATH"] = credentials_path
    os.environ["USE_MOCK_SERVICES"] = "true"
    os.environ["TESTING"] = "true"

    # Mock Firebase services
    with (
        patch("firebase_admin.initialize_app"),
        patch("firebase_admin.auth"),
        patch("firebase_admin.firestore"),
        # patch("app.services.firebase_auth.firebase_auth_service", mock_firebase_auth),
        # patch("app.infrastructure.firestore.user_repository.firestore", mock_firestore),
        # patch("app.services.rag.qdrant_client", mock_qdrant_client),
    ):
        yield

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings with Firebase overrides."""
    # Override settings for testing
    os.environ["APP_ENV"] = "test"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["LLM_API_KEY"] = "test-llm-key"
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["METRICS_ENABLED"] = "false"
    os.environ["PROMETHEUS_ENABLED"] = "false"

    # Firebase test settings
    os.environ["FIREBASE_PROJECT_ID"] = "test-project"
    os.environ["FIREBASE_CREDENTIALS_PATH"] = "/tmp/test-firebase-credentials.json"
    os.environ["FIREBASE_STORAGE_BUCKET"] = "test-project.appspot.com"
    os.environ["FIREBASE_REGION"] = "us-central1"

    # Qdrant test settings
    os.environ["QDRANT_URL"] = "http://localhost:6333"

    return settings


@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK."""
    with (
        patch("firebase_admin.initialize_app") as mock_init,
        patch("firebase_admin.credentials.Certificate") as mock_cert,
        # patch("firebase_admin.firestore.client") as mock_firestore,
        patch("firebase_admin.auth") as mock_auth,
        patch("firebase_admin.storage") as mock_storage,
    ):

        # Mock Firestore client
        # mock_firestore_client = Mock()
        # mock_firestore.return_value = mock_firestore_client

        # Mock Auth
        mock_auth.create_user = AsyncMock(return_value=Mock(uid="test-uid"))
        mock_auth.get_user = AsyncMock(
            return_value=Mock(uid="test-uid", email="test@example.com")
        )
        mock_auth.verify_id_token = AsyncMock(
            return_value={"uid": "test-uid", "email": "test@example.com"}
        )

        # Mock Storage
        mock_storage.bucket = Mock()

        yield {
            # "firestore": mock_firestore_client,
            "auth": mock_auth,
            "storage": mock_storage,
        }


@pytest.fixture
def mock_firebase_auth_service():
    """Mock Firebase Auth Service."""
    service = AsyncMock()
    service.create_user = AsyncMock(return_value="test-uid")
    service.verify_id_token = AsyncMock(
        return_value={"uid": "test-uid", "email": "test@example.com"}
    )
    service.get_user = AsyncMock(
        return_value=Mock(uid="test-uid", email="test@example.com")
    )
    service.update_user = AsyncMock(return_value=True)
    service.delete_user = AsyncMock(return_value=True)
    service.generate_password_reset_link = AsyncMock(
        return_value="http://test-reset-link"
    )
    service.generate_email_verification_link = AsyncMock(
        return_value="http://test-verify-link"
    )
    return service


@pytest.fixture
def mock_firestore_user_repository():
    """Mock Firestore User Repository."""
    repo = AsyncMock()
    repo.create = AsyncMock(
        return_value={"id": "test-uid", "email": "test@example.com"}
    )
    repo.get_by_id = AsyncMock(
        return_value={"id": "test-uid", "email": "test@example.com", "role": "viewer"}
    )
    repo.update = AsyncMock(return_value=True)
    repo.delete = AsyncMock(return_value=True)
    repo.update_last_login = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def test_db_engine():
    """Create a test database engine for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    
    # Create in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Import all models to ensure they are registered with SQLModel
    try:
        from app.models.user import User
        from app.models.session import Session
        from app.models.chat import ChatMessage, ChatSession
        from app.models.rag import Document
        from sqlmodel import SQLModel
        
        # Create all tables
        SQLModel.metadata.create_all(bind=engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        # If models are not available, create a mock engine
        pass
    except Exception as e:
        print(f"Error creating tables: {e}")
    
    return engine


@pytest.fixture
def client(
    test_settings,
    mock_firebase_admin,
    mock_firebase_auth_service,
    mock_firestore_user_repository,
) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app with Firebase mocks."""
    # Override Firebase dependencies for testing
    with (
        patch("os.environ.get", return_value="test"),  # Dummy patch to keep context manager valid
        # patch(
        #     "app.services.firebase_auth.firebase_auth_service",
        #     mock_firebase_auth_service,
        # ),
        # patch(
        #     "app.infrastructure.firestore.user_repository.FirestoreUserRepository",
        #     return_value=mock_firestore_user_repository,
        # ),
        # patch(
        #     "app.shared.middleware.firebase_auth.firebase_auth_required",
        #     return_value={"uid": "test-uid", "email": "test@example.com"},
        # ),
    ):

        with TestClient(fastapi_app) as test_client:
            yield test_client

    # Clean up
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(
    test_settings, mock_firebase_admin
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app with Firebase mocks."""
    from httpx import ASGITransport

    # Override Firebase dependencies for testing
    with (
        patch("os.environ.get", return_value="test"),  # Dummy patch to keep context manager valid
        # patch("app.services.firebase_auth.firebase_auth_service"),
        # patch("app.infrastructure.firestore.user_repository.FirestoreUserRepository"),
    ):

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
                    "role": "assistant",
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
    }


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    mock_qdrant = AsyncMock()

    # Mock search results
    mock_qdrant.search.return_value = [
        Mock(
            id="doc1",
            score=0.9,
            payload={"content": "Test document 1", "metadata": {"title": "Test Doc 1"}},
        ),
        Mock(
            id="doc2",
            score=0.8,
            payload={"content": "Test document 2", "metadata": {"title": "Test Doc 2"}},
        ),
    ]

    # Mock collection operations
    mock_qdrant.get_collections.return_value = Mock(
        collections=[
            Mock(name="documents"),
            Mock(name="legislative_docs"),
            Mock(name="chat_context"),
        ]
    )

    mock_qdrant.create_collection = AsyncMock(return_value=True)
    mock_qdrant.upsert = AsyncMock(return_value=True)
    mock_qdrant.delete = AsyncMock(return_value=True)

    return mock_qdrant


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client for testing."""
    mock_es = Mock()
    
    # Mock successful ping
    mock_es.ping.return_value = True
    
    # Mock index operations
    mock_es.indices.exists.return_value = False
    mock_es.indices.create.return_value = {"acknowledged": True}
    
    # Mock document indexing
    mock_es.index.return_value = {"_id": "test_doc_id", "result": "created"}
    
    # Mock search operations
    mock_es.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "doc1",
                    "_score": 0.9,
                    "_source": {
                        "content": "Test document content",
                        "title": "Test Document",
                        "source_type": "lei",
                        "municipio": "Test City",
                        "categoria": "municipal"
                    }
                }
            ]
        }
    }
    
    return mock_es


@pytest.fixture
def mock_firebase_auth_middleware():
    """Mock Firebase Auth middleware."""

    def mock_auth_required():
        return {
            "uid": "test-uid",
            "email": "test@example.com",
            "email_verified": True,
            "custom_claims": {"role": "viewer"},
        }

    return mock_auth_required


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as f:
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
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }


@pytest.fixture
def sample_rag_query():
    """Sample RAG query for testing."""
    return {
        "query": "What is the capital of Brazil?",
        "max_results": 5,
        "threshold": 0.7,
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {"content": "Hello, how can you help me?", "role": "user"}


# Mark all tests as asyncio
pytest_plugins = ("pytest_asyncio",)
