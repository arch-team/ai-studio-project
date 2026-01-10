# AI Training Platform - CDK Infrastructure

AWS CDK (Python) 基础设施代码，用于部署 AI 训练平台，支持 SageMaker HyperPod 与 EKS 集成的大规模 GPU 训练工作负载。

## 目录

- [架构概览](#架构概览)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [测试](#测试)
- [CI/CD](#cicd)
- [故障排除](#故障排除)

## 架构概览

### Stack 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 5: Network Ingress                      │
│                         AlbStack                                 │
│              (ALB + TLS 1.2+ + WAF for prod)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Layer 4: High-Performance Storage               │
│                       FsxLustreStack                             │
│                 (FSx for Lustre + S3 DRA)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 3b: HyperPod                            │
│                  SagemakerHyperPodStack                          │
│              (HyperPod Cluster + EKS 集成)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 3a: EKS Foundation                      │
│                        EksStack                                  │
│           (EKS Cluster + Add-ons + Helm Chart)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Layer 2: Data                               │
│              DatabaseStack    StorageStack                       │
│         (Aurora MySQL v2)   (S3 Buckets + KMS)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 1: Foundation                           │
│               NetworkStack      IamStack                         │
│            (VPC + Subnets)   (IAM Roles)                        │
└─────────────────────────────────────────────────────────────────┘
```

### VPC 设计

3 层子网架构：
- **Public** (/20): NAT Gateways, ALB
- **PrivateApp** (/19): EKS 节点, 计算资源 - 支持 ~1,200+ 节点
- **PrivateData** (/20, isolated): FSx for Lustre, Aurora MySQL

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 20+ (CDK CLI)
- AWS CLI 配置完成
- Helm 3.x (用于 HyperPod Helm Chart)

### 安装

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 AWS CDK CLI
npm install -g aws-cdk

# 4. 验证安装
cdk --version
```

### 首次部署前准备

```bash
# 1. 下载 HyperPod Helm Chart (首次部署必需)
./scripts/setup_helm_chart.sh

# 2. Bootstrap CDK (每个 Account/Region 只需一次)
cdk bootstrap aws://ACCOUNT_ID/REGION
```

## 环境配置

项目支持三个环境，通过 `--context env=` 参数切换：

| 环境 | 用途 | NAT | Aurora ACU | FSx 容量 | EKS 节点 |
|------|------|-----|------------|----------|----------|
| `dev` | 开发测试 | 1 | 0.5-8 | 10 TiB | 1-10 |
| `staging` | 预发布 | 2 | 1-16 | 20 TiB | 2-50 |
| `prod` | 生产 | 2 | 2-16 | 100 TiB | 2-100 |

### 环境特定配置

环境配置定义在 `config/environments.py`，使用工厂方法：

```python
from config import get_environment_config

# 获取环境配置
dev_config = get_environment_config("dev", account="123456789012", region="us-east-1")
```

## 部署指南

### 部署命令

```bash
# 查看变更
cdk diff --context env=dev

# 部署开发环境
cdk deploy --all --context env=dev

# 部署 staging 环境
cdk deploy --all --context env=staging

# 部署生产环境 (需要审批)
cdk deploy --all --context env=prod --require-approval broadening

# 部署特定 Stack
cdk deploy ai-platform-dev-network --context env=dev
```

### 指定 Account/Region

```bash
cdk deploy --all \
  --context env=dev \
  --context account=123456789012 \
  --context region=us-west-2
```

### 部署顺序

Stack 依赖已在代码中定义，CDK 会自动按正确顺序部署：

1. NetworkStack, IamStack (并行)
2. DatabaseStack, StorageStack (并行)
3. EksStack (包含 Helm Chart 自动安装)
4. SagemakerHyperPodStack
5. FsxLustreStack
6. AlbStack

## 开发指南

### 项目结构

```
.
├── app.py                    # CDK 入口点
├── config/
│   ├── __init__.py
│   └── environments.py       # 环境配置 (dataclass)
├── stacks/
│   ├── __init__.py
│   ├── network_stack.py      # VPC, 子网, VPC Endpoints
│   ├── iam_stack.py          # IAM 角色和策略
│   ├── database_stack.py     # Aurora MySQL Serverless v2
│   ├── storage_stack.py      # S3 Buckets
│   ├── eks_stack.py          # EKS Cluster + Add-ons
│   ├── sagemaker_hyperpod_stack.py  # HyperPod
│   ├── fsx_stack.py          # FSx for Lustre
│   └── alb_stack.py          # Application Load Balancer
├── custom_constructs/
│   └── gpu_node_group.py     # GPU 节点组 L3 Construct
├── tests/
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── scripts/
│   └── setup_helm_chart.sh   # HyperPod Helm Chart 下载
└── helm_charts/              # Helm Charts (gitignored)
```

### 代码规范

项目使用以下工具进行代码质量管理：

- **ruff**: Linting 和格式化
- **mypy**: 类型检查
- **pytest**: 测试框架

```bash
# 运行所有检查
make lint

# 或单独运行
ruff check .
ruff format .
mypy .
```

## 测试

### 运行测试

```bash
# 运行所有测试
make test

# 或使用 pytest 直接运行
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ --cov=stacks --cov=config --cov-report=term-missing

# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v
```

### 测试覆盖率

当前覆盖率: **79%** (97 个测试)

| 模块 | 覆盖率 |
|------|--------|
| config/ | 100% |
| stacks/iam_stack.py | 100% |
| stacks/network_stack.py | 98% |
| stacks/database_stack.py | 93% |
| stacks/storage_stack.py | 90% |

## CI/CD

项目配置了 GitHub Actions 自动化流水线：

### PR 检查 (cdk-ci.yml)

```
Lint → Test → Synth (并行 dev/staging/prod) → Diff
```

### 部署 (cdk-deploy.yml)

| 触发方式 | 目标环境 | 审批要求 |
|----------|----------|----------|
| main 推送 | dev | 自动 |
| 手动触发 | staging | 需审批 |
| 手动触发 | prod | 需审批 |

### 配置 GitHub Secrets

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCOUNT_ID
```

## 故障排除

### 常见问题

#### CDK Bootstrap 失败

```bash
# 确保 AWS 凭证配置正确
aws sts get-caller-identity

# 重新 Bootstrap
cdk bootstrap aws://ACCOUNT_ID/REGION --force
```

#### Helm Chart 未找到

```bash
# 运行 setup 脚本
./scripts/setup_helm_chart.sh

# 验证 Helm Chart 存在
ls helm_charts/HyperPodHelmChart/
```

#### CDK Synth 失败

```bash
# 检查 Python 依赖
pip install -r requirements.txt

# 验证语法
python -c "from app import create_app; create_app()"
```

#### Aurora 创建失败 (至少需要 2 个 AZ)

确保使用 Multi-AZ 部署模式，dev 环境默认配置已处理此问题。

### 获取帮助

- 查看 [AWS CDK 文档](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- 查看 [SageMaker HyperPod 文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html)
- 提交 Issue 到项目仓库

## 许可证

MIT License
