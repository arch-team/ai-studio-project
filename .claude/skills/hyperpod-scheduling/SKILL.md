---
name: hyperpod-scheduling
description: AWS SageMaker HyperPod + Kueue 任务调度与抢占实现，包含 5 个关键踩坑记录和快速诊断清单
---

# HyperPod Task Governance 任务调度与抢占实现

**提取日期:** 2025-01-25
**来源:** backend/src/modules/training/, infrastructure/k8s/hyperpod-addons/
**上下文:** AWS SageMaker HyperPod + Kueue 实现企业级 AI 训练任务调度

## 问题

在多租户 AI 训练平台中需要解决：
1. 公平的资源分配和优先级调度
2. 高优先级任务抢占低优先级任务
3. 被抢占任务的自动恢复
4. 连续抢占失败的处理

## 解决方案

### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (FastAPI)                          │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ TrainingService │  │    TrainingSyncService          │   │
│  │   (任务提交)     │  │    (状态同步 + 抢占处理)         │   │
│  └────────┬────────┘  └────────────────┬────────────────┘   │
│           │                             │                    │
│           ▼                             ▼                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              HyperPodClient (SDK 封装)                  │ │
│  │  - submit_training_job()  - get_training_job_status()  │ │
│  │  - trigger_preemption()   - resume_training_job()      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    HyperPod 集群 (EKS)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Kueue Controller                     │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │gpu-training │ │high-priority│ │ preprocessing   │  │  │
│  │  │   -queue    │ │   -queue    │ │    -queue       │  │  │
│  │  └──────┬──────┘ └──────┬──────┘ └───────┬─────────┘  │  │
│  │         └───────────────┴────────────────┘            │  │
│  │                         │                              │  │
│  │                   ai-platform-cohort                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                PyTorchJob Operator                     │  │
│  │         HyperPodPytorchJob → Worker Pods               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1. Kueue 调度标签配置

通过 Kubernetes Labels 将任务分配到指定队列和优先级：

```python
# backend/src/modules/training/infrastructure/hyperpod/client.py

def _build_kueue_labels(
    self, queue_name: str | None, priority_class: str | None
) -> dict[str, str]:
    """构建 Kueue 调度标签。"""
    labels: dict[str, str] = {}
    if queue_name:
        labels["kueue.x-k8s.io/queue-name"] = queue_name
    if priority_class:
        # 使用 Kueue 的 priority-class label 代替 Pod 的 priorityClassName
        # 注意: WorkloadPriorityClass (Kueue) ≠ PriorityClass (K8s 原生)
        labels["kueue.x-k8s.io/priority-class"] = priority_class
    return labels
```

**关键点**:
- 使用 `kueue.x-k8s.io/queue-name` 而非 Pod 的 `spec.queueName`
- 使用 `kueue.x-k8s.io/priority-class` 而非 `priorityClassName`
- SageMaker 只创建 `WorkloadPriorityClass`，不创建 K8s 原生 `PriorityClass`

### 2. ClusterQueue 抢占配置

```yaml
# infrastructure/k8s/hyperpod-addons/training/cluster-queues.yaml

# 主训练队列 - 允许被抢占
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: gpu-training-queue
spec:
  queueingStrategy: BestEffortFIFO

  preemption:
    withinClusterQueue: LowerPriority
    reclaimWithinCohort: LowerPriority
    borrowWithinCohort:
      policy: LowerPriority
      maxPriorityThreshold: 100

  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: nvidia-a100-40gb
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 64
              borrowingLimit: 32
              lendingLimit: 16

  cohort: ai-platform-cohort
```

**抢占配置要点**:
1. 两个 ClusterQueue 必须在同一个 Cohort 中才能互相抢占
2. `reclaimWithinCohort: Any` 允许无条件回收 Cohort 内资源
3. `borrowWithinCohort.policy: Never` + `lendingLimit: 0` = 独占资源
4. 总 nominal quota 不能超过物理资源，否则抢占逻辑失效

## 关键问题与解决方案 (踩坑记录)

### 问题 1: TopologyAwareScheduling (TAS) 配置问题 - 最难排查

**错误信息**: `topology "hyperpod-default" doesn't allow to fit any of 1 pod(s)`

**根因**: SageMaker Task Governance API 创建的 ResourceFlavor 自动启用 TAS，但 Kueue TAS 对节点拓扑匹配要求非常严格。

**解决方案**:
```bash
kubectl patch resourceflavor <name> --type=json \
  -p='[{"op": "remove", "path": "/spec/topologyName"}]'
```

### 问题 2: 抢占不生效问题

**根因**: Kueue 抢占有三个必要前提条件：
- 同一 Cohort
- 总 nominal ≤ 物理资源
- 非 `DontLend` 策略

**排查命令**:
```bash
kubectl get clusterqueues -o custom-columns=NAME:.metadata.name,COHORT:.spec.cohort
```

### 问题 3: PriorityClass 双重资源问题

**根因**: Kueue 使用 `WorkloadPriorityClass` (Kueue CRD)，而非 K8s 原生的 `PriorityClass`。

**解决方案**: 使用 `kueue.x-k8s.io/priority-class` label 代替 Pod 的 `priorityClassName`

### 问题 4: PodsRunning 状态与实际 Pod 状态不一致

**根因**: `PodsRunning` condition 依赖 Torch Elastic Agent 的就绪状态。

**解决方案**: 检测到有 `PodsRunning` condition 存在即认为 "running"，不依赖其 status 值。

### 问题 5: set_cluster_context 必须先调用

**根因**: HyperPod SDK 需要先调用 `set_cluster_context()` 配置 kubeconfig

## 快速诊断清单

```bash
# 1. 检查 Workload 状态
kubectl get workloads -n <namespace>
kubectl describe workload <name> -n <namespace>

# 2. 检查 ClusterQueue 状态和 Cohort
kubectl get clusterqueues -o wide

# 3. 检查 LocalQueue 绑定
kubectl describe localqueue <name> -n <namespace>

# 4. 检查 ResourceFlavor 和 TAS
kubectl get resourceflavors -o yaml | grep topologyName

# 5. 检查 WorkloadPriorityClass
kubectl get workloadpriorityclasses

# 6. 检查 Kueue 控制器日志
kubectl logs -n kueue-system -l app.kubernetes.io/name=kueue --tail=200

# 7. 检查实际 Pod 状态
kubectl get pods -l job-name=<job-name> -n <namespace>
```

## 何时使用

**适用场景:**
- 基于 AWS SageMaker HyperPod 构建 AI 训练平台
- 需要多优先级任务队列管理
- 需要实现高优先级任务抢占低优先级任务
- 需要处理被抢占任务的自动恢复

**关键配置清单:**
1. ClusterQueue 在同一 Cohort 中
2. 配置 `preemption.reclaimWithinCohort` 策略
3. 使用 `kueue.x-k8s.io/*` 标签而非 Pod 原生字段
4. 实现连续抢占失败计数和上限处理
5. 状态同步服务定期拉取 HyperPod 状态
