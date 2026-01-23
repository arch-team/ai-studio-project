---
paths:
  - "stacks/compute/sagemaker_hyperpod_stack.py"
  - "stacks/compute/hyperpod_addons_stack.py"
  - "stacks/compute/eks_stack.py"
  - "stacks/data/fsx_stack.py"
  - "resources/helm_charts/**/*"
---

# HyperPod 部署规范

## 概述

SageMaker HyperPod 是 AWS 提供的托管 GPU 集群服务，用于大规模分布式训练。本项目使用 HyperPod with EKS 模式。

---

## 部署架构

```
                    ┌─────────────────────────────────────┐
                    │           SageMaker HyperPod        │
                    │  ┌───────────────────────────────┐  │
                    │  │      Instance Groups          │  │
                    │  │  ┌─────────┐  ┌─────────┐     │  │
                    │  │  │Controller│  │ System  │     │  │
                    │  │  │ml.m5.xl │  │ml.m5.4xl│     │  │
                    │  │  └─────────┘  └─────────┘     │  │
                    │  │  ┌─────────────────────────┐  │  │
                    │  │  │     GPU Training        │  │  │
                    │  │  │  p4d.24xl / p5.48xl    │  │  │
                    │  │  └─────────────────────────┘  │  │
                    │  └───────────────────────────────┘  │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────┴───────────────────┐
                    │              EKS Cluster            │
                    │  ┌─────────────────────────────┐    │
                    │  │        Add-ons              │    │
                    │  │  • Training Operator        │    │
                    │  │  • Kueue (Task Governance)  │    │
                    │  │  • Prometheus + Grafana     │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────┴───────────────────┐
                    │           FSx for Lustre           │
                    │     (High-Performance Storage)      │
                    └─────────────────────────────────────┘
```

---

## 部署顺序

### 前置条件

```bash
# 1. 下载 HyperPod Helm Chart (首次部署前)
./resources/scripts/setup_helm_chart.sh
```

### 部署流程

```
1. EksStack (包含 Helm Chart 自动安装)
       ↓
2. SagemakerHyperPodStack
       ↓
3. HyperPodAddonsStack (Training Operator, Kueue, Observability)
       ↓
4. FsxLustreStack
```

---

## Stack 实现规范

### SagemakerHyperPodStack

```python
"""SageMaker HyperPod Stack"""
from aws_cdk import aws_sagemaker as sagemaker

class SagemakerHyperPodStack(Stack):
    """HyperPod 集群 Stack"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        vpc: ec2.IVpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._env_config = env_config

        # 创建实例组
        self._create_instance_groups()

        # 创建 HyperPod 集群
        self._create_cluster(eks_cluster, vpc)

    def _create_instance_groups(self) -> None:
        """创建实例组配置"""
        self._instance_groups = [
            # Controller 组 (必须)
            self._create_controller_group(),
            # System 组 (必须)
            self._create_system_group(),
            # GPU Training 组
            self._create_training_group(),
        ]

    def _create_controller_group(self) -> dict:
        """Controller 实例组"""
        return {
            "instance_group_name": INSTANCE_GROUP_NAMES.CONTROLLER,
            "instance_type": "ml.m5.xlarge",
            "instance_count": 1,
            "life_cycle_config": {
                "source_s3_uri": f"s3://{self._config_bucket}/lifecycle/controller/",
                "on_create": "on_create.sh",
            },
        }

    def _create_system_group(self) -> dict:
        """System 实例组"""
        return {
            "instance_group_name": INSTANCE_GROUP_NAMES.SYSTEM,
            "instance_type": "ml.m5.4xlarge",
            "instance_count": 2,
        }

    def _create_training_group(self) -> dict:
        """GPU Training 实例组"""
        config = self._env_config.hyperpod
        return {
            "instance_group_name": INSTANCE_GROUP_NAMES.GPU_TRAINING,
            "instance_type": config.gpu_instance_type,
            "instance_count": config.gpu_instance_count,
        }

    def _create_cluster(
        self,
        eks_cluster: eks.ICluster,
        vpc: ec2.IVpc,
    ) -> None:
        """创建 HyperPod 集群"""
        self._cluster = sagemaker.CfnCluster(
            self, "HyperPodCluster",
            cluster_name=f"{self._env_config.project_name}-{self._env_config.environment_name}",
            instance_groups=self._instance_groups,
            orchestrator=sagemaker.CfnCluster.OrchestratorProperty(
                eks=sagemaker.CfnCluster.EksProperty(
                    cluster_arn=eks_cluster.cluster_arn,
                ),
            ),
            vpc_config=sagemaker.CfnCluster.VpcConfigProperty(
                security_group_ids=[self._security_group.security_group_id],
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ).subnet_ids,
            ),
        )
```

### HyperPodAddonsStack

```python
"""HyperPod Add-ons Stack"""

class HyperPodAddonsStack(Stack):
    """HyperPod 附加组件 Stack"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        eks_cluster: eks.ICluster,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Training Operator
        self._install_training_operator(eks_cluster)

        # Kueue (Task Governance)
        self._install_kueue(eks_cluster)

        # Observability
        self._install_observability(eks_cluster)

    def _install_training_operator(self, cluster: eks.ICluster) -> None:
        """安装 Training Operator"""
        cluster.add_helm_chart(
            "TrainingOperator",
            chart=HELM_CONFIG.TRAINING_OPERATOR_CHART,
            repository=HELM_CONFIG.TRAINING_OPERATOR_REPO,
            version=HELM_CONFIG.TRAINING_OPERATOR_VERSION,
            namespace=K8S_NAMESPACES.TRAINING,
            create_namespace=True,
            values={
                "fullnameOverride": EKS_ADDON_NAMES.TRAINING_OPERATOR,
            },
            timeout=Duration.minutes(TIMEOUTS.HELM_INSTALL_MINUTES),
        )

    def _install_kueue(self, cluster: eks.ICluster) -> None:
        """安装 Kueue 任务治理"""
        cluster.add_helm_chart(
            "Kueue",
            chart=HELM_CONFIG.KUEUE_CHART,
            repository=HELM_CONFIG.KUEUE_REPO,
            version=HELM_CONFIG.KUEUE_VERSION,
            namespace=K8S_NAMESPACES.KUBE_SYSTEM,
            timeout=Duration.minutes(TIMEOUTS.HELM_INSTALL_MINUTES),
        )

    def _install_observability(self, cluster: eks.ICluster) -> None:
        """安装可观测性组件"""
        # Amazon Managed Prometheus
        self._prometheus = aps.CfnWorkspace(
            self, "Prometheus",
            alias=f"{self._env_config.project_name}-prometheus",
        )

        # Amazon Managed Grafana
        self._grafana = grafana.CfnWorkspace(
            self, "Grafana",
            account_access_type="CURRENT_ACCOUNT",
            authentication_providers=["AWS_SSO"],
            permission_type="SERVICE_MANAGED",
            data_sources=["PROMETHEUS"],
        )
```

---

## 实例组配置

### 环境特定配置

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

## Helm Chart 管理

### 目录结构

```
resources/helm_charts/
└── HyperPodHelmChart/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        └── ...
```

### 下载脚本

```bash
#!/bin/bash
# resources/scripts/setup_helm_chart.sh

set -e

CHART_DIR="resources/helm_charts/HyperPodHelmChart"

if [ -d "$CHART_DIR" ]; then
    echo "Helm chart already exists"
    exit 0
fi

echo "Downloading HyperPod Helm chart..."

# 从 AWS 官方源下载
aws s3 cp s3://sagemaker-hyperpod-helm-charts/HyperPodHelmChart.tgz .
tar -xzf HyperPodHelmChart.tgz -C resources/helm_charts/
rm HyperPodHelmChart.tgz

echo "Helm chart downloaded successfully"
```

### EKS 中安装

```python
# stacks/compute/eks_stack.py

def _install_hyperpod_helm_chart(self) -> None:
    """安装 HyperPod Helm Chart"""
    chart_path = Path(__file__).parent.parent.parent / HELM_CONFIG.HYPERPOD_CHART_PATH

    self._cluster.add_helm_chart(
        "HyperPodChart",
        chart=str(chart_path),
        namespace=K8S_NAMESPACES.KUBE_SYSTEM,
        values={
            "cluster": {
                "name": self._cluster.cluster_name,
            },
        },
        timeout=Duration.minutes(TIMEOUTS.HELM_INSTALL_MINUTES),  # 15 分钟
    )
```

---

## Training Operator 使用

### PyTorchJob CRD

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
            image: your-training-image:latest
            resources:
              limits:
                nvidia.com/gpu: 8
    Worker:
      replicas: 3
      template:
        spec:
          containers:
          - name: pytorch
            image: your-training-image:latest
            resources:
              limits:
                nvidia.com/gpu: 8
```

### Kueue 资源配额

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: gpu-cluster-queue
spec:
  resourceGroups:
  - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
    flavors:
    - name: gpu-flavor
      resources:
      - name: "cpu"
        nominalQuota: 1000
      - name: "memory"
        nominalQuota: "4000Gi"
      - name: "nvidia.com/gpu"
        nominalQuota: 32
```

---

## FSx for Lustre 集成

### 配置

```python
class FsxLustreStack(Stack):
    """FSx for Lustre Stack"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,
        training_bucket: s3.IBucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 创建 FSx 文件系统
        self._file_system = fsx.LustreFileSystem(
            self, "LustreFS",
            vpc=vpc,
            vpc_subnet=vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ).subnets[0],
            storage_capacity_gib=env_config.storage.fsx_capacity_tib * 1024,
            lustre_configuration=fsx.LustreConfiguration(
                deployment_type=fsx.LustreDeploymentType.PERSISTENT_2,
                per_unit_storage_throughput=250,  # MB/s/TiB
                data_compression_type=fsx.LustreDataCompressionType.LZ4,
            ),
        )

        # S3 数据仓库关联
        self._create_data_repository_association(training_bucket)
```

### 挂载到 EKS

```python
# CSI Driver 配置
fsx_csi_values = {
    "controller": {
        "serviceAccount": {
            "create": True,
            "annotations": {
                "eks.amazonaws.com/role-arn": fsx_csi_role.role_arn,
            },
        },
    },
}

cluster.add_helm_chart(
    "FsxCsiDriver",
    chart="aws-fsx-csi-driver",
    repository="https://kubernetes-sigs.github.io/aws-fsx-csi-driver",
    namespace="kube-system",
    values=fsx_csi_values,
)
```

---

## 监控和告警

### CloudWatch 指标

```python
def _create_alarms(self) -> None:
    """创建 HyperPod 告警"""

    # GPU 利用率告警
    cloudwatch.Alarm(
        self, "GpuUtilizationAlarm",
        metric=cloudwatch.Metric(
            namespace="AWS/SageMaker",
            metric_name="GPUUtilization",
            dimensions_map={
                "ClusterName": self._cluster.cluster_name,
            },
            statistic="Average",
            period=Duration.minutes(5),
        ),
        threshold=90,
        evaluation_periods=3,
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    )

    # 节点健康告警
    cloudwatch.Alarm(
        self, "NodeHealthAlarm",
        metric=cloudwatch.Metric(
            namespace="AWS/SageMaker",
            metric_name="UnhealthyNodeCount",
            dimensions_map={
                "ClusterName": self._cluster.cluster_name,
            },
            statistic="Maximum",
            period=Duration.minutes(1),
        ),
        threshold=0,
        evaluation_periods=1,
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    )
```

---

## 故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Helm 安装超时 | Chart 下载慢 | 增加超时到 15 分钟 |
| 节点组启动失败 | IAM 权限不足 | 检查节点角色策略 |
| GPU 不可用 | NVIDIA 驱动未安装 | 使用 GPU AMI |
| FSx 挂载失败 | 安全组规则 | 允许 988 端口 |

### 调试命令

```bash
# 检查 HyperPod 集群状态
aws sagemaker describe-cluster --cluster-name <cluster-name>

# 检查实例组状态
aws sagemaker list-cluster-nodes --cluster-name <cluster-name>

# 检查 EKS 节点
kubectl get nodes -l sagemaker.amazonaws.com/cluster-name=<cluster-name>

# 检查 Training Operator
kubectl get pods -n training -l app=training-operator
```
