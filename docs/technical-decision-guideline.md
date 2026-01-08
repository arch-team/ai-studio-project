# HyperPod SDK 技术选型决策指南

**版本**: Phase 0 技术验证
**日期**: 2026-01-08
**目标**: 为开发人员提供清晰的技术选型决策流程,确保使用最合适的工具实现每个功能
**研究来源**: [research.md](../specs/001-ai-training-platform/research.md), [hyperpod-sdk-capability-matrix.md](./hyperpod-sdk-capability-matrix.md)

---

## 概述

本文档提供一套系统化的技术选型决策流程,帮助开发人员在实现 AI 训练平台功能时做出正确的技术选择。

**决策原则**:
1. **优先级顺序**: sagemaker-hyperpod SDK > boto3 SageMaker API > AWS CLI > kubectl/kubernetes-client
2. **架构约束**: 遵循 [plan.md](../specs/001-ai-training-platform/plan.md) 中定义的技术栈约束
3. **最小权限**: 避免不必要的 Kubernetes 直接操作
4. **类型安全**: 优先选择提供类型定义的工具

---

## 通用决策流程

### 第一步: 识别功能类型

```
你的需求属于哪个类别?
├─ 训练任务管理 (CRUD, 状态查询, 日志) → 跳转到 §2.1
├─ 训练任务高级功能 (Checkpoint, 指标, 调度) → 跳转到 §2.2
├─ 开发空间管理 (Space CRUD, Lifecycle Config) → 跳转到 §2.3
├─ 集群管理 (资源监控, 节点列表) → 跳转到 §2.4
├─ 基础设施配置 (NetworkPolicy, Add-ons) → 跳转到 §2.5
├─ 成本与模型管理 (Cost Explorer, Model Registry) → 跳转到 §2.6
└─ 其他需求 → 继续阅读下一步
```

### 第二步: 评估 SDK 支持

```
功能在 sagemaker-hyperpod SDK 中可用吗?
├─ YES (✅) → 使用 SDK (优先选择)
│   └─ 参考: docs/hyperpod-sdk-reference.md
├─ PARTIAL (⚠️) → 评估 SDK 覆盖范围
│   ├─ SDK 覆盖 >70% 功能 → 使用 SDK + 补充工具
│   └─ SDK 覆盖 <70% 功能 → 跳转到第三步
└─ NO (❌) → 跳转到第三步
```

### 第三步: 评估 boto3 支持

```
功能在 boto3 SageMaker API 中可用吗?
├─ YES (✅) → 使用 boto3
│   └─ 参考: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html
├─ PARTIAL (⚠️) → 评估是否足够
│   ├─ boto3 可满足核心需求 → 使用 boto3
│   └─ boto3 功能不足 → 跳转到第四步
└─ NO (❌) → 跳转到第四步
```

### 第四步: 评估备选方案

```
需要实现的功能属于哪种类型?
├─ Kubernetes 资源查询 (只读) → 使用 kubernetes-client
│   ├─ 查询 Kueue Workload 状态
│   ├─ 查询 NetworkPolicy 配置
│   └─ 验证 Pod 状态
├─ 基础设施配置 (写入) → 使用 IaC (CDK/kubectl)
│   ├─ 配置 NetworkPolicy
│   ├─ 部署 Add-ons
│   └─ 配置 PriorityClass
├─ 自定义数据管理 → 后端自实现
│   ├─ 扫描 FSx 存储 (Checkpoint 管理)
│   ├─ 解析训练日志 (指标提取)
│   └─ 构建元数据索引
└─ AWS 原生服务 → 使用对应的 boto3 客户端
    ├─ Cost Explorer (成本追踪)
    ├─ CloudWatch (日志查询)
    └─ S3 (存储管理)
```

---

## 功能类别决策指南

### 2.1 训练任务管理

#### 训练任务 CRUD

**决策流程**:
```
需要实现训练任务 CRUD 功能
    ↓
[1] 使用 HyperPod SDK?
    ├─ YES → ✅ sagemaker-hyperpod SDK
    │         └─ API: HyperPodPytorchJob.create() / .get() / .delete()
    │         └─ 任务: T014 (创建), T036 (查询), T042 (删除)
    └─ NO  → 进入 T000-fallback 备选方案评估
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK**

**代码示例**:
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# 创建训练任务
job = HyperPodPytorchJob.create(
    name="llama3-70b-training",
    image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
    instance_type="ml.p4d.24xlarge",
    node_count=16,
    tasks_per_node=8,
    command=["torchrun", "--nproc_per_node=8", "train.py"]
)

# 查询任务状态
job = HyperPodPytorchJob.get(name="llama3-70b-training")
print(f"任务状态: {job.status}")

# 删除任务
job.delete()
```

**相关任务**: T014 (训练任务创建), T036 (训练任务查询), T042 (训练任务删除)

---

#### 实时状态查询

**决策流程**:
```
需要实时查询训练任务状态
    ↓
[1] SDK 支持实时查询?
    ├─ YES → ✅ HyperPodPytorchJob.get()
    │         └─ 返回实时状态,无需轮询
    └─ NO  → [2]

[2] boto3 支持?
    ├─ YES → ⚠️ 需要轮询 describe_training_job()
    │         └─ 注意: SageMaker 标准 API 不适用于 HyperPod
    └─ NO  → [3]

[3] kubernetes-client 查询 Pod 状态?
    └─ YES → ✅ kubectl get pytorchjob (备选方案)
              └─ 仅在 SDK 不可用时使用
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (首选), ✅ **kubernetes-client** (备选)

**代码示例**:
```python
# 首选: SDK 实时查询
job = HyperPodPytorchJob.get(name="llama3-70b-training")
print(f"状态: {job.status}, 进度: {job.progress}")

# 备选: kubernetes-client 查询
from kubernetes import client, config
config.load_kube_config()
api = client.CustomObjectsApi()

job_crd = api.get_namespaced_custom_object(
    group="kubeflow.org",
    version="v1",
    namespace="default",
    plural="pytorchjobs",
    name="llama3-70b-training"
)
print(f"状态: {job_crd['status']}")
```

**相关任务**: T036 (训练任务状态查询)

---

#### 训练 Pod 列表查询

**决策流程**:
```
需要查询训练任务的 Pod 列表
    ↓
[1] SDK 提供 list_pods() API?
    ├─ YES → ✅ job.list_pods()
    │         └─ 返回任务关联的所有 Pod
    └─ NO  → [2]

[2] kubernetes-client 查询?
    └─ YES → ✅ kubectl get pods -l job-name=...
              └─ 通过标签选择器过滤
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (首选), ✅ **kubernetes-client** (备选)

**代码示例**:
```python
# 首选: SDK
job = HyperPodPytorchJob.get(name="llama3-70b-training")
pods = job.list_pods()
for pod in pods:
    print(f"Pod: {pod.name}, 状态: {pod.status}, 节点: {pod.node}")

# 备选: kubernetes-client
from kubernetes import client, config
config.load_kube_config()
v1 = client.CoreV1Api()

pods = v1.list_namespaced_pod(
    namespace="default",
    label_selector=f"job-name=llama3-70b-training"
)
for pod in pods.items:
    print(f"Pod: {pod.metadata.name}, 状态: {pod.status.phase}")
```

**相关任务**: T036 (训练 Pod 状态监控)

---

#### 训练日志查询

**决策流程**:
```
需要查询训练任务日志
    ↓
[1] 使用场景?
    ├─ 调试场景 (实时日志) → kubectl logs (快速)
    ├─ 监控场景 (最近日志) → job.logs(tail=100) (推荐)
    └─ 历史日志 (归档查询) → CloudWatch Logs API
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (首选), ✅ **kubectl logs** (调试备选), ✅ **boto3 CloudWatch** (历史日志)

**代码示例**:
```python
# 首选: SDK 查询最近日志
job = HyperPodPytorchJob.get(name="llama3-70b-training")
logs = job.logs(tail=100)
print(logs)

# 备选1: kubectl logs (调试场景)
# kubectl logs -f llama3-70b-training-worker-0 -n default

# 备选2: CloudWatch Logs (历史日志)
import boto3
logs_client = boto3.client('logs', region_name='us-west-2')

response = logs_client.get_log_events(
    logGroupName='/aws/sagemaker/TrainingJobs',
    logStreamName='llama3-70b-training/worker-0',
    limit=100
)
for event in response['events']:
    print(event['message'])
```

**相关任务**: T036 (训练日志查询)

---

### 2.2 训练任务高级功能

#### Checkpoint 管理

**决策流程**:
```
需要管理训练检查点
    ↓
[1] SDK 提供 Checkpoint API?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ❌ SDK 不支持

[2] 实现方式?
    └─ 后端自实现:
        ├─ 用户训练脚本保存检查点到 FSx for Lustre
        ├─ 后端扫描服务定期扫描 FSx 目录
        └─ 构建元数据索引并提供查询 API
```

**推荐工具**: ✅ **后端自实现** (扫描 FSx 存储 + 元数据索引)

**实现架构**:
```
训练脚本 (用户) → 保存检查点到 FSx
    ↓
后端扫描服务 → 定期扫描 FSx 目录 (每 5 分钟)
    ↓
元数据数据库 → 存储检查点信息 (checkpoint_name, storage_path, epoch, size_bytes, created_at)
    ↓
API 层 → 提供 GET /api/v1/training-jobs/{job_id}/checkpoints
```

**代码示例**:
```python
# 后端扫描服务 (backend/src/services/checkpoint_service.py)
import os
from datetime import datetime

async def scan_checkpoints(job_id: int, checkpoint_dir: str):
    """扫描训练任务的检查点目录并生成元数据"""
    checkpoints = []

    for file in os.listdir(checkpoint_dir):
        if file.endswith('.pth') or file.endswith('.ckpt'):
            file_path = os.path.join(checkpoint_dir, file)
            size_bytes = os.path.getsize(file_path)
            epoch = extract_epoch_from_filename(file)  # 从文件名提取 epoch

            checkpoints.append({
                'job_id': job_id,
                'checkpoint_name': file,
                'storage_path': file_path,
                'epoch': epoch,
                'size_bytes': size_bytes,
                'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
            })

    # 批量插入数据库
    await db.checkpoints.bulk_insert(checkpoints)
    return checkpoints

# 用户训练脚本 (PyTorch 示例)
import torch

# 保存检查点到 FSx
checkpoint_dir = "/fsx/checkpoints/llama3-70b-training"
os.makedirs(checkpoint_dir, exist_ok=True)

checkpoint = {
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss,
}
torch.save(checkpoint, f"{checkpoint_dir}/checkpoint_epoch_{epoch}.pth")
```

**相关任务**: T044 (Checkpoint 列表查询), T045 (Checkpoint 恢复)

---

#### 训练指标采集

**决策流程**:
```
需要采集训练指标 (Loss, Accuracy 等)
    ↓
[1] SDK 提供指标 API?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ❌ SDK 不支持

[2] 实现方式?
    ├─ OpenTelemetry 集成 (推荐)
    │   ├─ 用户训练脚本集成 OpenTelemetry SDK
    │   ├─ HyperPod Observability Add-on 自动接收
    │   └─ 存储到 Prometheus 并提供查询
    └─ 解析训练日志 (备选)
        └─ 后端解析日志文件提取指标
```

**推荐工具**: ✅ **OpenTelemetry 集成** (首选), ⚠️ **日志解析** (备选)

**实现架构**:
```
用户训练脚本 → OpenTelemetry SDK 推送指标
    ↓
HyperPod Observability Add-on → OpenTelemetry Collector
    ↓
Prometheus → 存储时序指标数据
    ↓
前端 / Grafana → Prometheus API 查询并可视化
```

**代码示例**:
```python
# 用户训练脚本集成 OpenTelemetry
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# 配置 OpenTelemetry
exporter = OTLPMetricExporter(
    endpoint="hyperpod-otel-collector.hyperpod-observability:4317",
    insecure=True
)

reader = PeriodicExportingMetricReader(exporter, export_interval_millis=1000)
meter_provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(meter_provider)

# 创建指标
meter = metrics.get_meter("training-metrics")
loss_gauge = meter.create_gauge("training.loss")
accuracy_gauge = meter.create_gauge("training.accuracy")
throughput_counter = meter.create_counter("training.samples_per_second")

# 在训练循环中记录指标
for epoch in range(num_epochs):
    for step, batch in enumerate(dataloader):
        # 训练逻辑...
        loss_gauge.set(loss.item(), {"epoch": str(epoch), "step": str(step)})
        accuracy_gauge.set(accuracy, {"epoch": str(epoch)})
        throughput_counter.add(batch_size, {"epoch": str(epoch)})

# 后端查询 Prometheus 指标 (backend/src/services/metrics_service.py)
import requests

prometheus_url = "http://prometheus.hyperpod-observability:9090/api/v1/query"

def get_training_loss(job_name: str):
    query = f'training_loss{{job_name="{job_name}"}}'
    response = requests.get(prometheus_url, params={"query": query})
    return response.json()["data"]["result"]
```

**相关任务**: T038 (训练指标采集配置), T039 (指标查询 API)

---

#### Gang Scheduling

**决策流程**:
```
需要配置 Gang Scheduling (同时调度所有 Pod)
    ↓
[1] 是否需要手动配置?
    └─ NO → ✅ Training Operator 自动支持
              └─ PyTorchJob CRD 内置 Gang Scheduling 语义
```

**推荐工具**: ✅ **无需配置** (Training Operator 自动处理)

**说明**:
- HyperPod Training Operator 基于 Kubeflow Training Operator
- PyTorchJob 自动支持 Gang Scheduling 语义
- 所有 Worker Pod 必须同时调度成功,否则任务不会启动

**相关任务**: 无 (自动支持,无需实现)

---

#### 优先级调度

**决策流程**:
```
需要配置训练任务优先级
    ↓
[1] SDK 提供优先级参数?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ⚠️ SDK 不支持

[2] 实现方式?
    └─ Kueue ClusterQueue 配置:
        ├─ 后端设置 PriorityClass
        └─ Kueue Workload 自动继承优先级
```

**推荐工具**: ✅ **Kueue ClusterQueue** (通过后端设置 PriorityClass)

**实现架构**:
```
IaC (CDK/kubectl) → 创建 PriorityClass 资源
    ↓
后端创建训练任务 → 设置 priorityClassName
    ↓
Training Operator → 创建 PyTorchJob CRD
    ↓
Kueue Admission Controller → 创建 Workload 并继承优先级
    ↓
Kueue Scheduler → 按优先级调度任务
```

**代码示例**:
```yaml
# 1. IaC 阶段: 创建 PriorityClass (infrastructure/k8s/priority-classes.yaml)
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "高优先级训练任务"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: true
description: "低优先级训练任务"
```

```python
# 2. 后端创建任务时设置优先级 (backend/src/services/training_service.py)
from sagemaker.hyperpod.training import HyperPodPytorchJob

# 注意: 如果 SDK 不支持 priorityClassName 参数,需要使用 kubernetes-client
from kubernetes import client, config

config.load_kube_config()
api = client.CustomObjectsApi()

# 创建 PyTorchJob 并设置优先级
pytorchjob = {
    "apiVersion": "kubeflow.org/v1",
    "kind": "PyTorchJob",
    "metadata": {
        "name": "llama3-70b-training",
        "namespace": "default"
    },
    "spec": {
        "priorityClassName": "high-priority",  # 设置优先级
        "pytorchReplicaSpecs": {
            "Master": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "pytorch",
                            "image": "pytorch:2.1",
                            "command": ["torchrun", "train.py"]
                        }]
                    }
                }
            }
        }
    }
}

api.create_namespaced_custom_object(
    group="kubeflow.org",
    version="v1",
    namespace="default",
    plural="pytorchjobs",
    body=pytorchjob
)
```

**相关任务**: T037 (优先级调度配置)

---

#### Kueue Workload 监控

**决策流程**:
```
需要查询 Kueue Workload 状态
    ↓
[1] SDK 提供 Kueue API?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ❌ SDK 不支持

[2] kubernetes-client 可查询?
    └─ YES → ✅ kubernetes-client (只读查询)
              └─ 代码: api.get_namespaced_custom_object(group="kueue.x-k8s.io", ...)
              └─ ⚠️ 注意: 仅用于只读查询,不用于创建 Workload
```

**推荐工具**: ✅ **kubernetes-client** (只读查询)

**代码示例**:
```python
# backend/src/services/kueue_service.py
from kubernetes import client, config

config.load_kube_config()
api = client.CustomObjectsApi()

def get_workload_status(workload_name: str, namespace: str = "default"):
    """查询 Kueue Workload 状态 (只读)"""
    workload = api.get_namespaced_custom_object(
        group="kueue.x-k8s.io",
        version="v1beta1",
        namespace=namespace,
        plural="workloads",
        name=workload_name
    )

    return {
        "name": workload["metadata"]["name"],
        "status": workload.get("status", {}).get("conditions", []),
        "admitted": workload.get("status", {}).get("admission", {}).get("clusterQueue"),
        "priority": workload["spec"].get("priorityClassName"),
        "queue_position": workload.get("status", {}).get("admission", {}).get("clusterQueue")
    }

# API 路由 (backend/src/api/v1/training.py)
@router.get("/training-jobs/{job_id}/workload-status")
async def get_training_workload_status(job_id: int):
    job = await db.training_jobs.get(job_id)
    workload_name = f"{job.name}-workload"  # Kueue 自动生成的 Workload 名称
    return get_workload_status(workload_name)
```

**注意事项**:
- ⚠️ **仅用于只读查询**,不用于创建或更新 Workload
- ⚠️ Workload 的创建由 HyperPod Training Operator 自动处理
- ⚠️ 不要直接操作 Workload CRD,避免与 Operator 冲突

**相关任务**: T037 (Kueue Workload 监控)

---

### 2.3 开发空间管理

#### Space CRUD

**决策流程**:
```
需要实现开发空间 (Space) CRUD 功能
    ↓
[1] SDK 提供 Space API?
    ├─ YES → ✅ sagemaker-hyperpod SDK
    │         └─ API: Space.create() / .get() / .delete()
    └─ NO  → [2]

[2] boto3 提供等效 API?
    └─ YES → ✅ boto3 SageMaker API
              └─ API: create_space() / describe_space() / delete_space()
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (首选), ✅ **boto3 SageMaker API** (备选)

**代码示例**:
```python
# 首选: SDK
from sagemaker.hyperpod.space import Space

# 创建 JupyterLab Space
space = Space.create(
    name="user-dev-space",
    instance_type="ml.g5.xlarge",
    ide_type="jupyterlab",
    storage_size_gb=50
)

print(f"Space 已创建: {space.name}, URL: {space.studio_url}")

# 查询 Space 状态
space = Space.get(name="user-dev-space")
print(f"Space 状态: {space.status}")

# 删除 Space
space.delete()

# 备选: boto3
import boto3
sm = boto3.client('sagemaker', region_name='us-west-2')

response = sm.create_space(
    DomainId='d-xxxxx',
    SpaceName='user-dev-space',
    SpaceSettings={
        'JupyterServerAppSettings': {
            'DefaultResourceSpec': {
                'InstanceType': 'ml.g5.xlarge',
                'SageMakerImageArn': 'arn:aws:sagemaker:us-west-2:xxxxx:image/jupyter-server'
            }
        }
    }
)
```

**相关任务**: T050 (Space 创建), T051 (Space 查询), T052 (Space 删除)

---

#### Space Lifecycle Config

**决策流程**:
```
需要配置 Space Lifecycle Configuration
    ↓
[1] SDK 支持 Lifecycle Config?
    ├─ YES → ✅ 通过 lifecycle_config_arn 参数
    │         └─ 先用 boto3 创建 Lifecycle Config,再传递 ARN
    └─ NO  → 使用 boto3 直接创建
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** + **boto3** (组合使用)

**实现架构**:
```
boto3 SageMaker → 创建 Lifecycle Config 并获取 ARN
    ↓
sagemaker-hyperpod SDK → Space.create(lifecycle_config_arn=arn)
```

**代码示例**:
```python
import boto3
from sagemaker.hyperpod.space import Space

sm = boto3.client('sagemaker', region_name='us-west-2')

# 步骤 1: 创建 Lifecycle Config (boto3)
lifecycle_config = sm.create_studio_lifecycle_config(
    StudioLifecycleConfigName='dev-space-setup',
    StudioLifecycleConfigContent=base64.b64encode(b"""
#!/bin/bash
# 安装开发工具
pip install torch torchvision transformers
git config --global user.name "AI Developer"
    """.strip()).decode('utf-8'),
    StudioLifecycleConfigAppType='JupyterServer'
)

arn = lifecycle_config['StudioLifecycleConfigArn']

# 步骤 2: 创建 Space 并关联 Lifecycle Config (SDK)
space = Space.create(
    name="user-dev-space",
    instance_type="ml.g5.xlarge",
    ide_type="jupyterlab",
    lifecycle_config_arn=arn  # 传递 ARN
)
```

**相关任务**: T050 (Space 创建与 Lifecycle Config 配置)

---

### 2.4 集群管理

#### 集群资源监控

**决策流程**:
```
需要监控集群资源使用情况
    ↓
[1] 监控粒度?
    ├─ 集群级别 (总节点数, 可用节点) → SDK (Cluster.describe())
    ├─ 节点级别 (CPU/内存使用率) → Prometheus HTTP API
    └─ GPU 级别 (GPU 利用率) → Prometheus HTTP API (DCGM Exporter)
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (集群级别), ⚠️ **Prometheus** (细粒度监控)

**代码示例**:
```python
# 集群级别监控 (SDK)
from sagemaker.hyperpod.cluster import Cluster

cluster_info = Cluster.describe(cluster_name="my-hyperpod-cluster")
print(f"集群状态: {cluster_info['ClusterStatus']}")
print(f"总节点数: {sum(ig['InstanceCount'] for ig in cluster_info['InstanceGroups'])}")
print(f"实例类型: {[ig['InstanceType'] for ig in cluster_info['InstanceGroups']]}")

# 细粒度监控 (Prometheus HTTP API)
import requests

prometheus_url = "http://prometheus.hyperpod-observability:9090/api/v1/query"

# 查询 GPU 利用率
query = 'DCGM_FI_DEV_GPU_UTIL{job="dcgm-exporter"}'
response = requests.get(prometheus_url, params={"query": query})
gpu_metrics = response.json()["data"]["result"]

for metric in gpu_metrics:
    node = metric['metric']['instance']
    gpu_id = metric['metric']['gpu']
    utilization = metric['value'][1]
    print(f"节点: {node}, GPU {gpu_id} 利用率: {utilization}%")

# 查询节点内存使用率
query = 'node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100'
response = requests.get(prometheus_url, params={"query": query})
memory_metrics = response.json()["data"]["result"]

for metric in memory_metrics:
    node = metric['metric']['instance']
    memory_avail_pct = metric['value'][1]
    print(f"节点: {node}, 可用内存: {memory_avail_pct}%")
```

**相关任务**: T062 (集群资源监控)

---

#### 集群节点列表

**决策流程**:
```
需要查询集群节点列表
    ↓
[1] SDK 提供节点列表 API?
    ├─ YES → ✅ Cluster.list_nodes()
    └─ NO  → [2]

[2] boto3 提供?
    ├─ YES → ✅ list_cluster_nodes()
    └─ NO  → [3]

[3] kubernetes-client 查询?
    └─ YES → ✅ kubectl get nodes (备选)
```

**推荐工具**: ✅ **sagemaker-hyperpod SDK** (首选), ✅ **boto3** (备选), ✅ **kubernetes-client** (最后手段)

**代码示例**:
```python
# 首选: SDK
from sagemaker.hyperpod.cluster import Cluster

nodes = Cluster.list_nodes(cluster_name="my-hyperpod-cluster")
for node in nodes:
    print(f"节点: {node.name}, 状态: {node.status}, 实例类型: {node.instance_type}")

# 备选1: boto3
import boto3
sm = boto3.client('sagemaker', region_name='us-west-2')

response = sm.list_cluster_nodes(ClusterName='my-hyperpod-cluster')
for node in response['ClusterNodeSummaries']:
    print(f"节点: {node['InstanceId']}, 状态: {node['InstanceStatus']}")

# 备选2: kubernetes-client
from kubernetes import client, config
config.load_kube_config()
v1 = client.CoreV1Api()

nodes = v1.list_node()
for node in nodes.items:
    print(f"节点: {node.metadata.name}, 状态: {node.status.conditions[-1].type}")
```

**相关任务**: T062 (集群节点列表查询)

---

### 2.5 基础设施配置

#### Add-ons 配置

**决策流程**:
```
需要配置 HyperPod Add-ons (Observability, Resilience, EFA)
    ↓
[1] SDK 支持 Add-on 管理?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ⚠️ SDK 不支持

[2] 配置阶段?
    └─ IaC 阶段 → ✅ kubectl / CDK
                   └─ 在 T008d 中通过 IaC 配置
```

**推荐工具**: ✅ **kubectl / IaC (CDK)** (在 IaC 阶段配置)

**实现方式**:
```
IaC 阶段 (CDK/CloudFormation) → 创建 HyperPod 集群时配置 Add-ons
    ↓
HyperPod 控制平面 → 自动部署 Add-on 组件
    ↓
运行时验证 (T008d) → 使用 kubectl 验证 Add-on 状态
```

**代码示例**:
```yaml
# infrastructure/k8s/addons/observability.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hyperpod-observability-config
  namespace: hyperpod-observability
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'dcgm-exporter'
        static_configs:
          - targets: ['dcgm-exporter.hyperpod-observability:9400']
```

```python
# 运行时验证 (backend/tests/integration/test_addons.py)
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

def verify_observability_addon():
    """验证 Observability Add-on 部署状态"""
    pods = v1.list_namespaced_pod(namespace="hyperpod-observability")

    required_components = ["prometheus", "grafana", "otel-collector"]
    deployed_components = [pod.metadata.name for pod in pods.items]

    for component in required_components:
        assert any(component in name for name in deployed_components), \
            f"Add-on 组件 {component} 未部署"

    print("✅ Observability Add-on 验证通过")
```

**相关任务**: T008d (HyperPod Add-ons 配置与验证)

---

#### NetworkPolicy 配置

**决策流程**:
```
需要配置 Kubernetes NetworkPolicy
    ↓
[1] SDK 支持 NetworkPolicy?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ❌ SDK 不支持

[2] 配置阶段?
    ├─ IaC 阶段 → ✅ kubectl / CDK (T008f)
    └─ 验证阶段 → ✅ kubernetes-client (T008g)
```

**推荐工具**: ✅ **IaC (kubectl / CDK)** (配置), ✅ **kubernetes-client** (POC 验证/运行时监控)

**实现架构**:
```
IaC 阶段 (T008f) → kubectl apply -f network-policies.yaml
    ↓
Kubernetes API Server → 创建 NetworkPolicy 资源
    ↓
CNI Plugin (Calico/Cilium) → 应用网络隔离规则
    ↓
POC 验证 (T008g) → kubernetes-client 查询策略状态
    ↓
运行时监控 → kubernetes-client 监控策略生效情况
```

**代码示例**:
```yaml
# IaC 阶段: 配置 NetworkPolicy (infrastructure/k8s/network-policies/training-isolation.yaml)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: training-jobs-isolation
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: training-job
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: training-job  # 训练 Pod 之间可以通信
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: training-job
    - to:  # 允许访问 FSx for Lustre
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: TCP
          port: 988  # Lustre 默认端口
```

```python
# POC 验证阶段 (T008g): 验证 NetworkPolicy 生效 (backend/tests/integration/test_network_policy.py)
from kubernetes import client, config

config.load_kube_config()
api = client.NetworkingV1Api()

def verify_network_policy(name: str, namespace: str = "default"):
    """验证 NetworkPolicy 配置"""
    policy = api.read_namespaced_network_policy(name=name, namespace=namespace)

    print(f"NetworkPolicy: {policy.metadata.name}")
    print(f"Pod Selector: {policy.spec.pod_selector}")
    print(f"Ingress Rules: {len(policy.spec.ingress)} 条")
    print(f"Egress Rules: {len(policy.spec.egress)} 条")

    # 验证策略存在
    assert policy.metadata.name == name, "NetworkPolicy 未正确创建"
    print("✅ NetworkPolicy 验证通过")

# 运行时监控 (backend/src/services/network_policy_service.py)
def list_network_policies(namespace: str = "default"):
    """查询所有 NetworkPolicy (只读)"""
    policies = api.list_namespaced_network_policy(namespace=namespace)
    return [
        {
            "name": policy.metadata.name,
            "pod_selector": policy.spec.pod_selector,
            "ingress_rules": len(policy.spec.ingress or []),
            "egress_rules": len(policy.spec.egress or [])
        }
        for policy in policies.items
    ]
```

**注意事项**:
- ⚠️ NetworkPolicy 配置在 IaC 阶段完成 (`infrastructure/k8s/network-policies/`)
- ⚠️ kubernetes-client 仅用于 POC 验证 (T008g) 和运行时状态监控,不用于动态创建策略
- ⚠️ 不要在运行时动态修改 NetworkPolicy,避免破坏网络隔离

**相关任务**: T008f (NetworkPolicy 配置), T008g (NetworkPolicy 验证)

---

#### Spot 实例配置

**决策流程**:
```
需要配置 Spot 实例组
    ↓
[1] SDK 支持任务级 Spot 配置?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ⚠️ 集群级配置

[2] 配置阶段?
    └─ 集群创建时 → ✅ boto3 / CDK
                     └─ 在 T008e 中配置 Spot 实例组
```

**推荐工具**: ✅ **boto3 / CDK** (集群创建时配置 Spot 实例组)

**实现架构**:
```
IaC 阶段 (CDK/boto3) → 创建 HyperPod 集群时配置 Spot 实例组
    ↓
HyperPod 控制平面 → 自动管理 Spot 实例生命周期
    ↓
Spot 实例中断 → HyperPod 自动替换节点
    ↓
训练任务 → 通过 Checkpoint 恢复继续训练
```

**代码示例**:
```python
# IaC 阶段: 配置 Spot 实例组 (infrastructure/cdk/hyperpod_cluster.py)
import boto3

sm = boto3.client('sagemaker', region_name='us-west-2')

response = sm.create_cluster(
    ClusterName='my-hyperpod-cluster',
    InstanceGroups=[
        {
            'InstanceGroupName': 'on-demand-workers',
            'InstanceType': 'ml.p4d.24xlarge',
            'InstanceCount': 8,
            'LifeCycleConfig': {
                'SourceS3Uri': 's3://my-bucket/lifecycle-scripts/',
                'OnCreate': 'setup.sh'
            }
        },
        {
            'InstanceGroupName': 'spot-workers',  # Spot 实例组
            'InstanceType': 'ml.p4d.24xlarge',
            'InstanceCount': 16,
            'InstanceStorageConfigs': [{
                'EbsVolumeConfig': {
                    'VolumeSizeInGB': 500
                }
            }],
            'OnStartDeepHealthChecks': ['InstanceConnectivity', 'InstanceStress'],
            'ThreadsPerCore': 1,
            'LifeCycleConfig': {
                'SourceS3Uri': 's3://my-bucket/lifecycle-scripts/',
                'OnCreate': 'setup.sh'
            }
            # 注意: Spot 实例通过 Auto Scaling Group 配置,不在 CreateCluster API 中直接指定
        }
    ],
    VpcConfig={
        'SecurityGroupIds': ['sg-xxxxx'],
        'Subnets': ['subnet-xxxxx', 'subnet-yyyyy']
    }
)
```

**Spot 实例配置注意事项**:
1. ⚠️ Spot 实例在集群创建时通过 Auto Scaling Group 配置
2. ⚠️ HyperPod 自动管理 Spot 实例中断和替换
3. ⚠️ 训练任务需要实现 Checkpoint 恢复逻辑

**相关任务**: T008e (Spot 实例配置)

---

### 2.6 成本与模型管理

#### 成本追踪

**决策流程**:
```
需要统计训练任务成本
    ↓
[1] SDK 提供成本统计 API?
    ├─ YES → 使用 SDK
    └─ NO  → [2] ❌ SDK 不支持

[2] boto3 提供成本 API?
    └─ YES → ✅ boto3 Cost Explorer API
              └─ API: get_cost_and_usage()
```

**推荐工具**: ✅ **boto3 Cost Explorer API**

**代码示例**:
```python
# backend/src/services/cost_tracking_service.py
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-west-2')

def get_training_job_cost(start_date: str, end_date: str, job_tags: dict):
    """查询训练任务成本 (通过资源标签过滤)"""
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        Filter={
            'Tags': {
                'Key': 'training-job-id',
                'Values': [job_tags['training-job-id']]
            }
        }
    )

    total_cost = sum(
        float(result['Total']['UnblendedCost']['Amount'])
        for result in response['ResultsByTime']
    )

    return {
        'total_cost_usd': total_cost,
        'start_date': start_date,
        'end_date': end_date,
        'breakdown': response['ResultsByTime']
    }

# API 路由 (backend/src/api/v1/training.py)
from datetime import datetime, timedelta

@router.get("/training-jobs/{job_id}/cost")
async def get_training_job_cost_api(job_id: int):
    job = await db.training_jobs.get(job_id)

    start_date = job.created_at.strftime('%Y-%m-%d')
    end_date = (job.completed_at or datetime.now()).strftime('%Y-%m-%d')

    cost_data = get_training_job_cost(
        start_date=start_date,
        end_date=end_date,
        job_tags={'training-job-id': str(job_id)}
    )

    return cost_data
```

**成本追踪注意事项**:
1. ⚠️ 训练任务需要打上成本标签 (Tag: `training-job-id`)
2. ⚠️ Cost Explorer API 有 24 小时延迟,实时成本无法查询
3. ⚠️ 需要配置 Cost Allocation Tags 才能按训练任务分组

**相关任务**: T063 (成本追踪与查询)

---

#### 模型注册 (Model Registry)

**决策流程**:
```
需要将训练完成的模型注册到 SageMaker Model Registry
    ↓
[1] 这是 HyperPod SDK 范围吗?
    └─ NO → [2] ❌ 非 HyperPod SDK 范围

[2] boto3 提供 Model Registry API?
    └─ YES → ✅ boto3 SageMaker API
              └─ API: create_model_package()
```

**推荐工具**: ✅ **boto3 SageMaker API**

**代码示例**:
```python
# backend/src/services/model_registry_service.py
import boto3

sm = boto3.client('sagemaker', region_name='us-west-2')

def register_model(
    model_name: str,
    model_uri: str,
    training_job_id: str,
    inference_image_uri: str
):
    """注册训练完成的模型到 SageMaker Model Registry"""

    # 创建模型包组 (如果不存在)
    try:
        sm.create_model_package_group(
            ModelPackageGroupName=model_name,
            ModelPackageGroupDescription=f"Models for {model_name}"
        )
    except sm.exceptions.ResourceInUse:
        pass  # 模型包组已存在

    # 注册模型版本
    response = sm.create_model_package(
        ModelPackageGroupName=model_name,
        ModelPackageDescription=f"Model trained by job {training_job_id}",
        InferenceSpecification={
            'Containers': [{
                'Image': inference_image_uri,
                'ModelDataUrl': model_uri  # S3 URI (s3://bucket/model.tar.gz)
            }],
            'SupportedContentTypes': ['application/json'],
            'SupportedResponseMIMETypes': ['application/json'],
            'SupportedRealtimeInferenceInstanceTypes': [
                'ml.g5.xlarge',
                'ml.g5.2xlarge',
                'ml.p4d.24xlarge'
            ]
        },
        ModelApprovalStatus='PendingManualApproval'  # 需要手动审批
    )

    return response['ModelPackageArn']

# API 路由 (backend/src/api/v1/models.py)
@router.post("/training-jobs/{job_id}/register-model")
async def register_training_model(
    job_id: int,
    model_name: str,
    model_uri: str,
    inference_image_uri: str
):
    job = await db.training_jobs.get(job_id)

    if job.status != 'Completed':
        raise HTTPException(status_code=400, detail="训练任务未完成,无法注册模型")

    model_package_arn = register_model(
        model_name=model_name,
        model_uri=model_uri,
        training_job_id=str(job_id),
        inference_image_uri=inference_image_uri
    )

    # 更新数据库记录
    await db.training_jobs.update(job_id, {'model_package_arn': model_package_arn})

    return {
        'model_package_arn': model_package_arn,
        'status': 'PendingManualApproval'
    }
```

**相关任务**: T064 (模型注册到 Model Registry)

---

## 常见错误与解决方案

### 错误 1: boto3 API 冲突

**问题**: 使用 `boto3.client('sagemaker').create_training_job()` 创建 HyperPod 训练任务失败

**原因**: SageMaker 标准训练任务 API 不适用于 HyperPod,必须使用 `sagemaker-hyperpod` SDK

**解决方案**:
```python
# ❌ 错误: 使用 boto3 SageMaker API
import boto3
sm = boto3.client('sagemaker')
sm.create_training_job(...)  # 不支持 HyperPod

# ✅ 正确: 使用 sagemaker-hyperpod SDK
from sagemaker.hyperpod.training import HyperPodPytorchJob
job = HyperPodPytorchJob.create(...)
```

---

### 错误 2: kubectl 权限不足

**问题**: 使用 `kubernetes-client` 查询 Kueue Workload 失败,提示权限不足

**原因**: 后端服务的 Kubernetes ServiceAccount 缺少 RBAC 权限

**解决方案**:
```yaml
# infrastructure/k8s/rbac/backend-service-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-service-role
  namespace: default
rules:
  - apiGroups: ["kueue.x-k8s.io"]
    resources: ["workloads"]
    verbs: ["get", "list", "watch"]  # 只读权限
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-service-binding
  namespace: default
subjects:
  - kind: ServiceAccount
    name: backend-service
    namespace: default
roleRef:
  kind: Role
  name: backend-service-role
  apiGroup: rbac.authorization.k8s.io
```

---

### 错误 3: OpenTelemetry 指标丢失

**问题**: 用户训练脚本集成 OpenTelemetry 后,指标未在 Prometheus 中显示

**原因**: HyperPod Observability Add-on 未正确配置或 OpenTelemetry Collector 端点错误

**排查步骤**:
1. 验证 Observability Add-on 部署状态:
   ```bash
   kubectl get pods -n hyperpod-observability
   ```
2. 验证 OpenTelemetry Collector 服务:
   ```bash
   kubectl get svc -n hyperpod-observability | grep otel-collector
   ```
3. 检查训练脚本的 OpenTelemetry 端点配置:
   ```python
   exporter = OTLPMetricExporter(
       endpoint="hyperpod-otel-collector.hyperpod-observability:4317",  # 确保端点正确
       insecure=True
   )
   ```

---

### 错误 4: NetworkPolicy 阻止训练任务通信

**问题**: 训练任务启动后,Worker Pod 之间无法通信,导致分布式训练失败

**原因**: NetworkPolicy 配置过于严格,阻止了训练 Pod 之间的通信

**解决方案**:
```yaml
# 确保 NetworkPolicy 允许训练 Pod 之间通信
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: training-jobs-isolation
spec:
  podSelector:
    matchLabels:
      app: training-job
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: training-job  # 允许同类 Pod 通信
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: training-job  # 允许同类 Pod 通信
```

---

## 架构约束检查清单

在选择技术方案时,必须遵循以下架构约束:

### 1. 技术栈约束

- ✅ **后端**: 必须使用 Python 3.11 + FastAPI 0.109+
- ✅ **数据库**: 必须使用 Aurora MySQL 3.04.x (兼容 MySQL 8.0.28)
- ✅ **前端**: 必须使用 React 18 + TypeScript 5.3+ + AWS Cloudscape Design System
- ✅ **存储**: FSx for Lustre (训练数据) + S3 (模型制品)
- ✅ **SDK 优先级**: sagemaker-hyperpod SDK > boto3 > AWS CLI > kubectl

### 2. 安全约束

- ✅ **最小权限**: 后端服务只能拥有必要的 Kubernetes RBAC 权限
- ✅ **网络隔离**: 训练 Pod 必须通过 NetworkPolicy 隔离
- ✅ **数据加密**: FSx for Lustre 和 Aurora MySQL 必须启用加密
- ✅ **IAM 角色**: 所有 AWS 服务访问必须通过 IAM Role,不使用 Access Key

### 3. 性能约束

- ✅ **FSx 吞吐量**: ≥5GB/s (支持大规模分布式训练)
- ✅ **数据库连接池**: 使用 aiomysql 异步连接池,避免连接耗尽
- ✅ **API 响应时间**: 训练任务查询 API <200ms, 日志查询 API <500ms

### 4. 架构原则

- ✅ **不直接操作 Kubernetes CRD**: 训练任务通过 SDK 创建,不直接操作 PyTorchJob CRD
- ✅ **不绕过 Training Operator**: 不使用 kubectl 创建训练任务,避免与 Operator 冲突
- ✅ **只读查询 Kueue**: 仅查询 Kueue Workload 状态,不创建或修改 Workload

---

## 参考文档

- **HyperPod SDK 方法签名**: [docs/hyperpod-sdk-reference.md](./hyperpod-sdk-reference.md)
- **HyperPod SDK 能力矩阵**: [docs/hyperpod-sdk-capability-matrix.md](./hyperpod-sdk-capability-matrix.md)
- **HyperPod SDK 官方文档**: https://sagemaker-hyperpod-cli.readthedocs.io/
- **boto3 SageMaker 文档**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html
- **Kubernetes Python Client**: https://github.com/kubernetes-client/python
- **OpenTelemetry Python**: https://opentelemetry.io/docs/instrumentation/python/
- **Kueue 官方文档**: https://kueue.sigs.k8s.io/

---

**文档版本**: v1.0
**最后更新**: 2026-01-08
**审核状态**: Phase 0 技术验证完成
