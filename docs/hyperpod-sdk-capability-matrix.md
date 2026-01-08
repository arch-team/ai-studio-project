# HyperPod SDK 能力矩阵

**版本**: Phase 0 技术验证
**日期**: 2026-01-08
**目标**: 为每个平台功能确定最佳实现工具,建立开发时的技术选型指导框架
**研究来源**: [research.md](../specs/001-ai-training-platform/research.md), [plan.md](../specs/001-ai-training-platform/plan.md)

---

## 概述

本文档填充 plan.md 中定义的功能-工具矩阵,为每个功能注明最佳实现工具和选型依据,指导开发时的技术选型决策。

**工具分类**:
- **sagemaker-hyperpod SDK**: 官方 Python SDK (最高优先级)
- **boto3 SageMaker API**: AWS SDK for Python (次选)
- **AWS CLI**: 命令行工具 (第三选)
- **kubectl / kubernetes-client**: Kubernetes 客户端 (最后手段)

---

## SDK 能力矩阵

| 功能类别 | sagemaker-hyperpod SDK | boto3 SageMaker API | AWS CLI | kubectl / k8s-client | 推荐工具 |
|---------|------------------------|---------------------|---------|----------------------|---------|
| **训练任务 CRUD** | ✅ 首选<br>`HyperPodPytorchJob.create()` | ✅ 可用<br>`create_training_job()` (SageMaker 标准 API,不适用于 HyperPod) | ⚠️ 有限<br>`hyp create training-job` | ❌ 不推荐<br>直接操作 CRD 复杂 | ✅ **sagemaker-hyperpod SDK** |
| **实时状态查询** | ✅ 首选<br>`HyperPodPytorchJob.get()` | ⚠️ 需轮询<br>`describe_training_job()` (不适用于 HyperPod) | ❌ 不支持实时 | ✅ 备选<br>`kubectl get pytorchjob` | ✅ **sagemaker-hyperpod SDK** |
| **训练 Pod 列表** | ✅ 首选<br>`job.list_pods()` | ❌ 不支持 | ❌ 不支持 | ✅ 备选<br>`kubectl get pods -l job-name=...` | ✅ **sagemaker-hyperpod SDK** |
| **训练日志查询** | ✅ 首选<br>`job.logs(tail=100)` | ✅ 可用<br>`cloudwatch:GetLogEvents` | ✅ 可用<br>`aws logs tail` | ✅ 可用<br>`kubectl logs` | ✅ **sagemaker-hyperpod SDK** (首选)<br>✅ **kubectl logs** (备选,调试场景) |
| **Checkpoint 管理** | ❌ 不支持<br>SDK 无检查点 API | ❌ 不支持 | ❌ 不支持 | ⚠️ 底层操作<br>需扫描 FSx 存储 | ✅ **后端自实现**<br>扫描 FSx/S3 存储并构建元数据索引 |
| **训练指标采集** | ❌ 不支持<br>SDK 无指标 API | ❌ 不支持 | ❌ 不支持 | ⚠️ 需集成<br>OpenTelemetry/Prometheus | ✅ **OpenTelemetry 集成**<br>用户训练脚本集成 OpenTelemetry SDK |
| **Gang Scheduling** | ✅ 自动支持<br>Training Operator 内置 | ❌ 不适用 | ❌ 不适用 | ✅ 自动支持<br>PyTorchJob CRD 内置 | ✅ **无需配置**<br>Training Operator 自动处理 |
| **优先级调度** | ⚠️ 有限支持<br>SDK 无优先级参数 | ❌ 不支持 | ❌ 不支持 | ✅ 备选<br>设置 PriorityClass | ✅ **Kueue ClusterQueue**<br>通过后端设置 PriorityClass + Kueue Workload 配置 |
| **Kueue Workload 监控** | ❌ 不支持<br>SDK 未提供 Kueue API | ❌ 不支持 | ❌ 不支持 | ✅ 首选<br>`kubectl get workload` | ✅ **kubernetes-client** (只读查询)|
| **Space CRUD** | ✅ 首选<br>`Space.create()` | ✅ 可用<br>`create_space()` (SageMaker API) | ⚠️ 有限<br>`hyp create space` | ❌ 不适用 | ✅ **sagemaker-hyperpod SDK** |
| **Space 状态查询** | ✅ 首选<br>`Space.get()` | ✅ 可用<br>`describe_space()` | ⚠️ 有限<br>`hyp get space` | ❌ 不适用 | ✅ **sagemaker-hyperpod SDK** |
| **Space Lifecycle Config** | ✅ 支持<br>`lifecycle_config_arn` 参数 | ✅ 可用<br>`create_studio_lifecycle_config()` | ⚠️ 有限 | ❌ 不适用 | ✅ **sagemaker-hyperpod SDK**<br>Lifecycle Config 通过 boto3 创建后传递 ARN |
| **集群资源监控** | ✅ 支持<br>`Cluster.describe()` | ⚠️ 部分支持<br>`describe_cluster()` (仅集群级别) | ❌ 不支持实时 | ✅ 备选<br>`kubectl top nodes` | ✅ **sagemaker-hyperpod SDK**<br>⚠️ **Prometheus** (细粒度监控) |
| **集群节点列表** | ✅ 首选<br>`Cluster.list_nodes()` | ✅ 可用<br>`list_cluster_nodes()` | ⚠️ 有限 | ✅ 备选<br>`kubectl get nodes` | ✅ **sagemaker-hyperpod SDK** |
| **Add-ons 配置** | ⚠️ 有限<br>SDK 不支持 Add-on 管理 | ❌ 不支持 | ❌ 不支持 | ✅ 首选<br>`kubectl apply -f addon.yaml` | ✅ **kubectl / IaC (CDK)**<br>Add-ons 在 IaC 阶段配置 |
| **NetworkPolicy 配置** | ❌ 不支持 | ❌ 不支持 | ❌ 不支持 | ✅ 首选<br>`kubectl apply -f netpol.yaml` | ✅ **IaC (kubectl / CDK)**<br>NetworkPolicy 在 IaC 阶段配置 |
| **NetworkPolicy 验证** | ❌ 不支持 | ❌ 不支持 | ❌ 不支持 | ✅ 首选<br>`kubectl get networkpolicy` | ✅ **kubernetes-client** (POC 验证/运行时监控) |
| **Spot 实例配置** | ⚠️ 集群级配置<br>SDK 无任务级 Spot 配置 | ✅ 可用<br>`create_cluster()` 时配置 | ⚠️ 有限<br>`hyp create cluster-stack` | ❌ 不适用 | ✅ **boto3 / CDK**<br>集群创建时配置 Spot 实例组 |
| **成本追踪** | ❌ 不支持 | ✅ 首选<br>`cost_explorer:GetCostAndUsage` | ✅ 可用<br>`aws ce get-cost-and-usage` | ❌ 不适用 | ✅ **boto3 Cost Explorer API** |
| **模型注册 (Model Registry)** | ❌ 不支持<br>非 HyperPod SDK 范围 | ✅ 首选<br>`create_model_package()` | ✅ 可用<br>`aws sagemaker create-model-package` | ❌ 不适用 | ✅ **boto3 SageMaker API** |

---

## 符号说明

| 符号 | 说明 |
|------|------|
| ✅ 首选 | 功能完整、类型安全、文档齐全,优先使用 |
| ✅ 可用 | 功能可实现但需额外封装 |
| ⚠️ 有限/部分支持 | 仅支持部分场景或需复杂组合 |
| ❌ 不支持/不推荐 | 功能缺失或违反架构原则 |

---

## 详细功能说明

### 1. 训练任务 CRUD

**最佳工具**: sagemaker-hyperpod SDK

**推荐原因**:
- ✅ 完整的训练任务生命周期管理 API
- ✅ 类型安全 (TypeScript 类型定义)
- ✅ 自动注入分布式训练环境变量
- ✅ 官方支持和文档完善

**代码示例**:
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# 创建训练任务
job = HyperPodPytorchJob.create(
    name="my-training-job",
    image_uri="123456.dkr.ecr.us-west-2.amazonaws.com/pytorch:2.1",
    instance_type="ml.p4d.24xlarge",
    node_count=16,
    tasks_per_node=8,
    command=["torchrun", "--nproc_per_node=8", "train.py"]
)

# 查询任务状态
job = HyperPodPytorchJob.get(name="my-training-job")
print(f"任务状态: {job.status}")

# 删除任务
job.delete()
```

**备选方案**: 无 (boto3 不支持 HyperPod 训练任务管理)

---

### 2. Checkpoint 管理

**最佳工具**: 后端自实现 (扫描 FSx/S3 存储)

**原因**: ❌ SDK 不提供检查点 API

**实现方式**:
1. **用户训练脚本**: 保存检查点到共享存储 (FSx for Lustre)
2. **后端扫描服务**: 定期扫描 FSx 目录并构建元数据索引
3. **API 层**: 提供 `GET /api/v1/training-jobs/{job_id}/checkpoints` 查询接口

**代码示例**:
```python
# 后端扫描服务 (backend/src/services/checkpoint_service.py)
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

### 3. 训练指标采集

**最佳工具**: OpenTelemetry 集成

**原因**: ❌ SDK 不提供训练指标 API (Loss, Accuracy 等)

**实现方式**:
1. **用户训练脚本**: 集成 OpenTelemetry SDK 推送指标
2. **HyperPod Observability Add-on**: 自动接收并存储到 Prometheus
3. **前端**: 通过 Prometheus API 或 Grafana 查询指标

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

# 在训练循环中记录指标
for epoch in range(num_epochs):
    for step, batch in enumerate(dataloader):
        # 训练逻辑...
        loss_gauge.set(loss.item(), {"epoch": str(epoch)})
        accuracy_gauge.set(accuracy, {"epoch": str(epoch)})
```

**备选方案**: 解析训练日志提取指标 (适用于用户不使用 OpenTelemetry 的情况)

---

### 4. Kueue Workload 监控

**最佳工具**: kubernetes-client (只读查询)

**原因**: ❌ SDK 未提供 Kueue API

**使用场景**: 查询训练任务的 Kueue Workload 状态和优先级

**代码示例**:
```python
# backend/src/services/kueue_service.py
from kubernetes import client, config

config.load_kube_config()
api = client.CustomObjectsApi()

def get_workload_status(workload_name: str, namespace: str = "default"):
    """查询 Kueue Workload 状态"""
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
        "priority": workload["spec"].get("priorityClassName")
    }
```

**注意事项**:
- ⚠️ 仅用于只读状态查询,不用于创建或更新 Workload
- ⚠️ Workload 的创建由 HyperPod Training Operator 自动处理

---

### 5. NetworkPolicy 配置与验证

**最佳工具**: IaC (kubectl / CDK) 配置,kubernetes-client 验证

**原因**: ❌ SDK 不支持 NetworkPolicy 管理

**使用场景**:
- **配置阶段**: 在 IaC (T008f) 中使用 kubectl 或 CDK 创建 NetworkPolicy
- **验证阶段**: 在 POC (T008g) 中使用 kubernetes-client 验证策略生效
- **运行时监控**: 在监控服务中使用 kubernetes-client 查询 NetworkPolicy 状态

**代码示例**:
```python
# POC 验证 (backend/tests/integration/test_network_policy.py)
from kubernetes import client, config

config.load_kube_config()
api = client.NetworkingV1Api()

def verify_network_policy(name: str, namespace: str = "default"):
    """验证 NetworkPolicy 配置"""
    policy = api.read_namespaced_network_policy(name=name, namespace=namespace)

    print(f"NetworkPolicy: {policy.metadata.name}")
    print(f"Pod Selector: {policy.spec.pod_selector}")
    print(f"Ingress Rules: {policy.spec.ingress}")
    print(f"Egress Rules: {policy.spec.egress}")
```

**注意事项**:
- ⚠️ NetworkPolicy 配置在 IaC 阶段完成 (`infrastructure/k8s/network-policies/`)
- ⚠️ kubernetes-client 仅用于 POC 验证和运行时状态监控,不用于动态创建策略

---

### 6. Space (开发空间) 管理

**最佳工具**: sagemaker-hyperpod SDK

**推荐原因**:
- ✅ 完整的 Space CRUD API
- ✅ 支持 JupyterLab 和 VS Code IDE
- ✅ 支持 Lifecycle Configuration

**代码示例**:
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

# 查询 Space 状态
space = Space.get(name="user-dev-space")
print(f"Space 状态: {space.status}")

# 删除 Space
space.delete()
```

**备选方案**: boto3 SageMaker API (`create_space()`, `describe_space()`, `delete_space()`)

---

### 7. 集群资源监控

**最佳工具**: sagemaker-hyperpod SDK (集群级) + Prometheus (细粒度)

**推荐原因**:
- ✅ SDK 提供集群级别的资源信息 (总节点数、可用节点数、实例类型)
- ✅ Prometheus 提供细粒度监控 (GPU 利用率、内存使用率、Pod 状态)

**代码示例**:
```python
# 集群级别监控 (SDK)
from sagemaker.hyperpod.cluster import Cluster

cluster_info = Cluster.describe(cluster_name="my-hyperpod-cluster")
print(f"集群状态: {cluster_info['ClusterStatus']}")
print(f"总节点数: {sum(ig['InstanceCount'] for ig in cluster_info['InstanceGroups'])}")

# 细粒度监控 (Prometheus)
# 后端通过 Prometheus HTTP API 查询指标
import requests

prometheus_url = "http://prometheus.hyperpod-observability:9090/api/v1/query"
query = 'DCGM_FI_DEV_GPU_UTIL{job="dcgm-exporter"}'
response = requests.get(prometheus_url, params={"query": query})
gpu_utilization = response.json()["data"]["result"]

for metric in gpu_utilization:
    print(f"节点: {metric['metric']['instance']}, GPU 利用率: {metric['value'][1]}%")
```

---

### 8. 成本追踪

**最佳工具**: boto3 Cost Explorer API

**原因**: ❌ SDK 不提供成本统计 API

**代码示例**:
```python
# backend/src/services/cost_tracking_service.py
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-west-2')

def get_training_job_cost(start_date: str, end_date: str, job_tags: dict):
    """查询训练任务成本"""
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

    return total_cost
```

---

### 9. 模型注册 (Model Registry)

**最佳工具**: boto3 SageMaker API

**原因**: ❌ 非 HyperPod SDK 范围

**代码示例**:
```python
# backend/src/services/model_registry_service.py
import boto3

sm = boto3.client('sagemaker', region_name='us-west-2')

def register_model(model_name: str, model_uri: str, training_job_id: str):
    """注册训练完成的模型到 SageMaker Model Registry"""
    response = sm.create_model_package(
        ModelPackageGroupName=model_name,
        ModelPackageDescription=f"Model trained by job {training_job_id}",
        InferenceSpecification={
            'Containers': [{
                'Image': '763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference:2.1-gpu-py310',
                'ModelDataUrl': model_uri
            }],
            'SupportedContentTypes': ['application/json'],
            'SupportedResponseMIMETypes': ['application/json']
        }
    )

    return response['ModelPackageArn']
```

---

## 技术选型决策树

### 训练任务管理

```
需要实现训练任务 CRUD 功能
    ↓
[1] HyperPod SDK 提供 HyperPodPytorchJob API?
    ├─ YES → 使用 SDK (T014, T036)
    │         └─ 代码: HyperPodPytorchJob.create()
    └─ NO  → 进入备选方案评估 (T000-fallback)
```

### 集群管理

```
需要查询集群信息
    ↓
[1] HyperPod SDK 提供 Cluster API?
    ├─ YES → 使用 SDK (集群级别查询)
    │         └─ 代码: Cluster.describe()
    └─ NO  → [2]

[2] boto3 提供等效 API?
    ├─ YES → 使用 boto3 (仅集群管理,不适用于训练任务)
    │         └─ 代码: boto3.client('sagemaker').describe_cluster()
    └─ NO  → [3]

[3] 需要细粒度监控 (GPU/节点级别)?
    ├─ YES → 使用 Prometheus HTTP API (T062)
    │         └─ 查询 DCGM_FI_DEV_GPU_UTIL 指标
    └─ NO  → 评估 kubectl (最后手段)
```

### Kueue Workload 监控

```
需要查询 Kueue Workload 状态
    ↓
[1] HyperPod SDK 提供 Kueue API?
    ├─ YES → 使用 SDK
    └─ NO  → [2]

[2] kubernetes-client 可查询 Workload CRD?
    ├─ YES → 使用 kubernetes-client (只读查询,T037)
    │         └─ 代码: api.get_namespaced_custom_object(group="kueue.x-k8s.io", ...)
    │         └─ ⚠️ 注意: 仅用于只读查询,不用于创建 Workload
    └─ NO  → 无法实现 (上报缺口)
```

---

## 开发时快速参考

### 需要实现训练任务提交?
→ ✅ **使用 sagemaker-hyperpod SDK** (`HyperPodPytorchJob.create()`)

### 需要查询训练任务状态?
→ ✅ **使用 sagemaker-hyperpod SDK** (`HyperPodPytorchJob.get()`)

### 需要查询训练任务的检查点列表?
→ ✅ **后端自实现** (扫描 FSx 存储并构建元数据索引)

### 需要采集训练指标 (Loss/Accuracy)?
→ ✅ **OpenTelemetry 集成** (用户训练脚本集成 OpenTelemetry SDK)

### 需要查询 Kueue Workload 状态?
→ ✅ **kubernetes-client** (只读查询,`kubectl get workload`)

### 需要配置 NetworkPolicy?
→ ✅ **IaC (kubectl / CDK)** (在 T008f 中配置,在 T008g 中验证)

### 需要创建开发空间 (Space)?
→ ✅ **sagemaker-hyperpod SDK** (`Space.create()`)

### 需要查询集群资源使用情况?
→ ✅ **sagemaker-hyperpod SDK** (集群级别) + **Prometheus API** (细粒度)

### 需要查询训练任务成本?
→ ✅ **boto3 Cost Explorer API** (`get_cost_and_usage()`)

### 需要注册模型到 Model Registry?
→ ✅ **boto3 SageMaker API** (`create_model_package()`)

---

## 参考文档

- **HyperPod SDK 文档**: https://sagemaker-hyperpod-cli.readthedocs.io/
- **boto3 SageMaker 文档**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html
- **Kubernetes Python Client**: https://github.com/kubernetes-client/python
- **OpenTelemetry Python**: https://opentelemetry.io/docs/instrumentation/python/

---

**文档版本**: v1.0
**最后更新**: 2026-01-08
**审核状态**: Phase 0 技术验证完成
