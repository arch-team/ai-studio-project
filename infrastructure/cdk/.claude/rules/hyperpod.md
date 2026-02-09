---
paths:
  - "stacks/compute/sagemaker_hyperpod_stack.py"
  - "stacks/compute/hyperpod_addons_stack.py"
  - "stacks/compute/eks_stack.py"
  - "stacks/data/fsx_stack.py"
  - "resources/helm_charts/**/*"
---

# HyperPod 部署规范

## 架构

```
SageMaker HyperPod (Controller + System + GPU 节点)
        ↓
EKS Cluster (Training Operator + Kueue + Monitoring)
        ↓
FSx for Lustre (高性能存储)
```

## 部署顺序

```bash
# 前置
./resources/scripts/setup_helm_chart.sh

# 部署
EksStack → SagemakerHyperPodStack → HyperPodAddonsStack → FsxLustreStack
```

## 实例配置

| 实例组 | Dev | Prod |
|--------|-----|------|
| Controller | 1 x ml.m5.xlarge | 1 x ml.m5.xlarge |
| System | 1 x ml.m5.4xlarge | 2 x ml.m5.4xlarge |
| GPU | 1 x p4d.24xlarge | 4 x p5.48xlarge |

| GPU 类型 | 实例 | 显存 | 网络 |
|----------|------|------|------|
| A100 | p4d.24xlarge | 320GB | 400Gbps EFA |
| H100 | p5.48xlarge | 640GB | 3200Gbps EFA |

## Helm Chart 安装

```python
cluster.add_helm_chart("HyperPodChart",
    chart=str(chart_path),
    namespace="kube-system",
    timeout=Duration.minutes(15))  # 重要: 15 分钟超时
```

## Add-ons

```python
# Training Operator
cluster.add_helm_chart("TrainingOperator",
    chart="training-operator",
    repository="https://kubeflow.github.io/training-operator",
    namespace="training", create_namespace=True)

# Kueue
cluster.add_helm_chart("Kueue",
    chart="kueue", repository="https://kubernetes-sigs.github.io/kueue/charts",
    namespace="kube-system")
```

## FSx for Lustre

```python
fsx.LustreFileSystem(self, "LustreFS", vpc=vpc,
    vpc_subnet=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED).subnets[0],
    lustre_configuration=fsx.LustreConfiguration(
        deployment_type=fsx.LustreDeploymentType.PERSISTENT_2,
        per_unit_storage_throughput=250))
```

**安全组**: 允许端口 988 (Lustre)

## 故障排查

| 问题 | 解决 |
|------|------|
| Helm 超时 | 增加到 15 分钟 |
| GPU 不可用 | 使用 GPU AMI |
| FSx 挂载失败 | 检查 988 端口 |

```bash
aws sagemaker describe-cluster --cluster-name <name>
kubectl get nodes -l sagemaker.amazonaws.com/cluster-name=<name>
```
