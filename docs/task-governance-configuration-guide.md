# HyperPod Task Governance 配置指南

**版本**: 1.0
**日期**: 2026-01-24
**适用范围**: AWS SageMaker HyperPod Task Governance (EKS Add-on v1.1.3+, Kueue v0.12.0+)

---

## 概述

本文档提供 HyperPod Task Governance 的配置最佳实践，遵循项目的 **SDK-First 原则**。

### 配置原则

```
┌─────────────────────────────────────────────────────────────────┐
│                    配置方式优先级                                 │
├─────────────────────────────────────────────────────────────────┤
│  1. Task Governance API (Console/CLI)     ← 首选，托管配置        │
│  2. K8s 原生方式 (kubectl)                ← 仅用于 API 无法解决时  │
│  3. 直接修改 Kueue CRD                    ← 最后手段，可能被覆盖   │
└─────────────────────────────────────────────────────────────────┘
```

**重要警告** (来自 AWS 官方文档):
> "While Kubernetes administrators have the flexibility to modify the state of these resources,
> it is possible that any changes made to a SageMaker AI-managed resource may be updated and
> overwritten by the service."

---

## 1. Task Governance 安装

### 1.1 通过 AWS CLI 安装 Add-on

```bash
# 安装 Task Governance EKS Add-on
aws eks create-addon \
  --region us-west-2 \
  --cluster-name my-hyperpod-cluster \
  --addon-name amazon-sagemaker-hyperpod-taskgovernance

# 检查安装状态
aws eks describe-addon \
  --region us-west-2 \
  --cluster-name my-hyperpod-cluster \
  --addon-name amazon-sagemaker-hyperpod-taskgovernance
```

### 1.2 前置条件

- Kubernetes 版本 >= 1.30
- HyperPod 节点已存在于 EKS 集群
- 如已安装独立 Kueue，需先卸载

### 1.3 安装后自动创建的资源

Task Governance Add-on 安装后会自动创建以下 Kueue 资源：

| 资源类型 | 说明 | 管理方式 |
|---------|------|---------|
| `KueueManagerConfig` | Kueue 配置 | Task Governance 托管 |
| `ClusterQueue` | 集群级资源池 | Task Governance 托管 |
| `LocalQueue` | 命名空间级队列 | Task Governance 托管 |
| `WorkloadPriorityClass` | Kueue 优先级类 | Task Governance 托管 |
| `ResourceFlavor` | 资源类型定义 | Task Governance 托管 |

---

## 2. 策略配置 (通过 Task Governance API)

### 2.1 通过 Console 配置

1. 打开 SageMaker Console → HyperPod clusters → Cluster management
2. 选择集群 → **Policies** 标签页
3. 配置以下策略：

#### 计算优先级策略 (Compute Prioritization)

| 策略项 | 选项 | 说明 |
|-------|------|------|
| **Idle compute allocation** | First-come first-serve / Fair-share / Task prioritization | 空闲资源分配策略 |
| **Task prioritization** | First-come first-serve / Task ranking | 任务排序方式 |
| **Priority classes** | high / medium / low | 优先级类定义 |

#### 计算配额策略 (Compute Allocation)

| 配置项 | 说明 | 示例值 |
|-------|------|--------|
| **Team name** | 团队名称 | team-nlp |
| **Fair-share weight** | 公平共享权重 | 100 |
| **Task preemption** | 是否允许抢占 | Enabled |
| **Lending** | 是否出借空闲资源 | Enabled |
| **Borrowing** | 是否借用其他团队资源 | Enabled |
| **Borrow limit** | 借用上限 (% of allocated) | 200% |

### 2.2 通过 AWS CLI 配置配额

```bash
# 示例：创建团队配额 (fine-grained quota)
# 参考: https://aws.amazon.com/blogs/machine-learning/maximize-hyperpod-cluster-utilization-with-hyperpod-task-governance-fine-grained-quota-allocation/

# 查看当前配额策略
kubectl get clusterqueues -o yaml

# 查看团队本地队列
kubectl get localqueues -n hyperpod-ns-team-nlp -o yaml
```

---

## 3. 优先级配置

### 3.1 优先级类定义 (Task Governance 托管)

Task Governance 自动创建 `WorkloadPriorityClass` 资源：

| 优先级名称 | 数值 | 使用场景 |
|-----------|------|---------|
| `high-priority` | 1000 | VIP 用户、紧急任务 |
| `medium-priority` | 500 | 默认优先级 (globalDefault) |
| `low-priority` | 100 | Spot 实例、低优先级用户 |

### 3.2 任务提交时指定优先级

**方式 1: HyperPod CLI**

```bash
hyp create hyp-pytorch-job \
  --job-name my-training-job \
  --namespace hyperpod-ns-team-nlp \
  --queue-name hyperpod-ns-team-nlp-localqueue \
  --priority high-priority \
  --image 123456789012.dkr.ecr.us-west-2.amazonaws.com/training:latest
```

**方式 2: kubectl YAML**

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: my-training-job
  namespace: hyperpod-ns-team-nlp
  labels:
    kueue.x-k8s.io/queue-name: hyperpod-ns-team-nlp-localqueue
    kueue.x-k8s.io/priority-class: high-priority  # 指定优先级
spec:
  # ... 训练配置
```

### 3.3 注意事项

> **重要**: Task Governance 使用 `WorkloadPriorityClass` (Kueue) 而非 K8s 原生 `PriorityClass`。
>
> 使用 `kueue.x-k8s.io/priority-class` label 而非 Pod 的 `priorityClassName` 字段。

---

## 4. 抢占配置

### 4.1 抢占前提条件

根据项目验证 (参见 `backend/CLAUDE.md`)：

| 前提 | 说明 |
|-----|------|
| **Cohort 配置** | 两个 ClusterQueue 必须在同一个 Cohort 中 |
| **资源限制** | 总 nominal quota 不能超过物理资源 |
| **借用策略** | 高优先级队列: nominal=实际, borrow=0; 低优先级队列: nominal=0, borrow=实际 |

### 4.2 抢占策略配置 (通过 Console)

在 Policies → Compute allocation 中配置：

- **Task preemption**: Enabled
- **Lending**: Enabled (允许出借空闲资源)
- **Borrowing**: Enabled (允许借用其他团队资源)

### 4.3 已知问题

> **注意**: `ResourceSharingConfig.Strategy=DontLend` 会创建独立 Cohort，阻止跨队列抢占。
> 确保需要抢占的队列在同一 Cohort 中。

---

## 5. Topology-Aware Scheduling (TAS)

### 5.1 TAS 说明

TAS **不是默认启用的**，需要在工作负载级别主动配置。

**适用版本**: HyperPod Task Governance v1.2.2-eksbuild.1 或更高

**支持的实例类型**: ml.p4d.24xlarge, ml.p5.48xlarge, ml.trn1.32xlarge 等

### 5.2 启用 TAS

**方式 1: HyperPod CLI**

```bash
hyp create hyp-pytorch-job \
  --job-name my-distributed-job \
  --namespace hyperpod-ns-team-nlp \
  --queue-name hyperpod-ns-team-nlp-localqueue \
  --preferred-topology-label topology.k8s.aws/network-node-layer-3
```

**方式 2: YAML Annotation**

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: my-distributed-job
  namespace: hyperpod-ns-team-nlp
spec:
  pytorchReplicaSpecs:
    Worker:
      replicas: 8
      template:
        metadata:
          annotations:
            # 必需拓扑 - 资源不满足时任务挂起
            kueue.x-k8s.io/podset-required-topology: "topology.k8s.aws/network-node-layer-3"
            # 或：首选拓扑 - 尽量满足，不满足时降级
            # kueue.x-k8s.io/podset-preferred-topology: "topology.k8s.aws/network-node-layer-3"
```

### 5.3 TAS 拓扑层级

| 拓扑标签 | 说明 | 网络延迟 |
|---------|------|---------|
| `topology.k8s.aws/network-node-layer-1` | 最大范围 | 较高 |
| `topology.k8s.aws/network-node-layer-2` | 中等范围 | 中等 |
| `topology.k8s.aws/network-node-layer-3` | 最小范围（推荐） | 最低 |
| `topology.k8s.aws/ultraserver-id` | UltraServer 内 | 极低 |

---

## 6. 底层 Kueue CRD 参考 (仅供理解)

> **警告**: 以下配置仅供理解底层原理。生产环境应通过 Task Governance API 配置。
> 手动修改可能被 Task Governance 服务覆盖。

### 6.1 ClusterQueue 结构

```yaml
# 此为 Task Governance 自动生成的 ClusterQueue 结构参考
# 请勿直接创建或修改，使用 Console Policies 配置
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: hyperpod-team-nlp-clusterqueue
spec:
  # 资源组定义
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: nvidia-a100-40gb
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 8        # 标称配额
              borrowingLimit: 16     # 借用上限
              lendingLimit: 4        # 出借上限
            - name: "cpu"
              nominalQuota: 64
            - name: "memory"
              nominalQuota: 512Gi

  # Cohort - 同一 Cohort 内可借用/抢占
  cohort: hyperpod-default-cohort

  # 抢占策略
  preemption:
    reclaimWithinCohort: Any
    borrowWithinCohort:
      policy: LowerPriority
    withinClusterQueue: LowerPriority

  # 公平共享
  fairSharing:
    weight: 100
```

### 6.2 LocalQueue 结构

```yaml
# 此为 Task Governance 自动生成的 LocalQueue 结构参考
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  name: hyperpod-ns-team-nlp-localqueue
  namespace: hyperpod-ns-team-nlp
spec:
  clusterQueue: hyperpod-team-nlp-clusterqueue
```

### 6.3 ResourceFlavor 结构

```yaml
# 此为 Task Governance 自动生成的 ResourceFlavor 结构参考
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: nvidia-a100-40gb
spec:
  nodeLabels:
    node.kubernetes.io/instance-type: p4d.24xlarge
    nvidia.com/gpu.product: NVIDIA-A100-SXM4-40GB
  # 注意：不指定 topologyName 以禁用自动 TAS
  # TAS 应在工作负载级别通过 annotation 启用
```

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 任务一直 Pending | 配额不足或 TAS 约束 | 检查队列配额，放宽 TAS 约束 |
| 抢占不生效 | 不在同一 Cohort | 确保队列在同一 Cohort |
| TAS 调度失败 | 拓扑约束过严 | 使用 preferred-topology 替代 required-topology |
| 配置被覆盖 | 手动修改 CRD | 通过 Task Governance API 配置 |

### 7.2 诊断命令

```bash
# 查看 Workload 状态
kubectl get workloads -n hyperpod-ns-team-nlp

# 查看 ClusterQueue 状态
kubectl get clusterqueues -o wide

# 查看队列事件
kubectl describe localqueue hyperpod-ns-team-nlp-localqueue -n hyperpod-ns-team-nlp

# 查看 Kueue 日志
kubectl logs -n kueue-system -l app.kubernetes.io/name=kueue
```

---

## 8. 参考文档

| 文档 | 链接 |
|------|------|
| **Task Governance 官方文档** | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html |
| **TAS 配置指南** | https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance-tasks-scheduling.html |
| **最佳实践博客** | https://aws.amazon.com/blogs/machine-learning/best-practices-for-amazon-sagemaker-hyperpod-task-governance/ |
| **Fine-grained Quota** | https://aws.amazon.com/blogs/machine-learning/maximize-hyperpod-cluster-utilization-with-hyperpod-task-governance-fine-grained-quota-allocation/ |
| **Kueue 官方文档** | https://kueue.sigs.k8s.io/ |
| **项目 SDK-First 原则** | `specs/001-ai-training-platform/spec.md` §抽象层使用决策指南 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-24 | 初始版本，基于 AWS 官方文档和项目实践经验 |
