"""Kubernetes客户端服务

提供K8S集群操作的统一接口
"""

import logging
from typing import Any

from kubernetes import client, config
from kubernetes.client import ApiException

from config.settings import settings

logger = logging.getLogger(__name__)


class KubernetesClient:
    """Kubernetes客户端

    封装K8S API操作,提供统一的集群管理接口
    """

    def __init__(self):
        """初始化K8S客户端"""
        try:
            if settings.k8s_config_path:
                # 从配置文件加载
                config.load_kube_config(config_file=settings.k8s_config_path)
                logger.info(f"从配置文件加载K8S配置: {settings.k8s_config_path}")
            else:
                # 在集群内运行,使用ServiceAccount
                config.load_incluster_config()
                logger.info("使用集群内配置加载K8S客户端")

            # 初始化各类API客户端
            self.core_v1 = client.CoreV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()

            logger.info("Kubernetes客户端初始化成功")

        except Exception as e:
            logger.error(f"Kubernetes客户端初始化失败: {e}")
            raise

    # ==================== 命名空间管理 ====================

    def create_namespace(self, namespace: str, labels: dict[str, str] | None = None) -> dict:
        """创建命名空间

        Args:
            namespace: 命名空间名称
            labels: 标签

        Returns:
            dict: 创建的命名空间信息

        Raises:
            ApiException: K8S API异常
        """
        try:
            ns_body = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace, labels=labels or {})
            )
            result = self.core_v1.create_namespace(body=ns_body)
            logger.info(f"创建命名空间成功: {namespace}")
            return result.to_dict()
        except ApiException as e:
            if e.status == 409:  # 命名空间已存在
                logger.warning(f"命名空间已存在: {namespace}")
                return self.get_namespace(namespace)
            logger.error(f"创建命名空间失败: {namespace} - {e}")
            raise

    def get_namespace(self, namespace: str) -> dict | None:
        """获取命名空间信息

        Args:
            namespace: 命名空间名称

        Returns:
            dict: 命名空间信息,不存在返回None
        """
        try:
            result = self.core_v1.read_namespace(name=namespace)
            return result.to_dict()
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"获取命名空间失败: {namespace} - {e}")
            raise

    def delete_namespace(self, namespace: str) -> bool:
        """删除命名空间

        Args:
            namespace: 命名空间名称

        Returns:
            bool: 删除是否成功
        """
        try:
            self.core_v1.delete_namespace(name=namespace)
            logger.info(f"删除命名空间成功: {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"命名空间不存在: {namespace}")
                return False
            logger.error(f"删除命名空间失败: {namespace} - {e}")
            raise

    def list_namespaces(self, label_selector: str | None = None) -> list[dict]:
        """列出命名空间

        Args:
            label_selector: 标签选择器

        Returns:
            list: 命名空间列表
        """
        try:
            result = self.core_v1.list_namespace(label_selector=label_selector)
            return [item.to_dict() for item in result.items]
        except ApiException as e:
            logger.error(f"列出命名空间失败: {e}")
            raise

    # ==================== ConfigMap管理 ====================

    def create_configmap(
        self, namespace: str, name: str, data: dict[str, str], labels: dict[str, str] | None = None
    ) -> dict:
        """创建ConfigMap

        Args:
            namespace: 命名空间
            name: ConfigMap名称
            data: 配置数据
            labels: 标签

        Returns:
            dict: 创建的ConfigMap信息
        """
        try:
            cm_body = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=name, namespace=namespace, labels=labels or {}),
                data=data,
            )
            result = self.core_v1.create_namespaced_config_map(namespace=namespace, body=cm_body)
            logger.info(f"创建ConfigMap成功: {namespace}/{name}")
            return result.to_dict()
        except ApiException as e:
            logger.error(f"创建ConfigMap失败: {namespace}/{name} - {e}")
            raise

    def get_configmap(self, namespace: str, name: str) -> dict | None:
        """获取ConfigMap

        Args:
            namespace: 命名空间
            name: ConfigMap名称

        Returns:
            dict: ConfigMap信息,不存在返回None
        """
        try:
            result = self.core_v1.read_namespaced_config_map(name=name, namespace=namespace)
            return result.to_dict()
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"获取ConfigMap失败: {namespace}/{name} - {e}")
            raise

    def delete_configmap(self, namespace: str, name: str) -> bool:
        """删除ConfigMap

        Args:
            namespace: 命名空间
            name: ConfigMap名称

        Returns:
            bool: 删除是否成功
        """
        try:
            self.core_v1.delete_namespaced_config_map(name=name, namespace=namespace)
            logger.info(f"删除ConfigMap成功: {namespace}/{name}")
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            logger.error(f"删除ConfigMap失败: {namespace}/{name} - {e}")
            raise

    # ==================== Secret管理 ====================

    def create_secret(
        self,
        namespace: str,
        name: str,
        data: dict[str, str],
        secret_type: str = "Opaque",
        labels: dict[str, str] | None = None,
    ) -> dict:
        """创建Secret

        Args:
            namespace: 命名空间
            name: Secret名称
            data: 密钥数据(会自动进行base64编码)
            secret_type: Secret类型
            labels: 标签

        Returns:
            dict: 创建的Secret信息
        """
        try:
            # K8S Secret的data需要base64编码,使用string_data可以自动编码
            secret_body = client.V1Secret(
                metadata=client.V1ObjectMeta(name=name, namespace=namespace, labels=labels or {}),
                string_data=data,
                type=secret_type,
            )
            result = self.core_v1.create_namespaced_secret(namespace=namespace, body=secret_body)
            logger.info(f"创建Secret成功: {namespace}/{name}")
            return result.to_dict()
        except ApiException as e:
            logger.error(f"创建Secret失败: {namespace}/{name} - {e}")
            raise

    def get_secret(self, namespace: str, name: str) -> dict | None:
        """获取Secret

        Args:
            namespace: 命名空间
            name: Secret名称

        Returns:
            dict: Secret信息,不存在返回None
        """
        try:
            result = self.core_v1.read_namespaced_secret(name=name, namespace=namespace)
            return result.to_dict()
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"获取Secret失败: {namespace}/{name} - {e}")
            raise

    def delete_secret(self, namespace: str, name: str) -> bool:
        """删除Secret

        Args:
            namespace: 命名空间
            name: Secret名称

        Returns:
            bool: 删除是否成功
        """
        try:
            self.core_v1.delete_namespaced_secret(name=name, namespace=namespace)
            logger.info(f"删除Secret成功: {namespace}/{name}")
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            logger.error(f"删除Secret失败: {namespace}/{name} - {e}")
            raise


# 全局单例
_k8s_client: KubernetesClient | None = None


def get_k8s_client() -> KubernetesClient:
    """获取K8S客户端单例

    Returns:
        KubernetesClient: K8S客户端实例
    """
    global _k8s_client
    if _k8s_client is None:
        _k8s_client = KubernetesClient()
    return _k8s_client


__all__ = ["KubernetesClient", "get_k8s_client"]
