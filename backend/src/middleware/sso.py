"""SSO Integration middleware for AWS IAM Identity Center.

Task: T013a - SSO 集成实现
集成 AWS IAM Identity Center (SAML 2.0/OIDC),配置 IdP 元数据,
实现用户自动映射和角色同步
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from jose import jwt
from pydantic import BaseModel

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class SSOUserInfo(BaseModel):
    """User information from SSO provider."""

    sub: str  # Subject identifier
    email: str
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    groups: list[str] = []
    roles: list[str] = []


class SSOConfig(BaseModel):
    """SSO Configuration loaded from IdP metadata."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    end_session_endpoint: Optional[str] = None
    scopes_supported: list[str] = ["openid", "email", "profile"]


@dataclass
class SSOTokenResponse:
    """Token response from SSO provider."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class SSOClient:
    """Client for AWS IAM Identity Center OIDC integration."""

    def __init__(self):
        """Initialize SSO client with configuration."""
        self.settings = get_settings()
        self._config: Optional[SSOConfig] = None
        self._jwks: Optional[dict[str, Any]] = None

    @property
    def is_enabled(self) -> bool:
        """Check if SSO is enabled."""
        return (
            self.settings.sso_enabled
            and self.settings.sso_issuer_url is not None
            and self.settings.sso_client_id is not None
        )

    async def discover_configuration(self) -> SSOConfig:
        """Discover OIDC configuration from well-known endpoint.

        Returns:
            SSOConfig with IdP metadata

        Raises:
            RuntimeError: If discovery fails
        """
        if not self.settings.sso_issuer_url:
            raise RuntimeError("SSO issuer URL not configured")

        discovery_url = f"{self.settings.sso_issuer_url}/.well-known/openid-configuration"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(discovery_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                self._config = SSOConfig(
                    issuer=data["issuer"],
                    authorization_endpoint=data["authorization_endpoint"],
                    token_endpoint=data["token_endpoint"],
                    userinfo_endpoint=data["userinfo_endpoint"],
                    jwks_uri=data["jwks_uri"],
                    end_session_endpoint=data.get("end_session_endpoint"),
                    scopes_supported=data.get("scopes_supported", ["openid", "email", "profile"]),
                )
                return self._config
            except httpx.HTTPError as e:
                logger.error(f"Failed to discover SSO configuration: {e}")
                raise RuntimeError(f"SSO discovery failed: {e}")

    async def get_jwks(self) -> dict[str, Any]:
        """Fetch JSON Web Key Set for token verification.

        Returns:
            JWKS dictionary
        """
        if not self._config:
            await self.discover_configuration()

        async with httpx.AsyncClient() as client:
            response = await client.get(self._config.jwks_uri, timeout=10.0)
            response.raise_for_status()
            self._jwks = response.json()
            return self._jwks

    def get_authorization_url(self, state: str, nonce: str) -> str:
        """Generate authorization URL for SSO login.

        Args:
            state: CSRF protection state parameter
            nonce: Replay protection nonce

        Returns:
            Authorization URL to redirect user
        """
        if not self._config:
            raise RuntimeError("SSO not configured. Call discover_configuration first.")

        params = {
            "client_id": self.settings.sso_client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": self.settings.sso_redirect_uri,
            "state": state,
            "nonce": nonce,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self._config.authorization_endpoint}?{query_string}"

    async def exchange_code_for_tokens(self, code: str) -> SSOTokenResponse:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            RuntimeError: If token exchange fails
        """
        if not self._config:
            await self.discover_configuration()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._config.token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.settings.sso_redirect_uri,
                        "client_id": self.settings.sso_client_id,
                        "client_secret": self.settings.sso_client_secret,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                return SSOTokenResponse(
                    access_token=data["access_token"],
                    token_type=data["token_type"],
                    expires_in=data["expires_in"],
                    refresh_token=data.get("refresh_token"),
                    id_token=data.get("id_token"),
                    scope=data.get("scope"),
                )
            except httpx.HTTPError as e:
                logger.error(f"Token exchange failed: {e}")
                raise RuntimeError(f"Token exchange failed: {e}")

    async def get_userinfo(self, access_token: str) -> SSOUserInfo:
        """Fetch user information from SSO provider.

        Args:
            access_token: OAuth access token

        Returns:
            SSOUserInfo with user details

        Raises:
            RuntimeError: If userinfo request fails
        """
        if not self._config:
            await self.discover_configuration()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self._config.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                return SSOUserInfo(
                    sub=data["sub"],
                    email=data.get("email", ""),
                    name=data.get("name"),
                    preferred_username=data.get("preferred_username"),
                    groups=data.get("groups", []),
                    roles=data.get("roles", []),
                )
            except httpx.HTTPError as e:
                logger.error(f"Userinfo request failed: {e}")
                raise RuntimeError(f"Userinfo request failed: {e}")

    def verify_id_token(self, id_token: str, nonce: Optional[str] = None) -> dict[str, Any]:
        """Verify and decode ID token.

        Args:
            id_token: JWT ID token
            nonce: Expected nonce value

        Returns:
            Decoded token claims

        Raises:
            RuntimeError: If verification fails
        """
        if not self._jwks:
            raise RuntimeError("JWKS not loaded. Call get_jwks first.")

        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")

            # Find matching key in JWKS
            key = None
            for k in self._jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break

            if not key:
                raise RuntimeError(f"Key {kid} not found in JWKS")

            # Verify and decode token
            claims = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=self.settings.sso_client_id,
                issuer=self._config.issuer if self._config else None,
            )

            # Verify nonce if provided
            if nonce and claims.get("nonce") != nonce:
                raise RuntimeError("Nonce mismatch")

            return claims
        except Exception as e:
            logger.error(f"ID token verification failed: {e}")
            raise RuntimeError(f"ID token verification failed: {e}")

    async def logout_url(self, id_token: Optional[str] = None) -> Optional[str]:
        """Generate logout URL for SSO logout.

        Args:
            id_token: ID token for logout hint

        Returns:
            Logout URL or None if not supported
        """
        if not self._config or not self._config.end_session_endpoint:
            return None

        params = {"client_id": self.settings.sso_client_id}
        if id_token:
            params["id_token_hint"] = id_token
        if self.settings.sso_redirect_uri:
            params["post_logout_redirect_uri"] = self.settings.sso_redirect_uri.rsplit("/", 1)[0]

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self._config.end_session_endpoint}?{query_string}"


def map_sso_user_to_role(sso_user: SSOUserInfo) -> str:
    """Map SSO user groups/roles to platform role.

    Args:
        sso_user: User information from SSO

    Returns:
        Platform role name (admin/project_manager/engineer/viewer)
    """
    # Role mapping based on SSO groups
    # These group names should match IAM Identity Center group names
    admin_groups = ["platform-admins", "administrators", "admin"]
    pm_groups = ["project-managers", "team-leads"]
    engineer_groups = ["engineers", "developers", "ml-engineers"]

    # Check groups for role assignment
    user_groups = [g.lower() for g in sso_user.groups]

    for group in admin_groups:
        if group in user_groups:
            return "admin"

    for group in pm_groups:
        if group in user_groups:
            return "project_manager"

    for group in engineer_groups:
        if group in user_groups:
            return "engineer"

    # Default role
    return "viewer"


# Singleton instance
_sso_client: Optional[SSOClient] = None


def get_sso_client() -> SSOClient:
    """Get or create SSO client singleton.

    Returns:
        SSOClient instance
    """
    global _sso_client
    if _sso_client is None:
        _sso_client = SSOClient()
    return _sso_client
