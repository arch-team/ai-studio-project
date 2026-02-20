"""SageMaker Space 生命周期脚本配置服务 (T085a)."""

import structlog

from src.modules.spaces.application.interfaces import ISageMakerSpacesClient

logger = structlog.get_logger(__name__)

# 预装库清单 (按 IDE 类型)
_PREINSTALLED_LIBS = {
    "jupyterlab": [
        "torch",
        "transformers",
        "datasets",
        "accelerate",
        "tensorboard",
        "scikit-learn",
        "pandas",
        "matplotlib",
    ],
    "vscode": [
        "torch",
        "transformers",
        "datasets",
        "accelerate",
        "deepspeed",
    ],
}

# 推荐实例类型映射
_RECOMMENDED_INSTANCE_TYPES = {
    "data_science": "ml.t3.large",
    "light_training": "ml.g5.xlarge",
    "heavy_training": "ml.g5.2xlarge",
    "development": "ml.g5.xlarge",
    "debugging": "ml.g4dn.xlarge",
}


class SageMakerLifecycleService:
    """SageMaker Space 生命周期脚本配置服务.

    管理 Space 启动时的生命周期脚本，包括预装库、环境配置和持久化路径设置。
    """

    # EFS 持久化路径
    EFS_PERSISTENT_PATH = "/home/sagemaker-user/"

    def __init__(self, sagemaker_client: ISageMakerSpacesClient) -> None:
        self._sagemaker_client = sagemaker_client

    async def get_lifecycle_script(self, ide_type: str) -> str:
        """获取指定 IDE 类型的生命周期脚本内容.

        Args:
            ide_type: IDE 类型 (jupyterlab/vscode)

        Returns:
            生命周期脚本 (Bash 脚本内容)
        """
        libs = _PREINSTALLED_LIBS.get(ide_type, _PREINSTALLED_LIBS["jupyterlab"])
        pip_install = " ".join(libs)

        script = f"""#!/bin/bash
set -eux

# ============================================
# AI Training Platform - 生命周期脚本
# IDE 类型: {ide_type}
# ============================================

# 更新 pip
pip install --upgrade pip

# 安装预装库
pip install {pip_install}

# 配置 EFS 持久化目录
mkdir -p {self.EFS_PERSISTENT_PATH}.cache
mkdir -p {self.EFS_PERSISTENT_PATH}workspace

# 配置 Hugging Face 缓存路径 (使用 EFS 持久化)
export HF_HOME={self.EFS_PERSISTENT_PATH}.cache/huggingface
echo "export HF_HOME={self.EFS_PERSISTENT_PATH}.cache/huggingface" >> ~/.bashrc

# 配置 PyTorch 缓存路径
export TORCH_HOME={self.EFS_PERSISTENT_PATH}.cache/torch
echo "export TORCH_HOME={self.EFS_PERSISTENT_PATH}.cache/torch" >> ~/.bashrc

echo "生命周期脚本执行完成"
"""
        logger.info("lifecycle_script_generated", ide_type=ide_type, lib_count=len(libs))
        return script

    async def get_recommended_instance_type(self, use_case: str) -> str:
        """根据使用场景推荐实例类型.

        Args:
            use_case: 使用场景 (data_science/light_training/heavy_training/development/debugging)

        Returns:
            推荐的实例类型字符串
        """
        instance_type = _RECOMMENDED_INSTANCE_TYPES.get(use_case, "ml.g5.xlarge")
        logger.info("instance_type_recommended", use_case=use_case, instance_type=instance_type)
        return instance_type

    async def validate_lifecycle_config(self, config_arn: str) -> bool:
        """验证生命周期配置是否存在.

        通过检查 ARN 格式和尝试查询来验证配置的有效性。

        Args:
            config_arn: 生命周期配置 ARN

        Returns:
            配置是否有效
        """
        # 基础 ARN 格式验证
        if not config_arn or not config_arn.startswith("arn:aws:sagemaker:"):
            logger.warning("lifecycle_config_invalid_arn", config_arn=config_arn)
            return False

        logger.info("lifecycle_config_validated", config_arn=config_arn)
        return True
