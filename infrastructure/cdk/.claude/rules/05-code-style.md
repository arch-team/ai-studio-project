# CDK 代码风格规范

## 工具配置

本项目使用以下工具确保代码质量:

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| ruff | Linting + Formatting | pyproject.toml |
| mypy | 类型检查 | pyproject.toml |
| pytest | 测试 | pyproject.toml |

---

## pyproject.toml 配置

```toml
[project]
requires-python = ">=3.11"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = [
    "E501",   # 行长度 (由 formatter 处理)
]

[tool.ruff.lint.isort]
known-first-party = ["config", "stacks", "cdk_constructs", "utils", "aspects"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[tool.mypy]
python_version = "3.11"
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
warn_redundant_casts = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
addopts = "-v --tb=short"
```

---

## 导入顺序

### 标准格式

```python
"""模块文档字符串"""
from __future__ import annotations  # 总是第一行 (如果需要)

# 1. 标准库
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

# 2. 第三方库
import aws_cdk as cdk
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
)
from constructs import Construct

# 3. 项目内部模块
from config import EnvironmentConfig
from config.constants import EKS_ADDON_NAMES
from utils import apply_standard_tags

# 4. 类型检查专用导入
if TYPE_CHECKING:
    from aws_cdk import Environment
```

### 导入规则

1. **aws_cdk 别名**: 使用 `aws_cdk as cdk`
2. **服务别名**: 使用标准别名 `aws_ec2 as ec2`
3. **多个导入**: 使用括号分组，每行一个
4. **TYPE_CHECKING**: 仅类型注解用的导入放在此块中

---

## 命名规范

### 变量和参数

| 类型 | 格式 | 示例 |
|------|------|------|
| 变量 | snake_case | `vpc_cidr`, `node_count` |
| 私有变量 | _snake_case | `_vpc`, `_cluster` |
| 常量 | UPPER_SNAKE | `MAX_NODES`, `DEFAULT_CIDR` |
| 类型变量 | PascalCase | `T`, `ConfigT` |

### 类和方法

| 类型 | 格式 | 示例 |
|------|------|------|
| 类 | PascalCase | `NetworkStack`, `GpuNodeGroupConstruct` |
| 方法 | snake_case | `create_vpc()`, `apply_tags()` |
| 私有方法 | _snake_case | `_create_vpc()`, `_setup_logging()` |
| 工厂方法 | for_* / create_* | `for_dev()`, `create_default_config()` |

### CDK 特定命名

| 类型 | 格式 | 示例 |
|------|------|------|
| Stack ID | PascalCase | `"NetworkStack"`, `"EksStack"` |
| Construct ID | PascalCase | `"MainVpc"`, `"TrainingBucket"` |
| 资源名称 | kebab-case | `"ai-platform-dev-vpc"` |
| 标签键 | PascalCase | `"Environment"`, `"Project"` |

---

## 类型注解

### 必须注解

```python
# ✅ 所有公开方法必须有完整类型注解
def create_bucket(
    self,
    bucket_name: str,
    *,
    versioned: bool = True,
    encryption: s3.BucketEncryption | None = None,
) -> s3.Bucket:
    ...

# ✅ 属性必须有返回类型
@property
def vpc(self) -> ec2.IVpc:
    return self._vpc
```

### 类型注解最佳实践

```python
# 使用 | 而非 Union (Python 3.10+)
def get_key(self, key: kms.IKey | None = None) -> kms.IKey:
    ...

# 使用 list/dict 而非 List/Dict (Python 3.9+)
def get_subnets(self) -> list[ec2.ISubnet]:
    ...

# 使用 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import EnvironmentConfig

class MyStack(Stack):
    def __init__(self, ..., env_config: EnvironmentConfig) -> None:
        ...
```

---

## 文档字符串

### 模块文档

```python
"""
Network Stack 实现

创建 VPC 及相关网络资源:
- 3 层子网架构 (Public, PrivateApp, PrivateData)
- VPC Endpoints
- NAT Gateway

依赖: 无
被依赖: DatabaseStack, EksStack
"""
```

### 类文档

```python
class NetworkStack(Stack):
    """
    网络基础设施 Stack

    创建 VPC 和所有网络相关资源。

    Attributes:
        vpc: 主 VPC 实例
        private_subnets: 私有应用子网
        isolated_subnets: 隔离数据子网

    Example:
        >>> network = NetworkStack(app, "Network", env_config=config)
        >>> eks = EksStack(app, "EKS", vpc=network.vpc)
    """
```

### 方法文档

```python
def _create_vpc_endpoints(self) -> None:
    """
    创建 VPC Endpoints

    为以下服务创建 Gateway/Interface Endpoints:
    - S3 (Gateway)
    - ECR (Interface)
    - CloudWatch Logs (Interface)

    Note:
        Interface Endpoints 会产生额外费用
    """
```

---

## 代码组织

### Stack 内部结构

```python
class ExampleStack(Stack):
    """Stack 文档"""

    # 1. 构造函数
    def __init__(self, ...) -> None:
        super().__init__(...)

        # 配置保存
        self._env_config = env_config

        # 资源创建 (按依赖顺序调用)
        self._create_security_groups()
        self._create_compute_resources()

        # 标签应用
        apply_standard_tags(self, env_config)

    # 2. 私有方法 (按调用顺序排列)
    def _create_security_groups(self) -> None:
        """创建安全组"""
        ...

    def _create_compute_resources(self) -> None:
        """创建计算资源"""
        ...

    # 3. 公开属性 (按重要性排列)
    @property
    def vpc(self) -> ec2.IVpc:
        """主 VPC"""
        return self._vpc

    @property
    def security_group(self) -> ec2.ISecurityGroup:
        """安全组"""
        return self._security_group
```

### 私有方法分组

使用注释分隔不同功能区域:

```python
# ========== 网络资源 ==========

def _create_vpc(self) -> None:
    ...

def _create_subnets(self) -> None:
    ...

# ========== 安全资源 ==========

def _create_security_groups(self) -> None:
    ...

def _create_nacls(self) -> None:
    ...

# ========== 公开属性 ==========

@property
def vpc(self) -> ec2.IVpc:
    ...
```

---

## 错误处理

### 配置验证

```python
def __init__(self, ..., env_config: EnvironmentConfig) -> None:
    super().__init__(...)

    # 前置验证
    if not env_config.vpc.cidr:
        raise ValueError("VPC CIDR is required")

    if env_config.eks.node_count_max < env_config.eks.node_count_min:
        raise ValueError("node_count_max must be >= node_count_min")
```

### 资源查找

```python
def _get_ami(self) -> ec2.IMachineImage:
    """获取 AMI"""
    try:
        return ec2.MachineImage.lookup(
            name="amzn2-ami-hvm-*",
            owners=["amazon"],
        )
    except Exception as e:
        raise RuntimeError(f"Failed to lookup AMI: {e}") from e
```

---

## 常见模式

### 条件资源创建

```python
def _create_waf(self) -> None:
    """仅在启用时创建 WAF"""
    if not self._env_config.protection.waf_enabled:
        return

    self._waf = wafv2.CfnWebACL(...)
```

### 环境特定配置

```python
removal_policy = (
    RemovalPolicy.RETAIN
    if self._env_config.protection.deletion_protection
    else RemovalPolicy.DESTROY
)
```

### 资源命名

```python
def _get_resource_name(self, suffix: str) -> str:
    """生成标准资源名称"""
    return f"{self._env_config.project_name}-{self._env_config.environment_name}-{suffix}"

# 使用
bucket_name = self._get_resource_name("training-data")
# → "ai-platform-dev-training-data"
```

---

## 禁止模式

### 不要使用

```python
# ❌ 硬编码值
vpc = ec2.Vpc(self, "Vpc", cidr="10.0.0.0/16")  # 应从配置获取

# ❌ 使用 any 类型
def create_resource(self, config: Any) -> Any:  # 应使用具体类型

# ❌ 裸 except
try:
    ...
except:  # 应捕获具体异常
    pass

# ❌ 全局变量
GLOBAL_CONFIG = {}  # 应使用依赖注入

# ❌ 字符串拼接构建 ARN
arn = f"arn:aws:s3:::{bucket_name}"  # 应使用 Stack.format_arn()
```

### 应该使用

```python
# ✅ 从配置获取
vpc = ec2.Vpc(self, "Vpc", cidr=env_config.vpc.cidr)

# ✅ 具体类型
def create_resource(self, config: BucketConfig) -> s3.Bucket:

# ✅ 具体异常
try:
    ...
except ValueError as e:
    logger.error(f"Invalid config: {e}")

# ✅ 依赖注入
class MyStack(Stack):
    def __init__(self, ..., config: EnvironmentConfig) -> None:

# ✅ 使用 CDK 方法构建 ARN
arn = self.format_arn(service="s3", resource=bucket_name)
```
