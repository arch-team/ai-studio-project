---
paths:
  - "stacks/**/*.py"
  - "app.py"
---

# CDK Stack 设计规范

## Stack 结构模板

每个 Stack 必须遵循以下结构:

```python
"""
Stack 功能描述 (一句话)

职责:
- 职责1
- 职责2

依赖:
- NetworkStack (VPC)
- IamStack (IAM 角色)
"""
from __future__ import annotations

# 标准库
from typing import TYPE_CHECKING

# AWS CDK
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

# 项目内部
from config import EnvironmentConfig
from utils import apply_standard_tags

if TYPE_CHECKING:
    from aws_cdk import Environment


class ExampleStack(Stack):
    """Stack 类文档字符串"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,  # 依赖注入
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. 保存配置
        self._env_config = env_config

        # 2. 创建资源 (调用私有方法)
        self._create_security_groups(vpc)
        self._create_compute_resources()

        # 3. 应用标签
        apply_standard_tags(self, env_config)

    # ========== 私有方法: 资源创建 ==========

    def _create_security_groups(self, vpc: ec2.IVpc) -> None:
        """创建安全组"""
        self._security_group = ec2.SecurityGroup(
            self, "SecurityGroup",
            vpc=vpc,
            description="Example security group",
        )

    def _create_compute_resources(self) -> None:
        """创建计算资源"""
        pass

    # ========== 公开属性: 资源导出 ==========

    @property
    def security_group(self) -> ec2.ISecurityGroup:
        """导出安全组供其他 Stack 使用"""
        return self._security_group
```

---

## 私有方法命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `_create_*` | 创建资源 | `_create_vpc()`, `_create_bucket()` |
| `_configure_*` | 配置现有资源 | `_configure_logging()` |
| `_setup_*` | 设置关联 | `_setup_permissions()` |
| `_add_*` | 添加子资源 | `_add_vpc_endpoints()` |
| `_get_*` | 获取/计算值 | `_get_subnet_selection()` |

---

## 依赖注入模式

### 必须注入的资源

| 资源类型 | 注入方式 | 原因 |
|----------|----------|------|
| VPC | 构造函数参数 | 网络隔离边界 |
| IAM 角色 | 构造函数参数 | 权限边界 |
| KMS Key | 构造函数参数 | 加密策略 |
| Security Group | 构造函数参数 | 网络安全 |

### 注入示例

```python
class DatabaseStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,                    # 必须注入
        kms_key: kms.IKey | None = None,  # 可选注入
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 使用注入的 KMS Key 或创建新的
        self._kms_key = kms_key or kms.Key(
            self, "DatabaseKey",
            enable_key_rotation=True,
        )
```

---

## 条件资源创建

### 环境特定资源

```python
def _create_waf(self) -> None:
    """仅在生产环境创建 WAF"""
    if not self._env_config.protection.waf_enabled:
        return

    self._waf = wafv2.CfnWebACL(
        self, "WebAcl",
        ...
    )

def _create_nat_gateway(self) -> None:
    """根据环境配置 NAT 数量"""
    nat_count = self._env_config.vpc.nat_gateways
    # 使用 nat_count
```

### 功能开关模式

```python
# config/environments.py
@dataclass
class ProtectionConfig:
    waf_enabled: bool = False
    deletion_protection: bool = False

# Stack 中使用
if self._env_config.protection.deletion_protection:
    bucket.apply_removal_policy(RemovalPolicy.RETAIN)
```

---

## 跨 Stack 通信

### 正确模式: 属性传递

```python
# app.py
network_stack = NetworkStack(app, "Network", ...)
database_stack = DatabaseStack(
    app, "Database",
    vpc=network_stack.vpc,              # 直接传递
    subnet_group=network_stack.db_subnet_group,
)
```

### 错误模式: Fn.import_value

```python
# ❌ 禁止: 使用 CloudFormation 导出/导入
vpc_id = Fn.import_value("NetworkStack-VpcId")
vpc = ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpc_id)
```

---

## Stack 删除策略

### 数据资源保护

```python
def _create_database(self) -> None:
    self._cluster = rds.DatabaseCluster(
        self, "Database",
        ...
        removal_policy=(
            RemovalPolicy.RETAIN
            if self._env_config.protection.deletion_protection
            else RemovalPolicy.DESTROY
        ),
    )
```

### 环境特定策略

| 资源类型 | Dev | Staging | Prod |
|----------|-----|---------|------|
| 数据库 | DESTROY | RETAIN | RETAIN |
| S3 Bucket | DESTROY | RETAIN | RETAIN |
| KMS Key | DESTROY | RETAIN | RETAIN |
| EKS Cluster | DESTROY | SNAPSHOT | SNAPSHOT |
| FSx Volume | DESTROY | SNAPSHOT | SNAPSHOT |

---

## Stack 验证

### 合成时验证

```python
def __init__(self, ...):
    super().__init__(...)

    # 验证配置
    self._validate_config()

def _validate_config(self) -> None:
    """验证配置有效性"""
    if self._env_config.eks.node_count_max < self._env_config.eks.node_count_min:
        raise ValueError(
            f"max_nodes ({self._env_config.eks.node_count_max}) "
            f"must >= min_nodes ({self._env_config.eks.node_count_min})"
        )
```

### 使用 CDK Aspects 验证

```python
# aspects/validation.py
class RequiredTagsAspect(IAspect):
    """验证所有资源都有必需标签"""

    REQUIRED_TAGS = ["Environment", "Project", "Owner"]

    def visit(self, node: IConstruct) -> None:
        if Tags.of(node).tag_values():
            missing = set(self.REQUIRED_TAGS) - set(Tags.of(node).tag_values().keys())
            if missing:
                Annotations.of(node).add_error(f"Missing required tags: {missing}")
```
