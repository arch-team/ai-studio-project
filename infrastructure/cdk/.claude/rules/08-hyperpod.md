---
paths:
  - "stacks/compute/sagemaker_hyperpod_stack.py"
  - "stacks/compute/hyperpod_addons_stack.py"
  - "stacks/compute/eks_stack.py"
  - "stacks/data/fsx_stack.py"
  - "resources/helm_charts/**/*"
---

# HyperPod 部署规范

## 架构概览

```
┌─────────────────────────────────────┐
│       SageMaker HyperPod            │
│  ┌─────────┐ ┌─────────┐ ┌───────┐  │
│  │Controller│ │ System  │ │  GPU  │  │
│  │ml.m5.xl │ │ml.m5.4xl│ │p4d/p5 │  │
│  └─────────┘ └─────────┘ └───────┘  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────┴───────────────────┐
│            EKS Cluster              │
│  • Training Operator (PyTorchJob)   │
│  • Kueue (Task Governance)          │
│  • Prometheus + Grafana             │
└─────────────────┬───────────────────┘
                  │
┌─────────────────┴───────────────────┐
│         FSx for Lustre              │
└─────────────────────────────────────┘
```

---

## 部署顺序

**前置条件**:
```bash
./resources/scripts/setup_helm_chart.sh  # 下载 Helm Chart
```

**部署流程**:
```
EksStack → SagemakerHyperPodStack → HyperPodAddonsStack → FsxLustreStack
```

---

## 实例组配置

| 实例组 | Dev | Staging | Prod |
|--------|-----|---------|------|
| Controller | 1 x ml.m5.xlarge | 1 x ml.m5.xlarge | 1 x ml.m5.xlarge |
| System | 1 x ml.m5.4xlarge | 2 x ml.m5.4xlarge | 2 x ml.m5.4xlarge |
| GPU Training | 1 x p4d.24xlarge | 2 x p4d.24xlarge | 4 x p5.48xlarge |

### GPU 实例类型

| 类型 | GPU | 显存 | 网络 | 用途 |
|------|-----|------|------|------|
| p4d.24xlarge | 8x A100 | 320GB | 400 Gbps EFA | 标准训练 |
| p5.48xlarge | 8x H100 | 640GB | 3200 Gbps EFA | 大模型训练 |
| trn1.32xlarge | 16x Trainium | 512GB | 800 Gbps EFA | 成本优化 |

---

## Helm Chart 安装

### 目录结构

```
resources/helm_charts/HyperPodHelmChart/
├── Chart.yaml
├── values.yaml
└── templates/
```

### EKS 中安装

```python
def _install_hyperpod_helm_chart(self) -> None:
    chart_path = Path(__file__).parent.parent.parent / HELM_CONFIG.HYPERPOD_CHART_PATH

    self._cluster.add_helm_chart(
        "HyperPodChart",
        chart=str(chart_path),
        namespace=K8S_NAMESPACES.KUBE_SYSTEM,
        timeout=Duration.minutes(15),  # 重要: 15 分钟超时
    )
```

---

## Add-ons 安装

### Training Operator

```python
cluster.add_helm_chart(
    "TrainingOperator",
    chart=HELM_CONFIG.TRAINING_OPERATOR_CHART,
    repository=HELM_CONFIG.TRAINING_OPERATOR_REPO,
    namespace=K8S_NAMESPACES.TRAINING,
    create_namespace=True,
    timeout=Duration.minutes(15),
)
```

### Kueue

```python
cluster.add_helm_chart(
    "Kueue",
    chart=HELM_CONFIG.KUEUE_CHART,
    repository=HELM_CONFIG.KUEUE_REPO,
    namespace=K8S_NAMESPACES.KUBE_SYSTEM,
    timeout=Duration.minutes(15),
)
```

---

## FSx for Lustre

```python
self._file_system = fsx.LustreFileSystem(
    self, "LustreFS",
    vpc=vpc,
    vpc_subnet=vpc.select_subnets(
        subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
    ).subnets[0],
    storage_capacity_gib=env_config.storage.fsx_capacity_tib * 1024,
    lustre_configuration=fsx.LustreConfiguration(
        deployment_type=fsx.LustreDeploymentType.PERSISTENT_2,
        per_unit_storage_throughput=250,
        data_compression_type=fsx.LustreDataCompressionType.LZ4,
    ),
)
```

**安全组**: 允许端口 988 (Lustre)

---

## PyTorchJob 示例

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: distributed-training
  namespace: training
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      template:
        spec:
          containers:
          - name: pytorch
            image: your-image:latest
            resources:
              limits:
                nvidia.com/gpu: 8
    Worker:
      replicas: 3
      template:
        spec:
          containers:
          - name: pytorch
            image: your-image:latest
            resources:
              limits:
                nvidia.com/gpu: 8
```

---

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Helm 安装超时 | Chart 下载慢 | 增加超时到 15 分钟 |
| 节点组启动失败 | IAM 权限不足 | 检查节点角色策略 |
| GPU 不可用 | NVIDIA 驱动未安装 | 使用 GPU AMI |
| FSx 挂载失败 | 安全组规则 | 允许 988 端口 |

### 调试命令

```bash
# HyperPod 状态
aws sagemaker describe-cluster --cluster-name <name>
aws sagemaker list-cluster-nodes --cluster-name <name>

# EKS 节点
kubectl get nodes -l sagemaker.amazonaws.com/cluster-name=<name>

# Training Operator
kubectl get pods -n training -l app=training-operator
```
