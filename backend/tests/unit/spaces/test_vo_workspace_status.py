"""Workspace CRD 状态 -> 平台 SpaceStatus 映射测试。"""

from src.modules.spaces.domain.value_objects import SpaceStatus, map_workspace_status


class TestMapWorkspaceStatus:
    def test_creating_maps_pending(self) -> None:
        assert map_workspace_status("Creating") is SpaceStatus.PENDING

    def test_running_maps_running(self) -> None:
        assert map_workspace_status("Running") is SpaceStatus.RUNNING

    def test_stopped_maps_stopped(self) -> None:
        assert map_workspace_status("Stopped") is SpaceStatus.STOPPED

    def test_failed_maps_failed(self) -> None:
        assert map_workspace_status("Failed") is SpaceStatus.FAILED

    def test_degraded_maps_failed(self) -> None:
        assert map_workspace_status("Degraded") is SpaceStatus.FAILED

    def test_none_maps_stopped(self) -> None:
        # CRD 不存在 = 无运行实例 = 已停止（同方式一语义）
        assert map_workspace_status(None) is SpaceStatus.STOPPED

    def test_unknown_maps_none(self) -> None:
        assert map_workspace_status("WeirdStatus") is None
