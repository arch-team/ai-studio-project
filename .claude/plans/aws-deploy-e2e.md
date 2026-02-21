# 增量部署到 AWS Dev 环境 - 支持 E2E 测试

## Context

全部 11 个 CDK Stack 已部署到 us-east-1 (Account 897473508751)，但应用层 K8s 清单 (T105c) 完全缺失。本计划将后端 (FastAPI) 和前端 (React/Nginx) 容器化部署到 EKS，通过 ALB 暴露，为 E2E 测试提供真实环境。

## 已部署资源

| 资源 | 值 |
|------|---|
| EKS 集群 | `ai-platform-dev-eks` |
| ECR (Backend) | `897473508751.dkr.ecr.us-east-1.amazonaws.com/ai-platform-dev-backend` |
| ALB DNS | `ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com` |
| Aurora (Proxy) | `ai-platform-dev-aurora-proxy.proxy-cqm7um8tgaji.us-east-1.rds.amazonaws.com:3306` |
| DB Secret | `arn:aws:secretsmanager:...:ai-platform-dev/aurora/credentials-CZuGXk` |
| S3 Buckets | `ai-platform-dev-{datasets,models,checkpoints}` |
| Backend TG | `arn:aws:elasticloadbalancing:...:targetgroup/ai-platform-dev-api/b20b338b9ba0a420` |
| Frontend TG | `arn:aws:elasticloadbalancing:...:targetgroup/ai-platform-dev-frontend/fa8a0251575dab05` |
| ALB SG | `sg-05c1520322739b62a` |

---

## 阻塞问题 (Phase 1 解决)

| 问题 | 文件 | 修复 |
|------|------|------|
| EKS 访问权限: Admin 用户无法 assume eks-admin-role | `stacks/compute/eks_stack.py` | 添加 Admin 用户到 masters_role 信任策略 |
| AWS LB Controller 未安装 (无 TargetGroupBinding CRD) | `stacks/compute/eks_stack.py` | 添加 aws-load-balancer-controller add-on |
| Frontend TG port=3000, nginx 监听 80 | `stacks/networking/alb_stack.py:247` | `port=3000` → `port=80` |
| IRSA namespace=backend, 应用部署到 ai-platform | `stacks/foundation/iam_stack.py:246` | `backend` → `ai-platform` |
| 缺少 Frontend ECR 仓库 | `stacks/application/application_stack.py` | 添加 frontend ECR |

---

## Phase 1: CDK 基础设施修补

### 1.1 EKS 访问权限
**文件**: `infrastructure/cdk/stacks/compute/eks_stack.py`
- 为 masters_role 信任策略添加当前 IAM 用户

### 1.2 安装 AWS Load Balancer Controller
**文件**: `infrastructure/cdk/stacks/compute/eks_stack.py`
- 添加 `aws-load-balancer-controller` EKS add-on + Pod Identity 关联

### 1.3 Frontend TG 端口修复
**文件**: `infrastructure/cdk/stacks/networking/alb_stack.py`
- 第 247 行: `port=3000` → `port=80`

### 1.4 IRSA Namespace 修复
**文件**: `infrastructure/cdk/stacks/foundation/iam_stack.py`
- 第 246 行: `backend:backend-service-sa` → `ai-platform:backend-service-sa`

### 1.5 Frontend ECR 仓库
**文件**: `infrastructure/cdk/stacks/application/application_stack.py`
- 添加 `_create_frontend_repository()` (复用 backend 仓库配置)
- 添加输出: FrontendRepositoryUri, FrontendRepositoryArn

### 部署
```bash
cd infrastructure/cdk
make diff-check
cdk deploy ai-platform-dev-iam ai-platform-dev-eks ai-platform-dev-alb ai-platform-dev-application --context env=dev
```

---

## Phase 2: Docker 镜像构建推送

### 2.1 修改 nginx.conf
**文件**: `frontend/nginx.conf`
- 第 18 行: `proxy_pass http://backend:8000` → `proxy_pass http://backend-svc.ai-platform.svc.cluster.local:8000`

### 2.2 构建推送
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 897473508751.dkr.ecr.us-east-1.amazonaws.com

# Backend
docker build --target production -t 897473508751.dkr.ecr.us-east-1.amazonaws.com/ai-platform-dev-backend:v1.0.0 backend/
docker push 897473508751.dkr.ecr.us-east-1.amazonaws.com/ai-platform-dev-backend:v1.0.0

# Frontend
docker build --target production -t 897473508751.dkr.ecr.us-east-1.amazonaws.com/ai-platform-dev-frontend:v1.0.0 frontend/
docker push 897473508751.dkr.ecr.us-east-1.amazonaws.com/ai-platform-dev-frontend:v1.0.0
```

---

## Phase 3: K8s 应用清单 (新建 11 个文件)

**目录**: `infrastructure/k8s/base/application/`

| 文件 | 内容 |
|------|------|
| `kustomization.yaml` | 聚合所有资源 |
| `namespace.yaml` | Namespace `ai-platform`, PSA restricted |
| `backend-serviceaccount.yaml` | SA + IRSA annotation (backend-service-role) |
| `backend-configmap.yaml` | 非敏感环境变量 (AWS_REGION, S3, CORS 等) |
| `backend-deployment.yaml` | replicas:1, port:8000, probes:/health, requests:250m/512Mi |
| `backend-service.yaml` | ClusterIP, port:8000 |
| `frontend-deployment.yaml` | replicas:1, port:80, probes:/, requests:100m/128Mi |
| `frontend-service.yaml` | ClusterIP, port:80 |
| `backend-tgb.yaml` | TargetGroupBinding → Backend TG, targetType:ip |
| `frontend-tgb.yaml` | TargetGroupBinding → Frontend TG, targetType:ip |
| `db-migration-job.yaml` | Job: alembic upgrade head (独立应用) |

**修改**: `infrastructure/k8s/base/kustomization.yaml` - 添加 `- application/`

---

## Phase 4: 部署到 EKS

### 4.1 创建 Secret 脚本
**新建**: `infrastructure/scripts/create-backend-secret.sh`
- 从 Secrets Manager 读取 Aurora 凭证
- 构建 DATABASE_URL (mysql+aiomysql://user:pass@proxy:3306/db)
- `kubectl create secret generic backend-secrets -n ai-platform`

### 4.2 部署顺序
```bash
# kubeconfig
aws eks update-kubeconfig --name ai-platform-dev-eks --region us-east-1

# Namespace + Secret
kubectl apply -f infrastructure/k8s/base/application/namespace.yaml
bash infrastructure/scripts/create-backend-secret.sh

# 所有清单
kubectl apply -k infrastructure/k8s/overlays/dev/

# 数据库迁移 + 种子数据
kubectl apply -f infrastructure/k8s/base/application/db-migration-job.yaml
kubectl logs -f job/db-migration -n ai-platform
kubectl create job db-seed --from=job/db-migration -n ai-platform -- python scripts/seed_data.py
```

---

## Phase 5: E2E 测试配置

**修改**: `frontend/playwright.config.ts`
- 支持 `E2E_BASE_URL` 环境变量覆盖 baseURL
- 外部 URL 时跳过 webServer 启动

```bash
E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com npx playwright test
```

---

## 验证检查点

| 检查 | 命令 | 预期 |
|------|------|------|
| Pods 运行 | `kubectl get pods -n ai-platform` | backend + frontend Running |
| TGB 就绪 | `kubectl get tgb -n ai-platform` | Active |
| Health | `curl ALB_DNS/health` | 200 |
| Frontend | `curl -I ALB_DNS/` | 200 |
| API 代理 | `curl ALB_DNS/api/v1/training-jobs` | JSON |
| E2E | `npx playwright test` | Pass |

---

## 文件变更摘要

**修改 (7)**: eks_stack.py, iam_stack.py, alb_stack.py, application_stack.py, base/kustomization.yaml, nginx.conf, playwright.config.ts

**新建 (12)**: application/ 目录下 11 个 K8s 清单 + create-backend-secret.sh
