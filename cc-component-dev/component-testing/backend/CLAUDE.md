# Backend CLAUDE.md

> **语言要求参见根目录 `CLAUDE.md`**

## Overview

AI Training Platform 后端服务 - FastAPI + SQLAlchemy + AWS SageMaker HyperPod

## Tech Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.109.0 + Uvicorn
- **ORM**: SQLAlchemy 2.0 (async) + Alembic
- **Database**: MySQL 8.0 (aiomysql)
- **Validation**: Pydantic 2.5
- **AWS**: boto3, sagemaker-hyperpod

## Commands

```bash
# 开发服务器
uvicorn src.main:app --reload

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "xxx"

# 测试
pytest tests/unit -v
pytest tests/integration -v
pytest --cov=src

# 代码质量
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Architecture

**目录结构**:
```
src/
├── modules/<module>/     # 功能模块
│   ├── api/             # HTTP 端点、Schema
│   ├── application/     # 业务服务
│   ├── domain/          # 实体、值对象、仓库接口
│   └── infrastructure/  # ORM 模型、仓库实现
├── shared/              # 共享内核
│   ├── domain/          # 基础实体、跨模块接口
│   ├── infrastructure/  # 数据库、配置
│   └── api/             # 中间件、异常处理
└── main.py              # 应用入口
```

## Module Matrix

| 模块 | 职责 | 核心实体 | 外部依赖 |
|------|------|---------|---------|
| auth | 认证授权、RBAC | User, LoginAttempt | SSO Provider |
| training | 训练任务管理 | TrainingJob, Checkpoint | HyperPod, Kueue |
| models | 模型版本控制 | Model, ModelVersion | Model Registry |
| quotas | 资源配额管理 | ResourceQuota | Kueue ClusterQueue |
| spaces | 开发环境管理 | Space | SageMaker Spaces |
| audit | 审计日志 | AuditLog | - |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | 数据库连接串 |
| `AWS_REGION` | `us-east-1` | AWS 区域 |
| `S3_BUCKET_NAME` | - | S3 桶名称 |
| `SECRET_KEY` | - | JWT 密钥 |

## Testing

详见 `tests/CLAUDE.md`

## Related Rules

| 规则 | 文件 |
|------|------|
| SDK 优先 | `.claude/rules/backend/sdk-first.md` |
| 架构规范 | `.claude/rules/backend/clean-arch.md` |
| 注释规范 | `.claude/rules/backend/docstring.md` |

## Related Docs

| 文档 | 位置 |
|------|------|
| 架构规范 | `docs/ARCHITECTURE.md` |
| 测试规范 | `tests/CLAUDE.md` |
| 功能规范 | `specs/001-ai-training-platform/spec.md` |
