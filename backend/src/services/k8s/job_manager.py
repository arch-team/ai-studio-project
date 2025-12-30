"""Kubernetes Job管理服务

管理训练任务对应的K8S Job资源
"""

import logging
from typing import Any

from kubernetes import client
from kubernetes.client import ApiException

from .client import get_k8s_client

logger = logging.getLogger(__name__)


class JobManager:
    """K8S Job管理器

    负责创建、查询、删除训练任务对应的K8S Job
    """

    def __init__(self):
        """初始化Job管理器"""
        self.k8s_client = get_k8s_client()
        self.batch_v1 = self.k8s_client.batch_v1

    def create_training_job(
        self,
        namespace: str,
        job_name: str,
        image: str,
        command: list[str],
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
        node_count: int = 1,
        gpu_per_node: int = 1,
        cpu_per_node: int = 8,
        memory_per_node_gb: int = 32,
        gpu_type: str | None = None,
        labels: dict[str, str] | None = None,
        volume_mounts: list[dict] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict:
        """创建训练任务Job

        Args:
            namespace: 命名空间
            job_name: Job名称
            image: Docker镜像
            command: 执行命令
            args: 命令参数
            env_vars: 环境变量
            node_count: 节点数量(分布式训练)
            gpu_per_node: 每节点GPU数
            cpu_per_node: 每节点CPU数
            memory_per_node_gb: 每节点内存(GB)
            gpu_type: GPU型号
            labels: 标签
            volume_mounts: 卷挂载配置
            timeout_seconds: 超时时间(秒)

        Returns:
            dict: 创建的Job信息
        """
        try:
            # 构建容器环境变量
            env_list = []
            if env_vars:
                env_list = [client.V1EnvVar(name=k, value=v) for k, v in env_vars.items()]

            # 添加分布式训练环境变量
            if node_count > 1:
                env_list.extend([
                    client.V1EnvVar(name="WORLD_SIZE", value=str(node_count)),
                    client.V1EnvVar(name="MASTER_ADDR", value=f"{job_name}-0"),
                    client.V1EnvVar(name="MASTER_PORT", value="29500"),
                ])

            # 构建资源请求和限制
            resources = client.V1ResourceRequirements(
                requests={
                    "cpu": str(cpu_per_node),
                    "memory": f"{memory_per_node_gb}Gi",
                    "nvidia.com/gpu": str(gpu_per_node) if gpu_per_node > 0 else "0",
                },
                limits={
                    "cpu": str(cpu_per_node),
                    "memory": f"{memory_per_node_gb}Gi",
                    "nvidia.com/gpu": str(gpu_per_node) if gpu_per_node > 0 else "0",
                },
            )

            # 构建容器配置
            container = client.V1Container(
                name="training",
                image=image,
                command=command,
                args=args or [],
                env=env_list,
                resources=resources,
                image_pull_policy="IfNotPresent",
            )

            # 如果有volume_mounts配置,添加卷挂载
            if volume_mounts:
                # TODO: 实现卷挂载逻辑
                pass

            # 构建Pod模板
            pod_template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels or {}),
                spec=client.V1PodSpec(
                    containers=[container],
                    restart_policy="OnFailure",
                    # GPU节点选择器
                    node_selector={"node.kubernetes.io/gpu": gpu_type} if gpu_type else None,
                ),
            )

            # 构建Job配置
            job_spec = client.V1JobSpec(
                template=pod_template,
                backoff_limit=3,  # 最多重试3次
                completions=node_count,  # 需要成功完成的Pod数
                parallelism=node_count,  # 并行执行的Pod数
                active_deadline_seconds=timeout_seconds,  # 超时时间
            )

            # 创建Job对象
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(name=job_name, namespace=namespace, labels=labels or {}),
                spec=job_spec,
            )

            # 提交Job到K8S
            result = self.batch_v1.create_namespaced_job(namespace=namespace, body=job)
            logger.info(f"创建训练Job成功: {namespace}/{job_name}")
            return result.to_dict()

        except ApiException as e:
            logger.error(f"创建训练Job失败: {namespace}/{job_name} - {e}")
            raise

    def get_job(self, namespace: str, job_name: str) -> dict | None:
        """获取Job信息

        Args:
            namespace: 命名空间
            job_name: Job名称

        Returns:
            dict: Job信息,不存在返回None
        """
        try:
            result = self.batch_v1.read_namespaced_job(name=job_name, namespace=namespace)
            return result.to_dict()
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"获取Job失败: {namespace}/{job_name} - {e}")
            raise

    def get_job_status(self, namespace: str, job_name: str) -> dict | None:
        """获取Job状态

        Args:
            namespace: 命名空间
            job_name: Job名称

        Returns:
            dict: Job状态信息
        """
        job = self.get_job(namespace, job_name)
        if not job:
            return None

        status = job.get("status", {})
        return {
            "active": status.get("active", 0),  # 运行中的Pod数
            "succeeded": status.get("succeeded", 0),  # 成功的Pod数
            "failed": status.get("failed", 0),  # 失败的Pod数
            "start_time": status.get("start_time"),
            "completion_time": status.get("completion_time"),
            "conditions": status.get("conditions", []),
        }

    def delete_job(self, namespace: str, job_name: str, propagation_policy: str = "Foreground") -> bool:
        """删除Job

        Args:
            namespace: 命名空间
            job_name: Job名称
            propagation_policy: 删除传播策略(Foreground/Background/Orphan)

        Returns:
            bool: 删除是否成功
        """
        try:
            self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                propagation_policy=propagation_policy,
            )
            logger.info(f"删除Job成功: {namespace}/{job_name}")
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            logger.error(f"删除Job失败: {namespace}/{job_name} - {e}")
            raise

    def list_jobs(
        self, namespace: str, label_selector: str | None = None
    ) -> list[dict]:
        """列出Job

        Args:
            namespace: 命名空间
            label_selector: 标签选择器

        Returns:
            list: Job列表
        """
        try:
            result = self.batch_v1.list_namespaced_job(
                namespace=namespace, label_selector=label_selector
            )
            return [item.to_dict() for item in result.items]
        except ApiException as e:
            logger.error(f"列出Job失败: {namespace} - {e}")
            raise


__all__ = ["JobManager"]
