# CDK Stacks 部署日志

## 部署顺序
NetworkStack → IamStack → DatabaseStack → StorageStack → EksStack → SagemakerHyperPodStack → FsxLustreStack → AlbStack

## 部署状态汇总

| Stack | 状态 | 时间 | 备注 |
|-------|------|------|------|
| NetworkStack | ✅ CREATE_COMPLETE | 已部署 | - |
| IamStack | ✅ CREATE_COMPLETE | 已部署 | - |
| DatabaseStack | ✅ CREATE_COMPLETE | 已部署 | - |
| StorageStack | ✅ CREATE_COMPLETE | 已部署 | - |
| EksStack | ⏳ 待部署 | - | 包含 Helm Chart 自动安装 |
| SagemakerHyperPodStack | ⏳ 待部署 | - | 依赖 EksStack |
| FsxLustreStack | ⏳ 待部署 | - | 依赖 EksStack |
| AlbStack | ⏳ 待部署 | - | 依赖 FsxLustreStack |

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

### Iteration 6 (当前) - CDK HelmChart 自动化
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
- 下一步：运行 `./scripts/setup_helm_chart.sh`，然后部署 `ai-platform-dev-eks`

## 部署新架构 (自动化版本)

新的部署顺序：
1. NetworkStack ✅ (已部署)
2. IamStack ✅ (已部署)
3. DatabaseStack ✅ (已部署)
4. StorageStack ✅ (已部署)
5. **EksStack** ⏳ (待部署) - 包含 Helm Chart 自动安装
6. **SagemakerHyperPodStack** ⏳ (待部署)
7. FsxLustreStack ⏳ (待部署)
8. AlbStack ⏳ (待部署)

### 部署步骤

```bash
# 1. 首次部署前，下载 HyperPod Helm Chart
cd infrastructure/cdk
./scripts/setup_helm_chart.sh

# 2. 部署 EKS Stack (包含 Helm Chart 自动安装)
cdk deploy ai-platform-dev-eks

# 3. 部署 SageMaker HyperPod Stack
cdk deploy ai-platform-dev-sagemaker-hyperpod

# 4. 部署其他 Stacks
cdk deploy ai-platform-dev-fsx ai-platform-dev-alb
```

### Helm Chart 更新步骤 (当需要更新 Helm Chart 时)

```bash
# 重新运行下载脚本获取最新版本
./scripts/setup_helm_chart.sh

# 重新部署 EKS Stack
cdk deploy ai-platform-dev-eks
```
