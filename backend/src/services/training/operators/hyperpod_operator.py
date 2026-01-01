"""HyperPod Training Operator集成

负责与AWS SageMaker HyperPod Training Operator交互,
管理Kubernetes HyperPodPytorchJob资源的生命周期
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml
from kubernetes import client
from kubernetes.client.exceptions import ApiException

from config.settings import settings
from models.training import (
    FrameworkType,
    TrainingJob,
    TrainingJobConfig,
    TrainingJobStatus,
)
from services.training.templates import TemplateRenderer

logger = logging.getLogger(__name__)

# K8s API组和版本(HyperPod使用标准Kubeflow Training Operator的API)
PYTORCH_JOB_GROUP = "kubeflow.org"
PYTORCH_JOB_VERSION = "v1"
PYTORCH_JOB_PLURAL = "pytorchjobs"


class HyperPodOperatorError(Exception):
    """HyperPod Operator异常基类"""

    pass


class JobCreationError(HyperPodOperatorError):
    """任务创建失败异常"""

    pass


class JobNotFoundError(HyperPodOperatorError):
    """任务不存在异常"""

    pass


class JobStatusError(HyperPodOperatorError):
    """任务状态查询失败异常"""

    pass


class HyperPodOperator:
    """HyperPod Training Operator客户端

    封装与Kubernetes HyperPodPytorchJob CRD的交互逻辑
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        in_cluster: bool = False,
        templates_dir: Optional[Path] = None,
    ):
        """初始化HyperPod Operator客户端

        Args:
            kubeconfig_path: Kubernetes配置文件路径(本地开发时使用)
            in_cluster: 是否运行在集群内(生产环境使用ServiceAccount)
            templates_dir: 模板文件目录,默认为None(使用TemplateRenderer默认目录)
        """
        self.kubeconfig_path = kubeconfig_path or settings.k8s_config_path
        self.in_cluster = in_cluster or settings.k8s_in_cluster

        # 初始化K8s客户端
        self._init_k8s_client()

        # 初始化模板渲染器
        self.template_renderer = TemplateRenderer(templates_dir=templates_dir)

        logger.info(
            f"HyperPod Operator初始化成功 (in_cluster={self.in_cluster})"
        )

    def _init_k8s_client(self) -> None:
        """初始化Kubernetes客户端

        Raises:
            HyperPodOperatorError: 客户端初始化失败
        """
        try:
            if self.in_cluster:
                # 使用集群内ServiceAccount
                from kubernetes import config as k8s_config

                k8s_config.load_incluster_config()
                logger.info("使用集群内ServiceAccount初始化K8s客户端")
            else:
                # 使用kubeconfig文件
                from kubernetes import config as k8s_config

                k8s_config.load_kube_config(config_file=self.kubeconfig_path)
                logger.info(
                    f"使用kubeconfig初始化K8s客户端: {self.kubeconfig_path}"
                )

            # 创建CustomObjectsApi客户端(用于CRD操作)
            self.custom_api = client.CustomObjectsApi()
            # 创建CoreV1Api客户端(用于Pod操作)
            self.core_api = client.CoreV1Api()

        except Exception as e:
            raise HyperPodOperatorError(
                f"K8s客户端初始化失败: {str(e)}"
            ) from e


    async def create_pytorch_job(
        self,
        job: TrainingJob,
        config: TrainingJobConfig,
        priority: str = "normal",
        queue_name: Optional[str] = None,
    ) -> str:
        """创建HyperPodPytorchJob

        Args:
            job: 训练任务对象
            config: 训练任务配置
            priority: Kueue优先级(low/normal/high),默认normal
            queue_name: Kueue LocalQueue名称,默认使用项目队列

        Returns:
            K8s Job名称

        Raises:
            JobCreationError: Job创建失败
        """
        try:
            # 生成K8s Job名称(需要符合DNS-1123规范)
            k8s_job_name = self._generate_job_name(job)

            # 渲染模板(传递Kueue参数)
            job_manifest = self._render_job_manifest(
                job=job,
                config=config,
                k8s_job_name=k8s_job_name,
                priority=priority,
                queue_name=queue_name,
            )

            # 解析YAML为字典
            job_dict = yaml.safe_load(job_manifest)

            # 创建CustomResource
            logger.info(
                f"开始创建PyTorchJob: {k8s_job_name} (namespace={job.k8s_namespace})"
            )

            # 使用asyncio.to_thread包装同步API调用
            await asyncio.to_thread(
                self.custom_api.create_namespaced_custom_object,
                group=PYTORCH_JOB_GROUP,
                version=PYTORCH_JOB_VERSION,
                namespace=job.k8s_namespace,
                plural=PYTORCH_JOB_PLURAL,
                body=job_dict,
            )

            logger.info(f"PyTorchJob创建成功: {k8s_job_name}")
            return k8s_job_name

        except ApiException as e:
            error_msg = f"K8s API调用失败 (status={e.status}): {e.reason}"
            logger.error(error_msg)
            raise JobCreationError(error_msg) from e
        except Exception as e:
            error_msg = f"PyTorchJob创建失败: {str(e)}"
            logger.error(error_msg)
            raise JobCreationError(error_msg) from e

    def _generate_job_name(self, job: TrainingJob) -> str:
        """生成Kubernetes Job名称

        符合DNS-1123规范: 小写字母、数字、连字符,最长63字符

        Args:
            job: 训练任务对象

        Returns:
            K8s Job名称
        """
        # 使用job ID和时间戳确保唯一性
        timestamp = datetime.utcnow().strftime("%y%m%d-%H%M%S")
        # 转换为小写并替换下划线为连字符
        name_prefix = job.name.lower().replace("_", "-").replace(" ", "-")
        # 截断到合适长度(预留时间戳和ID空间)
        name_prefix = name_prefix[:35]
        # 组合: prefix-id-timestamp
        k8s_job_name = f"{name_prefix}-{job.id}-{timestamp}"

        return k8s_job_name

    def _render_job_manifest(
        self,
        job: TrainingJob,
        config: TrainingJobConfig,
        k8s_job_name: str,
        priority: str = "normal",
        queue_name: Optional[str] = None,
    ) -> str:
        """渲染PyTorchJob YAML清单

        Args:
            job: 训练任务对象
            config: 训练任务配置
            k8s_job_name: K8s Job名称
            priority: Kueue优先级
            queue_name: Kueue队列名称

        Returns:
            渲染后的YAML字符串
        """
        # 使用TemplateRenderer渲染模板(传递Kueue参数)
        rendered = self.template_renderer.render_pytorch_job(
            job=job,
            config=config,
            k8s_job_name=k8s_job_name,
            priority=priority,
            queue_name=queue_name,
        )
        return rendered


    async def get_job_status(
        self,
        job_name: str,
        namespace: str,
    ) -> dict[str, Any]:
        """查询PyTorchJob状态

        Args:
            job_name: K8s Job名称
            namespace: K8s命名空间

        Returns:
            Job状态字典,包含:
            - status: 任务状态(Pending/Running/Succeeded/Failed)
            - conditions: 状态条件列表
            - replica_statuses: 副本状态(Master/Worker)
            - start_time: 开始时间
            - completion_time: 完成时间

        Raises:
            JobNotFoundError: Job不存在
            JobStatusError: 状态查询失败
        """
        try:
            logger.debug(f"查询PyTorchJob状态: {job_name} (namespace={namespace})")

            # 使用asyncio.to_thread包装同步API调用
            job_obj = await asyncio.to_thread(
                self.custom_api.get_namespaced_custom_object,
                group=PYTORCH_JOB_GROUP,
                version=PYTORCH_JOB_VERSION,
                namespace=namespace,
                plural=PYTORCH_JOB_PLURAL,
                name=job_name,
            )

            # 提取状态信息
            status_dict = self._parse_job_status(job_obj)

            logger.debug(
                f"PyTorchJob状态: {job_name} -> {status_dict['status']}"
            )
            return status_dict

        except ApiException as e:
            if e.status == 404:
                raise JobNotFoundError(
                    f"PyTorchJob不存在: {job_name} (namespace={namespace})"
                ) from e
            error_msg = f"K8s API调用失败 (status={e.status}): {e.reason}"
            logger.error(error_msg)
            raise JobStatusError(error_msg) from e
        except Exception as e:
            error_msg = f"PyTorchJob状态查询失败: {str(e)}"
            logger.error(error_msg)
            raise JobStatusError(error_msg) from e

    def _parse_job_status(self, job_obj: dict[str, Any]) -> dict[str, Any]:
        """解析PyTorchJob状态对象

        Args:
            job_obj: K8s CustomObject

        Returns:
            标准化的状态字典
        """
        status = job_obj.get("status", {})

        # 提取条件(conditions)
        conditions = status.get("conditions", [])
        # 找到最新的条件
        latest_condition = conditions[-1] if conditions else {}
        condition_type = latest_condition.get("type", "Pending")

        # 映射K8s状态到TrainingJobStatus
        status_mapping = {
            "Created": TrainingJobStatus.QUEUED,
            "Running": TrainingJobStatus.RUNNING,
            "Succeeded": TrainingJobStatus.COMPLETED,
            "Failed": TrainingJobStatus.FAILED,
        }
        job_status = status_mapping.get(
            condition_type, TrainingJobStatus.PENDING
        )

        # 提取副本状态
        replica_statuses = status.get("replicaStatuses", {})

        # 提取时间
        start_time = status.get("startTime")
        completion_time = status.get("completionTime")

        return {
            "status": job_status,
            "conditions": conditions,
            "replica_statuses": replica_statuses,
            "start_time": start_time,
            "completion_time": completion_time,
            "message": latest_condition.get("message", ""),
            "reason": latest_condition.get("reason", ""),
        }

    async def delete_job(
        self,
        job_name: str,
        namespace: str,
    ) -> bool:
        """删除PyTorchJob

        Args:
            job_name: K8s Job名称
            namespace: K8s命名空间

        Returns:
            是否删除成功

        Raises:
            JobNotFoundError: Job不存在
            HyperPodOperatorError: 删除失败
        """
        try:
            logger.info(
                f"开始删除PyTorchJob: {job_name} (namespace={namespace})"
            )

            # 使用asyncio.to_thread包装同步API调用
            await asyncio.to_thread(
                self.custom_api.delete_namespaced_custom_object,
                group=PYTORCH_JOB_GROUP,
                version=PYTORCH_JOB_VERSION,
                namespace=namespace,
                plural=PYTORCH_JOB_PLURAL,
                name=job_name,
            )

            logger.info(f"PyTorchJob删除成功: {job_name}")
            return True

        except ApiException as e:
            if e.status == 404:
                logger.warning(f"PyTorchJob不存在(可能已删除): {job_name}")
                raise JobNotFoundError(
                    f"PyTorchJob不存在: {job_name}"
                ) from e
            error_msg = f"K8s API调用失败 (status={e.status}): {e.reason}"
            logger.error(error_msg)
            raise HyperPodOperatorError(error_msg) from e
        except Exception as e:
            error_msg = f"PyTorchJob删除失败: {str(e)}"
            logger.error(error_msg)
            raise HyperPodOperatorError(error_msg) from e

    async def sync_job_status(
        self,
        job: TrainingJob,
    ) -> tuple[TrainingJobStatus, Optional[str], Optional[str]]:
        """同步PyTorchJob状态到数据库

        Args:
            job: 训练任务对象

        Returns:
            (新状态, 错误信息, 退出码)

        Raises:
            JobNotFoundError: Job不存在
            JobStatusError: 状态查询失败
        """
        if not job.k8s_job_name:
            raise ValueError(f"训练任务 {job.id} 尚未创建K8s Job")

        # 查询K8s状态
        status_dict = await self.get_job_status(
            job_name=job.k8s_job_name,
            namespace=job.k8s_namespace,
        )

        new_status = status_dict["status"]
        error_message = None
        exit_code = None

        # 如果任务失败,提取错误信息
        if new_status == TrainingJobStatus.FAILED:
            error_message = status_dict.get("message", "训练任务失败")
            # 尝试从Pod日志中提取更多信息
            try:
                pod_logs = await self._get_failed_pod_logs(
                    job_name=job.k8s_job_name,
                    namespace=job.k8s_namespace,
                )
                if pod_logs:
                    error_message += f"\n\nPod日志摘要:\n{pod_logs[:500]}"
            except Exception as e:
                logger.warning(f"获取Pod日志失败: {e}")

        logger.info(
            f"同步训练任务状态: {job.id} ({job.status.value} -> {new_status.value})"
        )

        return new_status, error_message, exit_code

    async def _get_failed_pod_logs(
        self,
        job_name: str,
        namespace: str,
        tail_lines: int = 100,
    ) -> Optional[str]:
        """获取失败Pod的日志

        Args:
            job_name: K8s Job名称
            namespace: K8s命名空间
            tail_lines: 日志行数

        Returns:
            Pod日志字符串
        """
        try:
            # 查询Job的所有Pod
            label_selector = f"training-job-id={job_name}"
            pod_list = await asyncio.to_thread(
                self.core_api.list_namespaced_pod,
                namespace=namespace,
                label_selector=label_selector,
            )

            # 找到失败的Pod
            failed_pods = [
                pod
                for pod in pod_list.items
                if pod.status.phase in ["Failed", "Error"]
            ]

            if not failed_pods:
                return None

            # 获取第一个失败Pod的日志
            pod_name = failed_pods[0].metadata.name
            logs = await asyncio.to_thread(
                self.core_api.read_namespaced_pod_log,
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
            )

            return logs

        except Exception as e:
            logger.warning(f"获取Pod日志失败: {e}")
            return None

    async def get_pod_list(
        self,
        job_name: str,
        namespace: str,
    ) -> list[str]:
        """获取训练任务的Pod列表

        Args:
            job_name: K8s Job名称
            namespace: K8s命名空间

        Returns:
            Pod名称列表
        """
        try:
            label_selector = f"training-job-id={job_name}"
            pod_list = await asyncio.to_thread(
                self.core_api.list_namespaced_pod,
                namespace=namespace,
                label_selector=label_selector,
            )

            pod_names = [pod.metadata.name for pod in pod_list.items]
            return pod_names

        except Exception as e:
            logger.error(f"获取Pod列表失败: {e}")
            return []


__all__ = [
    "HyperPodOperator",
    "HyperPodOperatorError",
    "JobCreationError",
    "JobNotFoundError",
    "JobStatusError",
]
