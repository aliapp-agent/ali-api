"""Mock services for testing.

This package contains mock implementations of external services
to facilitate testing without requiring actual service connections.
"""

from unittest.mock import AsyncMock, MagicMock
import json
from typing import Dict, Any, Optional


class MockFirebaseAuth:
    """Mock Firebase Authentication service for testing."""

    def __init__(self):
        self.users = {}
        self.next_uid = 1

    async def create_user(self, email: str, password: str, display_name: Optional[str] = None, role: str = "viewer") -> str:
        """Mock user creation."""
        uid = f"mock_uid_{self.next_uid}"
        self.next_uid += 1

        self.users[uid] = {
            'uid': uid,
            'email': email,
            'display_name': display_name,
            'email_verified': False,
            'role': role,
            'custom_claims': {'role': role}
        }

        return uid

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Mock token verification."""
        if token == "invalid_token":
            raise Exception("Invalid token")

        # Return mock user data
        return {
            'uid': 'mock_uid_1',
            'email': 'test@example.com',
            'email_verified': True,
            'custom_claims': {'role': 'viewer'}
        }

    async def update_user(self, uid: str, **kwargs) -> None:
        """Mock user update."""
        if uid in self.users:
            self.users[uid].update(kwargs)

    async def delete_user(self, uid: str) -> None:
        """Mock user deletion."""
        if uid in self.users:
            del self.users[uid]

    async def generate_password_reset_link(self, email: str) -> str:
        """Mock password reset link generation."""
        return f"https://mock-firebase.com/reset?email={email}"

    async def generate_email_verification_link(self, email: str) -> str:
        """Mock email verification link generation."""
        return f"https://mock-firebase.com/verify?email={email}"


class MockFirestore:
    """Mock Firestore database for testing."""

    def __init__(self):
        self.collections = {}

    def collection(self, name: str):
        """Get or create a collection."""
        if name not in self.collections:
            self.collections[name] = {}
        return MockCollection(self.collections[name])


class MockCollection:
    """Mock Firestore collection."""

    def __init__(self, data: Dict):
        self.data = data

    def document(self, doc_id: str):
        """Get or create a document."""
        return MockDocument(self.data, doc_id)

    async def add(self, data: Dict[str, Any]) -> MockDocument:
        """Add a document with auto-generated ID."""
        doc_id = f"auto_id_{len(self.data) + 1}"
        self.data[doc_id] = data
        return MockDocument(self.data, doc_id)

    def stream(self):
        """Stream all documents."""
        for doc_id, data in self.data.items():
            yield MockDocumentSnapshot(doc_id, data)


class MockDocument:
    """Mock Firestore document."""

    def __init__(self, collection_data: Dict, doc_id: str):
        self.collection_data = collection_data
        self.doc_id = doc_id

    async def set(self, data: Dict[str, Any]) -> None:
        """Set document data."""
        self.collection_data[self.doc_id] = data

    async def update(self, data: Dict[str, Any]) -> None:
        """Update document data."""
        if self.doc_id in self.collection_data:
            self.collection_data[self.doc_id].update(data)

    async def get(self) -> 'MockDocumentSnapshot':
        """Get document snapshot."""
        data = self.collection_data.get(self.doc_id)
        return MockDocumentSnapshot(self.doc_id, data)

    async def delete(self) -> None:
        """Delete document."""
        if self.doc_id in self.collection_data:
            del self.collection_data[self.doc_id]


class MockDocumentSnapshot:
    """Mock Firestore document snapshot."""

    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    def exists(self) -> bool:
        """Check if document exists."""
        return self._data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Convert to dictionary."""
        return self._data


class MockQdrantClient:
    """Mock Qdrant client for testing."""

    def __init__(self):
        self.collections = {}

    async def create_collection(self, name: str, **kwargs) -> None:
        """Create a collection."""
        self.collections[name] = {}

    async def upsert(self, collection_name: str, points: list) -> None:
        """Upsert points."""
        if collection_name not in self.collections:
            self.collections[collection_name] = {}

        for point in points:
            self.collections[collection_name][point.id] = point

    async def search(self, collection_name: str, query_vector: list, limit: int = 10) -> list:
        """Search for similar vectors."""
        # Return mock search results
        return [
            {
                'id': 'mock_result_1',
                'score': 0.95,
                'payload': {'text': 'Mock result 1'}
            },
            {
                'id': 'mock_result_2',
                'score': 0.85,
                'payload': {'text': 'Mock result 2'}
            }
        ]


# Mock instances for easy import
mock_firebase_auth = MockFirebaseAuth()
mock_firestore = MockFirestore()
mock_qdrant_client = MockQdrantClient()


def create_mock_firebase_credentials():
    """Create mock Firebase credentials for testing."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "mock-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "mock-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }


__all__ = [
    "MockFirebaseAuth",
    "MockFirestore",
    "MockCollection",
    "MockDocument",
    "MockDocumentSnapshot",
    "MockQdrantClient",
    "mock_firebase_auth",
    "mock_firestore",
    "mock_qdrant_client",
    "create_mock_firebase_credentials"
]
