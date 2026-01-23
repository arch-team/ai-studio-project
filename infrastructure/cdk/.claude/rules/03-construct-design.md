---
paths:
  - "cdk_constructs/**/*.py"
  - "aspects/**/*.py"
---

# CDK Construct 设计规范

## Construct 分层

CDK 提供三层 Construct 抽象:

| 层级 | 说明 | 本项目位置 |
|------|------|------------|
| L1 | CloudFormation 资源直接映射 | 避免使用 |
| L2 | AWS CDK 提供的高级抽象 | 优先使用 |
| L3 | 自定义可复用模式 | `cdk_constructs/` |

---

## L3 Construct 设计原则

### 何时创建 L3 Construct

1. **重复模式**: 同一资源组合出现 2+ 次
2. **复杂配置**: 配置项 > 5 个且有内在关联
3. **最佳实践封装**: 需要强制执行安全/运维标准
4. **领域概念**: 业务领域有对应抽象

### L3 Construct 模板

```python
"""
GPU 节点组 Construct

封装 EKS GPU 节点组的最佳实践配置:
- Launch Template 配置
- GPU 优化 AMI
- NVMe/EFA 支持
- 自动标签和污点
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import aws_cdk as cdk
from aws_cdk import aws_eks as eks, aws_ec2 as ec2
from constructs import Construct

if TYPE_CHECKING:
    from config import EnvironmentConfig


@dataclass(frozen=True)
class GpuNodeGroupProps:
    """GPU 节点组配置 (不可变)"""

    instance_type: ec2.InstanceType
    min_size: int = 0
    max_size: int = 10
    desired_size: int = 0
    disk_size: int = 200
    gpu_count: int = 8
    enable_efa: bool = False


class GpuNodeGroupConstruct(Construct):
    """GPU 节点组 L3 Construct"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        cluster: eks.ICluster,
        props: GpuNodeGroupProps,
        env_config: EnvironmentConfig,
    ) -> None:
        super().__init__(scope, construct_id)

        self._props = props
        self._env_config = env_config

        # 创建资源
        self._launch_template = self._create_launch_template()
        self._node_group = self._create_node_group(cluster)

    def _create_launch_template(self) -> ec2.LaunchTemplate:
        """创建 Launch Template"""
        return ec2.LaunchTemplate(
            self, "LaunchTemplate",
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=self._props.disk_size,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        encrypted=True,
                    ),
                )
            ],
            require_imdsv2=True,  # 安全要求
        )

    def _create_node_group(self, cluster: eks.ICluster) -> eks.Nodegroup:
        """创建节点组"""
        return eks.Nodegroup(
            self, "NodeGroup",
            cluster=cluster,
            instance_types=[self._props.instance_type],
            min_size=self._props.min_size,
            max_size=self._props.max_size,
            desired_size=self._props.desired_size,
            ami_type=eks.NodegroupAmiType.AL2_X86_64_GPU,
            launch_template_spec=eks.LaunchTemplateSpec(
                id=self._launch_template.launch_template_id or "",
                version=self._launch_template.latest_version_number,
            ),
            labels={"gpu-type": self._get_gpu_type()},
            taints=[
                eks.TaintSpec(
                    key="nvidia.com/gpu",
                    value="true",
                    effect=eks.TaintEffect.NO_SCHEDULE,
                )
            ],
        )

    def _get_gpu_type(self) -> str:
        """根据实例类型返回 GPU 类型"""
        instance_name = self._props.instance_type.to_string()
        if "p4d" in instance_name:
            return "a100"
        elif "p5" in instance_name:
            return "h100"
        elif "trn1" in instance_name:
            return "trainium"
        return "unknown"

    # ========== 公开属性 ==========

    @property
    def node_group(self) -> eks.Nodegroup:
        """导出节点组"""
        return self._node_group

    @property
    def launch_template(self) -> ec2.LaunchTemplate:
        """导出 Launch Template"""
        return self._launch_template
```

---

## Props 设计规范

### 使用 dataclass

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)  # 不可变
class BucketProps:
    """S3 Bucket 配置"""

    bucket_name: str
    versioned: bool = True
    encryption: s3.BucketEncryption = s3.BucketEncryption.KMS_MANAGED
    lifecycle_rules: list[s3.LifecycleRule] = field(default_factory=list)

    def __post_init__(self) -> None:
        """验证配置"""
        if not self.bucket_name:
            raise ValueError("bucket_name is required")
```

### Props vs 构造函数参数

| 场景 | 使用 Props | 使用参数 |
|------|-----------|----------|
| 配置项 >= 5 个 | ✅ | |
| 配置有默认值 | ✅ | |
| 配置需要验证 | ✅ | |
| 配置项 < 5 个 | | ✅ |
| 依赖注入 | | ✅ |

---

## 工厂函数模式

### 预配置资源创建

```python
# cdk_constructs/gpu_node_group.py

def create_default_gpu_node_groups(
    scope: Construct,
    cluster: eks.ICluster,
    env_config: EnvironmentConfig,
) -> dict[str, GpuNodeGroupConstruct]:
    """创建默认 GPU 节点组集合"""

    return {
        "p4d": GpuNodeGroupConstruct(
            scope, "P4dNodeGroup",
            cluster=cluster,
            props=GpuNodeGroupProps(
                instance_type=ec2.InstanceType("p4d.24xlarge"),
                gpu_count=8,
                enable_efa=True,
            ),
            env_config=env_config,
        ),
        "p5": GpuNodeGroupConstruct(
            scope, "P5NodeGroup",
            cluster=cluster,
            props=GpuNodeGroupProps(
                instance_type=ec2.InstanceType("p5.48xlarge"),
                gpu_count=8,
                enable_efa=True,
            ),
            env_config=env_config,
        ),
    }
```

---

## Construct 组合模式

### 正确: 组合优于继承

```python
class TrainingInfraConstruct(Construct):
    """训练基础设施 (组合多个 Construct)"""

    def __init__(self, scope: Construct, construct_id: str, ...) -> None:
        super().__init__(scope, construct_id)

        # 组合子 Construct
        self._storage = TrainingStorageConstruct(self, "Storage", ...)
        self._compute = GpuNodeGroupConstruct(self, "Compute", ...)
        self._monitoring = MonitoringConstruct(self, "Monitoring", ...)
```

### 避免: 深度继承

```python
# ❌ 不推荐
class GpuNodeGroupConstruct(BaseNodeGroupConstruct):
    pass

class A100NodeGroupConstruct(GpuNodeGroupConstruct):
    pass

class H100NodeGroupConstruct(GpuNodeGroupConstruct):
    pass
```

---

## Aspect 设计

### 全局标签 Aspect

```python
# aspects/tagging.py
from aws_cdk import IAspect, Tags
from constructs import IConstruct


class StandardTaggingAspect(IAspect):
    """应用标准标签到所有资源"""

    def __init__(self, env_config: EnvironmentConfig) -> None:
        self._env_config = env_config

    def visit(self, node: IConstruct) -> None:
        Tags.of(node).add("Environment", self._env_config.environment_name)
        Tags.of(node).add("Project", self._env_config.project_name)
        Tags.of(node).add("ManagedBy", "CDK")
```

### Aspect 应用

```python
# app.py
from aspects import StandardTaggingAspect

app = cdk.App()
# ... 创建 Stacks ...

# 应用 Aspect (在所有 Stack 创建后)
cdk.Aspects.of(app).add(StandardTaggingAspect(env_config))
```

---

## Construct 测试

### 单元测试模板

```python
# tests/unit/test_gpu_node_group.py
import pytest
from aws_cdk import App, Stack
from aws_cdk.assertions import Template

from cdk_constructs import GpuNodeGroupConstruct, GpuNodeGroupProps


class TestGpuNodeGroupConstruct:
    """GPU 节点组 Construct 测试"""

    @pytest.fixture
    def template(self, dev_config, mock_cluster) -> Template:
        app = App()
        stack = Stack(app, "TestStack")

        GpuNodeGroupConstruct(
            stack, "TestNodeGroup",
            cluster=mock_cluster,
            props=GpuNodeGroupProps(
                instance_type=ec2.InstanceType("p4d.24xlarge"),
            ),
            env_config=dev_config,
        )

        return Template.from_stack(stack)

    def test_creates_node_group(self, template: Template) -> None:
        template.resource_count_is("AWS::EKS::Nodegroup", 1)

    def test_uses_gpu_ami(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {"AmiType": "AL2_x86_64_GPU"},
        )

    def test_applies_gpu_taint(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "Taints": [
                    {
                        "Key": "nvidia.com/gpu",
                        "Value": "true",
                        "Effect": "NO_SCHEDULE",
                    }
                ]
            },
        )
```
