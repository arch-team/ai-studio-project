"""S3 生命周期规则构建器。"""

from aws_cdk import Duration
from aws_cdk import aws_s3 as s3


class LifecycleRuleBuilder:
    """S3 生命周期规则构建器。

    提供常用生命周期规则的快速创建方法，避免重复代码。

    Example:
        ```python
        builder = LifecycleRuleBuilder()

        rules = [
            builder.incomplete_multipart_rule(days=7),
            builder.old_versions_rule(days=90),
            builder.transition_rule(
                "TransitionToIA",
                [(s3.StorageClass.INFREQUENT_ACCESS, 90)]
            ),
        ]
        ```
    """

    @staticmethod
    def incomplete_multipart_rule(days: int = 7) -> s3.LifecycleRule:
        """创建未完成分片上传清理规则。

        Args:
            days: 清理天数，默认 7 天

        Returns:
            配置好的生命周期规则
        """
        return s3.LifecycleRule(
            id="AbortIncompleteMultipartUpload",
            enabled=True,
            abort_incomplete_multipart_upload_after=Duration.days(days),
        )

    @staticmethod
    def old_versions_rule(days: int) -> s3.LifecycleRule:
        """创建旧版本过期规则。

        Args:
            days: 保留天数

        Returns:
            配置好的生命周期规则
        """
        return s3.LifecycleRule(
            id="ExpireOldVersions",
            enabled=True,
            noncurrent_version_expiration=Duration.days(days),
        )

    @staticmethod
    def transition_rule(
        rule_id: str,
        transitions: list[tuple[s3.StorageClass, int]],
    ) -> s3.LifecycleRule:
        """创建存储类型转换规则。

        Args:
            rule_id: 规则 ID
            transitions: 转换配置列表，每项为 (存储类, 天数)

        Returns:
            配置好的生命周期规则

        Example:
            ```python
            builder.transition_rule(
                "TransitionToIA",
                [
                    (s3.StorageClass.INFREQUENT_ACCESS, 90),
                    (s3.StorageClass.GLACIER, 365),
                ]
            )
            ```
        """
        return s3.LifecycleRule(
            id=rule_id,
            enabled=True,
            transitions=[
                s3.Transition(
                    storage_class=storage_class,
                    transition_after=Duration.days(days),
                )
                for storage_class, days in transitions
            ],
        )

    @staticmethod
    def expiration_rule(
        rule_id: str,
        days: int,
        prefix: str | None = None,
    ) -> s3.LifecycleRule:
        """创建对象过期规则。

        Args:
            rule_id: 规则 ID
            days: 过期天数
            prefix: 可选的对象前缀过滤 (例如 "cold/")

        Returns:
            配置好的生命周期规则

        Example:
            ```python
            # 仅对 cold/ 前缀的对象应用 90 天过期规则
            builder.expiration_rule("ExpireColdCheckpoints", 90, prefix="cold/")
            ```

        T038b-2 说明:
            使用前缀过滤可以避免误删热/温检查点，仅对冷检查点应用自动删除规则。
            冷检查点由 CheckpointMigrationService (T038b-1) 迁移到 S3 时放置在 cold/ 目录下。
        """
        return s3.LifecycleRule(
            id=rule_id,
            enabled=True,
            expiration=Duration.days(days),
            prefix=prefix,
        )
