"""HyperPod 训练任务配置构建工具。

提取共享的配置构建逻辑，供 JobClient 和 CheckpointClient 复用。
"""

from typing import Any


def build_env_list(env_dict: dict[str, Any] | None) -> list[Any] | None:
    """构建环境变量列表。"""
    if not env_dict:
        return None

    from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import Env

    return [Env(name=k, value=str(v)) for k, v in env_dict.items()]


def build_container(
    image_uri: str | None,
    command: str | list[str] | None,
    env_dict: dict[str, Any] | None,
    gpu_count: int = 0,
) -> Any:
    """构建容器配置。"""
    from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
        Containers,
        Resources,
    )

    env_list = build_env_list(env_dict)

    resources = None
    if gpu_count > 0:
        resources = Resources(
            limits={"nvidia.com/gpu": str(gpu_count)},
            requests={"nvidia.com/gpu": str(gpu_count)},
        )

    cmd = None
    if command:
        cmd = command if isinstance(command, list) else [command]

    return Containers(
        name="pytorch",
        image=image_uri,
        command=cmd,
        env=env_list,
        resources=resources,
    )


def build_kueue_labels(queue_name: str | None, priority_class: str | None) -> dict[str, str]:
    """构建 Kueue 调度标签。"""
    labels: dict[str, str] = {}
    if queue_name:
        labels["kueue.x-k8s.io/queue-name"] = queue_name
    if priority_class:
        labels["kueue.x-k8s.io/priority-class"] = priority_class
    return labels


def build_replica_spec(container: Any, node_count: int) -> Any:
    """构建 ReplicaSpec 配置。"""
    from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
        ReplicaSpec,
        Spec,
        Template,
    )

    return ReplicaSpec(
        name="worker",
        replicas=node_count,
        template=Template(spec=Spec(containers=[container])),
    )
