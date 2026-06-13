"""ISpaceBackendClient 接口契约测试。"""

import inspect

from src.modules.spaces.application.interfaces import ISpaceBackendClient


class TestISpaceBackendClient:
    def test_has_required_methods(self) -> None:
        for name in (
            "provision_space",
            "delete_space",
            "start_space",
            "stop_space",
            "describe_space",
            "create_access_url",
        ):
            assert hasattr(ISpaceBackendClient, name)

    def test_methods_are_async(self) -> None:
        assert inspect.iscoroutinefunction(ISpaceBackendClient.provision_space)
        assert inspect.iscoroutinefunction(ISpaceBackendClient.create_access_url)
