# HyperPod SDK 功能缺口分析

**版本**: Phase 0 技术验证
**日期**: 2026-01-08
**目标**: 识别 HyperPod SDK 的功能缺口,提供备选方案,评估对开发路线的影响
**研究来源**: [research.md](../specs/001-ai-training-platform/research.md), [hyperpod-sdk-capability-matrix.md](./hyperpod-sdk-capability-matrix.md)

---

## 概述

本文档系统分析 HyperPod SDK 的功能缺口,为每个缺口提供备选方案,并评估对项目开发路线的影响程度。

**缺口分类**:
- **关键缺口 (🔴 Critical)**: 缺失的核心功能,需要立即实现备选方案
- **重要缺口 (🟡 Important)**: 影响用户体验或开发效率,需要优先处理
- **次要缺口 (🟢 Minor)**: 功能完整性问题,可以延后处理

---

## 功能缺口汇总

| 功能缺口 | 严重程度 | 备选方案 | 开发工作量 | 任务 ID | 风险等级 |
|---------|---------|---------|-----------|---------|---------|
| Checkpoint 管理 API | 🔴 Critical | 后端扫描 FSx 存储 + 元数据索引 | 中等 (5-7 天) | T044, T045 | 中 |
| 训练指标采集 API | 🔴 Critical | OpenTelemetry 集成 | 中等 (3-5 天) | T038, T039 | 中 |
| Kueue Workload 监控 API | 🟡 Important | kubernetes-client 只读查询 | 低 (1-2 天) | T037 | 低 |
| NetworkPolicy 配置 API | 🟡 Important | IaC (kubectl/CDK) 配置 | 低 (1-2 天) | T008f, T008g | 低 |
| 任务级优先级调度参数 | 🟡 Important | 后端设置 PriorityClass + Kueue | 中等 (3-4 天) | T037 | 中 |
| Add-ons 配置 API | 🟢 Minor | IaC (kubectl/CDK) 配置 | 低 (1 天) | T008d | 低 |
| 集群级 Spot 实例配置 | 🟢 Minor | boto3 / CDK 集群创建时配置 | 低 (1-2 天) | T008e | 低 |
| 成本统计 API | 🟢 Minor | boto3 Cost Explorer API | 低 (2-3 天) | T063 | 低 |
| Model Registry 集成 | 🟢 Minor | boto3 SageMaker API | 低 (2-3 天) | T064 | 低 |

**总体评估**:
- ✅ **核心训练任务管理功能完整**: SDK 支持训练任务 CRUD、状态查询、日志查询、Pod 列表
- ⚠️ **高级功能需要自实现**: Checkpoint 管理、训练指标采集需要后端自实现
- ✅ **开发路线可行**: 所有缺口都有明确的备选方案,不影响项目整体进度

---

## 关键缺口 (🔴 Critical)

### 1. Checkpoint 管理 API 缺失

**缺口描述**: SDK 不提供训练检查点的查询、列表、恢复 API

**影响分析**:
- ❌ 无法查询训练任务的检查点列表
- ❌ 无法获取检查点的元数据 (epoch, size, created_at)
- ❌ 无法通过 API 恢复训练任务到指定检查点

**备选方案**: 后端扫描 FSx 存储并构建元数据索引

**实现架构**:
```
用户训练脚本 (PyTorch) → 保存检查点到 FSx for Lustre
    ├─ 路径: /fsx/checkpoints/{job_name}/checkpoint_epoch_{epoch}.pth
    └─ 元数据: epoch, model_state_dict, optimizer_state_dict, loss
        ↓
后端扫描服务 (定期任务,每 5 分钟)
    ├─ 扫描 FSx 目录: /fsx/checkpoints/{job_name}/
    ├─ 提取文件元数据: size_bytes, created_at
    └─ 解析文件名提取 epoch
        ↓
元数据数据库 (Aurora MySQL)
    └─ 表: checkpoints
        ├─ checkpoint_id (PK)
        ├─ training_job_id (FK)
        ├─ checkpoint_name (VARCHAR)
        ├─ storage_path (VARCHAR)
        ├─ epoch (INT)
        ├─ size_bytes (BIGINT)
        └─ created_at (DATETIME)
        ↓
API 层 (FastAPI)
    └─ GET /api/v1/training-jobs/{job_id}/checkpoints
        └─ 返回检查点列表和元数据
```

**代码示例**:
```python
# 后端扫描服务 (backend/src/services/checkpoint_service.py)
import os
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class CheckpointScanner:
    def __init__(self, fsx_mount_path: str = "/fsx/checkpoints"):
        self.fsx_mount_path = fsx_mount_path

    async def scan_job_checkpoints(self, job_id: int, job_name: str, session: AsyncSession):
        """扫描单个训练任务的检查点目录"""
        checkpoint_dir = os.path.join(self.fsx_mount_path, job_name)

        if not os.path.exists(checkpoint_dir):
            return []

        checkpoints = []
        for file in os.listdir(checkpoint_dir):
            if file.endswith('.pth') or file.endswith('.ckpt'):
                file_path = os.path.join(checkpoint_dir, file)
                size_bytes = os.path.getsize(file_path)
                epoch = self._extract_epoch(file)

                checkpoints.append({
                    'training_job_id': job_id,
                    'checkpoint_name': file,
                    'storage_path': file_path,
                    'epoch': epoch,
                    'size_bytes': size_bytes,
                    'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
                })

        # 批量插入数据库
        if checkpoints:
            await self._upsert_checkpoints(session, checkpoints)

        return checkpoints

    def _extract_epoch(self, filename: str) -> int:
        """从文件名提取 epoch (例如: checkpoint_epoch_10.pth → 10)"""
        import re
        match = re.search(r'epoch_(\d+)', filename)
        return int(match.group(1)) if match else 0

    async def _upsert_checkpoints(self, session: AsyncSession, checkpoints: list):
        """批量插入或更新检查点元数据"""
        from backend.src.models.checkpoint import Checkpoint

        for cp_data in checkpoints:
            # 使用 storage_path 作为唯一键,避免重复插入
            existing = await session.execute(
                select(Checkpoint).where(Checkpoint.storage_path == cp_data['storage_path'])
            )
            if not existing.scalar():
                checkpoint = Checkpoint(**cp_data)
                session.add(checkpoint)

        await session.commit()

# 定期扫描任务 (backend/src/tasks/checkpoint_scan.py)
async def periodic_checkpoint_scan():
    """定期扫描所有活跃训练任务的检查点"""
    scanner = CheckpointScanner()

    while True:
        async with get_db_session() as session:
            # 查询所有运行中或最近完成的训练任务
            active_jobs = await session.execute(
                select(TrainingJob).where(
                    TrainingJob.status.in_(['Running', 'Completed'])
                )
            )

            for job in active_jobs.scalars():
                await scanner.scan_job_checkpoints(job.id, job.name, session)

        await asyncio.sleep(300)  # 每 5 分钟扫描一次
```

**API 端点**:
```python
# backend/src/api/v1/training.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/training-jobs/{job_id}/checkpoints")
async def list_checkpoints(job_id: int, session: AsyncSession = Depends(get_db_session)):
    """查询训练任务的检查点列表"""
    checkpoints = await session.execute(
        select(Checkpoint).where(Checkpoint.training_job_id == job_id).order_by(Checkpoint.epoch.desc())
    )

    return {
        'checkpoints': [
            {
                'checkpoint_id': cp.checkpoint_id,
                'checkpoint_name': cp.checkpoint_name,
                'epoch': cp.epoch,
                'size_mb': cp.size_bytes / (1024 * 1024),
                'created_at': cp.created_at.isoformat()
            }
            for cp in checkpoints.scalars()
        ]
    }
```

**开发工作量**: 中等 (5-7 天)
- 后端扫描服务: 2-3 天
- 数据库模型和 API: 2 天
- 单元测试和集成测试: 1-2 天

**相关任务**: T044 (Checkpoint 列表查询), T045 (Checkpoint 恢复)

**风险等级**: 中
- ⚠️ FSx for Lustre 性能: 需要优化目录扫描性能,避免影响训练任务
- ⚠️ 元数据一致性: 扫描延迟可能导致元数据与实际文件不一致
- ⚠️ 存储容量: 需要定期清理旧检查点,避免存储爆满

---

### 2. 训练指标采集 API 缺失

**缺口描述**: SDK 不提供训练指标 (Loss, Accuracy, Throughput 等) 的采集和查询 API

**影响分析**:
- ❌ 无法通过 SDK 获取训练指标时序数据
- ❌ 无法在前端可视化训练曲线 (Loss Curve, Accuracy Curve)
- ❌ 无法对比不同训练任务的性能表现

**备选方案**: OpenTelemetry 集成 (推荐) 或日志解析 (备选)

#### 方案 A: OpenTelemetry 集成 (推荐)

**实现架构**:
```
用户训练脚本 (PyTorch) → OpenTelemetry SDK 推送指标
    ├─ Meter: training-metrics
    ├─ Gauge: training.loss, training.accuracy
    └─ Counter: training.samples_per_second
        ↓
HyperPod Observability Add-on → OpenTelemetry Collector
    ├─ 接收端点: hyperpod-otel-collector.hyperpod-observability:4317
    └─ 处理管道: 聚合、过滤、格式转换
        ↓
Prometheus → 存储时序指标数据
    ├─ 数据保留: 30 天
    └─ 抓取间隔: 15 秒
        ↓
后端 API (FastAPI) → Prometheus HTTP API 查询
    └─ GET /api/v1/training-jobs/{job_id}/metrics
        ├─ 查询 training_loss{job_name="..."}
        └─ 查询 training_accuracy{job_name="..."}
        ↓
前端 (React + Cloudscape) → 可视化训练曲线
    └─ LineChart 组件渲染 Loss/Accuracy 曲线
```

**用户训练脚本集成**:
```python
# user_training_script.py
import torch
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
loss_gauge = meter.create_gauge("training.loss", description="Training loss per epoch")
accuracy_gauge = meter.create_gauge("training.accuracy", description="Training accuracy")
throughput_counter = meter.create_counter("training.samples_per_second", description="Training throughput")

# 在训练循环中记录指标
for epoch in range(num_epochs):
    for step, batch in enumerate(dataloader):
        # 训练逻辑...
        outputs = model(batch)
        loss = criterion(outputs, targets)

        # 记录指标
        loss_gauge.set(loss.item(), {"epoch": str(epoch), "step": str(step)})
        if step % 100 == 0:
            accuracy = evaluate_accuracy(model, val_dataloader)
            accuracy_gauge.set(accuracy, {"epoch": str(epoch)})

        throughput_counter.add(batch_size, {"epoch": str(epoch)})
```

**后端查询 Prometheus**:
```python
# backend/src/services/metrics_service.py
import requests
from datetime import datetime, timedelta

class MetricsService:
    def __init__(self, prometheus_url: str = "http://prometheus.hyperpod-observability:9090"):
        self.prometheus_url = prometheus_url

    async def get_training_loss(self, job_name: str, start_time: datetime, end_time: datetime):
        """查询训练 Loss 时序数据"""
        query = f'training_loss{{job_name="{job_name}"}}'
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={
                "query": query,
                "start": start_time.timestamp(),
                "end": end_time.timestamp(),
                "step": "15s"
            }
        )

        data = response.json()["data"]["result"]

        return [
            {
                "timestamp": datetime.fromtimestamp(float(value[0])),
                "loss": float(value[1])
            }
            for result in data
            for value in result["values"]
        ]

    async def get_training_accuracy(self, job_name: str):
        """查询训练 Accuracy 时序数据"""
        query = f'training_accuracy{{job_name="{job_name}"}}'
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query_range",
            params={"query": query}
        )

        data = response.json()["data"]["result"]

        return [
            {
                "timestamp": datetime.fromtimestamp(float(value[0])),
                "accuracy": float(value[1])
            }
            for result in data
            for value in result["values"]
        ]

# API 路由
@router.get("/training-jobs/{job_id}/metrics")
async def get_training_metrics(job_id: int):
    job = await db.training_jobs.get(job_id)
    metrics_service = MetricsService()

    loss_data = await metrics_service.get_training_loss(
        job_name=job.name,
        start_time=job.created_at,
        end_time=job.completed_at or datetime.now()
    )

    accuracy_data = await metrics_service.get_training_accuracy(job_name=job.name)

    return {
        'loss': loss_data,
        'accuracy': accuracy_data
    }
```

**前端可视化**:
```typescript
// frontend/src/pages/TrainingJobDetail.tsx
import { LineChart } from '@cloudscape-design/components';

const TrainingMetricsChart = ({ jobId }: { jobId: number }) => {
  const { data } = useQuery(['training-metrics', jobId], () =>
    api.get(`/training-jobs/${jobId}/metrics`)
  );

  return (
    <LineChart
      series={[
        {
          title: 'Training Loss',
          type: 'line',
          data: data.loss.map(d => ({ x: new Date(d.timestamp), y: d.loss }))
        },
        {
          title: 'Training Accuracy',
          type: 'line',
          data: data.accuracy.map(d => ({ x: new Date(d.timestamp), y: d.accuracy }))
        }
      ]}
      xDomain={[data.loss[0]?.timestamp, data.loss[data.loss.length - 1]?.timestamp]}
      yDomain={[0, 'auto']}
      xTitle="Time"
      yTitle="Metric Value"
    />
  );
};
```

**开发工作量**: 中等 (3-5 天)
- OpenTelemetry 集成文档: 1 天
- 后端 Prometheus 查询服务: 1-2 天
- 前端可视化组件: 1-2 天

#### 方案 B: 日志解析 (备选)

**适用场景**: 用户不使用 OpenTelemetry,只能通过日志提取指标

**实现方式**:
1. 后端定期查询训练日志 (`job.logs(tail=1000)`)
2. 使用正则表达式提取指标 (例如: `Epoch 10, Loss: 0.345, Accuracy: 0.89`)
3. 存储到数据库并提供查询 API

**缺点**:
- ⚠️ 日志格式不统一,需要支持多种正则模式
- ⚠️ 实时性差,延迟 1-2 分钟
- ⚠️ 解析性能开销大

**相关任务**: T038 (训练指标采集配置), T039 (指标查询 API)

**风险等级**: 中
- ⚠️ 用户学习成本: 需要提供 OpenTelemetry 集成文档和示例代码
- ⚠️ Observability Add-on 依赖: 需要确保 HyperPod Observability Add-on 正确部署
- ⚠️ Prometheus 存储容量: 需要配置合理的数据保留策略

---

## 重要缺口 (🟡 Important)

### 3. Kueue Workload 监控 API 缺失

**缺口描述**: SDK 不提供 Kueue Workload 状态查询 API

**影响分析**:
- ⚠️ 无法查询训练任务的队列位置和优先级
- ⚠️ 无法监控 Workload 的 Admitted/Pending 状态
- ⚠️ 影响用户体验,用户无法了解任务排队情况

**备选方案**: kubernetes-client 只读查询 Kueue Workload CRD

**实现架构**:
```
Training Operator → 创建 PyTorchJob CRD
    ↓
Kueue Admission Controller → 自动创建 Workload CRD
    ├─ Workload Name: {pytorchjob-name}-workload
    ├─ Status: Pending / Admitted
    └─ Priority: 从 PriorityClass 继承
        ↓
后端 kubernetes-client → 查询 Workload 状态 (只读)
    └─ api.get_namespaced_custom_object(group="kueue.x-k8s.io", ...)
        ↓
API 层 (FastAPI)
    └─ GET /api/v1/training-jobs/{job_id}/workload-status
        └─ 返回 Workload 状态和优先级
```

**代码示例**:
```python
# backend/src/services/kueue_service.py
from kubernetes import client, config

class KueueService:
    def __init__(self):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()

    def get_workload_status(self, workload_name: str, namespace: str = "default"):
        """查询 Kueue Workload 状态 (只读)"""
        try:
            workload = self.api.get_namespaced_custom_object(
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
                "queue_position": self._extract_queue_position(workload)
            }
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return {"error": "Workload not found"}
            raise

    def _extract_queue_position(self, workload: dict) -> int:
        """从 Workload 状态提取队列位置"""
        conditions = workload.get("status", {}).get("conditions", [])
        for condition in conditions:
            if condition["type"] == "QuotaReserved":
                return condition.get("message", "").split("position: ")[-1]
        return 0

# API 路由
@router.get("/training-jobs/{job_id}/workload-status")
async def get_training_workload_status(job_id: int):
    job = await db.training_jobs.get(job_id)
    kueue_service = KueueService()

    # Kueue 自动生成的 Workload 名称格式: {pytorchjob-name}-workload
    workload_name = f"{job.name}-workload"
    workload_status = kueue_service.get_workload_status(workload_name)

    return workload_status
```

**RBAC 配置**:
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
```

**开发工作量**: 低 (1-2 天)
- kubernetes-client 查询服务: 1 天
- RBAC 配置和测试: 0.5 天
- API 端点和前端展示: 0.5 天

**相关任务**: T037 (Kueue Workload 监控)

**风险等级**: 低
- ✅ 只读操作,不会影响 Kueue 调度器
- ⚠️ 需要配置正确的 RBAC 权限

---

### 4. NetworkPolicy 配置 API 缺失

**缺口描述**: SDK 不提供 Kubernetes NetworkPolicy 配置和验证 API

**影响分析**:
- ⚠️ 无法通过 SDK 动态配置网络隔离策略
- ⚠️ 无法验证 NetworkPolicy 是否正确生效
- ⚠️ 需要依赖 IaC (kubectl/CDK) 在部署阶段配置

**备选方案**: IaC (kubectl/CDK) 配置 + kubernetes-client 验证

**实现架构**:
```
IaC 阶段 (T008f) → kubectl apply -f network-policies.yaml
    ├─ 配置训练 Pod 网络隔离策略
    └─ 配置 FSx for Lustre 访问规则
        ↓
Kubernetes API Server → 创建 NetworkPolicy 资源
    ↓
CNI Plugin (Calico/Cilium) → 应用网络隔离规则
    ↓
POC 验证阶段 (T008g) → kubernetes-client 查询策略状态
    └─ api.read_namespaced_network_policy()
        ↓
运行时监控 → kubernetes-client 监控策略生效情况
    └─ GET /api/v1/network-policies
```

**NetworkPolicy 配置示例**:
```yaml
# infrastructure/k8s/network-policies/training-isolation.yaml
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
              app: training-job  # 训练 Pod 之间可以通信
    - to:  # 允许访问 FSx for Lustre
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: TCP
          port: 988  # Lustre 默认端口
```

**POC 验证代码**:
```python
# backend/tests/integration/test_network_policy.py
from kubernetes import client, config

def test_network_policy_isolation():
    """验证 NetworkPolicy 配置"""
    config.load_kube_config()
    api = client.NetworkingV1Api()

    policy = api.read_namespaced_network_policy(
        name="training-jobs-isolation",
        namespace="default"
    )

    # 验证策略存在
    assert policy.metadata.name == "training-jobs-isolation"

    # 验证 Pod Selector
    assert policy.spec.pod_selector.match_labels["app"] == "training-job"

    # 验证 Ingress 规则
    assert len(policy.spec.ingress) == 1
    assert policy.spec.ingress[0].from_[0].pod_selector.match_labels["app"] == "training-job"

    # 验证 Egress 规则
    assert len(policy.spec.egress) == 2

    print("✅ NetworkPolicy 验证通过")
```

**开发工作量**: 低 (1-2 天)
- NetworkPolicy YAML 配置: 0.5 天
- POC 验证脚本: 0.5 天
- 运行时监控 API: 0.5 天

**相关任务**: T008f (NetworkPolicy 配置), T008g (NetworkPolicy 验证)

**风险等级**: 低
- ✅ NetworkPolicy 在 IaC 阶段配置,不影响运行时
- ⚠️ 需要确保 CNI Plugin 支持 NetworkPolicy (Calico/Cilium)

---

### 5. 任务级优先级调度参数缺失

**缺口描述**: SDK 不提供训练任务的优先级参数,无法在创建任务时指定优先级

**影响分析**:
- ⚠️ 无法通过 SDK 直接设置训练任务优先级
- ⚠️ 需要后端额外设置 PriorityClass
- ⚠️ 影响多租户场景的资源调度公平性

**备选方案**: 后端设置 PriorityClass + Kueue 继承优先级

**实现架构**:
```
IaC 阶段 → 创建 PriorityClass 资源
    ├─ high-priority (value: 1000)
    ├─ medium-priority (value: 500)
    └─ low-priority (value: 100)
        ↓
后端创建训练任务 → 根据用户配额设置 priorityClassName
    └─ 如果 SDK 不支持,使用 kubernetes-client 创建 PyTorchJob
        ↓
Training Operator → 创建 PyTorchJob CRD 并设置 priorityClassName
    ↓
Kueue Admission Controller → 创建 Workload 并继承优先级
    ↓
Kueue Scheduler → 按优先级调度任务
```

**PriorityClass 配置**:
```yaml
# infrastructure/k8s/priority-classes.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "高优先级训练任务 (VIP 用户或紧急任务)"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: medium-priority
value: 500
globalDefault: true
description: "中等优先级训练任务 (默认)"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
description: "低优先级训练任务 (Spot 实例或低优先级用户)"
```

**后端设置优先级**:
```python
# backend/src/services/training_service.py
from kubernetes import client, config

class TrainingService:
    def __init__(self):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()

    async def create_training_job_with_priority(
        self,
        job_name: str,
        image_uri: str,
        instance_type: str,
        node_count: int,
        priority: str = "medium-priority"  # high-priority / medium-priority / low-priority
    ):
        """创建训练任务并设置优先级"""

        # 注意: 如果 SDK 支持 priorityClassName 参数,优先使用 SDK
        # 如果 SDK 不支持,使用 kubernetes-client 创建 PyTorchJob

        pytorchjob = {
            "apiVersion": "kubeflow.org/v1",
            "kind": "PyTorchJob",
            "metadata": {
                "name": job_name,
                "namespace": "default"
            },
            "spec": {
                "priorityClassName": priority,  # 设置优先级
                "pytorchReplicaSpecs": {
                    "Master": {
                        "replicas": 1,
                        "template": {
                            "spec": {
                                "containers": [{
                                    "name": "pytorch",
                                    "image": image_uri,
                                    "command": ["torchrun", "train.py"]
                                }]
                            }
                        }
                    },
                    "Worker": {
                        "replicas": node_count - 1,
                        "template": {
                            "spec": {
                                "containers": [{
                                    "name": "pytorch",
                                    "image": image_uri,
                                    "command": ["torchrun", "train.py"]
                                }]
                            }
                        }
                    }
                }
            }
        }

        self.api.create_namespaced_custom_object(
            group="kubeflow.org",
            version="v1",
            namespace="default",
            plural="pytorchjobs",
            body=pytorchjob
        )

# API 路由
@router.post("/training-jobs")
async def create_training_job(
    name: str,
    image_uri: str,
    instance_type: str,
    node_count: int,
    priority: str = "medium-priority"  # 用户可以指定优先级
):
    training_service = TrainingService()
    await training_service.create_training_job_with_priority(
        job_name=name,
        image_uri=image_uri,
        instance_type=instance_type,
        node_count=node_count,
        priority=priority
    )

    return {"message": "训练任务已创建", "priority": priority}
```

**开发工作量**: 中等 (3-4 天)
- PriorityClass 配置: 0.5 天
- 后端优先级设置逻辑: 1-2 天
- 前端优先级选择器: 1 天
- 集成测试: 0.5-1 天

**相关任务**: T037 (优先级调度配置)

**风险等级**: 中
- ⚠️ 如果 SDK 不支持 priorityClassName,需要使用 kubernetes-client 直接创建 PyTorchJob
- ⚠️ 需要确保 Kueue Admission Controller 正确配置

---

## 次要缺口 (🟢 Minor)

### 6. Add-ons 配置 API 缺失

**缺口描述**: SDK 不提供 HyperPod Add-ons (Observability, Resilience, EFA) 的配置和管理 API

**影响分析**:
- 🟢 Add-ons 在集群创建时配置,不需要运行时动态管理
- 🟢 不影响训练任务的核心功能

**备选方案**: IaC (kubectl/CDK) 在集群创建时配置

**实现方式**: 在 T008d 中通过 IaC 配置 Add-ons,不需要额外的运行时 API

**开发工作量**: 低 (1 天)

**相关任务**: T008d (HyperPod Add-ons 配置与验证)

**风险等级**: 低

---

### 7. 集群级 Spot 实例配置缺失

**缺口描述**: SDK 不提供训练任务级别的 Spot 实例配置,只能在集群创建时配置 Spot 实例组

**影响分析**:
- 🟢 Spot 实例在集群级别配置,不影响训练任务的创建
- 🟢 HyperPod 自动管理 Spot 实例中断和替换

**备选方案**: boto3 / CDK 在集群创建时配置 Spot 实例组

**实现方式**: 在 T008e 中通过 IaC 配置 Spot 实例组

**开发工作量**: 低 (1-2 天)

**相关任务**: T008e (Spot 实例配置)

**风险等级**: 低

---

### 8. 成本统计 API 缺失

**缺口描述**: SDK 不提供训练任务成本统计 API

**影响分析**:
- 🟢 成本统计不是 HyperPod SDK 的核心功能
- 🟢 AWS Cost Explorer API 提供完整的成本统计功能

**备选方案**: boto3 Cost Explorer API

**实现方式**: 在 T063 中使用 boto3 Cost Explorer API 查询训练任务成本

**开发工作量**: 低 (2-3 天)

**相关任务**: T063 (成本追踪与查询)

**风险等级**: 低

---

### 9. Model Registry 集成缺失

**缺口描述**: SDK 不提供模型注册到 SageMaker Model Registry 的集成 API

**影响分析**:
- 🟢 Model Registry 不是 HyperPod SDK 的核心功能
- 🟢 boto3 SageMaker API 提供完整的 Model Registry 功能

**备选方案**: boto3 SageMaker API

**实现方式**: 在 T064 中使用 boto3 SageMaker API 注册模型

**开发工作量**: 低 (2-3 天)

**相关任务**: T064 (模型注册到 Model Registry)

**风险等级**: 低

---

## 缺口对开发路线的影响评估

### Phase 0 影响

✅ **无阻塞影响**: 所有缺口都有明确的备选方案,不影响 Phase 0 技术验证

### Phase 1 影响

⚠️ **中等影响**: 需要实现以下备选方案才能完成 Phase 1 核心功能开发
- Checkpoint 管理 (后端扫描服务)
- 训练指标采集 (OpenTelemetry 集成)
- Kueue Workload 监控 (kubernetes-client 只读查询)

### Phase 2 影响

🟢 **低影响**: 次要缺口的备选方案可以在 Phase 2 并行实现
- NetworkPolicy 配置 (IaC 阶段完成)
- 优先级调度 (后端设置 PriorityClass)
- 成本统计 (boto3 Cost Explorer API)

### Phase 3 影响

🟢 **无影响**: Phase 3 主要关注高级功能和优化,缺口已在 Phase 1-2 解决

---

## 备选方案开发工作量汇总

| 缺口 | 备选方案 | 开发工作量 | 阶段 |
|-----|---------|-----------|------|
| Checkpoint 管理 | 后端扫描 FSx + 元数据索引 | 5-7 天 | Phase 1 |
| 训练指标采集 | OpenTelemetry 集成 | 3-5 天 | Phase 1 |
| Kueue Workload 监控 | kubernetes-client 只读查询 | 1-2 天 | Phase 1 |
| NetworkPolicy 配置 | IaC (kubectl/CDK) | 1-2 天 | Phase 1 |
| 优先级调度 | 后端设置 PriorityClass | 3-4 天 | Phase 1 |
| Add-ons 配置 | IaC (kubectl/CDK) | 1 天 | Phase 1 |
| Spot 实例配置 | boto3 / CDK | 1-2 天 | Phase 1 |
| 成本统计 | boto3 Cost Explorer API | 2-3 天 | Phase 2 |
| Model Registry | boto3 SageMaker API | 2-3 天 | Phase 2 |
| **总计** | | **20-31 天** | |

---

## 风险缓解措施

### 1. Checkpoint 管理风险

**风险**: FSx 扫描性能影响训练任务

**缓解措施**:
- ✅ 使用低优先级后台任务进行扫描
- ✅ 限制扫描频率 (每 5 分钟)
- ✅ 使用增量扫描,只扫描最近修改的文件
- ✅ 配置 FSx for Lustre 的缓存策略,减少扫描延迟

### 2. OpenTelemetry 集成风险

**风险**: 用户学习成本高,集成复杂

**缓解措施**:
- ✅ 提供详细的集成文档和示例代码
- ✅ 提供 Docker 镜像预集成 OpenTelemetry SDK
- ✅ 在前端提供"指标未配置"提示,引导用户集成
- ✅ 提供备选方案 (日志解析),支持无 OpenTelemetry 的场景

### 3. kubernetes-client 权限风险

**风险**: RBAC 配置错误导致权限不足或权限过大

**缓解措施**:
- ✅ 使用最小权限原则,只授予 `get`, `list`, `watch` 权限
- ✅ 在 IaC 阶段配置 RBAC,避免运行时动态授权
- ✅ 定期审计 RBAC 配置,确保权限合规

---

## 结论

### 总体评估

✅ **HyperPod SDK 核心功能完整**: 训练任务 CRUD、状态查询、日志查询、Pod 列表等核心功能完整

⚠️ **高级功能需要自实现**: Checkpoint 管理、训练指标采集需要后端自实现,但都有明确的备选方案

✅ **开发路线可行**: 所有缺口都有备选方案,不影响项目整体进度

### T000-fallback 评估

**是否需要触发 T000-fallback?**
→ ❌ **不需要**

**原因**:
1. ✅ HyperPod SDK 的核心功能 (训练任务管理) 完整且可用
2. ✅ 所有功能缺口都有明确的备选方案
3. ✅ 备选方案的开发工作量在可接受范围内 (20-31 天)
4. ✅ 备选方案不会影响项目的整体架构和开发路线

### 建议

1. ✅ **继续使用 sagemaker-hyperpod SDK** 作为主要开发工具
2. ⚠️ **按优先级实现备选方案**:
   - Phase 1: Checkpoint 管理、训练指标采集、Kueue Workload 监控
   - Phase 2: 成本统计、Model Registry
3. ✅ **为用户提供 OpenTelemetry 集成文档**,降低学习成本
4. ✅ **在 IaC 阶段完成基础设施配置** (NetworkPolicy, PriorityClass, Add-ons)

---

## 参考文档

- **HyperPod SDK 方法签名**: [docs/hyperpod-sdk-reference.md](./hyperpod-sdk-reference.md)
- **HyperPod SDK 能力矩阵**: [docs/hyperpod-sdk-capability-matrix.md](./hyperpod-sdk-capability-matrix.md)
- **技术选型决策指南**: [docs/technical-decision-guideline.md](./technical-decision-guideline.md)
- **HyperPod SDK 官方文档**: https://sagemaker-hyperpod-cli.readthedocs.io/
- **boto3 SageMaker 文档**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html
- **Kueue 官方文档**: https://kueue.sigs.k8s.io/
- **OpenTelemetry Python**: https://opentelemetry.io/docs/instrumentation/python/

---

**文档版本**: v1.0
**最后更新**: 2026-01-08
**审核状态**: Phase 0 技术验证完成
**T000-fallback 状态**: ❌ 不需要触发
