"""JWT Token Management - Token generation, validation, and refresh using Authlib."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Any

from authlib.jose import JoseError
from authlib.jose import jwt as authlib_jwt
from authlib.jose.errors import ExpiredTokenError as AuthlibExpiredTokenError

from src.shared.infrastructure.config import get_settings
from src.shared.infrastructure.security.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.shared.infrastructure.security.exceptions import InvalidTokenError, TokenExpiredError


class TokenType(str, Enum):
    """JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"


@dataclass
class TokenPayload:
    """JWT payload structure."""

    sub: str  # User ID
    username: str
    email: str
    role: str
    exp: datetime
    iat: datetime
    token_type: TokenType
    jti: str  # JWT ID for revocation

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from decoded JWT dict."""
        return cls(
            sub=data["sub"],
            username=data.get("username", ""),
            email=data.get("email", ""),
            role=data.get("role", ""),
            exp=datetime.fromtimestamp(data["exp"], tz=UTC),
            iat=datetime.fromtimestamp(data["iat"], tz=UTC),
            token_type=TokenType(data.get("type", TokenType.ACCESS.value)),
            jti=data.get("jti", ""),
        )


class JWTManager:
    """JWT token management using Authlib."""

    def __init__(self):
        self.settings = get_settings()
        self._header = {"alg": "HS256"}

    def _create_token(
        self,
        payload: dict[str, Any],
        expires_delta: timedelta,
        token_type: TokenType,
    ) -> str:
        """Create a JWT token with given payload and expiration."""
        now = datetime.now(UTC)
        expire = now + expires_delta

        token_payload = {
            **payload,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": token_type.value,
            "jti": str(uuid.uuid4()),
        }

        return authlib_jwt.encode(
            self._header,
            token_payload,
            self.settings.secret_key,
        ).decode("utf-8")

    def create_access_token(
        self,
        user_id: int,
        username: str,
        email: str,
        role: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create access token for authenticated user."""
        payload = {
            "sub": str(user_id),
            "username": username,
            "email": email,
            "role": role,
        }

        delta = expires_delta or timedelta(
            minutes=self.settings.access_token_expire_minutes
            or ACCESS_TOKEN_EXPIRE_MINUTES
        )

        return self._create_token(payload, delta, TokenType.ACCESS)

    def create_refresh_token(
        self,
        user_id: int,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create refresh token for token renewal."""
        payload = {"sub": str(user_id)}

        delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        return self._create_token(payload, delta, TokenType.REFRESH)

    def create_password_reset_token(
        self,
        user_id: int,
        email: str,
    ) -> str:
        """Create password reset token with 15-minute validity."""
        payload = {
            "sub": str(user_id),
            "email": email,
        }

        delta = timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

        return self._create_token(payload, delta, TokenType.PASSWORD_RESET)

    def verify_token(
        self,
        token: str,
        expected_type: TokenType | None = None,
    ) -> TokenPayload:
        """Verify and decode a JWT token."""
        try:
            claims = authlib_jwt.decode(token, self.settings.secret_key)
            claims.validate()

            # Validate token type if specified
            token_type = claims.get("type")
            if expected_type and token_type != expected_type.value:
                raise InvalidTokenError(
                    f"Invalid token type: expected {expected_type.value}, got {token_type}"
                )

            return TokenPayload.from_dict(claims)

        except AuthlibExpiredTokenError:
            raise TokenExpiredError("Token has expired")
        except JoseError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except KeyError as e:
            raise InvalidTokenError(f"Missing required claim: {str(e)}")

    def get_user_id_from_token(self, token: str) -> int:
        """Extract user ID from token without full validation."""
        try:
            claims = authlib_jwt.decode(token, self.settings.secret_key)
            return int(claims["sub"])
        except (JoseError, KeyError, ValueError) as e:
            raise InvalidTokenError(f"Cannot extract user ID: {str(e)}")


@lru_cache
def get_jwt_manager() -> JWTManager:
    """Get cached JWT manager instance."""
    return JWTManager()
