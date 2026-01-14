"""SSO Middleware - AWS IAM Identity Center integration with fault tolerance."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import jwt as authlib_jwt
from authlib.jose.errors import JoseError

from src.core.security.constants import (
    SSO_MAX_CONSECUTIVE_FAILURES,
    SSO_RECOVERY_CHECK_INTERVAL_MINUTES,
    SSO_TIMEOUT_SECONDS,
)
from src.core.security.exceptions import SSODegradedModeError, SSOError
from src.core.utils import utc_now


@dataclass
class SSOHealthState:
    """Track SSO service health status."""

    consecutive_failures: int = 0
    is_degraded: bool = False
    last_failure_at: Optional[datetime] = None
    last_recovery_check_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None


@dataclass
class SSOUserInfo:
    """User information from SSO provider."""

    identity_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    groups: List[str] = field(default_factory=list)


class SSOHealthTracker:
    """Track SSO service health and manage degraded mode."""

    def __init__(self):
        self._state = SSOHealthState()
        self._lock = asyncio.Lock()

    @property
    def is_degraded(self) -> bool:
        """Check if SSO is in degraded mode."""
        return self._state.is_degraded

    async def record_success(self) -> None:
        """Record successful SSO operation."""
        async with self._lock:
            self._state.consecutive_failures = 0
            self._state.last_success_at = utc_now()
            if self._state.is_degraded:
                self._state.is_degraded = False

    async def record_failure(self) -> None:
        """Record failed SSO operation."""
        async with self._lock:
            self._state.consecutive_failures += 1
            self._state.last_failure_at = utc_now()

            if self._state.consecutive_failures >= SSO_MAX_CONSECUTIVE_FAILURES:
                self._state.is_degraded = True

    async def should_attempt_recovery(self) -> bool:
        """Check if it's time to attempt SSO recovery."""
        if not self._state.is_degraded:
            return True

        if self._state.last_recovery_check_at is None:
            return True

        recovery_interval = timedelta(minutes=SSO_RECOVERY_CHECK_INTERVAL_MINUTES)
        time_since_check = utc_now() - self._state.last_recovery_check_at

        return time_since_check >= recovery_interval

    async def mark_recovery_check(self) -> None:
        """Mark that a recovery check was performed."""
        async with self._lock:
            self._state.last_recovery_check_at = utc_now()

    def get_status(self) -> Dict:
        """Get current health status."""
        return {
            "is_degraded": self._state.is_degraded,
            "consecutive_failures": self._state.consecutive_failures,
            "last_failure_at": (
                self._state.last_failure_at.isoformat()
                if self._state.last_failure_at
                else None
            ),
            "last_success_at": (
                self._state.last_success_at.isoformat()
                if self._state.last_success_at
                else None
            ),
        }


class SSOService:
    """SSO authentication service using AWS IAM Identity Center."""

    def __init__(
        self,
        issuer_url: str,
        client_id: str,
        client_secret: Optional[str] = None,
        jwks_uri: Optional[str] = None,
    ):
        self._issuer_url = issuer_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._jwks_uri = jwks_uri or f"{issuer_url}/.well-known/jwks.json"
        self._health_tracker = SSOHealthTracker()
        self._jwks_cache: Optional[Dict] = None
        self._jwks_cache_time: Optional[datetime] = None

    @property
    def health_tracker(self) -> SSOHealthTracker:
        """Get health tracker instance."""
        return self._health_tracker

    async def validate_id_token(self, id_token: str) -> SSOUserInfo:
        """Validate SSO ID token and extract user info."""
        # Check if SSO is degraded
        if self._health_tracker.is_degraded:
            if not await self._health_tracker.should_attempt_recovery():
                raise SSODegradedModeError()
            await self._health_tracker.mark_recovery_check()

        try:
            # Get JWKS for token validation
            jwks = await self._get_jwks()

            # Decode and validate token using Authlib
            claims = authlib_jwt.decode(id_token, jwks)

            # Validate standard claims
            claims.validate(leeway=60)  # Allow 60 seconds clock skew

            # Validate issuer and audience
            if claims.get("iss") != self._issuer_url:
                raise SSOError("Invalid token issuer")

            if claims.get("aud") != self._client_id:
                # Check if aud is a list
                aud = claims.get("aud")
                if isinstance(aud, list) and self._client_id not in aud:
                    raise SSOError("Invalid token audience")
                elif not isinstance(aud, list):
                    raise SSOError("Invalid token audience")

            # Extract user info
            user_info = SSOUserInfo(
                identity_id=claims.get("sub", ""),
                username=claims.get("preferred_username", claims.get("email", "")),
                email=claims.get("email", ""),
                display_name=claims.get("name"),
                groups=claims.get("groups", []),
            )

            await self._health_tracker.record_success()
            return user_info

        except JoseError as e:
            await self._health_tracker.record_failure()
            raise SSOError(f"Token validation failed: {str(e)}")
        except httpx.TimeoutException:
            await self._health_tracker.record_failure()
            raise SSOError("SSO service timeout")
        except httpx.HTTPError as e:
            await self._health_tracker.record_failure()
            raise SSOError(f"SSO service error: {str(e)}")

    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        redirect_uri: str,
    ) -> Dict[str, str]:
        """Exchange authorization code for tokens (OAuth2 flow)."""
        if self._health_tracker.is_degraded:
            if not await self._health_tracker.should_attempt_recovery():
                raise SSODegradedModeError()
            await self._health_tracker.mark_recovery_check()

        try:
            async with AsyncOAuth2Client(
                client_id=self._client_id,
                client_secret=self._client_secret,
                timeout=SSO_TIMEOUT_SECONDS,
            ) as client:
                token_endpoint = f"{self._issuer_url}/oauth2/token"

                token = await client.fetch_token(
                    token_endpoint,
                    grant_type="authorization_code",
                    code=authorization_code,
                    redirect_uri=redirect_uri,
                )

                await self._health_tracker.record_success()

                return {
                    "access_token": token.get("access_token"),
                    "id_token": token.get("id_token"),
                    "refresh_token": token.get("refresh_token"),
                    "expires_in": token.get("expires_in"),
                }

        except httpx.TimeoutException:
            await self._health_tracker.record_failure()
            raise SSOError("SSO service timeout during token exchange")
        except httpx.HTTPError as e:
            await self._health_tracker.record_failure()
            raise SSOError(f"Token exchange failed: {str(e)}")

    async def _get_jwks(self) -> Dict:
        """Get JWKS with caching."""
        # Check cache (5 minute cache)
        if self._jwks_cache and self._jwks_cache_time:
            cache_age = utc_now() - self._jwks_cache_time
            if cache_age < timedelta(minutes=5):
                return self._jwks_cache

        # Fetch JWKS
        async with httpx.AsyncClient(timeout=SSO_TIMEOUT_SECONDS) as client:
            response = await client.get(self._jwks_uri)
            response.raise_for_status()

            self._jwks_cache = response.json()
            self._jwks_cache_time = utc_now()

            return self._jwks_cache

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scope: str = "openid email profile",
    ) -> str:
        """Generate SSO authorization URL."""
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self._issuer_url}/oauth2/authorize?{query}"


# Role mapping from IAM Identity Center groups
DEFAULT_ROLE_MAPPING: Dict[str, str] = {
    "AI-Platform-Admins": "admin",
    "AI-Platform-ProjectManagers": "project_manager",
    "AI-Platform-Engineers": "engineer",
    "AI-Platform-Viewers": "viewer",
}


def map_groups_to_role(
    groups: List[str], role_mapping: Optional[Dict[str, str]] = None
) -> str:
    """Map SSO groups to platform role (highest privilege wins)."""
    mapping = role_mapping or DEFAULT_ROLE_MAPPING

    from src.core.security.constants import ROLE_HIERARCHY

    best_role = "viewer"  # Default role
    best_level = ROLE_HIERARCHY.get(best_role, 0)

    for group in groups:
        if group in mapping:
            role = mapping[group]
            level = ROLE_HIERARCHY.get(role, 0)
            if level > best_level:
                best_role = role
                best_level = level

    return best_role


# Singleton instance
_sso_service: Optional[SSOService] = None


def get_sso_service() -> Optional[SSOService]:
    """Get SSO service singleton (None if not configured)."""
    return _sso_service


def configure_sso_service(
    issuer_url: str,
    client_id: str,
    client_secret: Optional[str] = None,
) -> SSOService:
    """Configure and return SSO service."""
    global _sso_service
    _sso_service = SSOService(
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
    )
    return _sso_service
