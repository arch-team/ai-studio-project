"""Application Stack — 后端应用部署 (ECR 镜像仓库)。"""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr

from config import EnvironmentConfig
from constructs import Construct
from utils.outputs import create_output


class ApplicationStack(cdk.Stack):
    """Application Stack — ECR 镜像仓库 + 生命周期策略。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: EnvironmentConfig,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self._backend_repository = self._create_backend_repository()
        self._create_outputs()

    def _create_backend_repository(self) -> ecr.Repository:
        """创建后端 Docker 镜像仓库 (不可变标签, push 时扫描, 自动清理)。"""
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
        """创建 CloudFormation 输出。"""
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
