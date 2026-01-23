---
paths:
  - "config/**/*.py"
  - "cdk.json"
---

# 配置管理规范

## 架构

```
config/
├── constants.py      # 常量 (不变值)
└── environments.py   # 环境配置 (可变值)
```

## 常量定义 (constants.py)

```python
@dataclass(frozen=True)
class KubernetesNamespaces:
    KUBE_SYSTEM: Final[str] = "kube-system"
    TRAINING: Final[str] = "training"

K8S_NAMESPACES = KubernetesNamespaces()  # 全局单例
```

## 环境配置 (environments.py)

```python
@dataclass(frozen=True)
class VpcConfig:
    cidr: str = "10.0.0.0/16"
    nat_gateways: int = 1

@dataclass(frozen=True)
class EnvironmentConfig:
    environment_name: str
    account: str
    region: str
    vpc: VpcConfig = field(default_factory=VpcConfig)

    @classmethod
    def for_dev(cls, account: str, region: str) -> EnvironmentConfig:
        return cls(environment_name="dev", account=account, region=region,
                   vpc=VpcConfig(nat_gateways=1))

    @classmethod
    def for_prod(cls, account: str, region: str) -> EnvironmentConfig:
        return cls(environment_name="prod", account=account, region=region,
                   vpc=VpcConfig(nat_gateways=2))
```

## 配置获取

```python
# app.py
env_name = app.node.try_get_context("env") or "dev"
config = {"dev": EnvironmentConfig.for_dev, "prod": EnvironmentConfig.for_prod}[env_name](account, region)
```

```bash
cdk deploy --context env=dev
```

## 环境差异速查

| 配置 | Dev | Staging | Prod |
|------|-----|---------|------|
| NAT | 1 | 2 | 2 |
| 多 AZ | ❌ | ✅ | ✅ |
| WAF | ❌ | ❌ | ✅ |
| 删除保护 | ❌ | ✅ | ✅ |
| CDK Nag | 跳过 | 启用 | 启用 |
