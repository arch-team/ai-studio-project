"""SSO Middleware Integration Tests."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List
from unittest.mock import patch

import pytest

from src.api.middleware.sso import (
    DEFAULT_ROLE_MAPPING,
    SSOHealthState,
    SSOHealthTracker,
    SSOService,
    SSOUserInfo,
    map_groups_to_role,
)
from src.core.security.constants import (
    SSO_MAX_CONSECUTIVE_FAILURES,
    SSO_RECOVERY_CHECK_INTERVAL_MINUTES,
)
from src.core.security.exceptions import SSODegradedModeError, SSOError
from src.core.utils import utc_now


class TestSSOHealthTracker:
    """Tests for SSO health state tracking."""

    @pytest.fixture
    def health_tracker(self) -> SSOHealthTracker:
        """Create a fresh health tracker."""
        return SSOHealthTracker()

    def test_sso_health_initial_state(self, health_tracker: SSOHealthTracker) -> None:
        """Test initial health state is not degraded."""
        assert health_tracker.is_degraded is False
        assert health_tracker._state.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_sso_health_record_success(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test recording success resets state."""
        # First cause some failures
        await health_tracker.record_failure()
        await health_tracker.record_failure()
        assert health_tracker._state.consecutive_failures == 2

        # Record success
        await health_tracker.record_success()

        assert health_tracker._state.consecutive_failures == 0
        assert health_tracker._state.last_success_at is not None
        assert health_tracker.is_degraded is False

    @pytest.mark.asyncio
    async def test_sso_health_record_failure(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test recording failure increments counter."""
        await health_tracker.record_failure()

        assert health_tracker._state.consecutive_failures == 1
        assert health_tracker._state.last_failure_at is not None

    @pytest.mark.asyncio
    async def test_sso_health_3_failures_degraded(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test 3 consecutive failures triggers degraded mode."""
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await health_tracker.record_failure()

        assert health_tracker.is_degraded is True
        assert (
            health_tracker._state.consecutive_failures == SSO_MAX_CONSECUTIVE_FAILURES
        )

    @pytest.mark.asyncio
    async def test_sso_health_recovery_check_too_soon(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test recovery check returns False if too soon after last check."""
        # Trigger degraded mode
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await health_tracker.record_failure()

        # Mark a recovery check as just performed
        await health_tracker.mark_recovery_check()

        # Check immediately after marking - should be False (too soon)
        should_attempt = await health_tracker.should_attempt_recovery()

        assert should_attempt is False

    @pytest.mark.asyncio
    async def test_sso_health_recovery_check_interval(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test recovery check returns True after interval."""
        # Trigger degraded mode
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await health_tracker.record_failure()

        # Set last recovery check to past (use utcnow to match implementation)
        health_tracker._state.last_recovery_check_at = utc_now() - timedelta(
            minutes=SSO_RECOVERY_CHECK_INTERVAL_MINUTES + 1
        )

        should_attempt = await health_tracker.should_attempt_recovery()

        assert should_attempt is True

    def test_sso_health_get_status(self, health_tracker: SSOHealthTracker) -> None:
        """Test get_status returns correct dict."""
        status = health_tracker.get_status()

        assert "is_degraded" in status
        assert "consecutive_failures" in status
        assert "last_failure_at" in status
        assert "last_success_at" in status

    @pytest.mark.asyncio
    async def test_sso_health_success_clears_degraded(
        self, health_tracker: SSOHealthTracker
    ) -> None:
        """Test success after degraded clears the flag."""
        # Trigger degraded
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await health_tracker.record_failure()
        assert health_tracker.is_degraded is True

        # Record success
        await health_tracker.record_success()

        assert health_tracker.is_degraded is False


class TestSSOUserInfo:
    """Tests for SSOUserInfo dataclass."""

    def test_sso_user_info_creation(self) -> None:
        """Test SSOUserInfo creation."""
        info = SSOUserInfo(
            identity_id="sso-123",
            username="ssouser",
            email="sso@example.com",
            display_name="SSO User",
            groups=["group1", "group2"],
        )

        assert info.identity_id == "sso-123"
        assert info.username == "ssouser"
        assert info.email == "sso@example.com"
        assert len(info.groups) == 2

    def test_sso_user_info_optional_fields(self) -> None:
        """Test SSOUserInfo with optional fields."""
        info = SSOUserInfo(
            identity_id="sso-123",
            username="ssouser",
            email="sso@example.com",
        )

        assert info.display_name is None
        assert info.groups == [] or info.groups is None


class TestMapGroupsToRole:
    """Tests for group to role mapping."""

    def test_map_groups_to_role_admin(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test admin group maps to admin role."""
        role = map_groups_to_role(sso_user_groups["admin_groups"])

        assert role == "admin"

    def test_map_groups_to_role_manager(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test project manager group maps correctly."""
        role = map_groups_to_role(sso_user_groups["manager_groups"])

        assert role == "project_manager"

    def test_map_groups_to_role_engineer(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test engineer group maps correctly."""
        role = map_groups_to_role(sso_user_groups["engineer_groups"])

        assert role == "engineer"

    def test_map_groups_to_role_viewer(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test viewer group maps correctly."""
        role = map_groups_to_role(sso_user_groups["viewer_groups"])

        assert role == "viewer"

    def test_map_groups_to_role_default(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test unmapped groups default to viewer."""
        role = map_groups_to_role(sso_user_groups["no_mapping_groups"])

        assert role == "viewer"

    def test_map_groups_to_role_multiple_highest(
        self, sso_user_groups: Dict[str, List[str]]
    ) -> None:
        """Test multiple groups returns highest privilege role."""
        role = map_groups_to_role(sso_user_groups["multiple_groups"])

        # Admin is highest, should be selected
        assert role == "admin"

    def test_map_groups_to_role_empty(self) -> None:
        """Test empty groups defaults to viewer."""
        role = map_groups_to_role([])

        assert role == "viewer"

    def test_map_groups_to_role_custom_mapping(self) -> None:
        """Test custom role mapping."""
        custom_mapping = {
            "Custom-Admins": "admin",
            "Custom-Users": "engineer",
        }
        role = map_groups_to_role(["Custom-Admins"], role_mapping=custom_mapping)

        assert role == "admin"


class TestSSOService:
    """Tests for SSO service functionality."""

    @pytest.fixture
    def sso_service(self) -> SSOService:
        """Create SSO service with test config."""
        return SSOService(
            issuer_url="https://test-issuer.example.com",
            client_id="test-client-id",
            client_secret="test-secret",
        )

    @pytest.mark.asyncio
    async def test_validate_id_token_degraded_mode(
        self, sso_service: SSOService
    ) -> None:
        """Test validation raises error in degraded mode when recovery too soon."""
        # Trigger degraded mode
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await sso_service._health_tracker.record_failure()

        # Mark recovery check as just performed (so next attempt is "too soon")
        await sso_service._health_tracker.mark_recovery_check()

        with pytest.raises(SSODegradedModeError):
            await sso_service.validate_id_token("some-token")

    @pytest.mark.asyncio
    async def test_validate_id_token_invalid(self, sso_service: SSOService) -> None:
        """Test validation with invalid token."""
        with patch.object(sso_service, "_get_jwks", return_value={}):
            with pytest.raises(SSOError):
                await sso_service.validate_id_token("invalid.token.here")

    def test_get_authorization_url(self, sso_service: SSOService) -> None:
        """Test authorization URL generation."""
        url = sso_service.get_authorization_url(
            redirect_uri="https://app.example.com/callback",
            state="random-state-string",
        )

        assert "https://test-issuer.example.com" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "state=random-state-string" in url
        assert "scope=" in url

    def test_get_authorization_url_custom_scope(self, sso_service: SSOService) -> None:
        """Test authorization URL with custom scope."""
        url = sso_service.get_authorization_url(
            redirect_uri="https://app.example.com/callback",
            state="state",
            scope="openid email profile groups",
        )

        assert "scope=" in url
        assert "groups" in url

    @pytest.mark.asyncio
    async def test_exchange_code_degraded_mode(self, sso_service: SSOService) -> None:
        """Test code exchange raises error in degraded mode when recovery too soon."""
        # Trigger degraded mode
        for _ in range(SSO_MAX_CONSECUTIVE_FAILURES):
            await sso_service._health_tracker.record_failure()

        # Mark recovery check as just performed (so next attempt is "too soon")
        await sso_service._health_tracker.mark_recovery_check()

        with pytest.raises(SSODegradedModeError):
            await sso_service.exchange_code_for_tokens(
                authorization_code="test-code",
                redirect_uri="https://app.example.com/callback",
            )


class TestSSOHealthState:
    """Tests for SSOHealthState dataclass."""

    def test_health_state_defaults(self) -> None:
        """Test SSOHealthState default values."""
        state = SSOHealthState()

        assert state.consecutive_failures == 0
        assert state.is_degraded is False
        assert state.last_failure_at is None
        assert state.last_recovery_check_at is None
        assert state.last_success_at is None

    def test_health_state_with_values(self) -> None:
        """Test SSOHealthState with explicit values."""
        now = datetime.now(timezone.utc)
        state = SSOHealthState(
            consecutive_failures=3,
            is_degraded=True,
            last_failure_at=now,
            last_success_at=now - timedelta(hours=1),
        )

        assert state.consecutive_failures == 3
        assert state.is_degraded is True
        assert state.last_failure_at == now


class TestDefaultRoleMapping:
    """Tests for DEFAULT_ROLE_MAPPING constant."""

    def test_default_mapping_has_all_roles(self) -> None:
        """Test default mapping has admin, PM, engineer, viewer groups."""
        assert "AI-Platform-Admins" in DEFAULT_ROLE_MAPPING
        assert "AI-Platform-ProjectManagers" in DEFAULT_ROLE_MAPPING
        assert "AI-Platform-Engineers" in DEFAULT_ROLE_MAPPING
        assert "AI-Platform-Viewers" in DEFAULT_ROLE_MAPPING

    def test_default_mapping_values(self) -> None:
        """Test default mapping maps to correct roles."""
        assert DEFAULT_ROLE_MAPPING["AI-Platform-Admins"] == "admin"
        assert DEFAULT_ROLE_MAPPING["AI-Platform-ProjectManagers"] == "project_manager"
        assert DEFAULT_ROLE_MAPPING["AI-Platform-Engineers"] == "engineer"
        assert DEFAULT_ROLE_MAPPING["AI-Platform-Viewers"] == "viewer"
