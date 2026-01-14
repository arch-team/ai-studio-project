"""JWT Manager Unit Tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from authlib.jose import jwt as authlib_jwt
from authlib.jose.errors import ExpiredTokenError as AuthlibExpiredTokenError

from src.core.security.exceptions import InvalidTokenError, TokenExpiredError
from src.core.security.jwt import JWTManager, TokenPayload, TokenType, get_jwt_manager


class TestJWTManagerTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_valid(self, jwt_manager: JWTManager) -> None:
        """Test that create_access_token returns a valid token string."""
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
        )

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_access_token_payload(self, jwt_manager: JWTManager) -> None:
        """Test that access token contains correct payload claims."""
        token = jwt_manager.create_access_token(
            user_id=42,
            username="testuser",
            email="test@example.com",
            role="admin",
        )

        payload = jwt_manager.verify_token(token)

        assert payload.sub == "42"
        assert payload.username == "testuser"
        assert payload.email == "test@example.com"
        assert payload.role == "admin"
        assert payload.token_type == TokenType.ACCESS
        assert payload.jti is not None
        assert payload.exp is not None
        assert payload.iat is not None

    def test_create_access_token_custom_expiry(self, jwt_manager: JWTManager) -> None:
        """Test that custom expiry delta is applied."""
        custom_delta = timedelta(hours=2)
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
            expires_delta=custom_delta,
        )

        payload = jwt_manager.verify_token(token)
        expected_exp = datetime.now(timezone.utc) + custom_delta
        # Allow 5 second tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 5

    def test_create_refresh_token_valid(self, jwt_manager: JWTManager) -> None:
        """Test that create_refresh_token returns a valid token."""
        token = jwt_manager.create_refresh_token(user_id=1)

        assert isinstance(token, str)
        assert token.count(".") == 2

        payload = jwt_manager.verify_token(token, expected_type=TokenType.REFRESH)
        assert payload.token_type == TokenType.REFRESH
        assert payload.sub == "1"

    def test_create_refresh_token_7_day_expiry(self, jwt_manager: JWTManager) -> None:
        """Test that refresh token has ~7 day expiry by default."""
        token = jwt_manager.create_refresh_token(user_id=1)

        payload = jwt_manager.verify_token(token, expected_type=TokenType.REFRESH)
        expected_exp = datetime.now(timezone.utc) + timedelta(days=7)
        # Allow 10 second tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 10

    def test_create_password_reset_token_valid(self, jwt_manager: JWTManager) -> None:
        """Test that create_password_reset_token returns a valid token."""
        token = jwt_manager.create_password_reset_token(
            user_id=1,
            email="test@example.com",
        )

        assert isinstance(token, str)
        assert token.count(".") == 2

        payload = jwt_manager.verify_token(
            token, expected_type=TokenType.PASSWORD_RESET
        )
        assert payload.token_type == TokenType.PASSWORD_RESET
        assert payload.sub == "1"
        assert payload.email == "test@example.com"

    def test_create_password_reset_token_15_minute_expiry(
        self, jwt_manager: JWTManager
    ) -> None:
        """Test that password reset token has ~15 minute expiry."""
        token = jwt_manager.create_password_reset_token(
            user_id=1,
            email="test@example.com",
        )

        payload = jwt_manager.verify_token(
            token, expected_type=TokenType.PASSWORD_RESET
        )
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
        # Allow 5 second tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 5

    def test_each_token_has_unique_jti(self, jwt_manager: JWTManager) -> None:
        """Test that each token has a unique JTI."""
        tokens = [
            jwt_manager.create_access_token(
                user_id=1,
                username="testuser",
                email="test@example.com",
                role="engineer",
            )
            for _ in range(5)
        ]

        jtis = [jwt_manager.verify_token(t).jti for t in tokens]
        assert len(set(jtis)) == 5  # All unique


class TestJWTManagerTokenVerification:
    """Tests for JWT token verification."""

    def test_verify_token_valid(self, jwt_manager: JWTManager) -> None:
        """Test verification of a valid token."""
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
        )

        payload = jwt_manager.verify_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == "1"
        assert payload.username == "testuser"

    def test_verify_token_expired(self, jwt_manager: JWTManager) -> None:
        """Test that expired tokens raise TokenExpiredError."""
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(TokenExpiredError):
            jwt_manager.verify_token(token)

    def test_verify_token_invalid_signature(
        self, jwt_manager: JWTManager, jwt_secret_key: str
    ) -> None:
        """Test that tokens with invalid signatures raise InvalidTokenError."""
        # Create token with different secret using authlib directly
        header = {"alg": "HS256"}
        payload = {
            "sub": "1",
            "username": "testuser",
            "email": "test@example.com",
            "role": "engineer",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "type": "access",
            "jti": "test-jti",
        }
        # Use a different secret key to create the token
        token = authlib_jwt.encode(
            header, payload, "different-secret-key-for-testing!"
        ).decode("utf-8")

        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token(token)

    def test_verify_token_wrong_type(self, jwt_manager: JWTManager) -> None:
        """Test that tokens with wrong type raise InvalidTokenError."""
        refresh_token = jwt_manager.create_refresh_token(user_id=1)

        with pytest.raises(InvalidTokenError) as exc_info:
            jwt_manager.verify_token(refresh_token, expected_type=TokenType.ACCESS)

        assert "Invalid token type" in str(exc_info.value)

    def test_verify_token_missing_claims(
        self, jwt_manager: JWTManager, jwt_secret_key: str
    ) -> None:
        """Test that tokens with missing claims raise InvalidTokenError."""
        # Create a token without required claims
        header = {"alg": "HS256"}
        payload = {
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            # Missing: sub, token_type
        }
        token = authlib_jwt.encode(header, payload, jwt_secret_key).decode("utf-8")

        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token(token)

    def test_verify_token_malformed(self, jwt_manager: JWTManager) -> None:
        """Test that malformed tokens raise InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token("not-a-valid-jwt-token")

    def test_verify_token_empty_string(self, jwt_manager: JWTManager) -> None:
        """Test that empty token raises InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token("")


class TestJWTManagerHelpers:
    """Tests for JWT helper methods."""

    def test_get_user_id_from_token(self, jwt_manager: JWTManager) -> None:
        """Test extracting user ID from token."""
        token = jwt_manager.create_access_token(
            user_id=42,
            username="testuser",
            email="test@example.com",
            role="engineer",
        )

        user_id = jwt_manager.get_user_id_from_token(token)

        assert user_id == 42

    def test_get_user_id_from_invalid_token(self, jwt_manager: JWTManager) -> None:
        """Test that invalid tokens raise error when extracting user ID."""
        with pytest.raises(InvalidTokenError):
            jwt_manager.get_user_id_from_token("invalid-token")


class TestJWTManagerSingleton:
    """Tests for JWTManager singleton behavior."""

    def test_jwt_manager_singleton_returns_same_instance(self) -> None:
        """Test that get_jwt_manager returns the same instance."""
        manager1 = get_jwt_manager()
        manager2 = get_jwt_manager()

        assert manager1 is manager2

    def test_jwt_manager_singleton_creates_valid_manager(self) -> None:
        """Test that singleton creates a functional JWTManager."""
        manager = get_jwt_manager()

        token = manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
        )

        assert isinstance(token, str)
        assert token.count(".") == 2


class TestTokenPayload:
    """Tests for TokenPayload dataclass."""

    def test_token_payload_creation(self) -> None:
        """Test TokenPayload dataclass creation."""
        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            sub="1",
            username="testuser",
            email="test@example.com",
            role="engineer",
            exp=now + timedelta(hours=1),
            iat=now,
            token_type=TokenType.ACCESS,
            jti="unique-id",
        )

        assert payload.sub == "1"
        assert payload.username == "testuser"
        assert payload.token_type == TokenType.ACCESS

    def test_token_payload_from_dict_with_defaults(self) -> None:
        """Test TokenPayload.from_dict provides defaults for missing optional fields."""
        now = datetime.now(timezone.utc)
        data = {
            "sub": "1",
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
            "type": "refresh",
            "jti": "unique-id",
            # Missing: username, email, role
        }

        payload = TokenPayload.from_dict(data)

        assert payload.sub == "1"
        assert payload.username == ""
        assert payload.email == ""
        assert payload.role == ""
        assert payload.token_type == TokenType.REFRESH


class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_type_values(self) -> None:
        """Test TokenType enum has expected values."""
        assert TokenType.ACCESS.value == "access"
        assert TokenType.REFRESH.value == "refresh"
        assert TokenType.PASSWORD_RESET.value == "password_reset"

    def test_token_type_from_string(self) -> None:
        """Test creating TokenType from string."""
        assert TokenType("access") == TokenType.ACCESS
        assert TokenType("refresh") == TokenType.REFRESH
        assert TokenType("password_reset") == TokenType.PASSWORD_RESET


class TestTokenExpiryBoundary:
    """Tests for token expiry boundary conditions."""

    def test_token_valid_just_before_expiry(self, jwt_manager: JWTManager) -> None:
        """Test token is valid just before expiry."""
        # Create token that expires in 2 seconds
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
            expires_delta=timedelta(seconds=2),
        )

        # Should be valid immediately
        payload = jwt_manager.verify_token(token)
        assert payload.sub == "1"

    def test_token_invalid_just_after_expiry(self, jwt_manager: JWTManager) -> None:
        """Test token is invalid just after expiry."""
        # Create token that is already expired (negative delta)
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="engineer",
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(TokenExpiredError):
            jwt_manager.verify_token(token)
