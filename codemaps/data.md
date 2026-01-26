# 数据模型与基础设施

**更新时间**: 2026-01-26 10:30
**版本**: 1.0.0

## 核心实体

### 实体命名规范

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 数据集版本 | `DatasetVersion` | `dataset_versions` | `/datasets/:id/versions` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 模型版本 | `ModelVersion` | `model_versions` | `/models/:id/versions` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |
| 用户 | `User` | `users` | `/users` |
| 审计日志 | `AuditLog` | `audit_logs` | `/audit-logs` |

### 实体关系图 (ER)

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    User     │───1:N─│  TrainingJob    │───1:N─│ Checkpoint  │
└─────────────┘       └─────────────────┘       └─────────────┘
      │                      │
      │                      │ N:1
      │                      ▼
      │               ┌─────────────┐
      │               │    Model    │
      │               └─────────────┘
      │                      │
      │                      │ 1:N
      │                      ▼
      │               ┌─────────────────┐
      │               │  ModelVersion   │
      │               └─────────────────┘
      │
      ├───1:N─────────┬─────────────┐
      │               │             │
      ▼               ▼             ▼
┌─────────────┐ ┌───────────┐ ┌─────────────────┐
│   Dataset   │ │   Space   │ │ ResourceQuota   │
└─────────────┘ └───────────┘ └─────────────────┘
      │
      │ 1:N
      ▼
┌─────────────────┐
│ DatasetVersion  │
└─────────────────┘
```

### 训练任务状态机

```
           ┌──────────────────────────────────────────┐
           │                                          │
           ▼                                          │
┌──────────────┐     ┌─────────┐     ┌───────────────┐│
│  submitted   │────►│ running │────►│   completed   ││
└──────────────┘     └────┬────┘     └───────────────┘│
                          │                           │
                          ├─────────►┌──────────┐     │
                          │          │  failed  │─────┘
                          │          └──────────┘
                          │
                          ├─────────►┌──────────┐
                          │          │  paused  │───► running
                          │          └──────────┘
                          │
                          └─────────►┌───────────┐
                                     │ preempted │───► running
                                     └───────────┘
```

## CDK Stack 分层

### 依赖图

```
Layer 1 (并行)
├─ NetworkStack
│  ├─ VPC (10.0.0.0/16)
│  ├─ Public Subnets (/20)
│  ├─ Private App Subnets (/19)
│  ├─ Private Data Subnets (/20, isolated)
│  ├─ NAT Gateway (×2 for prod)
│  ├─ VPC Endpoints (S3, ECR, STS, CloudWatch, SageMaker)
│  └─ VPC Flow Logs
│
└─ IamStack
   ├─ EKS Node Role
   ├─ Training Execution Role
   ├─ Backend Service Role
   └─ KMS Usage Policy

Layer 2 (并行，依赖 NetworkStack)
├─ DatabaseStack
│  ├─ Aurora MySQL Serverless v2 (0.5-16 ACU)
│  ├─ RDS Proxy (连接池)
│  ├─ Security Group (3306)
│  └─ Secrets Manager
│
└─ StorageStack
   ├─ S3 Datasets Bucket
   ├─ S3 Models Bucket
   ├─ S3 Checkpoints Bucket
   ├─ SSE-KMS 加密
   ├─ Versioning
   └─ Lifecycle Rules

Layer 3 (顺序)
├─ EksStack
│  ├─ EKS Cluster (K8s 1.33+)
│  ├─ System Node Group (t3.medium)
│  ├─ GPU Node Groups (P4d, P5, Trn1, G5)
│  ├─ EKS Add-ons (EBS CSI, FSx CSI, VPC CNI)
│  └─ HyperPod Helm Chart
│
├─ SagemakerHyperPodStack (依赖 EksStack)
│  ├─ HyperPod Cluster
│  ├─ Lifecycle Scripts Bucket
│  ├─ Execution Role
│  └─ Instance Groups
│
└─ HyperPodAddonsStack (依赖 SageMaker)
   ├─ Training Operator
   ├─ Task Governance (Kueue)
   ├─ Observability (Prometheus/Grafana)
   └─ Pod Identity

Layer 4 (依赖 NetworkStack, StorageStack, EksStack)
└─ FsxLustreStack
   ├─ FSx for Lustre (PERSISTENT_2)
   ├─ Data Repository Association (DRA to S3)
   ├─ Security Group
   └─ CloudWatch Alarms

Layer 5 (依赖 NetworkStack, EksStack)
└─ AlbStack
   ├─ Application Load Balancer
   ├─ HTTPS Listener (TLS 1.2+)
   ├─ WAF Rules (prod only)
   └─ Target Groups
```

### 环境配置对比

| 参数 | Dev | Staging | Prod |
|------|-----|---------|------|
| VPC 模式 | SINGLE_AZ | MULTI_AZ | MULTI_AZ |
| Aurora ACU | 0.5-16 | 2-16 | 4-16 |
| FSx 容量 | 10 TiB | 50 TiB | 100+ TiB |
| FSx 吞吐量 | 125 MB/s/TiB | 250 MB/s/TiB | 500 MB/s/TiB |
| EKS 多 AZ | ❌ | ✅ | ✅ |
| WAF 启用 | ❌ | ❌ | ✅ |
| 删除保护 | ❌ | ✅ | ✅ |

## 存储架构

### S3 存储桶

```
┌─────────────────────────────────────────────────────────────┐
│                       S3 Datasets Bucket                     │
│  datasets/{user_id}/{dataset_id}/                           │
│  ├─ versions/{version_id}/                                  │
│  │   ├─ data/                     # 实际数据文件            │
│  │   └─ metadata.json             # 版本元数据              │
│  └─ manifest.json                 # 数据集清单              │
│                                                              │
│  Lifecycle: Standard → IA (30天) → Glacier (90天)           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       S3 Models Bucket                       │
│  models/{user_id}/{model_id}/                               │
│  ├─ versions/{version_id}/                                  │
│  │   ├─ artifacts/                # 模型权重、配置          │
│  │   └─ metadata.json             # 版本元数据              │
│  └─ manifest.json                 # 模型清单                │
│                                                              │
│  Lifecycle: Standard → IA (60天) → Glacier (180天)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    S3 Checkpoints Bucket                     │
│  checkpoints/{job_id}/                                       │
│  ├─ step_{step}/                  # 按步数组织              │
│  │   ├─ model_state.pt            # 模型状态                │
│  │   ├─ optimizer_state.pt        # 优化器状态              │
│  │   └─ metadata.json             # 检查点元数据            │
│  └─ latest -> step_{N}            # 最新检查点符号链接       │
│                                                              │
│  Lifecycle: Standard → IA (7天) → Delete (30天)             │
└─────────────────────────────────────────────────────────────┘
```

### FSx for Lustre

```
FSx Lustre 文件系统
├─ 挂载点: /fsx
├─ 容量: 10-100+ TiB
├─ 吞吐量: 125-1000 MB/s/TiB
├─ DRA (Data Repository Association)
│   └─ S3 → /fsx 自动同步
└─ 用途:
   ├─ 训练数据高速读取
   ├─ 检查点高速写入
   └─ 模型产物暂存
```

### Aurora MySQL

```
Aurora Serverless v2
├─ 引擎: MySQL 8.0
├─ ACU: 0.5-16 (自动扩缩)
├─ 多 AZ: 生产环境启用
├─ RDS Proxy: 连接池
├─ 备份: 7 天自动备份
└─ 数据库:
   └─ ai_training_platform
      ├─ users
      ├─ training_jobs
      ├─ checkpoints
      ├─ datasets
      ├─ dataset_versions
      ├─ models
      ├─ model_versions
      ├─ resource_quotas
      ├─ development_spaces
      └─ audit_logs
```

## K8s 集成

### 资源清单位置

```
infrastructure/k8s/
├─ hyperpod-addons/
│   ├─ training/
│   │   ├─ resource-flavors.yaml    # Kueue ResourceFlavor
│   │   ├─ cluster-queues.yaml      # ClusterQueue
│   │   ├─ local-queues.yaml        # LocalQueue
│   │   └─ training-operator-config.yaml
│   ├─ spaces/
│   │   ├─ efs-storage-class.yaml
│   │   ├─ space-templates.yaml
│   │   └─ spaces-controller.yaml
│   └─ ops/
│       ├─ prometheus-config.yaml
│       ├─ grafana-dashboards.yaml
│       ├─ alerting-rules.yaml
│       └─ dcgm-exporter.yaml
├─ storage/
│   └─ fsx-storage-class.yaml       # FSx CSI StorageClass
└─ network-policies/
    └─ default-deny-policy.yaml
```

### Kueue 队列配置

```yaml
# ClusterQueue 示例
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: high-priority
spec:
  namespaceSelector: {}
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: p4d-24xlarge
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 8
        - name: p5-48xlarge
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 8
  preemption:
    reclaimWithinCohort: Any
    borrowWithinCohort:
      policy: LowerPriority
```

### 训练任务 CRD

```yaml
# PyTorchJob 示例
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: training-job-{id}
  namespace: training
  labels:
    kueue.x-k8s.io/queue-name: high-priority
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      template:
        spec:
          containers:
            - name: pytorch
              image: {ecr}/training:latest
              resources:
                limits:
                  nvidia.com/gpu: 8
              volumeMounts:
                - name: fsx
                  mountPath: /fsx
          volumes:
            - name: fsx
              persistentVolumeClaim:
                claimName: fsx-pvc
    Worker:
      replicas: 3
      # ...
```

## 关键文件路径

| 用途 | 路径 |
|------|------|
| 数据模型设计 | `specs/001-ai-training-platform/data-model.md` |
| CDK 入口 | `infrastructure/cdk/app.py` |
| Network Stack | `infrastructure/cdk/stacks/foundation/network_stack.py` |
| IAM Stack | `infrastructure/cdk/stacks/foundation/iam_stack.py` |
| Database Stack | `infrastructure/cdk/stacks/data/database_stack.py` |
| Storage Stack | `infrastructure/cdk/stacks/data/storage_stack.py` |
| EKS Stack | `infrastructure/cdk/stacks/compute/eks_stack.py` |
| HyperPod Stack | `infrastructure/cdk/stacks/compute/sagemaker_hyperpod_stack.py` |
| FSx Stack | `infrastructure/cdk/stacks/data/fsx_stack.py` |
| ALB Stack | `infrastructure/cdk/stacks/networking/alb_stack.py` |
| 环境配置 | `infrastructure/cdk/config/environments.py` |
| K8s 资源 | `infrastructure/k8s/` |

## 部署命令

```bash
# 开发环境部署
cdk deploy --context env=dev \
  ai-platform-dev-network \
  ai-platform-dev-iam \
  ai-platform-dev-database \
  ai-platform-dev-storage

cdk deploy --context env=dev \
  ai-platform-dev-eks \
  ai-platform-dev-sagemaker-hyperpod \
  ai-platform-dev-hyperpod-addons \
  ai-platform-dev-fsx \
  ai-platform-dev-alb

# K8s 资源应用
kubectl apply -k infrastructure/k8s/hyperpod-addons/training/
kubectl apply -k infrastructure/k8s/hyperpod-addons/ops/
kubectl apply -f infrastructure/k8s/storage/fsx-storage-class.yaml
```
