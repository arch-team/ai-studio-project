# 分布式训练模板系统

企业级AI训练平台的分布式训练模板系统,支持PyTorch DDP/FSDP/DeepSpeed等多种分布式策略。

## 目录

- [概述](#概述)
- [模板类型](#模板类型)
- [架构设计](#架构设计)
- [使用指南](#使用指南)
- [模板说明](#模板说明)
- [配置参考](#配置参考)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

## 概述

本系统提供4种分布式训练模板,自动根据`TrainingJobType`和`FrameworkType`选择最优模板:

| 模板 | 适用场景 | 模型规模 | 特点 |
|------|---------|---------|------|
| **单节点模板** | 小模型训练 | <7B参数 | 简化配置,无分布式开销 |
| **DDP模板** | 中小模型 | ≤13B参数 | 数据并行,高效梯度同步 |
| **FSDP模板** | 大模型 | ≥70B参数 | 模型分片,支持CPU offload |
| **DeepSpeed模板** | 超大模型 | ≥100B参数 | ZeRO优化,内存高效 |

## 模板类型

### 1. 单节点模板 (`single-node-template.yaml`)

**适用场景**: 小模型训练,快速实验

**特点**:
- 单机单卡或单机多卡
- 无需torchrun启动器
- 最小配置开销
- 适合快速原型开发

**推荐配置**:
```python
TrainingJobConfig(
    node_count=1,
    gpu_per_node=1,  # 或 2, 4, 8
    framework=FrameworkType.PYTORCH,
    job_type=TrainingJobType.SINGLE_NODE
)
```

### 2. DDP模板 (`ddp-job-template.yaml`)

**适用场景**: 中小模型多机训练

**特点**:
- PyTorch原生DistributedDataParallel
- 每个进程持有完整模型副本
- 使用NCCL进行all-reduce梯度同步
- 支持InfiniBand/EFA高速互联

**推荐配置**:
```python
TrainingJobConfig(
    node_count=2-16,
    gpu_per_node=8,
    framework=FrameworkType.PYTORCH,
    job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
    env_vars={
        "NCCL_DEBUG": "INFO",
        "NCCL_IB_DISABLE": "0",  # 启用InfiniBand
    }
)
```

**环境变量**:
- `MASTER_ADDR`: Master节点地址(自动设置)
- `MASTER_PORT`: Master端口(默认23456)
- `WORLD_SIZE`: 总进程数(node_count * gpu_per_node)
- `RANK`: 全局进程Rank
- `LOCAL_RANK`: 节点内进程Rank

### 3. FSDP模板 (`fsdp-job-template.yaml`)

**适用场景**: 大模型训练(≥70B参数)

**特点**:
- 模型参数、梯度、优化器状态跨设备分片
- 支持CPU offload减少GPU内存占用
- 支持混合精度(BF16/FP16)
- 激活检查点(Activation Checkpointing)

**推荐配置**:
```python
TrainingJobConfig(
    node_count=4-32,
    gpu_per_node=8,
    gpu_type="p4d.24xlarge",  # 推荐高带宽实例
    framework=FrameworkType.PYTORCH,
    job_type=TrainingJobType.DISTRIBUTED_MODEL_PARALLEL,
    memory_per_node_gb=1024,  # FSDP需要更多内存
    env_vars={
        "FSDP_SHARDING_STRATEGY": "FULL_SHARD",  # 或 HYBRID_SHARD
        "FSDP_CPU_OFFLOAD": "False",  # 是否offload到CPU
        "FSDP_MIXED_PRECISION": "bf16",
        "FSDP_ACTIVATION_CHECKPOINTING": "True",
    }
)
```

**FSDP配置参数**:
- `FSDP_SHARDING_STRATEGY`:
  - `FULL_SHARD`: 完全分片(最大内存节省)
  - `HYBRID_SHARD`: 节点内复制+节点间分片
  - `SHARD_GRAD_OP`: 仅分片梯度和优化器状态
- `FSDP_CPU_OFFLOAD`: CPU offload(牺牲速度换内存)
- `FSDP_BACKWARD_PREFETCH`: 反向传播预取策略
- `FSDP_AUTO_WRAP_POLICY`: 自动包裹策略(transformer/size_based)

### 4. DeepSpeed模板 (`deepspeed-job-template.yaml`)

**适用场景**: 超大模型训练(≥100B参数)

**特点**:
- ZeRO优化(ZeRO-1/2/3)
- 支持offload到CPU和NVMe
- 梯度累积和混合精度
- 内置优化器和学习率调度器

**推荐配置**:
```python
TrainingJobConfig(
    node_count=8-64,
    gpu_per_node=8,
    gpu_type="p4d.24xlarge",
    framework=FrameworkType.DEEPSPEED,
    job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
    memory_per_node_gb=1536,  # DeepSpeed需要更多内存
    env_vars={
        "ZERO_STAGE": "2",  # ZeRO-1/2/3
        "OFFLOAD_OPTIMIZER": "False",
        "OFFLOAD_PARAM": "False",
        "GRADIENT_ACCUMULATION_STEPS": "4",
        "BF16_ENABLED": "True",
        "TRAIN_BATCH_SIZE": "32",
        "MICRO_BATCH_SIZE": "1",
    }
)
```

**ZeRO阶段说明**:
- **ZeRO-1**: 分片优化器状态(节省4x内存)
- **ZeRO-2**: 分片优化器状态+梯度(节省8x内存)
- **ZeRO-3**: 分片优化器+梯度+参数(节省N倍内存)

**DeepSpeed配置文件**: 模板自动生成ConfigMap(`deepspeed_config.json`)

## 架构设计

### 模板选择逻辑

`TemplateRenderer`根据`(TrainingJobType, FrameworkType)`映射选择模板:

```python
TEMPLATE_MAPPING = {
    # 单节点 - 所有框架使用统一模板
    (TrainingJobType.SINGLE_NODE, FrameworkType.PYTORCH): "single-node-template.yaml",

    # 数据并行 - PyTorch使用DDP, DeepSpeed使用专用模板
    (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.PYTORCH): "ddp-job-template.yaml",
    (TrainingJobType.DISTRIBUTED_DATA_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",

    # 模型并行 - PyTorch使用FSDP, DeepSpeed使用ZeRO-3
    (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.PYTORCH): "fsdp-job-template.yaml",
    (TrainingJobType.DISTRIBUTED_MODEL_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",

    # 混合并行 - 优先FSDP或DeepSpeed
    (TrainingJobType.HYBRID_PARALLEL, FrameworkType.PYTORCH): "fsdp-job-template.yaml",
    (TrainingJobType.HYBRID_PARALLEL, FrameworkType.DEEPSPEED): "deepspeed-job-template.yaml",
}
```

### 渲染流程

```
TrainingJob + TrainingJobConfig
         ↓
  TemplateRenderer.render_pytorch_job()
         ↓
  1. 选择模板(_select_template)
  2. 准备变量(_prepare_template_vars)
  3. 框架特定配置(_get_deepspeed_vars / _get_fsdp_vars)
  4. Jinja2渲染
         ↓
  Kubernetes PyTorchJob YAML
```

## 使用指南

### 基本使用

```python
from pathlib import Path
from services.training.templates import TemplateRenderer
from models.training import TrainingJob, TrainingJobConfig

# 初始化渲染器
renderer = TemplateRenderer()

# 创建训练任务和配置
job = TrainingJob(
    id=1,
    name="bert-training",
    job_type=TrainingJobType.DISTRIBUTED_DATA_PARALLEL,
    framework=FrameworkType.PYTORCH,
    k8s_namespace="ai-training-platform",
    # ...其他字段
)

config = TrainingJobConfig(
    node_count=4,
    gpu_per_node=8,
    cpu_per_node=64,
    memory_per_node_gb=512,
    gpu_type="p4d.24xlarge",
    docker_image="pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel",
    command=["python", "train.py"],
    args=["--epochs", "100"],
    # ...其他字段
)

# 渲染模板
yaml_manifest = renderer.render_pytorch_job(
    job=job,
    config=config,
    k8s_job_name="bert-training-001",
)

# 应用到Kubernetes
# kubectl apply -f <yaml_manifest>
```

### 与HyperPodOperator集成

```python
from services.training.operators import HyperPodOperator

# HyperPodOperator自动使用TemplateRenderer
operator = HyperPodOperator()

# 创建训练任务(自动选择模板)
k8s_job_name = await operator.create_pytorch_job(
    job=job,
    config=config,
)
```

### 自定义模板目录

```python
from pathlib import Path

# 使用自定义模板目录
custom_templates = Path("/path/to/custom/templates")
renderer = TemplateRenderer(templates_dir=custom_templates)
```

## 配置参考

### 通用配置参数

所有模板支持的通用参数:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `job_name` | str | ✅ | K8s Job名称(DNS-1123规范) |
| `namespace` | str | ✅ | K8s命名空间 |
| `node_count` | int | ✅ | 训练节点数量 |
| `gpu_per_node` | int | ✅ | 每节点GPU数量 |
| `cpu_per_node` | int | ✅ | 每节点CPU核心数 |
| `memory_per_node_gb` | int | ✅ | 每节点内存(GB) |
| `gpu_type` | str | ❌ | GPU实例类型(如p4d.24xlarge) |
| `docker_image` | str | ✅ | 训练容器镜像 |
| `command` | list | ✅ | 训练命令 |
| `args` | list | ❌ | 训练参数 |
| `env_vars` | dict | ❌ | 环境变量 |
| `dataset_path` | str | ❌ | 数据集路径 |
| `output_path` | str | ✅ | 输出路径 |
| `timeout_seconds` | int | ❌ | 超时时间(秒) |
| `max_retries` | int | ❌ | 最大重试次数 |

### 资源配置建议

| 模型规模 | 节点配置 | GPU类型 | 内存(GB/节点) | 推荐模板 |
|---------|---------|---------|-------------|---------|
| <7B参数 | 1节点 × 1-8 GPU | p3.2xlarge | 64 | 单节点 |
| 7B-13B | 2-4节点 × 8 GPU | p3.16xlarge | 512 | DDP |
| 13B-70B | 4-8节点 × 8 GPU | p4d.24xlarge | 1024 | FSDP |
| 70B-175B | 8-16节点 × 8 GPU | p4d.24xlarge | 1536 | DeepSpeed ZeRO-2 |
| >175B | 16-64节点 × 8 GPU | p4d.24xlarge | 2048 | DeepSpeed ZeRO-3 + Offload |

## 最佳实践

### 1. 选择合适的模板

**决策树**:
```
模型参数量?
├─ <7B → 单节点模板
├─ 7B-13B → DDP模板
├─ 13B-70B → FSDP模板
└─ >70B → DeepSpeed模板(ZeRO-2/3)
```

### 2. 网络优化

**启用高速互联**(DDP/FSDP/DeepSpeed必须):
```python
env_vars={
    "NCCL_IB_DISABLE": "0",  # 启用InfiniBand/EFA
    "NCCL_SOCKET_IFNAME": "eth0",
    "NCCL_MIN_NCHANNELS": "8",  # FSDP/DeepSpeed增加通道
}
```

**AWS EFA配置**(p4d实例):
```python
gpu_type="p4d.24xlarge"  # 自动启用EFA
env_vars={
    "FI_PROVIDER": "efa",
    "FI_EFA_USE_DEVICE_RDMA": "1",
}
```

### 3. 内存优化

**FSDP内存优化**:
```python
env_vars={
    "FSDP_SHARDING_STRATEGY": "FULL_SHARD",  # 最大内存节省
    "FSDP_CPU_OFFLOAD": "True",  # CPU offload(牺牲15-20%速度)
    "FSDP_ACTIVATION_CHECKPOINTING": "True",  # 激活检查点
}
```

**DeepSpeed内存优化**:
```python
env_vars={
    "ZERO_STAGE": "3",  # 最大内存节省
    "OFFLOAD_OPTIMIZER": "True",  # Offload优化器到CPU
    "OFFLOAD_PARAM": "True",  # Offload参数到CPU/NVMe
}
```

### 4. 混合精度训练

**BF16(推荐)**:
```python
env_vars={
    "FSDP_MIXED_PRECISION": "bf16",  # FSDP
    "BF16_ENABLED": "True",  # DeepSpeed
}
```

**FP16**:
```python
env_vars={
    "FSDP_MIXED_PRECISION": "fp16",
    "FP16_ENABLED": "True",
}
```

### 5. 梯度累积

减少通信开销,模拟更大batch size:
```python
env_vars={
    "GRADIENT_ACCUMULATION_STEPS": "4",  # 实际batch = micro_batch * accumulation_steps
}
```

### 6. 检查点策略

**本地NVMe + FSx双重保存**:
```yaml
volumeMounts:
  - name: checkpoint-local  # 快速本地保存
    mountPath: /mnt/nvme/checkpoints
  - name: checkpoint-fsx    # 持久化FSx保存
    mountPath: /mnt/fsx/checkpoints
```

**训练代码示例**:
```python
# 每N步保存到NVMe(快)
if step % 100 == 0:
    torch.save(model.state_dict(), "/mnt/nvme/checkpoints/ckpt_latest.pt")

# 每epoch保存到FSx(持久)
if epoch_end:
    torch.save(model.state_dict(), f"/mnt/fsx/checkpoints/ckpt_epoch_{epoch}.pt")
```

## 故障排查

### 常见问题

#### 1. Pod一直Pending

**原因**: 资源不足或节点选择器不匹配

**检查**:
```bash
kubectl describe pytorchjob <job-name> -n ai-training-platform
kubectl get nodes -o wide
```

**解决**:
- 调整`gpu_type`或移除节点选择器
- 增加集群节点
- 检查节点标签和容忍度

#### 2. NCCL初始化失败

**错误**: `NCCL error: unhandled system error`

**原因**: 网络配置问题

**解决**:
```python
env_vars={
    "NCCL_DEBUG": "INFO",  # 启用调试日志
    "NCCL_IB_DISABLE": "1",  # 临时禁用IB测试
    "NCCL_SOCKET_IFNAME": "eth0",  # 指定网络接口
}
```

#### 3. OOM (Out of Memory)

**FSDP解决方案**:
```python
env_vars={
    "FSDP_CPU_OFFLOAD": "True",
    "FSDP_ACTIVATION_CHECKPOINTING": "True",
}
memory_per_node_gb *= 1.5  # 增加内存配额
```

**DeepSpeed解决方案**:
```python
env_vars={
    "ZERO_STAGE": "3",
    "OFFLOAD_OPTIMIZER": "True",
    "OFFLOAD_PARAM": "True",
}
```

#### 4. 梯度不同步

**DDP检查**:
```python
env_vars={
    "TORCH_DISTRIBUTED_DEBUG": "DETAIL",  # 详细调试
}
```

**FSDP检查**:
```python
env_vars={
    "FSDP_SYNC_MODULE_STATES": "True",  # 确保模块状态同步
}
```

### 调试命令

```bash
# 查看Job状态
kubectl get pytorchjob -n ai-training-platform

# 查看Job详情
kubectl describe pytorchjob <job-name> -n ai-training-platform

# 查看Pod日志
kubectl logs <pod-name> -n ai-training-platform

# 查看Master节点日志
kubectl logs <job-name>-master-0 -n ai-training-platform

# 查看Worker节点日志
kubectl logs <job-name>-worker-0 -n ai-training-platform

# 进入Pod调试
kubectl exec -it <pod-name> -n ai-training-platform -- /bin/bash

# 查看NCCL测试
# (在Pod内)
nccl-test --nthreads 8 --ngpus 8
```

## 参考资料

### 官方文档
- [PyTorch DDP](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html)
- [PyTorch FSDP](https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html)
- [DeepSpeed](https://www.deepspeed.ai/getting-started/)
- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/)
- [AWS SageMaker HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html)

### 相关模块
- `services.training.operators.hyperpod_operator`: K8s Job管理
- `services.training.job_service`: 训练任务业务逻辑
- `models.training`: 数据模型定义

### 模板文件
- `ddp-job-template.yaml`: DDP训练模板
- `fsdp-job-template.yaml`: FSDP训练模板
- `deepspeed-job-template.yaml`: DeepSpeed训练模板
- `single-node-template.yaml`: 单节点训练模板
- `template_renderer.py`: 模板渲染器

---

**维护者**: AI训练平台团队
**最后更新**: 2025-01-01
**版本**: v1.0.0
