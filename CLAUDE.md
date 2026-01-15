# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

## Project Overview
AI Training Platform - 基于 AWS SageMaker HyperPod 构建的企业级 AI 训练平台，支持分布式训练、资源调度、数据管理和多租户。

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
- **Code Quality**: ESLint, TypeScript ESLint

### 基础设施 (infrastructure/cdk/)
- **IaC**: AWS CDK (Python) >= 2.170.0
- **Security**: cdk-nag >= 2.28.0
- **Compute**: EKS + SageMaker HyperPod
- **Storage**: FSx for Lustre, S3

### 数据存储
- **开发环境**: MySQL 8.0.28 (Docker)
- **生产环境**: Amazon Aurora MySQL 3.04.x (兼容 MySQL 8.0)
- **训练数据**: Amazon FSx for Lustre (≥5GB/s 吞吐量)
- **模型制品**: Amazon S3 + SageMaker Model Registry
- **检查点**: 分层存储 (NVMe → FSx for Lustre → S3)

## Common Commands

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload          # 启动开发服务器
alembic upgrade head                    # 数据库迁移
pytest                                  # 运行测试
black src/ && ruff check src/ && mypy src/  # 代码检查

# 前端开发
cd frontend
npm install
npm run dev                             # 启动开发服务器 (Vite)
npm run build                           # 构建生产版本
npm test                                # 运行测试

# Docker 开发环境
docker-compose up -d                    # 启动所有服务

# CDK 基础设施
cd infrastructure/cdk
source .venv/bin/activate
cdk synth                               # 合成 CloudFormation
cdk deploy --context env=dev            # 部署开发环境
cdk diff                                # 查看变更
```

## Project Structure

```
├── backend/                 # FastAPI 后端服务
│   ├── src/                # 源代码
│   │   ├── api/           # API 路由
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/      # 业务逻辑
│   │   └── core/          # 核心配置
│   └── alembic/           # 数据库迁移
├── frontend/               # React 前端应用
│   └── src/
│       ├── pages/         # 页面组件
│       ├── layouts/       # 布局组件
│       ├── hooks/         # 自定义 Hooks
│       ├── store/         # Zustand 状态
│       └── types/         # TypeScript 类型
├── infrastructure/         # 基础设施代码
│   ├── cdk/               # AWS CDK (Python)
│   └── k8s/               # Kubernetes 资源
├── specs/                  # 功能规范文档
│   └── 001-ai-training-platform/
└── claudedocs/            # 项目文档
```

## Key Documentation
- 功能规范: `specs/001-ai-training-platform/spec.md`
- 实施计划: `specs/001-ai-training-platform/plan.md`
- 数据模型: `specs/001-ai-training-platform/data-model.md`
- CDK 部署: `infrastructure/cdk/README.md`
- **前端设计规范**: `frontend/DESIGN.md`（快速参考）
- 前端设计详细指南: `specs/frontend-design-guide.md`（完整版）

## Frontend Development Guidelines

前端开发 MUST 遵循 `frontend/DESIGN.md` 中的设计规范：

- **组件库**: 仅使用 AWS Cloudscape Design System，禁止自定义样式覆盖
- **状态管理**: Zustand + TanStack Query
- **代码风格**: TypeScript 严格模式，ESLint 无警告
- **主题支持**: 支持亮色/暗色/跟随系统三种模式
- **提交前**: 完成 `frontend/DESIGN.md` 中的检查清单
