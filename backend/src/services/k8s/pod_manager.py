"""Kubernetes Pod管理服务

管理训练任务Pod的查询和日志获取
"""

import logging
from typing import Any

from kubernetes import client
from kubernetes.client import ApiException

from .client import get_k8s_client

logger = logging.getLogger(__name__)


class PodManager:
    """K8S Pod管理器

    负责查询Pod状态、获取日志等操作
    """

    def __init__(self):
        """初始化Pod管理器"""
        self.k8s_client = get_k8s_client()
        self.core_v1 = self.k8s_client.core_v1

    def get_pod(self, namespace: str, pod_name: str) -> dict | None:
        """获取Pod信息

        Args:
            namespace: 命名空间
            pod_name: Pod名称

        Returns:
            dict: Pod信息,不存在返回None
        """
        try:
            result = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            return result.to_dict()
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"获取Pod失败: {namespace}/{pod_name} - {e}")
            raise

    def get_pod_status(self, namespace: str, pod_name: str) -> dict | None:
        """获取Pod状态

        Args:
            namespace: 命名空间
            pod_name: Pod名称

        Returns:
            dict: Pod状态信息
        """
        pod = self.get_pod(namespace, pod_name)
        if not pod:
            return None

        status = pod.get("status", {})
        return {
            "phase": status.get("phase"),  # Pending/Running/Succeeded/Failed/Unknown
            "conditions": status.get("conditions", []),
            "container_statuses": status.get("container_statuses", []),
            "start_time": status.get("start_time"),
            "pod_ip": status.get("pod_ip"),
            "host_ip": status.get("host_ip"),
        }

    def list_pods(
        self, namespace: str, label_selector: str | None = None
    ) -> list[dict]:
        """列出Pod

        Args:
            namespace: 命名空间
            label_selector: 标签选择器

        Returns:
            list: Pod列表
        """
        try:
            result = self.core_v1.list_namespaced_pod(
                namespace=namespace, label_selector=label_selector
            )
            return [item.to_dict() for item in result.items]
        except ApiException as e:
            logger.error(f"列出Pod失败: {namespace} - {e}")
            raise

    def list_pods_for_job(self, namespace: str, job_name: str) -> list[dict]:
        """列出Job关联的所有Pod

        Args:
            namespace: 命名空间
            job_name: Job名称

        Returns:
            list: Pod列表
        """
        label_selector = f"job-name={job_name}"
        return self.list_pods(namespace, label_selector)

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: str | None = None,
        tail_lines: int | None = None,
        since_seconds: int | None = None,
        follow: bool = False,
    ) -> str:
        """获取Pod日志

        Args:
            namespace: 命名空间
            pod_name: Pod名称
            container: 容器名称(多容器Pod需要指定)
            tail_lines: 返回最后N行
            since_seconds: 返回最近N秒的日志
            follow: 是否持续跟踪日志(流式)

        Returns:
            str: Pod日志内容
        """
        try:
            result = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                since_seconds=since_seconds,
                follow=follow,
            )
            return result
        except ApiException as e:
            logger.error(f"获取Pod日志失败: {namespace}/{pod_name} - {e}")
            raise

    def delete_pod(self, namespace: str, pod_name: str) -> bool:
        """删除Pod

        Args:
            namespace: 命名空间
            pod_name: Pod名称

        Returns:
            bool: 删除是否成功
        """
        try:
            self.core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            logger.info(f"删除Pod成功: {namespace}/{pod_name}")
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            logger.error(f"删除Pod失败: {namespace}/{pod_name} - {e}")
            raise

    def get_pod_events(self, namespace: str, pod_name: str) -> list[dict]:
        """获取Pod事件

        Args:
            namespace: 命名空间
            pod_name: Pod名称

        Returns:
            list: 事件列表
        """
        try:
            field_selector = f"involvedObject.name={pod_name},involvedObject.kind=Pod"
            result = self.core_v1.list_namespaced_event(
                namespace=namespace, field_selector=field_selector
            )
            return [item.to_dict() for item in result.items]
        except ApiException as e:
            logger.error(f"获取Pod事件失败: {namespace}/{pod_name} - {e}")
            raise

    def get_pod_metrics(self, namespace: str, pod_name: str) -> dict | None:
        """获取Pod资源使用指标

        注意: 需要安装metrics-server

        Args:
            namespace: 命名空间
            pod_name: Pod名称

        Returns:
            dict: Pod指标信息,不支持返回None
        """
        try:
            # 使用CustomObjectsApi获取metrics
            custom_api = client.CustomObjectsApi(self.k8s_client.core_v1.api_client)
            result = custom_api.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                name=pod_name,
            )
            return result
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Pod指标不可用(可能未安装metrics-server): {namespace}/{pod_name}")
                return None
            logger.error(f"获取Pod指标失败: {namespace}/{pod_name} - {e}")
            raise


__all__ = ["PodManager"]
