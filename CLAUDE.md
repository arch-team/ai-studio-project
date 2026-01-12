# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

## Project Overview
AI Training Platform - 基于 AWS SageMaker HyperPod 构建的企业级 AI 训练平台，支持分布式训练、资源调度、数据管理和多租户。

## Project Constraints

### 基础设施约束
- **禁止使用 Fargate**: 所有 EKS 容器必须使用 EC2 托管节点组 (Managed Node Groups)
- **GPU 工作负载**: 使用专用 GPU 节点组 (p4d, p5 实例类型)

### 调度 API 使用原则
- **默认使用 HyperPod Task Governance API**: 所有资源调度操作通过 HyperPod SDK
- **Kueue 直接访问**: 仅在状态监控和故障诊断时通过 kubernetes-client 查询，需在代码注释中说明理由

## Tech Stack

### 后端 (backend/)
- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.109.0, uvicorn 0.27.0
- **ORM**: SQLAlchemy 2.0.25 (异步), Alembic 1.13.1
- **Validation**: Pydantic 2.5.3, pydantic-settings 2.1.0
- **AWS SDK**: boto3 1.34.14, sagemaker-hyperpod 1.0.0
- **Database Driver**: aiomysql 0.2.0
- **Logging**: structlog 24.1.0
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, ruff, mypy

### 前端 (frontend/)
- **Language**: TypeScript 5.3.3
- **Framework**: React 18.2.0, react-router-dom 6.21.2
- **State**: Zustand 4.4.7, TanStack Query 5.17.0
- **UI**: AWS Cloudscape Design System 3.0.0
- **Build**: Vite 5.0.12
- **Testing**: Vitest 1.2.1, Testing Library

### 基础设施 (infrastructure/cdk/)
- **IaC**: AWS CDK (Python) >= 2.170.0
- **Security**: cdk-nag >= 2.28.0
- **Compute**: EKS + SageMaker HyperPod
- **Storage**: FSx for Lustre, S3

## Architecture

### CDK Stack 分层 (部署顺序)
```
Layer 1 (Foundation):  NetworkStack, IamStack (并行)
                            ↓
Layer 2 (Data):        DatabaseStack, StorageStack (并行)
                            ↓
Layer 3a (Compute):    EksStack (EKS + Add-ons + Helm Chart)
                            ↓
Layer 3b (HyperPod):   SagemakerHyperPodStack
                            ↓
Layer 3c (Add-ons):    HyperPodAddonsStack (Training Operator, Task Governance, Observability)
                            ↓
Layer 4 (Storage):     FsxLustreStack
                            ↓
Layer 5 (Ingress):     AlbStack
```

### VPC 设计
- **Public** (/20): NAT Gateways, ALB
- **PrivateApp** (/19): EKS 节点, 计算资源 - 支持 ~1,200+ 节点
- **PrivateData** (/20, isolated): FSx for Lustre, Aurora MySQL

## Common Commands

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload          # 启动开发服务器
alembic upgrade head                    # 数据库迁移
alembic revision --autogenerate -m "description"  # 创建迁移
pytest                                  # 运行所有测试
pytest tests/test_file.py -v           # 运行单个测试文件
pytest tests/test_file.py::test_func -v  # 运行单个测试函数
pytest --cov=src --cov-report=html     # 测试覆盖率
black src/ && ruff check src/ && mypy src/  # 代码检查

# 前端开发
cd frontend
npm install
npm run dev                             # 启动开发服务器 (Vite)
npm run build                           # 构建生产版本
npm test                                # 运行所有测试
npm test -- src/path/to/test.tsx       # 运行单个测试
npm run test:coverage                   # 测试覆盖率
npm run lint                            # ESLint 检查

# Docker 开发环境
docker-compose up -d                    # 启动所有服务

# CDK 基础设施
cd infrastructure/cdk
source .venv/bin/activate
./scripts/setup_helm_chart.sh           # 首次部署前必须执行
cdk synth                               # 合成 CloudFormation
cdk deploy --all --context env=dev      # 部署开发环境
cdk deploy --all --context env=staging  # 部署预发布环境
cdk deploy --all --context env=prod --require-approval broadening  # 部署生产环境
cdk diff                                # 查看变更
pytest                                  # 运行 CDK 测试
pytest -m unit                          # 仅运行单元测试
ruff check . && ruff format . && mypy . # 代码检查
```

## Project Structure

```
├── backend/                 # FastAPI 后端服务
│   ├── src/
│   │   ├── api/v1/         # API 路由 (版本化)
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   ├── core/           # 配置 (config.py, database.py)
│   │   └── clients/        # 外部服务客户端
│   └── alembic/            # 数据库迁移
├── frontend/               # React 前端应用
│   └── src/
│       ├── pages/          # 页面组件
│       ├── layouts/        # 布局组件
│       ├── hooks/          # 自定义 Hooks
│       ├── store/          # Zustand 状态
│       ├── lib/            # 工具函数
│       └── types/          # TypeScript 类型
├── infrastructure/
│   ├── cdk/                # AWS CDK (Python)
│   │   ├── stacks/         # Stack 实现
│   │   ├── custom_constructs/  # L2/L3 Constructs
│   │   ├── config/         # 环境配置 (environments.py, constants.py)
│   │   ├── utils/          # 工具模块 (nag_suppressions, tagging, iam_helpers)
│   │   └── scripts/        # 部署脚本
│   └── k8s/                # Kubernetes 资源
└── specs/                  # 功能规范文档
    └── 001-ai-training-platform/
        ├── spec.md         # 功能规范 (含术语标准)
        ├── plan.md         # 实施计划
        └── data-model.md   # 数据模型
```

## Key Documentation
- 功能规范 (含术语标准): `specs/001-ai-training-platform/spec.md`
- 实施计划: `specs/001-ai-training-platform/plan.md`
- 数据模型: `specs/001-ai-training-platform/data-model.md`
- CDK 详细指南: `infrastructure/cdk/README.md`
- CDK 专用指南: `infrastructure/cdk/CLAUDE.md`
