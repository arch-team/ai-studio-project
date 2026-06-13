"""HyperPod Workspace CRD 状态映射。

状态字符串源自 AWS 文档（task-governance/create-manage-spaces），
Phase B 安装 add-on 后需对照真实集群 CRD schema 核验。
"""

from .space_enums import SpaceStatus

# Workspace.status.phase -> 平台 SpaceStatus
_WORKSPACE_STATUS_MAP: dict[str, SpaceStatus] = {
    "Creating": SpaceStatus.PENDING,
    "Pending": SpaceStatus.PENDING,
    "Running": SpaceStatus.RUNNING,
    "Stopped": SpaceStatus.STOPPED,
    "Failed": SpaceStatus.FAILED,
    "Degraded": SpaceStatus.FAILED,
}


def map_workspace_status(phase: str | None) -> SpaceStatus | None:
    """映射 Workspace CRD phase 到平台状态。

    None（CRD 不存在）映射为 STOPPED；无法识别的状态返回 None（调用方不变更状态）。
    """
    if phase is None:
        return SpaceStatus.STOPPED
    return _WORKSPACE_STATUS_MAP.get(phase)
