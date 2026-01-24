# AI Training Platform

企业级 AI 训练平台 - 基于 AWS SageMaker HyperPod 构建

## 目录

- [项目概述](#项目概述)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [文档](#文档)

---

## 项目概述

AI Training Platform 是面向企业的 AI 模型训练管理平台，基于 AWS SageMaker HyperPod with EKS 构建，提供分布式训练、资源调度、数据管理和多租户支持能力。

### 目标指标

| 目标 | 指标 | 说明 |
|------|------|------|
| GPU 利用率 | ≥70% | 智能调度和资源优化 |
| 训练效率 | 周期缩短 ≥50% | 同等规模任务下 |
| 成本优化 | 降低 ≥30% | 提高资源利用率 |
| 平台可用性 | 99%+ | 年度可用性目标 |
| 故障恢复 | <5 分钟 | 节点故障自动恢复 |

### 目标用户

- **算法工程师**: 提交和监控分布式训练任务
- **数据工程师**: 管理和版本控制训练数据集
- **平台管理员**: 配置资源配额，管理用户权限
- **项目经理**: 查看资源使用报表和成本分析

---

## 核心功能

### 分布式训练

| 训练模式 | 适用场景 |
|---------|---------|
| **DDP** | 多节点数据并行（推荐） |
| **FSDP** | 超大模型参数分片 |
| **DeepSpeed ZeRO** | 极大规模模型内存优化 |

### 资源调度

- **Gang Scheduling**: 分布式任务所有 Pod 同时调度（≤60秒）
- **优先级抢占**: High/Medium/Low 三级优先级，高优先级可抢占
- **资源配额**: 基于 Kueue 的按部门/项目配额管理

### 数据与检查点

- **数据集管理**: 版本控制、10GB+ 断点续传、FSx for Lustre 高性能存储
- **检查点管理**: 分层存储（NVMe → FSx → S3）、自动恢复（成功率 ≥99%）

### 企业级特性

- **多租户**: Kubernetes Namespace 隔离 + RBAC
- **SSO 认证**: SAML/OIDC 集成，本地账号降级
- **实时监控**: Prometheus + Grafana + MLflow
- **成本核算**: 按分钟计费、多级预警

---

## 技术架构

### 后端 (DDD + Modular Monolith)

```
backend/src/
├── modules/              # 业务模块 (垂直切分)
│   ├── auth/            # 认证授权
│   ├── training/        # 训练任务管理
│   ├── datasets/        # 数据集管理
│   ├── quotas/          # 资源配额
│   ├── models/          # 模型管理
│   ├── spaces/          # 开发空间
│   ├── audit/           # 审计日志
│   ├── billing/         # 成本计费
│   └── monitoring/      # 监控告警
└── shared/              # 共享内核
```

**每个模块遵循 Clean Architecture 四层结构**:
- `api/` → `application/` → `domain/` ← `infrastructure/`

> 详细架构规范: [backend/docs/ARCHITECTURE.md](./backend/docs/ARCHITECTURE.md)

### 前端 (Feature-Based)

```
frontend/src/
├── features/            # 功能模块
│   ├── training/       # 训练任务
│   ├── datasets/       # 数据集
│   ├── models/         # 模型
│   └── ...
├── shared/             # 共享组件/hooks
└── store/              # 全局状态 (Zustand)
```

> 详细开发指南: [frontend/CLAUDE.md](./frontend/CLAUDE.md)

### 基础设施 (AWS CDK)

```
CDK Stack 分层:

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

> 详细部署指南: [infrastructure/cdk/CLAUDE.md](./infrastructure/cdk/CLAUDE.md)

### 技术栈一览

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11, FastAPI, SQLAlchemy 2.0, MySQL/Aurora |
| **前端** | TypeScript, React 18, Vite, AWS Cloudscape |
| **基础设施** | AWS CDK, EKS 1.32+, SageMaker HyperPod |
| **存储** | S3, FSx for Lustre, Aurora MySQL |
| **监控** | Prometheus, Grafana, MLflow |

---

## 快速开始

### 前提条件

- Python 3.11+
- Node.js 18+ LTS
- Docker / Docker Compose v2+
- AWS CLI 2.x (可选)

### 一键启动

```bash
# 克隆项目
git clone <repository-url>
cd ai-studio-project

# 启动所有服务 (MySQL + 后端 + 前端)
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 手动启动

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload

# 前端 (新终端)
cd frontend
npm install && npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

---

## 项目结构

```
ai-studio-project/
├── backend/                 # 后端服务 (FastAPI)
│   ├── src/modules/        # 业务模块
│   ├── tests/              # 测试
│   ├── alembic/            # 数据库迁移
│   └── CLAUDE.md           # 后端开发指南
│
├── frontend/                # 前端应用 (React)
│   ├── src/features/       # 功能模块
│   └── CLAUDE.md           # 前端开发指南
│
├── infrastructure/          # 基础设施
│   ├── cdk/                # AWS CDK Stacks
│   │   └── CLAUDE.md       # CDK 开发指南
│   └── k8s/                # Kubernetes 资源
│
├── specs/                   # 功能规范 (Spec-Kit)
│   └── 001-ai-training-platform/
│       ├── spec.md         # 功能规范
│       ├── plan.md         # 实施计划
│       ├── tasks.md        # 任务清单
│       └── data-model.md   # 数据模型
│
├── docker-compose.yml       # 本地开发环境
└── CLAUDE.md               # 项目总体指南
```

---

## 开发指南

### TDD 工作流

项目全面采用测试驱动开发:

```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

### 常用命令

**后端**:
```bash
pytest                          # 运行测试
pytest --cov=src               # 带覆盖率
black src/ && ruff check src/  # 代码检查
alembic upgrade head           # 数据库迁移
```

**前端**:
```bash
npm test                       # 运行测试
npm run lint                   # ESLint 检查
npm run build                  # 生产构建
```

**CDK**:
```bash
cdk deploy --context env=dev   # 部署开发环境
pytest -m unit                 # CDK 单元测试
```

### 代码规范

| 层级 | 格式化 | Lint | 类型检查 |
|------|--------|------|---------|
| 后端 | black | ruff | mypy |
| 前端 | prettier | eslint | tsc |
| CDK | black | ruff | mypy |

---

## 文档

### 开发文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 后端开发指南 | [backend/CLAUDE.md](./backend/CLAUDE.md) | TDD 流程、命令、架构 |
| 后端架构规范 | [backend/docs/ARCHITECTURE.md](./backend/docs/ARCHITECTURE.md) | 模块化单体架构详解 |
| 前端开发指南 | [frontend/CLAUDE.md](./frontend/CLAUDE.md) | React 架构、组件规范 |
| CDK 部署指南 | [infrastructure/cdk/CLAUDE.md](./infrastructure/cdk/CLAUDE.md) | Stack 分层、部署流程 |

### 规范文档 (Spec-Kit)

| 文档 | 位置 | 说明 |
|------|------|------|
| 功能规范 | [specs/.../spec.md](./specs/001-ai-training-platform/spec.md) | 完整功能需求和术语 |
| 实施计划 | [specs/.../plan.md](./specs/001-ai-training-platform/plan.md) | 里程碑和技术方案 |
| 数据模型 | [specs/.../data-model.md](./specs/001-ai-training-platform/data-model.md) | 数据库设计 |
| 任务清单 | [specs/.../tasks.md](./specs/001-ai-training-platform/tasks.md) | 开发任务列表 |

---

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。
