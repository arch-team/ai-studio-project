# CI/CD 修复手册：GitHub Secrets + OIDC 角色配置

> **背景**: `.github/workflows/deploy.yaml` 最近 6 次 `main` push 触发的部署全部失败。根因有三层，前两层已由 `fix/ci-backend-deps` 分支修复，**第一层（AWS 凭证）必须由你在 GitHub/AWS 控制台操作**，本手册提供可直接执行的步骤。
>
> 生成时间: 2026-06-13 | 账号: `897473508751` | 区域: `us-east-1` | 仓库: `arch-team/ai-studio-project`

---

## 一、问题根因（三层串联失败）

| 层 | 失败点 | 状态 |
|----|--------|------|
| **1** | GitHub Secrets 完全未配置 → `ECR_REGISTRY` 拼接为空、`AWS_ROLE_ARN` 为空导致 `Could not load credentials` | ⏳ **本手册待你操作** |
| 2 | `requirements-dev.txt` 的 `ruff>=0.8.0` 与 `sagemaker-hyperpod` 钉死的 `ruff==0.6.2` 冲突 | ✅ 已修 (commit e65d245) |
| 3 | 90 lint errors + 20 format（全在 tests/scripts/alembic） | ✅ 已修 (commit e65d245) |

> 注：历史线上镜像（v1.2.29 等语义版本）一直靠**手动 build+push+deploy**，CI 实际从未成功部署过。本次也已手动部署 v1.2.30 解除 Phase C 阻塞。配好下方 secrets 后，CI 才能首次实现自动部署。

---

## 二、workflow 需要的 4 个 Secret

`deploy.yaml` 引用了以下 secrets（见 L10-13, 55-56, 157, 323）：

| Secret 名称 | 值 | 必需性 |
|-------------|-----|--------|
| `AWS_ACCOUNT_ID` | `897473508751` | 🔴 必需（拼接 ECR_REGISTRY） |
| `AWS_ROLE_ARN` | `arn:aws:iam::897473508751:role/github-actions-ai-studio-deploy`（**下方第三步创建**） | 🔴 必需（OIDC assume） |
| `AWS_REGION` | `us-east-1` | 🟡 可选（有默认值 us-east-1，建议显式配置） |
| `ECR_REGISTRY` | — | ⚪ 不需要单独配置（由 `AWS_ACCOUNT_ID` 自动拼接） |

### 配置命令（gh CLI）

```bash
# 在仓库根目录执行
gh secret set AWS_ACCOUNT_ID --body "897473508751"
gh secret set AWS_REGION --body "us-east-1"
# AWS_ROLE_ARN 待第三步创建角色后再设置（见下）
```

> 或通过 GitHub 网页：Settings → Secrets and variables → Actions → New repository secret。

---

## 三、创建专属 OIDC 部署角色

### 现状

- ✅ **OIDC Provider 已存在**，无需创建：`arn:aws:iam::897473508751:oidc-provider/token.actions.githubusercontent.com`
- ⚠️ 现有两个 GitHub Actions 角色的信任策略**都不绑定本仓库**（分别绑 `hyperpod-issue-agents`、`ai-agents-platform`），不能复用 → **需新建**。

### 角色需要的权限

| 用途 | workflow 步骤 | AWS 权限 |
|------|--------------|---------|
| 推送镜像到 ECR | backend-build / frontend-build | ECR push（backend + frontend 仓库） |
| 验证部署（更新 kubeconfig + kubectl） | verify-deployment (L326-330) | `eks:DescribeCluster` + 集群 RBAC |

### 步骤 1：创建信任策略文件

```bash
cat > /tmp/trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::897473508751:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:arch-team/ai-studio-project:*"
        }
      }
    }
  ]
}
EOF
```

> `sub` 用 `repo:arch-team/ai-studio-project:*` 允许该仓库所有分支/环境。若要收紧到仅 main 分支：改为 `repo:arch-team/ai-studio-project:ref:refs/heads/main`（但 workflow 也支持 release/* 和手动触发，`:*` 更匹配实际用法）。

### 步骤 2：创建权限策略文件

```bash
cat > /tmp/permissions-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages"
      ],
      "Resource": [
        "arn:aws:ecr:us-east-1:897473508751:repository/ai-platform-dev-backend",
        "arn:aws:ecr:us-east-1:897473508751:repository/ai-platform-dev-frontend"
      ]
    },
    {
      "Sid": "EKSDescribe",
      "Effect": "Allow",
      "Action": "eks:DescribeCluster",
      "Resource": "arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks"
    }
  ]
}
EOF
```

### 步骤 3：创建角色并附加策略

```bash
aws iam create-role \
  --role-name github-actions-ai-studio-deploy \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --description "GitHub Actions OIDC 部署角色 - arch-team/ai-studio-project"

aws iam put-role-policy \
  --role-name github-actions-ai-studio-deploy \
  --policy-name ecr-push-eks-describe \
  --policy-document file:///tmp/permissions-policy.json
```

### 步骤 4：把角色 ARN 写入 GitHub Secret

```bash
gh secret set AWS_ROLE_ARN \
  --body "arn:aws:iam::897473508751:role/github-actions-ai-studio-deploy"
```

---

## 四、授予角色访问 EKS 集群的 RBAC（verify-deployment 需要）

`verify-deployment` job 会 `kubectl get pods/svc/hpa` 和 `kubectl exec`（L356-371）。仅有 `eks:DescribeCluster` 还不够，需把角色加入集群的 `aws-auth`（或 EKS Access Entry）。

### 方式 A：EKS Access Entry（推荐，较新集群）

```bash
aws eks create-access-entry \
  --cluster-name ai-platform-dev-eks \
  --region us-east-1 \
  --principal-arn arn:aws:iam::897473508751:role/github-actions-ai-studio-deploy \
  --type STANDARD

# 关联只读策略（验证用途，避免给过大权限）
aws eks associate-access-policy \
  --cluster-name ai-platform-dev-eks \
  --region us-east-1 \
  --principal-arn arn:aws:iam::897473508751:role/github-actions-ai-studio-deploy \
  --access-scope type=namespace,namespaces=ai-platform \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy
```

> ⚠️ `kubectl exec`（健康检查 L370）需要比 View 更高权限。若健康检查报权限错，可改用 `AmazonEKSEditPolicy`，或接受该步失败（workflow 已设 `continue-on-error: true`，不阻断部署）。

### 方式 B：aws-auth ConfigMap（传统方式）

```bash
kubectl edit configmap aws-auth -n kube-system
# 在 mapRoles 下追加：
#   - rolearn: arn:aws:iam::897473508751:role/github-actions-ai-studio-deploy
#     username: github-actions-deploy
#     groups: [system:masters]   # 或自定义更小权限的 group
```

---

## 五、验证配置

配置完成后，触发一次部署验证（任选）：

```bash
# 方式 1: 手动触发 workflow（推荐，可选 backend-only 快速验证）
gh workflow run deploy.yaml -f environment=dev -f component=backend

# 方式 2: 推送一个 backend 改动到 main 自动触发

# 观察运行
gh run watch
```

**预期结果**：`backend-build` 的「配置 AWS 凭证 (OIDC)」「登录 ECR」「构建并推送镜像」全部通过（不再是之前的 `Could not load credentials`）。

---

## 六、配置检查清单

- [ ] `gh secret set AWS_ACCOUNT_ID 897473508751`
- [ ] `gh secret set AWS_REGION us-east-1`
- [ ] 创建 IAM 角色 `github-actions-ai-studio-deploy`（信任 + 权限策略）
- [ ] `gh secret set AWS_ROLE_ARN ...`
- [ ] EKS Access Entry / aws-auth 授权（verify-deployment 用）
- [ ] `gh workflow run deploy.yaml` 验证通过

---

## 附：关键标识速查

| 项 | 值 |
|----|-----|
| AWS Account | `897473508751` |
| Region | `us-east-1` |
| OIDC Provider (已存在) | `arn:aws:iam::897473508751:oidc-provider/token.actions.githubusercontent.com` |
| ECR backend | `arn:aws:ecr:us-east-1:897473508751:repository/ai-platform-dev-backend` |
| ECR frontend | `arn:aws:ecr:us-east-1:897473508751:repository/ai-platform-dev-frontend` |
| EKS 集群 | `ai-platform-dev-eks` |
| GitHub 仓库 | `arch-team/ai-studio-project` |
| 建议新建角色名 | `github-actions-ai-studio-deploy` |
