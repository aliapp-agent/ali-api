"""Tests for authentication functionality.

This module contains tests for authentication utilities,
JWT token management, and auth endpoints.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.auth import get_current_session, get_current_user
from app.schemas.auth import Token
from app.shared.utils.auth import (
    create_access_token,
    generate_secure_token,
    validate_token_claims,
    verify_token,
)


class TestTokenCreation:
    """Test suite for JWT token creation."""

    def test_create_access_token_success(self):
        """Test successful token creation."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30

            token = create_access_token("test-session-123")

            assert isinstance(token, Token)
            assert token.access_token is not None
            assert len(token.access_token) > 0
            assert token.expires_at > datetime.now(UTC)

    def test_create_access_token_with_custom_expiry(self):
        """Test token creation with custom expiry time."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"

            custom_expiry = timedelta(hours=1)
            token = create_access_token("test-session-123", custom_expiry)

            expected_expiry = datetime.now(UTC) + custom_expiry
            # Allow for small time differences in execution
            assert abs((token.expires_at - expected_expiry).total_seconds()) < 5

    def test_create_access_token_invalid_session_id(self):
        """Test token creation with invalid session ID."""
        with pytest.raises(ValueError, match="Session ID must be a non-empty string"):
            create_access_token("")

        with pytest.raises(ValueError, match="Session ID must be a non-empty string"):
            create_access_token(None)

    def test_create_access_token_missing_secret_key(self):
        """Test token creation when JWT secret key is missing."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = None
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30

            with pytest.raises(ValueError, match="JWT secret key is not configured"):
                create_access_token("test-session-123")

    def test_create_access_token_jwt_error(self):
        """Test token creation when JWT encoding fails."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            with patch("app.shared.utils.auth.jwt.encode") as mock_encode:
                mock_settings.JWT_SECRET_KEY = "test-secret-key"
                mock_settings.JWT_ALGORITHM = "HS256"
                mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30
                mock_encode.side_effect = Exception("JWT encoding failed")

                with pytest.raises(ValueError, match="Failed to create access token"):
                    create_access_token("test-session-123")


class TestTokenVerification:
    """Test suite for JWT token verification."""

    def test_verify_token_success(self):
        """Test successful token verification."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30

            # First create a token
            token = create_access_token("test-session-123")

            # Then verify it
            session_id = verify_token(token.access_token)

            assert session_id == "test-session-123"

    def test_verify_token_invalid_format(self):
        """Test token verification with invalid token format."""
        with pytest.raises(ValueError, match="Token must be a non-empty string"):
            verify_token("")

        with pytest.raises(ValueError, match="Token must be a non-empty string"):
            verify_token(None)

    def test_verify_token_expired(self):
        """Test verification of expired token."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30

            # Create token with negative expiry (already expired)
            expired_token = create_access_token(
                "test-session-123",
                timedelta(seconds=-1)
            )

            # Verify expired token returns None
            session_id = verify_token(expired_token.access_token)
            assert session_id is None

    def test_verify_token_invalid_signature(self):
        """Test verification of token with invalid signature."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS = 30

            # Create token with one secret
            token = create_access_token("test-session-123")

            # Try to verify with different secret
            mock_settings.JWT_SECRET_KEY = "different-secret-key"

            session_id = verify_token(token.access_token)
            assert session_id is None

    def test_verify_token_missing_secret_key(self):
        """Test token verification when JWT secret key is missing."""
        with patch("app.shared.utils.auth.getattr") as mock_getattr:
            # Mock getattr to return None for JWT_SECRET_KEY
            def side_effect(obj, attr, default=None):
                if attr == "JWT_SECRET_KEY":
                    return None
                elif attr == "JWT_ALGORITHM":
                    return "HS256"
                return default
            
            mock_getattr.side_effect = side_effect
            
            # Use a properly formatted JWT token
            valid_jwt_format = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            
            with pytest.raises(ValueError, match="JWT secret key is not configured"):
                verify_token(valid_jwt_format)

    def test_verify_token_invalid_token_type(self):
        """Test verification of token with wrong type."""
        with patch("app.shared.utils.auth.settings") as mock_settings:
            with patch("app.shared.utils.auth.jwt.decode") as mock_decode:
                mock_settings.JWT_SECRET_KEY = "test-secret-key"
                mock_settings.JWT_ALGORITHM = "HS256"

                # Mock payload with wrong token type
                mock_decode.return_value = {
                    "sub": "test-session-123",
                    "type": "refresh_token",  # Wrong type
                    "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
                    "iat": datetime.now(UTC).timestamp()
                }

                with patch("app.shared.utils.auth.validate_jwt_token", return_value="valid.jwt.token"):
                    session_id = verify_token("valid.jwt.token")
                    assert session_id is None


class TestSecureTokenGeneration:
    """Test suite for secure token generation."""

    def test_generate_secure_token_default_length(self):
        """Test secure token generation with default length."""
        token = generate_secure_token()

        # Default length is 32 bytes, hex encoded = 64 characters
        assert len(token) == 64
        assert all(c in '0123456789abcdef' for c in token)

    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        token = generate_secure_token(16)

        # 16 bytes, hex encoded = 32 characters
        assert len(token) == 32
        assert all(c in '0123456789abcdef' for c in token)

    def test_generate_secure_token_invalid_length(self):
        """Test secure token generation with invalid length."""
        with pytest.raises(ValueError, match="Token length must be between 16 and 128 bytes"):
            generate_secure_token(8)  # Too short

        with pytest.raises(ValueError, match="Token length must be between 16 and 128 bytes"):
            generate_secure_token(256)  # Too long


class TestTokenClaimsValidation:
    """Test suite for JWT token claims validation."""

    def test_validate_token_claims_success(self):
        """Test successful token claims validation."""
        future_time = datetime.now(UTC) + timedelta(hours=1)
        past_time = datetime.now(UTC) - timedelta(minutes=1)

        payload = {
            "sub": "test-session-123",
            "exp": future_time.timestamp(),
            "iat": past_time.timestamp()
        }

        assert validate_token_claims(payload) is True

    def test_validate_token_claims_missing_required_claim(self):
        """Test token claims validation with missing required claim."""
        payload = {
            "sub": "test-session-123",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            # Missing 'iat' claim
        }

        assert validate_token_claims(payload) is False

    def test_validate_token_claims_expired(self):
        """Test token claims validation with expired token."""
        past_time = datetime.now(UTC) - timedelta(hours=1)

        payload = {
            "sub": "test-session-123",
            "exp": past_time.timestamp(),
            "iat": (datetime.now(UTC) - timedelta(hours=2)).timestamp()
        }

        assert validate_token_claims(payload) is False

    def test_validate_token_claims_issued_in_future(self):
        """Test token claims validation with future issued time."""
        future_time = datetime.now(UTC) + timedelta(hours=2)

        payload = {
            "sub": "test-session-123",
            "exp": (datetime.now(UTC) + timedelta(hours=3)).timestamp(),
            "iat": future_time.timestamp()
        }

        assert validate_token_claims(payload) is False


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock user doesn't exist
            mock_db.get_user_by_email = AsyncMock(return_value=None)

            # Mock user creation
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_db.create_user = AsyncMock(return_value=mock_user)

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "StrongPassword123!"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert "token" in data

    def test_register_user_already_exists(self, client: TestClient):
        """Test user registration when email already exists."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock user already exists
            mock_user = Mock()
            mock_db.get_user_by_email = AsyncMock(return_value=mock_user)

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "StrongPassword123!"
                }
            )

            assert response.status_code == 400
            response_data = response.json()
            if "detail" in response_data:
                assert "Email already registered" in response_data["detail"]
            else:
                # Handle different error structure
                assert "Email already registered" in str(response_data)

    def test_login_success(self, client: TestClient):
        """Test successful user login."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock user exists and password is correct
            mock_user = Mock()
            mock_user.id = 1
            mock_user.verify_password.return_value = True
            mock_db.get_user_by_email = AsyncMock(return_value=mock_user)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "correct_password"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock user doesn't exist
            mock_db.get_user_by_email = AsyncMock(return_value=None)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "nonexistent@example.com",
                    "password": "wrong_password"
                }
            )

            assert response.status_code == 401
            response_data = response.json()
            if "detail" in response_data:
                assert "Incorrect email or password" in response_data["detail"]
            else:
                # Handle different error structure
                assert "Incorrect email or password" in str(response_data)

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock user exists but password is wrong
            mock_user = Mock()
            mock_user.verify_password.return_value = False
            mock_db.get_user_by_email = AsyncMock(return_value=mock_user)

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "wrong_password"
                }
            )

            assert response.status_code == 401
            response_data = response.json()
            if "detail" in response_data:
                assert "Incorrect email or password" in response_data["detail"]
            else:
                # Handle different error structure
                assert "Incorrect email or password" in str(response_data)


class TestAuthDependencies:
    """Test suite for authentication dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_db_engine):
        """Test successful current user retrieval."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            # Mock token verification
            with patch("app.api.v1.auth.verify_token", return_value="1"):
                # Mock user exists
                mock_user = Mock()
                mock_user.id = 1
                mock_db.get_user = AsyncMock(return_value=mock_user)

                # Mock credentials
                mock_credentials = Mock()
                mock_credentials.credentials = "valid.jwt.token"

                user = await get_current_user(mock_credentials)
                assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        with patch("app.api.v1.auth.verify_token", return_value=None):
            mock_credentials = Mock()
            mock_credentials.credentials = "invalid.jwt.token"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test current user retrieval when user doesn't exist."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            with patch("app.api.v1.auth.verify_token", return_value="999"):
                # Mock user doesn't exist
                mock_db.get_user = AsyncMock(return_value=None)

                mock_credentials = Mock()
                mock_credentials.credentials = "valid.jwt.token"

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials)

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_current_session_success(self):
        """Test successful current session retrieval."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            with patch("app.api.v1.auth.verify_token", return_value="session-123"):
                # Mock session exists
                mock_session = Mock()
                mock_session.id = "session-123"
                mock_db.get_session = AsyncMock(return_value=mock_session)

                mock_credentials = Mock()
                mock_credentials.credentials = "valid.jwt.token"

                session = await get_current_session(mock_credentials)
                assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_current_session_not_found(self):
        """Test current session retrieval when session doesn't exist."""
        with patch("app.api.v1.auth.db_service") as mock_db:
            with patch("app.api.v1.auth.verify_token", return_value="nonexistent-session"):
                # Mock session doesn't exist
                mock_db.get_session = AsyncMock(return_value=None)

                mock_credentials = Mock()
                mock_credentials.credentials = "valid.jwt.token"

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_session(mock_credentials)

                assert exc_info.value.status_code == 404
