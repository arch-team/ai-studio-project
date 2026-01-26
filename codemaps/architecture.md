# AI Training Platform 架构概览

**更新时间**: 2026-01-26 10:30
**版本**: 1.0.0

## 技术栈摘要

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python + FastAPI | 3.11+ / 0.109+ |
| **ORM** | SQLAlchemy (Async) | 2.0.25 |
| **数据库** | Aurora MySQL Serverless v2 | 8.0 |
| **前端** | React + TypeScript + Vite | 18.2 / 5.3+ / 5.0+ |
| **UI 库** | AWS Cloudscape | 3.0.0 |
| **状态** | TanStack Query + Zustand | 5.17 / 4.4.7 |
| **IaC** | AWS CDK (Python) | 2.x |
| **容器** | EKS + SageMaker HyperPod | 1.33+ |
| **调度** | Kueue (Gang Scheduling) | - |
| **存储** | S3 + FSx for Lustre | - |

## 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  React + TypeScript + AWS Cloudscape                            │
│  Feature-Sliced Design | TanStack Query | Zustand               │
│  11 功能模块 | EventBus 跨模块通信                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (HTTPS)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          BACKEND                                 │
│  Python + FastAPI + SQLAlchemy 2.0                              │
│  DDD + Modular Monolith + Clean Architecture                    │
│  9 业务模块 | EventBus + 共享接口                                │
├─────────────────────────────────────────────────────────────────┤
│  API → Application → Domain ← Infrastructure                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ boto3 / aioboto3
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                              │
│  AWS CDK (8 Stacks) + Kubernetes + HyperPod                     │
│  VPC | Aurora | S3 | EKS | FSx | ALB                            │
│  Training Operator | Kueue | Prometheus/Grafana                 │
└─────────────────────────────────────────────────────────────────┘
```

## 模块依赖图

### 后端模块 (9个)

```
SHARED KERNEL (基础层)
├── domain: BaseEntity, IRepository, DomainEvent, EventBus
├── infrastructure: Base, get_db, BaseRepository, Settings
├── api: exception_handlers, middleware, schemas
└── utils: datetime, pagination, mapping

业务模块 (垂直切分)
├── auth [19 exports] ──────────────────────────┐
├── training [24 exports] ← quotas (interface)  │ R4 例外:
├── models [11 exports]                         │ Auth 依赖
├── quotas [13 exports] → IQuotaChecker         │ 可在 API
├── spaces [14 exports]                         │ 层导入
├── datasets [5 exports] (部分实现)              │
├── audit [8 exports] ← EventBus 订阅           │
├── monitoring [0 exports] (骨架)               │
└── billing [0 exports] (空)                    ┘
```

### 前端模块 (11个)

```
App (Router + Providers)
├── features/
│   ├── auth        → authStore (Zustand)
│   ├── training    → TrainingJobTable, queries.ts
│   ├── models      → ModelTable, ModelVersionTable
│   ├── datasets    → (待实现)
│   ├── templates   → TemplateTable
│   ├── spaces      → (待实现)
│   ├── audit       → (待实现)
│   ├── monitoring  → (待实现)
│   ├── billing     → (待实现)
│   ├── resource-quotas → ResourceQuotasPage
│   └── templates   → PopularTemplates
└── shared/
    ├── api/client.ts (ApiClient)
    ├── hooks/ (useEntity, usePagination, useDebounce)
    ├── events/eventBus.ts (发布-订阅)
    └── types/errors.ts (AppError, ErrorCode)
```

### CDK Stack 分层 (5层)

```
Layer 1 (并行): NetworkStack, IamStack
    ↓
Layer 2 (并行): DatabaseStack, StorageStack
    ↓
Layer 3 (顺序): EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
    ↓
Layer 4: FsxLustreStack
    ↓
Layer 5: AlbStack
```

## 关键路径

### 训练任务生命周期

```
Frontend                    Backend                      AWS
   │                          │                           │
   │ POST /training-jobs      │                           │
   ├─────────────────────────►│                           │
   │                          │ IQuotaChecker.check()     │
   │                          ├──────────────────────────►│
   │                          │                           │
   │                          │ HyperPodClient.submit()   │
   │                          ├──────────────────────────►│
   │                          │                           │ Kueue Queue
   │                          │                           │ PyTorchJob
   │ SSE: status updates      │                           │
   │◄─────────────────────────┤ EventBus: JobStarted      │
   │                          │                           │
   │ GET /training-jobs/:id/logs                          │
   ├─────────────────────────►│ CloudWatch Logs           │
   │                          ├──────────────────────────►│
```

### 数据流

```
用户上传 → S3 (datasets/) → FSx Lustre (DRA) → Training Pod
                                    ↓
                            Checkpoint → S3 (checkpoints/)
                                    ↓
                            Model → S3 (models/) → Model Registry
```

## 目录结构速查

| 路径 | 用途 |
|------|------|
| `backend/src/modules/` | 9 个业务模块 |
| `backend/src/shared/` | 共享内核 |
| `frontend/src/features/` | 11 个功能模块 |
| `frontend/src/shared/` | 共享组件和工具 |
| `infrastructure/cdk/stacks/` | 8 个 CDK Stack |
| `infrastructure/k8s/` | Kubernetes 资源清单 |
| `specs/001-ai-training-platform/` | Spec-Kit 规范文档 |
| `codemaps/` | 架构文档 (本目录) |

## 关键文档

| 文档 | 位置 |
|------|------|
| 功能规范 | `specs/001-ai-training-platform/spec.md` |
| 实施计划 | `specs/001-ai-training-platform/plan.md` |
| 数据模型 | `specs/001-ai-training-platform/data-model.md` |
| 后端架构 | `backend/docs/ARCHITECTURE.md` |
| 后端开发 | `backend/CLAUDE.md` |
| 前端开发 | `frontend/CLAUDE.md` |
| CDK 开发 | `infrastructure/cdk/CLAUDE.md` |
