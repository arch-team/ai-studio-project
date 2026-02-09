---
paths:
  - "app.py"
  - "cdk.json"
---

# 部署规范

> **职责**: 定义部署执行规范，包括环境矩阵、CI/CD Pipeline、部署流程和回滚策略。

> **职责边界**: 本文档关注**部署执行**（环境矩阵、CI/CD、部署流程）。环境配置的**代码架构**（dataclass 结构）详见 [configuration.md](configuration.md)

---

## 0. 速查卡片

### 部署命令

```bash
# 查看变更
cdk diff --context env=dev

# 指定环境部署
cdk deploy --all --context env=dev
cdk deploy --all --context env=prod --require-approval broadening

# 仅部署特定 Stack
cdk deploy NetworkStack --context env=dev
```

### 环境矩阵

| 环境 | 用途 | 部署方式 | 审批 |
|------|------|---------|------|
| dev | 开发测试 | 手动 | 无 |
| staging | 预发布 | CI/CD | 自动 |
| prod | 生产 | CI/CD | 手动审批 |

---

## 1. RemovalPolicy 策略

> **SSOT**: 删除策略的单一真实源。`stack-design.md` 引用此处。

| 资源类型 | Dev | Staging | Prod |
|---------|-----|---------|------|
| 数据库 (Aurora) | DESTROY | SNAPSHOT | RETAIN |
| S3 Bucket | DESTROY | DESTROY | RETAIN |
| KMS Key | DESTROY | RETAIN | RETAIN |
| EKS Cluster | DESTROY | DESTROY | RETAIN |
| FSx for Lustre | DESTROY | DESTROY | SNAPSHOT |
| CloudWatch Logs | DESTROY | DESTROY | RETAIN |

```python
def get_removal_policy(env_name: str) -> cdk.RemovalPolicy:
    if env_name == "dev":
        return cdk.RemovalPolicy.DESTROY
    elif env_name == "staging":
        return cdk.RemovalPolicy.SNAPSHOT
    return cdk.RemovalPolicy.RETAIN
```

---

## 2. 部署顺序

### 标准部署 (L1 → L5)

```
L1: NetworkStack, IamStack           (并行，无依赖)
L2: DatabaseStack, StorageStack      (并行，依赖 L1)
L3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack (串行)
L4: FsxLustreStack                   (依赖 L3 的 EKS 集群)
L5: AlbStack                         (依赖 L3 的 EKS 集群)
```

### HyperPod 部署前置

> HyperPod 部署的前置条件和详细流程见 [hyperpod.md](hyperpod.md)（SSOT）

---

## 3. CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/cdk-deploy.yml
name: CDK Deploy

on:
  push:
    branches: [main]
    paths: ['infrastructure/cdk/**']
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, staging, prod]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check . && mypy .
      - run: pytest -m unit --cov=stacks --cov=cdk_constructs
      - run: cdk synth --context env=${{ inputs.environment || 'dev' }}

  deploy-dev:
    needs: test
    environment: dev
    steps:
      - run: cdk deploy --all --context env=dev --require-approval never

  deploy-prod:
    needs: deploy-staging
    environment:
      name: prod  # 需要手动审批
    steps:
      - run: cdk deploy --all --context env=prod --require-approval never
```

---

## 4. 手动部署流程

```bash
# 1. 确认环境
echo $AWS_PROFILE && aws sts get-caller-identity

# 2. 代码质量检查
ruff check . && mypy . && pytest -m unit

# 3. 合成并检查变更
cdk synth --context env=dev
cdk diff --context env=dev

# 4. 部署
cdk deploy --all --context env=dev

# 5. 验证
aws cloudformation describe-stacks --stack-name AiPlatformNetworkStack-dev --query 'Stacks[0].StackStatus'
```

---

## 5. 回滚策略

```bash
# 回滚到上一个版本 (CloudFormation 自动回滚)
cdk deploy --all --context env=dev --rollback

# 紧急: 销毁并重建单个 Stack
cdk destroy AlbStack-dev && cdk deploy AlbStack-dev --context env=dev
```

**HyperPod 回滚注意**: HyperPod 集群销毁后需要重新创建，数据在 FSx 中持久化。

---

## 6. 部署前安全检查

```bash
# CDK Nag 合规检查 (staging/prod 必须)
cdk synth --context env=staging 2>&1 | grep -i "error\|warning"

# 敏感信息检查
git secrets --scan

# 依赖漏洞检查
pip audit
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | Stack 依赖关系 |
| [configuration.md](configuration.md) | 环境配置代码架构 |
| [security.md](security.md) | 部署安全、CDK Nag |
| [hyperpod.md](hyperpod.md) | HyperPod 部署详细流程 |
| [cost-optimization.md](cost-optimization.md) | 环境成本管理 |
