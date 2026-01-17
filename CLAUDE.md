# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

## Project Overview
AI Training Platform - 基于 AWS SageMaker HyperPod 构建的企业级 AI 训练平台。

**核心功能**:
- 分布式训练管理 (PyTorch DDP, FSDP, DeepSpeed)
- 资源调度 (Gang Scheduling, 优先级抢占)
- 数据集管理 (版本控制, 大文件断点续传)
- 检查点管理 (分层存储, 自动恢复)
- 多租户支持 (RBAC, 资源配额)

## Architecture

### 后端: Clean Architecture + DDD

```
backend/src/
├── api/                    # API 层 (HTTP 适配器)
│   ├── v1/endpoints/      # REST 端点
│   ├── v1/schemas/        # Pydantic 请求/响应
│   ├── v1/dependencies/   # FastAPI 依赖注入
│   └── middleware/        # 中间件 (auth, audit, sso)
├── application/            # 应用层 (业务用例)
│   ├── services/          # 用例实现
│   ├── dto/               # 数据传输对象
│   └── interfaces/        # 端口定义
├── domain/                 # 域层 (核心业务)
│   ├── entities/          # 业务实体
│   ├── value_objects/     # 值对象
│   ├── repositories/      # 仓库接口
│   └── exceptions/        # 域异常
├── infrastructure/         # 基础设施层
│   ├── persistence/       # ORM 模型和仓库实现
│   └── external/          # 外部适配器 (hyperpod/, s3/, kueue/)
└── core/                   # 跨切关注点 (logging, security)
```

**依赖方向**: `API → Application → Domain ← Infrastructure`

### 基础设施: CDK Stack 分层

```
Layer 1: NetworkStack, IamStack (并行)
    ↓
Layer 2: DatabaseStack, StorageStack (并行)
    ↓
Layer 3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
    ↓
Layer 4: FsxLustreStack
    ↓
Layer 5: AlbStack
```

## Key Development Principles

### SDK-First 原则

| 领域 | 推荐方案 | 说明 |
|------|---------|------|
| 训练任务 | HyperPod Task Governance API | 所有配置操作通过 SDK |
| 调度状态查询 | kubernetes-client (例外) | 仅用于状态监控和故障诊断 |
| 后台任务 | K8s CronJob + Watch API | 无需 Celery |
| 日志 | structlog | 结构化 JSON |

### TDD 工作流

```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试分层**:
- Unit (`tests/unit/`): 实体、值对象、域逻辑
- Integration (`tests/integration/`): API 端点、仓库实现
- AWS Integration (`-m aws_integration`): HyperPod, S3 集成

## Terminology Standards

详细术语规范参见 `specs/001-ai-training-platform/spec.md`

**核心实体命名**:

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |

**训练任务状态**:
`submitted` → `running` → `completed` / `failed` / `paused` / `preempted`

## Key Documentation

| 文档 | 位置 | 用途 |
|------|------|------|
| **功能规范** | `specs/001-ai-training-platform/spec.md` | 完整功能需求和术语标准 |
| **实施计划** | `specs/001-ai-training-platform/plan.md` | 开发里程碑和任务分解 |
| **数据模型** | `specs/001-ai-training-platform/data-model.md` | 数据库设计和实体关系 |
| **后端开发指南** | `backend/CLAUDE.md` | TDD 流程、SDK 原则、代码风格 |
| **前端开发指南** | `frontend/CLAUDE.md` | React 架构、状态管理、设计规范 |
| **CDK 部署指南** | `infrastructure/cdk/CLAUDE.md` | Stack 分层、HyperPod 部署流程 |

## Spec-Kit 文件体系

本项目使用 Spec-Kit 进行规范驱动开发。文件结构和职责如下：

### 目录结构
```
.specify/memory/constitution.md    # 项目宪法 (全局约束)
specs/{feature}/
├── spec.md          # 功能规范 (WHAT/WHY)
├── plan.md          # 实施计划 (HOW)
├── tasks.md         # 任务清单 (DO)
├── data-model.md    # 数据模型设计
├── research.md      # 技术研究报告
├── quickstart.md    # 快速开始指南
├── checklists/      # 质量检查清单
└── contracts/       # OpenAPI 契约
```

### 文件职责速查

| 文件 | 生成命令 | 职责 |
|------|---------|------|
| `constitution.md` | `/speckit.constitution` | 不可违反的核心原则和技术约束 |
| `spec.md` | `/speckit.specify` | 用户故事、验收标准、术语定义 |
| `plan.md` | `/speckit.plan` | 技术选型、架构设计、里程碑 |
| `tasks.md` | `/speckit.tasks` | 可执行的原子任务清单 (0.5-2人日/任务) |
| `data-model.md` | (plan 附带) | 数据库表结构、持久化策略 |
| `research.md` | (plan 附带) | SDK 可行性验证、技术决策依据 |
| `contracts/*.yaml` | (plan 附带) | OpenAPI 3.0 API 接口规范 |
| `checklists/*.md` | `/speckit.checklist` | 架构/安全/UX 质量验证清单 |

### 工作流程
```
constitution → specify → [clarify] → plan → [checklist] → tasks → implement
```

### 一致性检查
运行 `/speckit.analyze` 检查 spec.md、plan.md、tasks.md 之间的一致性。
