"""Tests for database service.

This module contains tests for the DatabaseService class,
including user management, session management, and health checks.
"""

from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.models.session import Session as ChatSession
from app.models.user import User
from app.services.database import DatabaseService


class TestDatabaseService:
    """Test suite for DatabaseService."""

    def test_database_service_initialization(self):
        """Test DatabaseService initialization."""
        with patch("app.services.database.create_engine") as mock_create_engine:
            with patch("app.services.database.SQLModel") as mock_sqlmodel:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine

                db_service = DatabaseService()

                assert db_service.engine == mock_engine
                mock_create_engine.assert_called_once()
                mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)

    def test_database_service_initialization_error(self):
        """Test DatabaseService initialization with SQLAlchemy error."""
        with patch("app.services.database.create_engine") as mock_create_engine:
            with patch("app.services.database.settings") as mock_settings:
                # Mock non-production environment
                mock_settings.APP_ENV.value = "development"
                mock_settings.APP_ENV = Mock()
                mock_settings.APP_ENV.__ne__ = Mock(return_value=True)

                mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

                with pytest.raises(SQLAlchemyError):
                    DatabaseService()


class TestUserOperations:
    """Test suite for user-related database operations."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db_engine):
        """Test successful user creation."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        user = await db_service.create_user("test@example.com", "hashed_password")

        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_get_user_success(self, test_db_engine, sample_user_data):
        """Test successful user retrieval by ID."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user first
        created_user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )

        # Retrieve user
        retrieved_user = await db_service.get_user(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, test_db_engine):
        """Test user retrieval when user doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        user = await db_service.get_user(999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, test_db_engine, sample_user_data):
        """Test successful user retrieval by email."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user first
        await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )

        # Retrieve user by email
        retrieved_user = await db_service.get_user_by_email(sample_user_data["email"])

        assert retrieved_user is not None
        assert retrieved_user.email == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, test_db_engine):
        """Test user retrieval by email when user doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        user = await db_service.get_user_by_email("nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_delete_user_by_email_success(self, test_db_engine, sample_user_data):
        """Test successful user deletion by email."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user first
        await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )

        # Delete user
        result = await db_service.delete_user_by_email(sample_user_data["email"])

        assert result is True

        # Verify user is deleted
        deleted_user = await db_service.get_user_by_email(sample_user_data["email"])
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_delete_user_by_email_not_found(self, test_db_engine):
        """Test user deletion when user doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        result = await db_service.delete_user_by_email("nonexistent@example.com")

        assert result is False


class TestSessionOperations:
    """Test suite for session-related database operations."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, test_db_engine, sample_user_data):
        """Test successful session creation."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user first
        user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )

        # Create session
        session = await db_service.create_session(
            session_id="test_session_123", user_id=user.id, name="Test Session"
        )

        assert session.id == "test_session_123"
        assert session.user_id == user.id
        assert session.name == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_success(self, test_db_engine, sample_user_data):
        """Test successful session retrieval."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user and session first
        user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )
        created_session = await db_service.create_session(
            session_id="test_session_123", user_id=user.id, name="Test Session"
        )

        # Retrieve session
        retrieved_session = await db_service.get_session("test_session_123")

        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_db_engine):
        """Test session retrieval when session doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        session = await db_service.get_session("nonexistent_session")

        assert session is None

    @pytest.mark.asyncio
    async def test_delete_session_success(self, test_db_engine, sample_user_data):
        """Test successful session deletion."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user and session first
        user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )
        await db_service.create_session(
            session_id="test_session_123", user_id=user.id, name="Test Session"
        )

        # Delete session
        result = await db_service.delete_session("test_session_123")

        assert result is True

        # Verify session is deleted
        deleted_session = await db_service.get_session("test_session_123")
        assert deleted_session is None

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, test_db_engine):
        """Test session deletion when session doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        result = await db_service.delete_session("nonexistent_session")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, test_db_engine, sample_user_data):
        """Test retrieving all sessions for a user."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user first
        user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )

        # Create multiple sessions
        await db_service.create_session("session_1", user.id, "Session 1")
        await db_service.create_session("session_2", user.id, "Session 2")

        # Retrieve user sessions
        sessions = await db_service.get_user_sessions(user.id)

        assert len(sessions) == 2
        session_ids = [session.id for session in sessions]
        assert "session_1" in session_ids
        assert "session_2" in session_ids

    @pytest.mark.asyncio
    async def test_update_session_name_success(self, test_db_engine, sample_user_data):
        """Test successful session name update."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        # Create user and session first
        user = await db_service.create_user(
            sample_user_data["email"], sample_user_data["hashed_password"]
        )
        await db_service.create_session(
            session_id="test_session_123", user_id=user.id, name="Original Name"
        )

        # Update session name
        updated_session = await db_service.update_session_name(
            "test_session_123", "Updated Name"
        )

        assert updated_session.name == "Updated Name"

        # Verify the change persisted
        retrieved_session = await db_service.get_session("test_session_123")
        assert retrieved_session.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_session_name_not_found(self, test_db_engine):
        """Test session name update when session doesn't exist."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        with pytest.raises(HTTPException) as exc_info:
            await db_service.update_session_name("nonexistent_session", "New Name")

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)


class TestHealthCheck:
    """Test suite for database health check."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, test_db_engine):
        """Test successful database health check."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        result = await db_service.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test database health check failure."""
        db_service = DatabaseService()

        # Mock engine to raise exception
        mock_engine = Mock()
        mock_session = Mock()
        mock_session.exec.side_effect = Exception("Database connection failed")
        mock_engine.__enter__ = Mock(return_value=mock_session)
        mock_engine.__exit__ = Mock(return_value=None)

        with patch("app.services.database.Session") as mock_session_class:
            mock_session_class.return_value = mock_engine
            db_service.engine = Mock()

            result = await db_service.health_check()

            assert result is False


class TestSessionMaker:
    """Test suite for session maker functionality."""

    def test_get_session_maker(self, test_db_engine):
        """Test getting a session maker."""
        db_service = DatabaseService()
        db_service.engine = test_db_engine

        session_maker = db_service.get_session_maker()

        # The session maker should be a Session instance
        assert session_maker is not None
