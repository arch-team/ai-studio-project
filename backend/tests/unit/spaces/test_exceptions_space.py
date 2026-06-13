"""Spaces 模块异常测试。"""

from src.modules.spaces.domain.exceptions import (
    HyperPodSpaceBackendError,
    SpaceBackendUnavailableError,
)


class TestHyperPodSpaceBackendError:
    def test_http_status_400(self) -> None:
        err = HyperPodSpaceBackendError(message="CRD apply failed")
        assert err.http_status == 400
        assert err.error_code == "HYPERPOD_SPACE_BACKEND_ERROR"


class TestSpaceBackendUnavailableError:
    def test_http_status_503(self) -> None:
        err = SpaceBackendUnavailableError(message="add-on not installed")
        assert err.http_status == 503
        assert err.error_code == "SPACE_BACKEND_UNAVAILABLE"
