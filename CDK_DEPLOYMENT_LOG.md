# CDK Stacks 部署日志

## 部署顺序
NetworkStack → IamStack → DatabaseStack → StorageStack → EksStack → SagemakerHyperPodStack → FsxLustreStack → AlbStack

## 部署状态汇总

| Stack | 状态 | 部署时间 | 备注 |
|-------|------|----------|------|
| NetworkStack | ✅ CREATE_COMPLETE | 已部署 | VPC + 子网 + NAT Gateway |
| IamStack | ✅ CREATE_COMPLETE | 已部署 | EKS Node Role + Service Roles |
| DatabaseStack | ✅ CREATE_COMPLETE | 已部署 | Aurora MySQL Serverless v2 |
| StorageStack | ✅ CREATE_COMPLETE | 已部署 | S3 Buckets |
| EksStack | ✅ CREATE_COMPLETE | 2025-01-10 | K8s 1.33 + Add-ons + Helm Chart |
| SagemakerHyperPodStack | ✅ CREATE_COMPLETE | 2025-01-10 | HyperPod 集群 |
| FsxLustreStack | ✅ CREATE_COMPLETE | 2025-01-10 | 12 TiB FSx Lustre |
| AlbStack | ✅ CREATE_COMPLETE | 2025-01-10 | HTTP-only (dev 环境) |

---

## 问题记录与解决方案

### 问题 1: HyperPodStack ServiceAccount 冲突

**时间**: 首次部署

**错误现象**: Stack 状态为 ROLLBACK_COMPLETE

**错误原因**:
ServiceAccount 冲突 - EKS add-ons (aws-ebs-csi-driver, aws-fsx-csi-driver) 在安装时会自动创建 ServiceAccount (`ebs-csi-controller-sa`, `fsx-csi-controller-sa`)，而 CDK 代码中使用 `cluster.add_service_account()` 又试图创建同名的 ServiceAccount，导致 "AlreadyExists" 错误。

**解决方案**:
1. 移除 `add_service_account()` 调用，因为 add-on 会自动创建 ServiceAccount
2. 直接创建 IAM Role (用于 IRSA - IAM Roles for Service Accounts)
3. 在 EKS add-on 配置中通过 `serviceAccountRoleArn` 参数引用这个 Role

---

### 问题 2: HyperPod 执行角色缺少 EC2 权限

**时间**: Iteration 3 部署

**错误现象**:
```
Unable to retrieve subnets. Please ensure that the execution role allows the action sts:AssumeRole for the service principal sagemaker.amazonaws.com
```

**错误原因**:
HyperPod 执行角色只有 `AmazonSageMakerClusterInstanceRolePolicy` 托管策略，缺少 EKS 编排所需的 EC2 网络权限。

**解决方案**:
在 `_create_hyperpod_execution_role()` 中添加以下权限：
- `ec2:DescribeSubnets`, `ec2:DescribeSecurityGroups`, `ec2:DescribeVpcs` 等 EC2 网络权限
- `ec2:CreateNetworkInterface`, `ec2:DeleteNetworkInterface` 等网络接口管理权限
- `ecr:BatchGetImage`, `ecr:GetAuthorizationToken` 等 ECR 权限
- `eks-auth:AssumeRoleForPodIdentity` (可选)

**参考文档**: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-prerequisites-iam.html

---

### 问题 3: HyperPod 缺少 EKS Helm Chart 依赖

**时间**: Iteration 4 部署

**错误现象**:
```
The Amazon EKS orchestrator cluster ai-platform-dev-eks is missing one or more required dependencies.
```

**错误原因**:
SageMaker HyperPod 需要在 EKS 集群上预先安装 Helm Chart 依赖项，包括：
- Health monitoring agent
- Deep health check
- Job auto-restart
- Kubeflow MPI operator
- NVIDIA device plugin
- Neuron device plugin
- AWS EFA device plugin

CDK 直接部署 HyperPodCluster 时，这些依赖不会自动安装。

**解决方案 (v1 - 手动步骤)**:
需要将部署分为两个阶段：

**阶段 1**: 先部署 EKS 集群（不包含 HyperPod）
1. 创建独立的 `EksStack` 只包含 EKS 集群和 add-ons
2. 部署 EKS Stack
3. 配置 kubectl 访问 EKS 集群
4. 安装 HyperPod Helm Chart 依赖：
   ```bash
   git clone https://github.com/aws/sagemaker-hyperpod-cli.git
   cd sagemaker-hyperpod-cli/helm_chart
   helm dependencies update HyperPodHelmChart
   helm install hyperpod-dependencies HyperPodHelmChart --namespace kube-system
   ```

**阶段 2**: 再部署 HyperPod 集群
1. 创建独立的 `HyperPodStack` 引用已有的 EKS 集群
2. 部署 HyperPod Stack

**解决方案 (v2 - CDK 自动化) ✅ 当前采用**:
使用 CDK HelmChart + chartAsset 实现完全自动化部署：

1. 运行 `./scripts/setup_helm_chart.sh` 下载 Helm Chart
2. EksStack 使用 `add_helm_chart()` 自动安装 HyperPod 依赖
3. 单次 `cdk deploy ai-platform-dev-eks` 完成 EKS + Helm Chart 部署

**参考文档**: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-install-packages-using-helm-chart.html

---

### 问题 4: Helm Chart 安装超时

**时间**: Iteration 7 部署

**错误现象**:
```
UPGRADE FAILED: context deadline exceeded
```

**错误原因**:
CDK HelmChart 默认超时为 5 分钟，对于包含多个子 chart 的 HyperPod Helm Chart 来说不够。

**解决方案**:
在 `add_helm_chart()` 中添加 `timeout=cdk.Duration.minutes(15)` 参数：
```python
self._eks_cluster.add_helm_chart(
    "HyperPodDependencies",
    ...
    timeout=cdk.Duration.minutes(15),
)
```

---

### 问题 5: Helm Release 锁定状态

**时间**: Iteration 7 部署

**错误现象**:
```
UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress
```

**错误原因**:
前一次 Helm 操作失败或超时，导致 release 处于锁定状态。Helm 在 Kubernetes secrets 中保存 release 状态。

**解决方案**:
1. 删除卡住的 Helm release secrets：
```bash
kubectl delete secrets -n kube-system \
  sh.helm.release.v1.hyperpod-dependencies.v1 \
  sh.helm.release.v1.hyperpod-dependencies.v2 \
  sh.helm.release.v1.hyperpod-dependencies.v3
```

2. 防止未来发生：在 `add_helm_chart()` 中添加：
```python
wait=False,      # 不等待 pod ready（因为还没有节点）
skip_crds=True,  # 跳过已存在的 CRDs
```

---

### 问题 6: HyperPod IAM 角色传播延迟

**时间**: Iteration 7 部署

**错误现象**:
```
Unable to retrieve subnets. Please ensure that the execution role allows...
```
（IAM 角色权限正确配置，但 HyperPod 仍然报错）

**错误原因**:
IAM 角色和策略的更改需要时间传播。当 CloudFormation 创建 HyperPod 集群时，IAM 角色的策略可能还没有完全传播。

**解决方案**:
在 `sagemaker_hyperpod_stack.py` 中添加显式依赖：
```python
# Ensure HyperPod cluster is created after the IAM role and its policies are fully created
# This prevents "Unable to retrieve subnets" error due to IAM propagation delay
cluster.node.add_dependency(self._hyperpod_execution_role)
```

---

### 问题 7: ALB HTTPS 证书缺失

**时间**: Iteration 7 部署

**错误现象**:
```
Certificate ARN '' is not valid (Service: ElasticLoadBalancingV2)
```

**错误原因**:
AlbStack 需要 ACM 证书 ARN 用于 HTTPS Listener，但 dev 环境没有提供证书。

**解决方案**:
修改 `alb_stack.py` 支持 HTTP-only 模式（仅限 dev 环境）：
1. 添加 `_https_enabled` 标志检测是否需要 HTTPS
2. 创建 `_create_http_listener()` 方法用于 HTTP-only 模式
3. 根据环境选择创建 HTTPS + HTTP redirect 或 HTTP-only listener
4. 输出安全警告提醒 HTTP-only 不适合生产环境

**注意**: 生产环境必须提供 ACM 证书 ARN：
```bash
cdk deploy ai-platform-prod-alb --context certificate_arn=arn:aws:acm:...
```

---

## 迭代记录

### Iteration 1
- 检查现有 Stack 部署状态
- 发现 NetworkStack, IamStack, DatabaseStack, StorageStack 已成功部署
- HyperPodStack 处于 ROLLBACK_COMPLETE 状态
- 删除失败的 Stack
- 重新部署 HyperPodStack
- 再次失败：ServiceAccount 冲突错误

### Iteration 2
- 分析失败原因：EKS add-ons 自动创建 ServiceAccount，与 CDK 代码冲突
- 修改 hyperpod_stack.py，移除 add_service_account() 调用
- 改用直接创建 IAM Role 并配置 add-on 的 serviceAccountRoleArn
- CDK synth 失败：OIDC issuer URL 作为 map key 需要使用 CfnJson
- 修复：使用 cdk.CfnJson 延迟解析 OIDC issuer URL
- CDK synth 成功，开始重新部署

### Iteration 3
- 部署失败：HyperPod 执行角色缺少 EC2 权限
- 修改 hyperpod_stack.py，添加 EC2 网络权限、ECR 权限等
- 重新部署 HyperPodStack

### Iteration 4
- EKS 集群创建成功
- HyperPod 创建失败：缺少 Helm Chart 依赖
- 需要重构架构，将 EKS 和 HyperPod 分离为两个独立 Stack

### Iteration 5
- 创建 `EksStack` (eks_stack.py) - 只包含 EKS 集群和 add-ons
- 创建 `SagemakerHyperPodStack` (sagemaker_hyperpod_stack.py) - 引用已有 EKS 集群
- 更新 `__init__.py` 导出新 stacks
- 更新 `app.py` 添加新 stacks 定义和 CDK Nag suppressions
- CDK synth 验证成功，新 stacks 已添加
- 下一步：部署 EksStack，然后安装 Helm Chart，再部署 SagemakerHyperPodStack

### Iteration 6 - CDK HelmChart 自动化
- 实现 CDK HelmChart + chartAsset 自动化部署方案
- 创建 `scripts/setup_helm_chart.sh` - 自动下载 HyperPod Helm Chart
- 修改 `EksStack` 添加 `_install_hyperpod_helm_chart()` 方法
- 使用 `cluster.add_helm_chart()` 和 `chart_asset` 自动安装 Helm Chart
- 配置启用的组件：
  - ✅ trainingOperators
  - ✅ health-monitoring-agent
  - ✅ deep-health-check
  - ✅ job-auto-restart
  - ✅ mpi-operator
  - ✅ hyperpod-patching
  - ✅ nvidia-device-plugin
  - ✅ neuron-device-plugin
  - ✅ aws-efa-k8s-device-plugin
- CDK synth 验证成功

### Iteration 7 (当前) - 全部 Stack 部署完成 ✅

**部署过程**:

1. **EksStack 部署** - 遇到 Helm Chart 超时和锁定问题
   - 问题 4: 添加 `timeout=cdk.Duration.minutes(15)`
   - 问题 5: 删除锁定的 secrets，添加 `wait=False` 和 `skip_crds=True`
   - 配置 kubectl 访问权限
   - ✅ 部署成功

2. **SagemakerHyperPodStack 部署** - 遇到 IAM 传播延迟问题
   - 问题 6: 添加 `cluster.node.add_dependency(self._hyperpod_execution_role)`
   - ✅ 部署成功

3. **FsxLustreStack 部署**
   - ✅ 部署成功 (12 TiB FSx Lustre，~20 分钟)

4. **AlbStack 部署** - 遇到 HTTPS 证书缺失问题
   - 问题 7: 修改支持 HTTP-only 模式 (dev 环境)
   - ✅ 部署成功

**部署输出**:

| 资源 | 值 |
|------|-----|
| EKS Cluster | ai-platform-dev-eks |
| HyperPod Cluster | ai-platform-dev-hyperpod |
| FSx File System | fs-070fe86bfe83262c1 |
| FSx DNS Name | fs-070fe86bfe83262c1.fsx.us-east-1.amazonaws.com |
| FSx Mount Name | socgvamv |
| ALB DNS Name | ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com |

---

## 部署指南

### 首次部署 (完整流程)

```bash
cd infrastructure/cdk

# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 下载 HyperPod Helm Chart (首次部署必需)
./scripts/setup_helm_chart.sh

# 3. 部署所有 Stacks
cdk deploy --all --require-approval never
```

### 单独部署特定 Stack

```bash
# 部署 EKS Stack (包含 Helm Chart)
cdk deploy ai-platform-dev-eks

# 部署 HyperPod Stack
cdk deploy ai-platform-dev-sagemaker-hyperpod

# 部署 FSx Lustre Stack
cdk deploy ai-platform-dev-fsx

# 部署 ALB Stack (dev 环境 HTTP-only)
cdk deploy ai-platform-dev-alb

# 部署 ALB Stack (生产环境需要证书)
cdk deploy ai-platform-prod-alb --context certificate_arn=arn:aws:acm:...
```

### Helm Chart 更新

```bash
# 重新运行下载脚本获取最新版本
./scripts/setup_helm_chart.sh

# 重新部署 EKS Stack
cdk deploy ai-platform-dev-eks
```

### 配置 kubectl 访问

```bash
# 配置 kubeconfig
aws eks update-kubeconfig --name ai-platform-dev-eks --region us-east-1

# 添加 IAM 用户访问权限 (如需要)
aws eks create-access-entry --cluster-name ai-platform-dev-eks \
  --principal-arn arn:aws:iam::ACCOUNT:user/USERNAME --type STANDARD

aws eks associate-access-policy --cluster-name ai-platform-dev-eks \
  --principal-arn arn:aws:iam::ACCOUNT:user/USERNAME \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```
