"""HyperPod Workspace CRD 状态映射。

真实 CRD (workspace.jupyter.org/v1alpha1) 使用 K8s 标准 conditions 模型,
而非单一 phase 字段 (Phase B Task 15 对照真实集群核验确认)。

条件类型 (status.conditions[].type):
- Available: 资源完全就绪可用
- Progressing: 正在创建/更新/停止
- Degraded: 未能达到或维持目标状态
- Stopped: 已停止,资源已缩容

每个条件 status 为 "True" / "False" / "Unknown"。
"""

from .space_enums import SpaceStatus


def _is_true(conditions: list[dict[str, str]], cond_type: str) -> bool:
    """判断指定类型的 condition 是否为 True。"""
    for cond in conditions:
        if cond.get("type") == cond_type:
            return cond.get("status") == "True"
    return False


def map_workspace_status(conditions: list[dict[str, str]] | None) -> SpaceStatus | None:
    """映射 Workspace CRD conditions 到平台状态。

    判定优先级 (高 -> 低):
    1. None (CRD 不存在) -> STOPPED (无运行实例,同方式一语义)
    2. Stopped=True -> STOPPED (终态信号优先)
    3. Degraded=True -> FAILED (故障优先于进行中)
    4. Available=True -> RUNNING
    5. Progressing=True 或空列表 -> PENDING (启动/变更中)
    6. 其他 (全 False/Unknown) -> None (下游不变更状态)
    """
    if conditions is None:
        return SpaceStatus.STOPPED

    # 空列表: CRD 刚创建,controller 尚未写入状态 = 启动中
    if not conditions:
        return SpaceStatus.PENDING

    if _is_true(conditions, "Stopped"):
        return SpaceStatus.STOPPED
    if _is_true(conditions, "Degraded"):
        return SpaceStatus.FAILED
    if _is_true(conditions, "Available"):
        return SpaceStatus.RUNNING
    if _is_true(conditions, "Progressing"):
        return SpaceStatus.PENDING

    # 全 False/Unknown 且无明确信号: 无可用状态,下游不变更
    return None
