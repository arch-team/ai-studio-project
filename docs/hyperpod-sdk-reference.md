# HyperPod SDK 方法签名参考文档

**版本**: Phase 0 技术验证
**日期**: 2026-01-08
**SDK 版本**: sagemaker-hyperpod CLI (最新稳定版)
**研究来源**: [research.md](../specs/001-ai-training-platform/research.md)

---

## 概述

本文档提供 `sagemaker-hyperpod` SDK 的核心方法签名、参数说明和示例代码,用于指导平台后端开发。

**核心模块**:
- **Training 模块**: 训练任务生命周期管理
- **Space 模块**: 在线开发环境管理
- **Cluster 模块**: 集群状态查询

---

## Training 模块

### HyperPodPytorchJob 类

**导入**:
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob
```

#### 1. 创建训练任务

**方法签名**:
```python
@classmethod
def create(
    cls,
    name: str,                          # 训练任务名称 (全局唯一)
    image_uri: str,                     # Docker 镜像 URI
    instance_type: str,                 # 实例类型 (ml.p4d.24xlarge 等)
    node_count: int,                    # 节点数量
    tasks_per_node: int = 1,            # 每节点任务数 (GPU 数量)
    command: List[str] = None,          # 启动命令
    environment: Dict[str, str] = None, # 环境变量
    volumes: List[VolumeConfig] = None, # 存储卷配置
    **kwargs
) -> HyperPodPytorchJob
```

**参数说明**:
- `name`: HyperPod Job 名称,必须全局唯一,对应 Kubernetes 资源名称
- `image_uri`: 训练容器镜像 URI (ECR 或公开镜像)
- `instance_type`: AWS 实例类型
  - GPU 实例: `ml.p4d.24xlarge`, `ml.p5.48xlarge`, `ml.g5.xlarge`
  - Trainium 实例: `trn1.32xlarge`
- `node_count`: 分布式训练节点数 (单节点训练设为 1)
- `tasks_per_node`: 每节点并发任务数,通常等于每节点 GPU 数量
- `command`: 容器启动命令 (JSON 数组格式)
- `environment`: 环境变量 (JSON 对象格式)
- `volumes`: 存储卷配置列表 (FSx for Lustre 挂载等)

**示例代码**:
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob
from sagemaker.hyperpod.training.config import VolumeConfig

# 配置 FSx for Lustre 卷
volumes = [
    VolumeConfig(
        name="training-data",
        type="hostPath",
        mount_path="/data",
        path="/fsx/training-data"  # FSx for Lustre 挂载点
    ),
    VolumeConfig(
        name="checkpoints",
        type="hostPath",
        mount_path="/checkpoints",
        path="/fsx/checkpoints"
    )
]

# 创建训练任务
job = HyperPodPytorchJob.create(
    name="llama3-70b-training",
    image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
    instance_type="ml.p4d.24xlarge",
    node_count=16,           # 16个节点
    tasks_per_node=8,        # 每节点8个GPU (总共128个GPU)
    command=[
        "torchrun",
        "--nproc_per_node=8",
        "--nnodes=16",
        "train.py"
    ],
    environment={
        "NCCL_DEBUG": "INFO",
        "NCCL_SOCKET_IFNAME": "eth0",
        "OMP_NUM_THREADS": "1"
    },
    volumes=volumes
)

print(f"训练任务已创建: {job.name}, 状态: {job.status}")
```

**自动注入的环境变量**:
SDK 自动注入以下分布式训练环境变量:
- `MASTER_ADDR`: rank 0 节点地址
- `MASTER_PORT`: rank 0 节点端口 (默认 23456)
- `NODE_RANK`: 当前节点 rank (0 到 node_count-1)
- `WORLD_SIZE`: 总进程数 (node_count * tasks_per_node)
- `RANK`: 全局进程 rank

---

#### 2. 查询训练任务

**方法签名**:
```python
@classmethod
def get(cls, name: str) -> HyperPodPytorchJob
```

**参数说明**:
- `name`: 训练任务名称

**返回属性**:
- `job.name`: 任务名称
- `job.status`: 任务状态 (Pending/Running/Succeeded/Failed)
- `job.start_time`: 开始时间
- `job.end_time`: 结束时间

**示例代码**:
```python
job = HyperPodPytorchJob.get(name="llama3-70b-training")
print(f"任务状态: {job.status}")
print(f"开始时间: {job.start_time}")
```

**状态映射**:
```python
# HyperPod SDK 状态 → 平台标准化状态
STATUS_MAPPING = {
    "Pending": "submitted",      # 等待资源分配
    "Running": "running",        # 训练中
    "Succeeded": "completed",    # 成功完成
    "Failed": "failed",          # 失败
}
```

---

#### 3. 列出训练任务的 Pods

**方法签名**:
```python
def list_pods(self) -> List[Dict[str, Any]]
```

**返回值**: Pod 列表,每个 Pod 包含:
- `name`: Pod 名称
- `status`: Pod 状态 (Running/Pending/Failed/Succeeded)
- `node_name`: 所在节点名称
- `ip`: Pod IP 地址

**示例代码**:
```python
job = HyperPodPytorchJob.get(name="llama3-70b-training")
pods = job.list_pods()

for pod in pods:
    print(f"Pod: {pod['name']}, 状态: {pod['status']}, 节点: {pod['node_name']}")
```

---

#### 4. 查看训练日志

**方法签名**:
```python
def logs(self, tail: int = 100, follow: bool = False) -> str
```

**参数说明**:
- `tail`: 显示最后 N 行日志
- `follow`: 是否持续跟踪日志 (类似 `tail -f`)

**示例代码**:
```python
job = HyperPodPytorchJob.get(name="llama3-70b-training")

# 获取最后 100 行日志
logs = job.logs(tail=100)
print(logs)

# 持续跟踪日志 (阻塞式)
job.logs(follow=True)
```

---

#### 5. 删除训练任务

**方法签名**:
```python
def delete(self) -> None
```

**示例代码**:
```python
job = HyperPodPytorchJob.get(name="llama3-70b-training")
job.delete()
print(f"训练任务已删除: {job.name}")
```

---

### VolumeConfig 类

**导入**:
```python
from sagemaker.hyperpod.training.config import VolumeConfig
```

**构造函数签名**:
```python
def __init__(
    self,
    name: str,              # 卷名称
    type: str,              # 卷类型 (hostPath/pvc)
    mount_path: str,        # 容器内挂载路径
    path: str = None,       # hostPath 类型的主机路径
    claim_name: str = None  # pvc 类型的 PVC 名称
)
```

**支持的卷类型**:

| 类型 | 说明 | 使用场景 | 必需参数 |
|------|------|---------|---------|
| `hostPath` | 挂载节点主机路径 | FSx for Lustre 共享存储 | `path` (主机路径) |
| `pvc` | Kubernetes 持久卷声明 | EBS/EFS 存储 | `claim_name` (PVC 名称) |

**示例代码**:
```python
# hostPath 类型 (FSx for Lustre)
fsx_volume = VolumeConfig(
    name="training-data",
    type="hostPath",
    mount_path="/data",
    path="/fsx/training-data"
)

# PVC 类型 (EBS 持久卷)
ebs_volume = VolumeConfig(
    name="checkpoints",
    type="pvc",
    mount_path="/checkpoints",
    claim_name="checkpoint-pvc"
)
```

---

## Space 模块

### Space 类

**导入**:
```python
from sagemaker.hyperpod.space import Space
```

#### 1. 创建开发空间

**方法签名**:
```python
@classmethod
def create(
    cls,
    name: str,                          # Space 名称
    instance_type: str,                 # 实例类型
    ide_type: str = "jupyterlab",       # IDE 类型 (jupyterlab/vscode)
    lifecycle_config_arn: str = None,   # 生命周期配置 ARN
    storage_size_gb: int = 10,          # 存储大小 (GB)
    **kwargs
) -> Space
```

**参数说明**:
- `name`: Space 名称 (全局唯一)
- `instance_type`: 实例类型
  - 轻量级: `ml.t3.medium`, `ml.t3.large`
  - GPU: `ml.g5.xlarge`, `ml.g5.2xlarge`
- `ide_type`: IDE 类型
  - `jupyterlab`: JupyterLab (数据科学/ML 开发)
  - `vscode`: VS Code (通用开发)
- `lifecycle_config_arn`: Lifecycle Configuration ARN (预装库、配置环境)
- `storage_size_gb`: EFS 存储大小 (默认 10 GB)

**示例代码**:
```python
from sagemaker.hyperpod.space import Space

# 创建 JupyterLab Space
space = Space.create(
    name="user-dev-space",
    instance_type="ml.g5.xlarge",
    ide_type="jupyterlab",
    storage_size_gb=50
)

print(f"Space 已创建: {space.name}, URL: {space.studio_url}")
```

---

#### 2. 查询开发空间

**方法签名**:
```python
@classmethod
def get(cls, name: str) -> Space
```

**返回属性**:
- `space.name`: Space 名称
- `space.status`: Space 状态 (Pending/InService/Stopping/Stopped/Failed)
- `space.studio_url`: SageMaker Studio URL
- `space.instance_type`: 实例类型

**示例代码**:
```python
space = Space.get(name="user-dev-space")
print(f"Space 状态: {space.status}")
print(f"Studio URL: {space.studio_url}")
```

---

#### 3. 删除开发空间

**方法签名**:
```python
def delete(self) -> None
```

**示例代码**:
```python
space = Space.get(name="user-dev-space")
space.delete()
print(f"Space 已删除: {space.name}")
```

---

## Cluster 模块

### Cluster 类

**导入**:
```python
from sagemaker.hyperpod.cluster import Cluster
```

#### 1. 查询集群信息

**方法签名**:
```python
@classmethod
def describe(cls, cluster_name: str) -> Dict[str, Any]
```

**返回值**:
```python
{
    "ClusterName": "my-hyperpod-cluster",
    "ClusterArn": "arn:aws:sagemaker:us-west-2:123456:cluster/my-hyperpod-cluster",
    "ClusterStatus": "InService",  # Creating/InService/Updating/Deleting/Failed
    "InstanceGroups": [
        {
            "InstanceGroupName": "on-demand-workers",
            "InstanceType": "ml.p4d.24xlarge",
            "InstanceCount": 4,
            "CapacityType": "OnDemand"
        },
        {
            "InstanceGroupName": "spot-workers",
            "InstanceType": "ml.p4d.24xlarge",
            "InstanceCount": 16,
            "CapacityType": "Spot"
        }
    ],
    "VpcConfig": {
        "VpcId": "vpc-12345678",
        "Subnets": ["subnet-abc", "subnet-def"],
        "SecurityGroupIds": ["sg-xyz"]
    }
}
```

**示例代码**:
```python
from sagemaker.hyperpod.cluster import Cluster

cluster_info = Cluster.describe(cluster_name="my-hyperpod-cluster")
print(f"集群状态: {cluster_info['ClusterStatus']}")
print(f"总节点数: {sum(ig['InstanceCount'] for ig in cluster_info['InstanceGroups'])}")
```

---

#### 2. 列出集群节点

**方法签名**:
```python
@classmethod
def list_nodes(cls, cluster_name: str) -> List[Dict[str, Any]]
```

**返回值**: 节点列表,每个节点包含:
- `NodeId`: 节点 ID
- `NodeStatus`: 节点状态 (Running/NotReady/Failed)
- `InstanceType`: 实例类型
- `AvailabilityZone`: 可用区
- `LaunchTime`: 启动时间

**示例代码**:
```python
nodes = Cluster.list_nodes(cluster_name="my-hyperpod-cluster")

for node in nodes:
    print(f"节点: {node['NodeId']}, 状态: {node['NodeStatus']}, 类型: {node['InstanceType']}")
```

---

## 状态转换逻辑

### 训练任务状态

**HyperPod SDK 原始状态** → **平台标准化状态**:

```python
# 定义状态映射 (backend/src/services/hyperpod_service.py)
STATUS_MAPPING = {
    # HyperPod 状态 → 平台状态
    "Pending": "submitted",      # 等待资源分配
    "Running": "running",        # 训练中
    "Succeeded": "completed",    # 成功完成
    "Failed": "failed",          # 失败
}

def map_hyperpod_status(hyperpod_status: str) -> str:
    """将 HyperPod 状态映射为平台标准化状态"""
    return STATUS_MAPPING.get(hyperpod_status, "unknown")
```

**状态转换规则** (spec.md Section 2.2):
```
submitted → running → completed
                   ↘ failed
                   ↘ paused → running
                   ↘ preempted → running
```

---

## 分布式训练模式

### DDP (Data Distributed Parallel)

**支持状态**: ✅ **SDK 原生支持**

**配置方式**: 通过 `node_count` 和 `tasks_per_node` 参数

**示例代码**:
```python
job = HyperPodPytorchJob.create(
    name="ddp-training",
    node_count=4,           # 4个节点
    tasks_per_node=8,       # 每节点8个GPU
    command=[
        "torchrun",
        "--nproc_per_node=8",
        "--nnodes=4",
        "train.py"
    ]
)
```

**SDK 自动注入的环境变量**:
- `MASTER_ADDR`, `MASTER_PORT`, `NODE_RANK`, `WORLD_SIZE`, `RANK`

---

### FSDP (Fully Sharded Data Parallel)

**支持状态**: ⚠️ **用户脚本层面支持**

**配置方式**: 用户在 `train.py` 中使用 `torch.distributed.fsdp` API

**用户训练脚本示例**:
```python
# train.py
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = MyLargeModel()
model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    cpu_offload=CPUOffload(offload_params=True)
)

# 训练循环...
```

**HyperPod SDK 配置保持标准 DDP 方式**:
```python
job = HyperPodPytorchJob.create(
    node_count=16,
    tasks_per_node=8,
    command=["torchrun", "--nproc_per_node=8", "train.py"]  # 脚本内部使用 FSDP
)
```

---

### DeepSpeed ZeRO

**支持状态**: ⚠️ **用户脚本+容器支持**

**配置方式**: Docker 镜像包含 DeepSpeed + 使用 `deepspeed` launcher

**Dockerfile 示例**:
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8
RUN pip install deepspeed
```

**HyperPod SDK 配置**:
```python
job = HyperPodPytorchJob.create(
    name="deepspeed-training",
    image_uri="<image-with-deepspeed>",
    node_count=16,
    tasks_per_node=8,
    command=[
        "deepspeed",
        "--num_gpus=8",
        "--num_nodes=16",
        "train.py",
        "--deepspeed",
        "--deepspeed_config=ds_config.json"
    ]
)
```

---

## Gang Scheduling

**支持状态**: ✅ **Kubernetes Operator 原生支持**

**技术实现**: HyperPod 使用 SageMaker Training Operator (基于 Kubeflow Training Operator),内置 gang scheduling 支持。

**工作原理**:
- 确保所有训练 Pod 同时启动,避免部分节点空闲等待
- 如果无法同时获取所有资源,任务保持 Pending 状态
- 超时时间: 默认 60 秒 (可配置)

**开发者无需配置**: SDK 自动处理,无需额外代码。

---

## 检查点管理

**支持状态**: ❌ **SDK 不提供检查点 API**

**平台实现方式**: 后端层扫描 FSx for Lustre 存储并构建元数据索引。

**用户训练脚本实现**:
```python
import torch

def save_checkpoint(epoch, model, optimizer, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

# 训练循环中保存检查点
for epoch in range(num_epochs):
    train_one_epoch(model, optimizer, dataloader)
    if epoch % checkpoint_interval == 0:
        checkpoint_path = f"/checkpoints/checkpoint-epoch{epoch}.pth"
        save_checkpoint(epoch, model, optimizer, checkpoint_path)
```

**后端扫描服务**:
```python
# backend/src/services/checkpoint_service.py
import os

async def scan_checkpoints(job_id: int, checkpoint_dir: str):
    """扫描训练任务的检查点目录并生成元数据"""
    checkpoints = []
    for file in os.listdir(checkpoint_dir):
        if file.endswith('.pth') or file.endswith('.ckpt'):
            file_path = os.path.join(checkpoint_dir, file)
            size_bytes = os.path.getsize(file_path)
            epoch = extract_epoch_from_filename(file)

            checkpoints.append({
                'checkpoint_name': file,
                'storage_path': file_path,
                'epoch': epoch,
                'size_bytes': size_bytes,
                'created_at': os.path.getctime(file_path)
            })

    return checkpoints
```

---

## 限制和约束

### SDK 不支持的功能

以下功能 **SDK 不直接提供**,需要平台后端层实现:

1. **检查点元数据管理**: SDK 不提供 `list_checkpoints()` API
2. **训练指标采集**: SDK 不提供 `get_metrics()` API (需用户集成 OpenTelemetry)
3. **训练任务模板**: SDK 不提供模板管理 API
4. **自动重试机制**: SDK 不提供自动重试 (spot 实例被回收时)
5. **成本追踪**: SDK 不提供成本统计 API (需集成 AWS Cost Explorer)

### 任务命名约束

- **全局唯一性**: 训练任务名称必须在整个 HyperPod 集群中唯一
- **命名规则**: 仅允许小写字母、数字和连字符 (-)
- **长度限制**: 最大 128 字符

### 资源限制

- **最大节点数**: 取决于集群容量
- **最大任务数**: 取决于 Kueue 队列配额
- **实例类型**: 仅支持 HyperPod 支持的实例类型

---

## 参考文档

- **官方文档**: https://sagemaker-hyperpod-cli.readthedocs.io/
- **Training 快速开始**: https://sagemaker-hyperpod-cli.readthedocs.io/en/stable/getting_started/training.html
- **CLI 参考**: https://sagemaker-hyperpod-cli.readthedocs.io/en/stable/cli/training/cli_training.html
- **SDK 参考**: https://sagemaker-hyperpod-cli.readthedocs.io/en/stable/sdk/training/hyperpod_pytorch_job.html
- **示例代码**: https://github.com/aws/sagemaker-hyperpod-cli/tree/main/examples/training

---

**文档版本**: v1.0
**最后更新**: 2026-01-08
**审核状态**: Phase 0 技术验证完成
