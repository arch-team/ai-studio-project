"""SageMaker Studio 镜像配置服务 (T086)."""

from typing import Any

import aioboto3
import structlog

from src.modules.spaces.domain.exceptions import SpaceError
from src.shared.infrastructure import get_settings

logger = structlog.get_logger(__name__)

# 官方 SageMaker Studio 镜像定义
_OFFICIAL_IMAGES: list[dict[str, Any]] = [
    {
        "name": "Data Science 3.0",
        "framework": "data_science",
        "description": "通用数据科学环境，包含 NumPy、Pandas、Scikit-learn 等",
        "image_name": "sagemaker-data-science-310-v1",
        "python_version": "3.10",
        "supported_ide": ["jupyterlab", "vscode"],
    },
    {
        "name": "PyTorch 2.0 GPU",
        "framework": "pytorch",
        "description": "PyTorch 2.0 GPU 训练环境，支持 DDP 和 FSDP",
        "image_name": "pytorch-2.0-gpu-py310",
        "python_version": "3.10",
        "supported_ide": ["jupyterlab", "vscode"],
    },
    {
        "name": "PyTorch 2.1 GPU",
        "framework": "pytorch",
        "description": "PyTorch 2.1 最新 GPU 训练环境",
        "image_name": "pytorch-2.1-gpu-py311",
        "python_version": "3.11",
        "supported_ide": ["jupyterlab", "vscode"],
    },
    {
        "name": "TensorFlow 2.13 GPU",
        "framework": "tensorflow",
        "description": "TensorFlow 2.13 GPU 训练环境",
        "image_name": "tensorflow-2.13-gpu-py310",
        "python_version": "3.10",
        "supported_ide": ["jupyterlab", "vscode"],
    },
    {
        "name": "TensorFlow 2.14 GPU",
        "framework": "tensorflow",
        "description": "TensorFlow 2.14 最新 GPU 训练环境",
        "image_name": "tensorflow-2.14-gpu-py311",
        "python_version": "3.11",
        "supported_ide": ["jupyterlab", "vscode"],
    },
]

# 框架 → 默认镜像映射
_DEFAULT_IMAGE_MAP: dict[str, str] = {
    "data_science": "sagemaker-data-science-310-v1",
    "pytorch": "pytorch-2.1-gpu-py311",
    "tensorflow": "tensorflow-2.14-gpu-py311",
}


class SageMakerImageService:
    """SageMaker Studio 镜像配置服务.

    管理 SageMaker Studio 可用镜像列表，支持官方镜像查询和自定义镜像验证。
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._region = settings.aws_region
        self._session = aioboto3.Session()

    def get_available_images(self) -> list[dict[str, Any]]:
        """获取可用的 SageMaker Studio 镜像列表.

        Returns:
            官方镜像信息列表
        """
        return list(_OFFICIAL_IMAGES)

    def get_default_image(self, framework: str) -> dict[str, Any]:
        """根据框架获取默认镜像.

        Args:
            framework: 框架名称 (data_science/pytorch/tensorflow)

        Returns:
            默认镜像信息

        Raises:
            SpaceError: 不支持的框架
        """
        image_name = _DEFAULT_IMAGE_MAP.get(framework)
        if not image_name:
            raise SpaceError(message=f"不支持的框架: {framework}，可选: {list(_DEFAULT_IMAGE_MAP.keys())}")

        for image in _OFFICIAL_IMAGES:
            if image["image_name"] == image_name:
                return dict(image)

        raise SpaceError(message=f"默认镜像配置错误: {image_name}")

    async def validate_custom_image(self, image_uri: str) -> bool:
        """验证自定义镜像是否可用.

        通过调用 SageMaker DescribeImage API 检查镜像是否存在且可用。

        Args:
            image_uri: 自定义镜像 URI (ECR 地址)

        Returns:
            镜像是否可用
        """
        if not image_uri:
            return False

        # 基础 ECR URI 格式验证
        if ".dkr.ecr." not in image_uri and ".amazonaws.com" not in image_uri:
            logger.warning("custom_image_invalid_uri", image_uri=image_uri)
            return False

        try:
            async with self._session.client("sagemaker", region_name=self._region) as sm:
                # 从 URI 提取镜像名称 (ECR 格式: account.dkr.ecr.region.amazonaws.com/repo:tag)
                image_name = image_uri.split("/")[-1].split(":")[0] if "/" in image_uri else image_uri

                await sm.describe_image(ImageName=image_name)
                logger.info("custom_image_validated", image_uri=image_uri)
                return True

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFound":
                logger.info("custom_image_not_found", image_uri=image_uri)
                return False
            logger.error("custom_image_validation_failed", image_uri=image_uri, error=str(e))
            return False
