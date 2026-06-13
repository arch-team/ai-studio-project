"""Workspace CRD conditions -> 平台 SpaceStatus 映射测试。

真实 CRD (workspace.jupyter.org/v1alpha1) 使用 K8s 标准 conditions 模型,
而非单一 phase 字段。条件类型: Available / Progressing / Degraded / Stopped,
每个状态为 True / False / Unknown。映射规则按优先级判定 (Phase B Task 15 核验)。
"""

from src.modules.spaces.domain.value_objects import SpaceStatus, map_workspace_status


def _conditions(**types: str) -> list[dict[str, str]]:
    """构造 conditions 列表辅助函数。types 形如 Available="True", Progressing="False"。"""
    return [{"type": t, "status": s} for t, s in types.items()]


class TestMapWorkspaceStatus:
    def test_available_true_maps_running(self) -> None:
        conditions = _conditions(Available="True", Progressing="False", Degraded="False", Stopped="False")
        assert map_workspace_status(conditions) is SpaceStatus.RUNNING

    def test_progressing_true_maps_pending(self) -> None:
        # 启动中: Available=False, Progressing=True (真实观察到的启动态)
        conditions = _conditions(Available="False", Progressing="True", Degraded="False", Stopped="False")
        assert map_workspace_status(conditions) is SpaceStatus.PENDING

    def test_stopped_true_maps_stopped(self) -> None:
        conditions = _conditions(Available="False", Progressing="False", Degraded="False", Stopped="True")
        assert map_workspace_status(conditions) is SpaceStatus.STOPPED

    def test_degraded_true_maps_failed(self) -> None:
        conditions = _conditions(Available="False", Progressing="False", Degraded="True", Stopped="False")
        assert map_workspace_status(conditions) is SpaceStatus.FAILED

    def test_degraded_takes_precedence_over_progressing(self) -> None:
        # Degraded 优先级高于 Progressing: 故障态即使仍在尝试也判 FAILED
        conditions = _conditions(Available="False", Progressing="True", Degraded="True", Stopped="False")
        assert map_workspace_status(conditions) is SpaceStatus.FAILED

    def test_stopped_takes_precedence_over_available(self) -> None:
        # Stopped 是终态信号: 优先于 Available
        conditions = _conditions(Available="False", Progressing="False", Stopped="True")
        assert map_workspace_status(conditions) is SpaceStatus.STOPPED

    def test_none_maps_stopped(self) -> None:
        # conditions 为 None (CRD 不存在) = 无运行实例 = 已停止 (同方式一语义)
        assert map_workspace_status(None) is SpaceStatus.STOPPED

    def test_empty_list_maps_pending(self) -> None:
        # 空 conditions (CRD 刚创建,controller 尚未写入状态) = 启动中
        assert map_workspace_status([]) is SpaceStatus.PENDING

    def test_all_false_maps_none(self) -> None:
        # 所有条件均 False/Unknown 且无明确信号: 返回 None (下游不变更状态)
        conditions = _conditions(Available="Unknown", Progressing="Unknown", Degraded="Unknown")
        assert map_workspace_status(conditions) is None
