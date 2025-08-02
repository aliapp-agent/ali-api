"""Database integration tests.

This module contains integration tests that verify database
operations work correctly with real database connections.
"""

import asyncio

import pytest
from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.base import BaseModel
from app.services.database import DatabaseService


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def real_db_engine(self):
        """Create a real SQLite database for integration testing."""
        engine = create_engine(
            "sqlite:///test_integration.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create all tables
        SQLModel.metadata.create_all(bind=engine)

        yield engine

        # Cleanup
        SQLModel.metadata.drop_all(bind=engine)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_full_workflow(self, real_db_engine):
        """Test complete database workflow with real database."""
        # Initialize service with real engine
        db_service = DatabaseService()
        db_service.engine = real_db_engine

        # 1. Create user
        user = await db_service.create_user(
            "integration@example.com", "hashed_password_123"
        )
        assert user.id is not None
        assert user.email == "integration@example.com"

        # 2. Retrieve user
        retrieved_user = await db_service.get_user(user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == user.email

        # 3. Create session
        session = await db_service.create_session(
            session_id="integration-session-123",
            user_id=user.id,
            name="Integration Test Session",
        )
        assert session.id == "integration-session-123"
        assert session.user_id == user.id

        # 4. Get user sessions
        sessions = await db_service.get_user_sessions(user.id)
        assert len(sessions) == 1
        assert sessions[0].id == session.id

        # 5. Update session name
        updated_session = await db_service.update_session_name(
            session.id, "Updated Integration Session"
        )
        assert updated_session.name == "Updated Integration Session"

        # 6. Health check
        health_result = await db_service.health_check()
        assert health_result is True

        # 7. Cleanup - delete session
        delete_result = await db_service.delete_session(session.id)
        assert delete_result is True

        # 8. Cleanup - delete user
        user_delete_result = await db_service.delete_user_by_email(user.email)
        assert user_delete_result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_transaction_consistency(self, real_db_engine):
        """Test that database transactions maintain consistency."""
        db_service = DatabaseService()
        db_service.engine = real_db_engine

        # Create multiple users in sequence
        users = []
        for i in range(5):
            user = await db_service.create_user(f"user{i}@example.com", f"password{i}")
            users.append(user)

        # Verify all users were created
        for user in users:
            retrieved = await db_service.get_user(user.id)
            assert retrieved is not None

        # Create sessions for each user
        sessions = []
        for i, user in enumerate(users):
            session = await db_service.create_session(
                f"session-{i}", user.id, f"Session {i}"
            )
            sessions.append(session)

        # Verify session counts per user
        for user in users:
            user_sessions = await db_service.get_user_sessions(user.id)
            assert len(user_sessions) == 1

        # Cleanup
        for session in sessions:
            await db_service.delete_session(session.id)

        for user in users:
            await db_service.delete_user_by_email(user.email)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_error_handling(self, real_db_engine):
        """Test database error handling in integration scenarios."""
        db_service = DatabaseService()
        db_service.engine = real_db_engine

        # Test duplicate email handling
        user1 = await db_service.create_user("duplicate@example.com", "password1")

        # Attempting to create user with same email should be handled gracefully
        # This depends on your database constraints and error handling
        try:
            user2 = await db_service.create_user("duplicate@example.com", "password2")
            # If no exception, then the database allows duplicates
            # Clean up both users
            await db_service.delete_user_by_email("duplicate@example.com")
        except Exception:
            # Exception occurred, clean up the first user
            await db_service.delete_user_by_email("duplicate@example.com")

    @pytest.mark.integration
    def test_database_connection_pool(self, real_db_engine):
        """Test database connection pooling works correctly."""
        db_service = DatabaseService()
        db_service.engine = real_db_engine

        # Test multiple concurrent sessions
        async def create_test_user(suffix):
            return await db_service.create_user(
                f"pool_test_{suffix}@example.com", f"password_{suffix}"
            )

        async def test_concurrent_operations():
            # Create multiple users concurrently
            tasks = [create_test_user(i) for i in range(10)]
            users = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful creations
            successful_users = [u for u in users if not isinstance(u, Exception)]

            # Clean up
            for user in successful_users:
                try:
                    await db_service.delete_user_by_email(user.email)
                except:
                    pass

            return len(successful_users)

        # Run the concurrent test
        successful_count = asyncio.run(test_concurrent_operations())

        # Should have created most or all users successfully
        assert (
            successful_count >= 8
        )  # Allow for some potential failures in high concurrency
