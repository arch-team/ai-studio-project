# HyperPod 原生 Spaces — Phase B 基础设施部署记录

> **职责**: 记录 Phase B（基础设施就绪）在真实集群 `ai-platform-dev-eks` 上完成的全部变更，
> 作为环境重建与审计的权威依据。涵盖纯 manifest 无法表达的 CLI/console 操作。
>
> **集群**: `ai-platform-dev-eks` (EKS) / `ai-platform-dev-hyperpod` (HyperPod, ARN cluster/ndownj7gq0f5)
> **区域**: us-east-1 | **账户**: 897473508751
> **执行日期**: 2026-06-13 | **对应计划**: `docs/superpowers/plans/2026-06-13-hyperpod-native-spaces.md` Task 14-16

---

## 0. 关键真实值速查（前端/后端创建 HyperPod Space 必须传对）

| 字段 | 真实值 | 来源 |
|------|--------|------|
| Workspace 命名空间 | `hyperpod-ns-dev-spaces` | Task Governance 托管创建 |
| Kueue LocalQueue | `hyperpod-ns-dev-spaces-localqueue` | Task Governance 自动生成 |
| WorkloadPriorityClass | `interactive-space-priority` (权重 100) | 本阶段创建 |
| Workspace 模板 (Jupyter) | `sagemaker-jupyter-template` @ `jupyter-k8s-system` | add-on 预置 |
| Workspace 模板 (Code Editor) | `sagemaker-code-editor-template` @ `jupyter-k8s-system` | add-on 预置 |
| 访问策略 | `hyperpod-access-strategy` @ `jupyter-k8s-system` | add-on 预置 |
| Operator 命名空间 | `jupyter-k8s-system` | add-on 安装 |

> ⚠️ **注意**: 真实工作命名空间是 Task Governance 托管的 `hyperpod-ns-dev-spaces`，
> **不是**早期 IaC 设想的 `dev-spaces` 或 `sagemaker-spaces`。后者为过时占位（见 §5）。

---

## 1. Task 14: 安装 SageMaker Spaces add-on（基础模式，无 web UI）

### 1.1 依赖核查（全部已就绪）
EKS Pod Identity Agent ✅ · Cert-manager ✅ · EBS CSI Driver ✅ · AWS Load Balancer Controller ✅ · Kueue (HyperPod Task Governance) ✅

### 1.2 为 add-on 创建两个 Pod Identity IAM 角色

add-on 的 controller-manager 与 authmiddleware 两个 SA 需 IAM 角色获取 AWS 凭证。
CLI 安装（非 console quick install）需手动创建：

```bash
# Pod Identity 信任策略 (pods.eks.amazonaws.com)
cat > pod-identity-trust.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
"Principal":{"Service":"pods.eks.amazonaws.com"},
"Action":["sts:AssumeRole","sts:TagSession"]}]}
EOF

aws iam create-role --role-name SageMakerSpacesControllerRole-ai-platform-dev \
  --assume-role-policy-document file://pod-identity-trust.json
aws iam attach-role-policy --role-name SageMakerSpacesControllerRole-ai-platform-dev \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerSpacesControllerPolicy

aws iam create-role --role-name SageMakerSpacesRouterRole-ai-platform-dev \
  --assume-role-policy-document file://pod-identity-trust.json
aws iam attach-role-policy --role-name SageMakerSpacesRouterRole-ai-platform-dev \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerSpacesRouterPolicy
```

### 1.3 安装 add-on（基础模式）

```bash
# 基础模式配置: 仅启用 workspacePodWatching，不配 clusterWebUI
cat > addon-config.yaml <<'EOF'
jupyter-k8s:
  workspacePodWatching:
    enable: true
EOF

aws eks create-addon \
  --cluster-name ai-platform-dev-eks \
  --addon-name amazon-sagemaker-spaces \
  --addon-version v0.1.6-eksbuild.1 \
  --configuration-values file://addon-config.yaml \
  --pod-identity-associations \
      'serviceAccount=jupyter-k8s-controller-manager,roleArn=arn:aws:iam::897473508751:role/SageMakerSpacesControllerRole-ai-platform-dev' \
      'serviceAccount=jupyter-k8s-authmiddleware,roleArn=arn:aws:iam::897473508751:role/SageMakerSpacesRouterRole-ai-platform-dev' \
  --resolve-conflicts OVERWRITE --region us-east-1
```

### 1.4 验证
- CRD: `workspaces` / `workspacetemplates` / `workspaceaccessstrategies` (`.workspace.jupyter.org`)
- Operator pod: `jupyter-k8s-controller-manager` @ `jupyter-k8s-system` Running (2/2)
- add-on health: no issues

> **web UI 模式（未启用）**: 需注册域名 + Route53 hosted zone + ACM 证书 + KMS 非对称密钥，
> 留待后续按需启用。基础模式下 Workspace `status.accessURL` 不自动填充（无 access-strategy 后端域名）。

---

## 2. Task 16: 修复底层依赖（Workspace pod 拉起的前提）

### 2.1 PodSecurity: dev-spaces 从 restricted 放宽到 baseline

SageMaker Spaces pod（含 ssm-agent-sidecar、init-container）不符合 `restricted` PSS。
真实工作命名空间 `hyperpod-ns-dev-spaces`（Task Governance 托管）默认无 enforce 标签（privileged），
可正常运行。原 `dev-spaces` 命名空间的 PSA 标签已在 manifest 修正：

> 见 `infrastructure/k8s/security/namespace-psa-labels.yaml`（dev-spaces: restricted → baseline）。
> 训练命名空间 `training-jobs` 同为 baseline，保持一致。

### 2.2 EBS CSI Driver 补 HyperPod 专属权限

Workspace 持久卷挂载报 `AccessDeniedException: AttachClusterNodeVolume`。
官方文档（sagemaker-hyperpod-eks-ebs）要求为 EBS CSI 角色补 HyperPod 专属权限：

```bash
# 为 ai-platform-dev-ebs-csi-role 补 inline policy
cat > ebs-hyperpod-policy.json <<'EOF'
{"Version":"2012-10-17","Statement":[
 {"Sid":"HyperPodVolumeAttachDetach","Effect":"Allow",
  "Action":["sagemaker:AttachClusterNodeVolume","sagemaker:DetachClusterNodeVolume"],
  "Resource":"arn:aws:sagemaker:us-east-1:897473508751:cluster/*"},
 {"Sid":"HyperPodEksDescribe","Effect":"Allow",
  "Action":["eks:DescribeCluster"],
  "Resource":"arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks"},
 {"Sid":"HyperPodEc2VolumeOps","Effect":"Allow",
  "Action":["ec2:AttachVolume","ec2:DetachVolume","ec2:DescribeVolumes"],
  "Resource":"*"}]}
EOF

aws iam put-role-policy --role-name ai-platform-dev-ebs-csi-role \
  --policy-name HyperPodClusterVolumeAccess \
  --policy-document file://ebs-hyperpod-policy.json

# 重启 EBS CSI controller 刷新凭证
kubectl rollout restart deployment/ebs-csi-controller -n kube-system
```

---

## 3. Task 16: Kueue 治理（经 SageMaker Task Governance API）

> 配额与队列**不手动 kubectl 创建**，而经 Task Governance API 托管（符合宪法 I）。
> API 自动生成对应的 ClusterQueue / LocalQueue / 托管命名空间。

### 3.1 为 dev-spaces 团队创建 compute quota

```bash
cat > quota-config.json <<'EOF'
{"ComputeQuotaResources":[{"InstanceType":"ml.g5.2xlarge","VCpu":4.0,"MemoryInGiB":16.0}],
 "ResourceSharingConfig":{"Strategy":"Lend"},
 "PreemptTeamTasks":"LowerPriority"}
EOF

aws sagemaker create-compute-quota \
  --name "Team-Dev-Spaces" \
  --description "Interactive Spaces 团队配额 (HyperPod 原生 Spaces, 优先级 100)" \
  --cluster-arn arn:aws:sagemaker:us-east-1:897473508751:cluster/ndownj7gq0f5 \
  --compute-quota-config file://quota-config.json \
  --compute-quota-target "TeamName=dev-spaces,FairShareWeight=100" \
  --activation-state Enabled --region us-east-1
# → ComputeQuotaId: 419zsprig1ii
```

配置依据 AWS Task Governance for Interactive Spaces 文档：
- **FairShareWeight 100**: Interactive Spaces 最高优先级（训练 75 / 评估 50 / 批处理 25）
- **Lend 策略 (Flexible Resource Sharing)**: 借出空闲资源但不借入，避免开发环境被抢占驱逐
- **PreemptTeamTasks LowerPriority**: intra-team 抢占，开发 Pod 可抢占同队列低优先级任务
- **4 vCPU / 16 GiB**: 够 1-2 个默认 Jupyter space（每个 2C/8Gi），CPU 工作负载（GPU=0）

### 3.2 自动生成的 Kueue 资源（只读核验）
```
namespace      hyperpod-ns-dev-spaces                (含 sagemaker-managed-queue=true)
clusterqueue   hyperpod-ns-dev-spaces-clusterqueue   (cohort shared-pool, cpu=4 memory=16Gi)
localqueue     hyperpod-ns-dev-spaces-localqueue
```

### 3.3 创建 WorkloadPriorityClass（纯 K8s 资源，可固化）
见 `infrastructure/k8s/hyperpod-addons/spaces/workspace-priority-class.yaml`。

```bash
kubectl apply -f infrastructure/k8s/hyperpod-addons/spaces/workspace-priority-class.yaml
```

### 3.4 Kueue 集成实测验证（关键）

在 `hyperpod-ns-dev-spaces` 创建带 Kueue label 的 Workspace，确认治理链路成立：

| 验证项 | 结果 |
|--------|------|
| Workspace label 传播到底层 Deployment/Pod | ✅ `kueue.x-k8s.io/queue-name`、`priority-class` 均传播 |
| Kueue 生成 Workload 对象 | ✅ `pod-workspace-...` ADMITTED=True |
| Pod 带 `kueue.x-k8s.io/managed=true` | ✅ Kueue pod integration 接管 |
| LocalQueue 准入计数 | ✅ admitted=1（配额校验通过） |

> 结论: Workspace CRD 本身不在 Kueue integration 列表，但其底层 Deployment/Pod
> 在 `pod`/`deployment` integration 范围内，Kueue label 经传播实现治理。
> 验证后已删除测试 Workspace，配额释放。

---

## 4. Task 16: 后端 ServiceAccount RBAC

Workspace CRD 权限已合并进现有 `backend-service` ClusterRole（非独立角色），
绑定 `ai-platform/backend-service-sa`，对所有命名空间（含 hyperpod-ns-dev-spaces）生效。

> 见 `infrastructure/k8s/base/application/backend-rbac.yaml`（追加 workspaces +
> workspacetemplates/workspaceaccessstrategies 规则）。

```bash
kubectl apply -f infrastructure/k8s/base/application/backend-rbac.yaml
# 验证: kubectl auth can-i create workspaces.workspace.jupyter.org \
#   --as=system:serviceaccount:ai-platform:backend-service-sa -n hyperpod-ns-dev-spaces → yes
```

---

## 5. 过时 manifest 处置说明

`infrastructure/k8s/hyperpod-addons/spaces/` 下早期 IaC（Phase 1, commit 47d4a31）的
以下文件基于**错误的 CRD 假设**（自建 `sagemaker.aws/spaces` CRD + `sagemaker-spaces` 命名空间），
与真实 add-on（`workspace.jupyter.org` + `jupyter-k8s-system`）不符，且从未部署
（集群中 `sagemaker-spaces` 命名空间与 `spaces.sagemaker.aws` CRD 均不存在）：

| 文件 | 状态 | 说明 |
|------|------|------|
| `spaces-namespace.yaml` | ⚠️ 过时 | 假设 `sagemaker-spaces` ns + 自建 controller RBAC |
| `spaces-controller.yaml` | ⚠️ 过时 | 自建 controller，实际由 add-on 提供 |
| `space-templates.yaml` | ⚠️ 过时 | Pod 模板 ConfigMap，实际用 WorkspaceTemplate CRD |
| `efs-storage-class.yaml` | ⚠️ 过时 | 实际用 EBS `sagemaker-spaces-default-storage-class` |
| `kustomization.yaml` | ⚠️ 过时 | 引用上述过时资源 |
| `workspace-priority-class.yaml` | ✅ 有效 | 本阶段新建，反映真实架构 |

> **处置建议**: 过时文件保留但不纳入部署流（argocd/gitops 未引用），
> 待后续清理任务统一移除或重写。本阶段不删除，避免误伤未知引用。

---

## 6. 回滚指引

```bash
# 删除 Task Governance 配额（连带删除 Kueue 资源与托管命名空间）
aws sagemaker delete-compute-quota --compute-quota-id 419zsprig1ii --region us-east-1
# 删除 WorkloadPriorityClass
kubectl delete workloadpriorityclass interactive-space-priority
# 卸载 add-on（连带删除 CRD 与 operator）
aws eks delete-addon --cluster-name ai-platform-dev-eks --addon-name amazon-sagemaker-spaces --region us-east-1
# 删除 add-on IAM 角色
aws iam delete-role-policy ... && aws iam delete-role --role-name SageMakerSpaces{Controller,Router}Role-ai-platform-dev
# EBS 权限回滚
aws iam delete-role-policy --role-name ai-platform-dev-ebs-csi-role --policy-name HyperPodClusterVolumeAccess
# 后端 RBAC：从 backend-rbac.yaml 移除 workspace 规则后重新 apply
```
