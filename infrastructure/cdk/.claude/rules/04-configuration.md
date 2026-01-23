---
paths:
  - "config/**/*.py"
  - "cdk.json"
---

# CDK 配置管理规范

## 配置架构

```
config/
├── constants.py      # 常量定义 (不变值)
└── environments.py   # 环境配置 (可变值)
```

---

## 常量管理 (constants.py)

### 设计原则

1. **集中化**: 所有魔法字符串必须定义为常量
2. **分类组织**: 按领域分组 (EKS, K8s, SageMaker)
3. **类型安全**: 使用 dataclass 或 class 封装
4. **单例访问**: 提供全局实例便于访问

### 常量类模板

```python
"""CDK 项目常量定义"""
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class EksAddonNames:
    """EKS Add-on 名称常量"""

    TRAINING_OPERATOR: Final[str] = "training-operator"
    KUEUE: Final[str] = "kueue"
    PROMETHEUS: Final[str] = "prometheus"
    GRAFANA: Final[str] = "grafana"


@dataclass(frozen=True)
class KubernetesNamespaces:
    """Kubernetes 命名空间常量"""

    KUBE_SYSTEM: Final[str] = "kube-system"
    TRAINING: Final[str] = "training"
    MONITORING: Final[str] = "monitoring"


@dataclass(frozen=True)
class HelmChartConfig:
    """Helm Chart 配置常量"""

    HYPERPOD_CHART_PATH: Final[str] = "resources/helm_charts/HyperPodHelmChart"
    HYPERPOD_CHART_VERSION: Final[str] = "1.0.0"
    TRAINING_OPERATOR_REPO: Final[str] = "https://kubeflow.github.io/training-operator"
    TRAINING_OPERATOR_VERSION: Final[str] = "1.8.0"


@dataclass(frozen=True)
class Timeouts:
    """超时配置常量"""

    HELM_INSTALL_MINUTES: Final[int] = 15
    ADDON_INSTALL_MINUTES: Final[int] = 10
    DATABASE_CREATION_MINUTES: Final[int] = 30


# ========== 全局单例 ==========

EKS_ADDON_NAMES = EksAddonNames()
K8S_NAMESPACES = KubernetesNamespaces()
HELM_CONFIG = HelmChartConfig()
TIMEOUTS = Timeouts()
```

### 使用示例

```python
from config.constants import EKS_ADDON_NAMES, K8S_NAMESPACES

namespace = K8S_NAMESPACES.TRAINING
addon_name = EKS_ADDON_NAMES.TRAINING_OPERATOR
```

---

## 环境配置 (environments.py)

### 配置层次结构

```python
EnvironmentConfig (根配置)
├── VpcConfig           # VPC 配置
├── DatabaseConfig      # 数据库配置
├── StorageConfig       # 存储配置
├── EksConfig          # EKS 配置
│   └── EksAddonVersions   # Add-on 版本
├── HyperPodConfig     # HyperPod 配置
└── ProtectionConfig   # 保护配置
```

### 配置类模板

```python
"""环境配置定义"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final


class DeploymentMode(Enum):
    """部署模式"""
    SINGLE_AZ = "single_az"
    MULTI_AZ = "multi_az"


@dataclass(frozen=True)
class VpcConfig:
    """VPC 配置"""

    cidr: str = "10.0.0.0/16"
    max_azs: int = 3
    nat_gateways: int = 1
    deployment_mode: DeploymentMode = DeploymentMode.SINGLE_AZ

    # 子网 CIDR 掩码
    public_subnet_mask: int = 20
    private_app_subnet_mask: int = 19
    private_data_subnet_mask: int = 20


@dataclass(frozen=True)
class DatabaseConfig:
    """Aurora 数据库配置"""

    min_acu: float = 0.5
    max_acu: float = 8
    backup_retention_days: int = 7
    multi_az: bool = False


@dataclass(frozen=True)
class EksAddonVersions:
    """EKS Add-on 版本配置"""

    vpc_cni: str = "v1.18.5-eksbuild.1"
    coredns: str = "v1.11.3-eksbuild.1"
    kube_proxy: str = "v1.30.6-eksbuild.1"
    ebs_csi: str = "v1.36.0-eksbuild.1"

    @classmethod
    def for_k8s_1_32(cls) -> EksAddonVersions:
        """K8s 1.32 兼容版本"""
        return cls(
            vpc_cni="v1.19.0-eksbuild.1",
            coredns="v1.11.4-eksbuild.1",
            kube_proxy="v1.32.0-eksbuild.1",
            ebs_csi="v1.37.0-eksbuild.1",
        )

    @classmethod
    def for_k8s_1_33(cls) -> EksAddonVersions:
        """K8s 1.33 兼容版本"""
        return cls(
            vpc_cni="v1.19.2-eksbuild.1",
            coredns="v1.12.0-eksbuild.1",
            kube_proxy="v1.33.0-eksbuild.1",
            ebs_csi="v1.38.0-eksbuild.1",
        )


@dataclass(frozen=True)
class ProtectionConfig:
    """资源保护配置"""

    deletion_protection: bool = False
    waf_enabled: bool = False
    skip_cdk_nag: bool = True
```

### 根配置类

```python
@dataclass(frozen=True)
class EnvironmentConfig:
    """环境根配置"""

    environment_name: str
    project_name: str
    account: str
    region: str

    vpc: VpcConfig = field(default_factory=VpcConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    eks: EksConfig = field(default_factory=EksConfig)
    protection: ProtectionConfig = field(default_factory=ProtectionConfig)

    # ========== 工厂方法 ==========

    @classmethod
    def for_dev(cls, account: str, region: str) -> EnvironmentConfig:
        """开发环境配置"""
        return cls(
            environment_name="dev",
            project_name="ai-platform",
            account=account,
            region=region,
            vpc=VpcConfig(
                nat_gateways=1,
                deployment_mode=DeploymentMode.SINGLE_AZ,
            ),
            database=DatabaseConfig(
                min_acu=0.5,  # 可暂停
                max_acu=8,
            ),
            protection=ProtectionConfig(
                deletion_protection=False,
                skip_cdk_nag=True,
            ),
        )

    @classmethod
    def for_staging(cls, account: str, region: str) -> EnvironmentConfig:
        """预发布环境配置"""
        return cls(
            environment_name="staging",
            project_name="ai-platform",
            account=account,
            region=region,
            vpc=VpcConfig(
                nat_gateways=2,
                deployment_mode=DeploymentMode.MULTI_AZ,
            ),
            database=DatabaseConfig(
                min_acu=1,
                max_acu=16,
                multi_az=True,
            ),
            protection=ProtectionConfig(
                deletion_protection=True,
                skip_cdk_nag=False,
            ),
        )

    @classmethod
    def for_prod(cls, account: str, region: str) -> EnvironmentConfig:
        """生产环境配置"""
        return cls(
            environment_name="prod",
            project_name="ai-platform",
            account=account,
            region=region,
            vpc=VpcConfig(
                nat_gateways=2,
                deployment_mode=DeploymentMode.MULTI_AZ,
            ),
            database=DatabaseConfig(
                min_acu=2,
                max_acu=16,
                backup_retention_days=14,
                multi_az=True,
            ),
            protection=ProtectionConfig(
                deletion_protection=True,
                waf_enabled=True,
                skip_cdk_nag=False,
            ),
        )
```

---

## 配置获取

### 从 CDK Context 获取

```python
# app.py
def get_environment_config(app: cdk.App) -> EnvironmentConfig:
    """从 CDK context 获取环境配置"""

    env_name = app.node.try_get_context("env") or "dev"
    account = app.node.try_get_context("account") or os.environ.get("CDK_DEFAULT_ACCOUNT")
    region = app.node.try_get_context("region") or os.environ.get("CDK_DEFAULT_REGION")

    if not account or not region:
        raise ValueError("Account and region must be specified")

    factory_map = {
        "dev": EnvironmentConfig.for_dev,
        "staging": EnvironmentConfig.for_staging,
        "prod": EnvironmentConfig.for_prod,
    }

    factory = factory_map.get(env_name)
    if not factory:
        raise ValueError(f"Unknown environment: {env_name}")

    return factory(account, region)
```

### 命令行使用

```bash
# 指定环境
cdk deploy --context env=dev

# 覆盖 Account/Region
cdk deploy --context env=prod --context account=123456789012 --context region=us-west-2
```

---

## 配置验证

### dataclass 后处理验证

```python
@dataclass(frozen=True)
class EksConfig:
    node_count_min: int = 1
    node_count_max: int = 10

    def __post_init__(self) -> None:
        if self.node_count_max < self.node_count_min:
            raise ValueError(
                f"node_count_max ({self.node_count_max}) "
                f"must be >= node_count_min ({self.node_count_min})"
            )
```

### 运行时验证

```python
def validate_environment_config(config: EnvironmentConfig) -> None:
    """验证环境配置完整性"""

    errors = []

    if config.environment_name not in ("dev", "staging", "prod"):
        errors.append(f"Invalid environment: {config.environment_name}")

    if config.database.min_acu > config.database.max_acu:
        errors.append("Database min_acu > max_acu")

    if errors:
        raise ValueError(f"Configuration errors: {errors}")
```

---

## 环境配置对比表

| 配置项 | Dev | Staging | Prod |
|--------|-----|---------|------|
| **VPC** ||||
| NAT Gateways | 1 | 2 | 2 |
| 部署模式 | SINGLE_AZ | MULTI_AZ | MULTI_AZ |
| **Database** ||||
| ACU 范围 | 0.5-8 | 1-16 | 2-16 |
| 备份保留 | 7 天 | 7 天 | 14 天 |
| 多 AZ | ❌ | ✅ | ✅ |
| **EKS** ||||
| 节点范围 | 1-10 | 2-50 | 2-100 |
| GPU 实例数 | 1 | 2 | 4 |
| **Protection** ||||
| 删除保护 | ❌ | ✅ | ✅ |
| WAF | ❌ | ❌ | ✅ |
| CDK Nag | 跳过 | 启用 | 启用 |
