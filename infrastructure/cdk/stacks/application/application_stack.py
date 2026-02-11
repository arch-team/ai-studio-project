"""
Application Stack for AI Training Platform.

This stack creates application deployment resources:
- ECR Repository for backend Docker images
- Image lifecycle policy for cost optimization
"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr

from config import EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output


class ApplicationStack(cdk.Stack):
    """后端应用部署 Stack.

    创建:
    - ECR Repository (后端 Docker 镜像仓库)
    - 镜像生命周期策略 (自动清理旧镜像)

    Attributes:
        backend_repository: ECR Repository for backend images
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config

        # Create ECR Repository
        self._backend_repository = self._create_backend_repository()

        # Create outputs
        self._create_outputs()

    def _create_backend_repository(self) -> ecr.Repository:
        """创建后端 Docker 镜像仓库.

        配置:
        - 镜像标签不可变 (防止覆盖)
        - 扫描 push 时自动执行
        - 生命周期规则: 保留最近 30 个镜像
        """
        repository = ecr.Repository(
            self,
            "BackendRepository",
            repository_name=f"{self.env_config.resource_prefix}-backend",
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            image_scan_on_push=True,
            removal_policy=self.env_config.protection.removal_policy,
            empty_on_delete=(
                self.env_config.protection.removal_policy == cdk.RemovalPolicy.DESTROY
            ),
            encryption=ecr.RepositoryEncryption.AES_256,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="删除 90 天前的未标记镜像",
                    max_image_age=cdk.Duration.days(90),
                    tag_status=ecr.TagStatus.UNTAGGED,
                    rule_priority=1,
                ),
                ecr.LifecycleRule(
                    description="保留最近 30 个镜像",
                    max_image_count=30,
                    tag_status=ecr.TagStatus.ANY,
                    rule_priority=10,
                ),
            ],
        )

        cdk.Tags.of(repository).add(
            "Name", f"{self.env_config.resource_prefix}-backend"
        )

        return repository

    def _create_outputs(self) -> None:
        """创建 CloudFormation 输出."""
        create_output(
            self,
            "BackendRepositoryUri",
            self._backend_repository.repository_uri,
            "ECR repository URI for backend Docker images",
        )
        create_output(
            self,
            "BackendRepositoryArn",
            self._backend_repository.repository_arn,
            "ECR repository ARN for backend Docker images",
        )

    @property
    def backend_repository(self) -> ecr.Repository:
        return self._backend_repository
