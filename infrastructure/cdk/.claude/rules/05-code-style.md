---
paths:
  - "**/*.py"
---

# 代码风格规范

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 类 | PascalCase | `NetworkStack` |
| 方法/变量 | snake_case | `create_vpc` |
| 私有 | _snake_case | `_create_vpc`, `_vpc` |
| 常量 | UPPER_SNAKE | `MAX_NODES` |
| Construct ID | PascalCase | `"MainVpc"` |
| 资源名称 | kebab-case | `"ai-platform-dev-vpc"` |

## 导入顺序

```python
from __future__ import annotations
# 1. 标准库
from typing import TYPE_CHECKING
# 2. 第三方
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
# 3. 项目内部
from config import EnvironmentConfig
# 4. 类型检查
if TYPE_CHECKING:
    from aws_cdk import Environment
```

## 类型注解

```python
# ✅ 必须: 公开方法、属性
def create_bucket(self, name: str) -> s3.Bucket: ...

@property
def vpc(self) -> ec2.IVpc: ...

# ✅ 使用现代语法
def get_key(self, key: kms.IKey | None = None) -> kms.IKey: ...
def get_subnets(self) -> list[ec2.ISubnet]: ...
```

## 禁止模式

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| 硬编码 `cidr="10.0.0.0/16"` | `env_config.vpc.cidr` |
| `Any` 类型 | 具体类型 |
| 裸 `except:` | `except ValueError:` |
| 字符串拼接 ARN | `self.format_arn()` |
| 全局变量 | 依赖注入 |

## 工具

```bash
ruff check . && ruff format .   # Lint + Format
mypy .                          # 类型检查 (strict)
```
