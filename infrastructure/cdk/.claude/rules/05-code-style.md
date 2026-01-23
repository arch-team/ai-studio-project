# CDK 代码风格规范

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 类 | PascalCase | `NetworkStack`, `GpuNodeGroupConstruct` |
| 方法 | snake_case | `create_vpc()`, `apply_tags()` |
| 私有方法 | _snake_case | `_create_vpc()` |
| 变量 | snake_case | `vpc_cidr`, `node_count` |
| 私有变量 | _snake_case | `_vpc`, `_cluster` |
| 常量 | UPPER_SNAKE | `MAX_NODES` |
| Stack/Construct ID | PascalCase | `"NetworkStack"`, `"MainVpc"` |
| 资源名称 | kebab-case | `"ai-platform-dev-vpc"` |
| 工厂方法 | for_* / create_* | `for_dev()`, `create_default_config()` |

---

## 导入顺序

```python
"""模块文档"""
from __future__ import annotations

# 1. 标准库
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

# 2. 第三方库
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2, aws_eks as eks
from constructs import Construct

# 3. 项目内部
from config import EnvironmentConfig
from utils import apply_standard_tags

# 4. 类型检查专用
if TYPE_CHECKING:
    from aws_cdk import Environment
```

**规则**:
- `aws_cdk as cdk`, `aws_ec2 as ec2` 标准别名
- 多个导入用括号分组
- TYPE_CHECKING 放最后

---

## 类型注解

```python
# ✅ 所有公开方法必须有类型注解
def create_bucket(self, name: str, *, versioned: bool = True) -> s3.Bucket:
    ...

# ✅ 属性必须有返回类型
@property
def vpc(self) -> ec2.IVpc:
    return self._vpc

# ✅ 使用 | 而非 Union
def get_key(self, key: kms.IKey | None = None) -> kms.IKey:
    ...

# ✅ 使用 list/dict 而非 List/Dict
def get_subnets(self) -> list[ec2.ISubnet]:
    ...
```

---

## 禁止模式

```python
# ❌ 硬编码值
vpc = ec2.Vpc(self, "Vpc", cidr="10.0.0.0/16")
# ✅ 从配置获取
vpc = ec2.Vpc(self, "Vpc", cidr=env_config.vpc.cidr)

# ❌ Any 类型
def create_resource(self, config: Any) -> Any:
# ✅ 具体类型
def create_resource(self, config: BucketConfig) -> s3.Bucket:

# ❌ 裸 except
try: ...
except: pass
# ✅ 具体异常
except ValueError as e:

# ❌ 字符串拼接 ARN
arn = f"arn:aws:s3:::{bucket_name}"
# ✅ CDK 方法
arn = self.format_arn(service="s3", resource=bucket_name)

# ❌ 全局变量
GLOBAL_CONFIG = {}
# ✅ 依赖注入
def __init__(self, ..., config: EnvironmentConfig):
```

---

## Stack 结构

```python
class ExampleStack(Stack):
    def __init__(self, ..., env_config: EnvironmentConfig) -> None:
        super().__init__(...)
        self._env_config = env_config

        # 按依赖顺序创建
        self._create_security_groups()
        self._create_compute_resources()

        apply_standard_tags(self, env_config)

    # ========== 私有方法 ==========

    def _create_security_groups(self) -> None:
        ...

    # ========== 公开属性 ==========

    @property
    def vpc(self) -> ec2.IVpc:
        return self._vpc
```

---

## 工具配置

```bash
ruff check .    # Lint
ruff format .   # Format
mypy .          # 类型检查 (strict=true)
```

配置见 `pyproject.toml`
