# 实施计划：为 HyperPod 添加 GPU 实例组 (ml.g5.2xlarge)

## 概述

为 CDK 项目的 SageMaker HyperPod Stack 添加 GPU 训练实例组，使用 `ml.g5.2xlarge` 实例类型。

## 需求分析

### ml.g5.2xlarge 规格
- **GPU**: 1x NVIDIA A10G (24 GB GPU 内存)
- **vCPU**: 8
- **内存**: 32 GB
- **网络**: 最高 10 Gbps
- **适用场景**: 中小规模推理、单 GPU 训练、开发测试

### 当前架构

现有 HyperPod 实例组 (`sagemaker_hyperpod_stack.py:269-281`):
```python
instance_groups = [
    controller-group: ml.m5.xlarge (1 实例)
    system-group: ml.m5.4xlarge (1 实例)
]
```

## 实施方案

### 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `config/constants.py` | 添加 `GPU_G5_2XLARGE` 常量 |
| `config/environments.py` | 添加 GPU 实例组配置到 `EksConfig` |
| `stacks/compute/sagemaker_hyperpod_stack.py` | 创建 GPU 实例组 |
| `tests/unit/test_sagemaker_hyperpod_stack.py` | 添加 GPU 实例组测试 |

---

### 1. 更新常量定义

**文件**: `config/constants.py`

在 `SageMakerInstanceTypes` 类中添加:
```python
GPU_G5_2XLARGE: str = "ml.g5.2xlarge"
```

---

### 2. 添加环境配置

**文件**: `config/environments.py`

在 `EksConfig` 中添加 GPU 实例组配置:
```python
@dataclass(frozen=True)
class GpuInstanceGroupConfig:
    """GPU 实例组配置"""
    instance_type: str = "ml.g5.2xlarge"
    instance_count: int = 1
    enabled: bool = True

@dataclass(frozen=True)
class EksConfig:
    # ... 现有字段
    gpu_instance_group: GpuInstanceGroupConfig = field(
        default_factory=GpuInstanceGroupConfig
    )
```

环境差异配置 ✅ (用户确认):
- **dev**: `instance_count=1`, `enabled=True`
- **staging**: `instance_count=2`, `enabled=True`
- **prod**: `instance_count=4`, `enabled=True`

---

### 3. 创建 GPU 实例组

**文件**: `stacks/compute/sagemaker_hyperpod_stack.py`

在 `_create_hyperpod_cluster()` 方法中添加 GPU 实例组:

```python
instance_groups = [
    # 现有实例组
    self._create_instance_group(
        name=INSTANCE_GROUPS.CONTROLLER,
        instance_type=SAGEMAKER_INSTANCES.CONTROLLER,
        instance_count=1,
    ),
    self._create_instance_group(
        name=INSTANCE_GROUPS.SYSTEM,
        instance_type=SAGEMAKER_INSTANCES.SYSTEM,
        instance_count=1,
    ),
    # 新增 GPU 实例组
    self._create_instance_group(
        name=INSTANCE_GROUPS.GPU_TRAINING,
        instance_type=SAGEMAKER_INSTANCES.GPU_G5_2XLARGE,
        instance_count=self.env_config.eks.gpu_instance_group.instance_count,
    ),
]
```

条件创建逻辑（仅当 `gpu_instance_group.enabled=True` 时）:
```python
if self.env_config.eks.gpu_instance_group.enabled:
    instance_groups.append(
        self._create_instance_group(...)
    )
```

---

### 4. 添加单元测试

**文件**: `tests/unit/test_sagemaker_hyperpod_stack.py`

新增测试类:
```python
class TestGpuInstanceGroup:
    """Tests for GPU instance group configuration."""

    def test_gpu_instance_group_created(self, template: Template) -> None:
        """Verify GPU training instance group is created."""
        template.has_resource_properties(
            "AWS::SageMaker::Cluster",
            {
                "InstanceGroups": Match.array_with([
                    Match.object_like({
                        "InstanceGroupName": "gpu-training-group",
                        "InstanceType": "ml.g5.2xlarge",
                    })
                ])
            },
        )

    def test_gpu_instance_count_matches_config(self, template: Template) -> None:
        """Verify GPU instance count matches environment config."""
        # 验证实例数量与配置一致
```

---

## 验证步骤

### 1. 代码质量检查
```bash
cd infrastructure/cdk
ruff check .
ruff format .
mypy .
```

### 2. 单元测试
```bash
pytest tests/unit/test_sagemaker_hyperpod_stack.py -v
```

### 3. CDK Synth 验证
```bash
cdk synth --context env=dev 2>&1 | grep -A5 "gpu-training-group"
```

### 4. CDK Diff 查看变更
```bash
cdk diff --context env=dev
```

---

## 注意事项

1. **实例配额**: 确保 AWS 账户有 `ml.g5.2xlarge` 的服务配额
2. **成本**: ml.g5.2xlarge 按小时计费，开发环境建议设置 `instance_count=1`
3. **生命周期脚本**: 现有 `on_create.sh` 脚本应兼容 GPU 实例，无需修改
4. **IAM 权限**: 现有 HyperPod 执行角色已包含所需权限
