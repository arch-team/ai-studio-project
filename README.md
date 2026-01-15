# AI Training Platform

企业级 AI 训练平台 - 基于 AWS SageMaker HyperPod 构建

## 项目概述

AI Training Platform 是一个面向企业的 AI 模型训练管理平台，基于 AWS SageMaker HyperPod with EKS 构建，提供完整的分布式训练、资源调度、数据管理和多租户支持能力。

### 核心目标

| 目标 | 指标 | 说明 |
|------|------|------|
| GPU 利用率 | ≥70% | 通过智能调度和资源优化提升集群利用率 |
| 训练效率 | 周期缩短≥50% | 在同等规模任务下，训练周期缩短一半 |
| 成本优化 | 降低≥30% | 通过提高资源利用率和优化调度降低算力成本 |
| 平台可用性 | 99%+ | 年度可用性目标 |
| 故障恢复 | 5分钟内 | 节点故障后自动恢复时间 |

### 目标用户

- **算法工程师**: 提交和监控分布式训练任务，使用在线开发环境
- **数据工程师**: 管理和版本控制训练数据集
- **平台管理员**: 配置资源配额，监控集群状态，管理用户权限
- **项目经理**: 查看资源使用报表和成本分析

## 核心功能

### 分布式训练管理

支持 PyTorch 分布式训练框架：

| 训练模式 | 适用场景 | 说明 |
|---------|---------|------|
| **DataParallel** | 单机多卡 | 基础分布式能力，适合小规模训练 |
| **DDP** | 多节点数据并行 | 推荐的多节点训练模式，性能优于 DataParallel |
| **FSDP** | 超大模型 | 支持参数分片，适用于大模型训练 |
| **DeepSpeed ZeRO** | 极大规模模型 | Stage 1/2/3，提供内存优化和并行策略 |

### 资源调度

- **Gang Scheduling**: 确保分布式训练任务的所有 Pod 同时调度（时间窗口≤60秒）
- **三级优先级**: High/Medium/Low 优先级体系
- **抢占式调度**: 高优先级任务可抢占低优先级任务资源，抢占前自动创建检查点
- **资源配额**: 按部门/项目分配 GPU/CPU/内存配额

### 数据集管理

- **大文件上传**: 支持 10GB+ 文件断点续传，上传成功率 99%
- **版本控制**: 数据集版本创建、标记和比较
- **高性能存储**: 基于 FSx for Lustre，单任务数据读取吞吐量≥5GB/s

### 检查点管理

- **自动检查点**: 定期创建（默认 10-15 分钟间隔）
- **分层存储**: NVMe 本地存储 → FSx for Lustre → S3
- **断点续训**: 支持从检查点自动恢复，成功率≥99%

### 多租户支持

- **资源隔离**: 基于 Kubernetes Namespace 的资源隔离
- **RBAC**: 基于角色的访问控制，遵循最小权限原则
- **配额管理**: 通过 HyperPod Task Governance (Kueue) 管理资源配额

### 实时监控

- **训练指标**: Loss、Accuracy、学习率、训练吞吐量（指标刷新≤30秒）
- **资源监控**: GPU/CPU/内存利用率（Prometheus 采集间隔 15 秒）
- **日志流**: 实时日志查看（延迟<10秒）
- **实验追踪**: 基于 SageMaker Managed MLflow 的实验和模型版本管理

### 企业级认证

- **SSO 集成**: 支持 SAML/OIDC 企业身份系统
- **本地账号**: SSO 不可用时的备用认证方式
- **故障转移**: 自动检测 SSO 故障并降级到本地认证

### 成本核算

- **按分钟计费**: 精确的资源使用成本追踪
- **多级预警**: 80%/90%/100% 预算预警阈值
- **使用报表**: 按时间、项目、用户维度的资源使用统计

### 在线开发环境

- **JupyterLab/VS Code**: 基于 SageMaker Spaces 的在线 IDE
- **GPU 直连**: 直接访问 GPU 资源进行实验
- **启动时间**: <3 分钟冷启动

## 系统架构

### 后端架构 (Clean Architecture + DDD)

```
┌─────────────────────────────────────────────────────────────┐
│                      API 层 (Adapters)                       │
│   FastAPI 端点、Pydantic 请求/响应模型、依赖注入              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    应用层 (Use Cases)                        │
│   业务用例实现、DTO、端口定义 (HyperPod, Storage)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      域层 (Core)                             │
│   实体、值对象、仓库接口、域异常、域事件                     │
└─────────────────────────▲───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   基础设施层 (Adapters)                       │
│   ORM 模型、仓库实现、外部适配器 (HyperPod/S3/Kueue)         │
└─────────────────────────────────────────────────────────────┘

依赖方向: API → Application → Domain ← Infrastructure
```

**目录结构:**

```
backend/src/
├── api/                    # API 层
│   ├── v1/endpoints/      # REST 端点
│   ├── v1/schemas/        # Pydantic 请求/响应模型
│   ├── v1/dependencies/   # FastAPI 依赖注入
│   └── middleware/        # 中间件 (auth, audit, sso)
├── application/            # 应用层
│   ├── services/          # 用例实现
│   ├── dto/               # 数据传输对象
│   └── interfaces/        # 端口定义
├── domain/                 # 域层
│   ├── entities/          # 业务实体
│   ├── value_objects/     # 值对象
│   ├── repositories/      # 仓库接口
│   └── exceptions/        # 域异常
├── infrastructure/         # 基础设施层
│   ├── persistence/       # ORM 模型和仓库实现
│   └── external/          # 外部适配器 (hyperpod/, s3/, kueue/)
└── core/                   # 跨切关注点 (logging, security)
```

### 前端架构 (Feature-Based)

```
frontend/src/
├── features/              # 业务功能模块
│   ├── auth/             # 认证模块
│   ├── training-jobs/    # 训练任务管理
│   ├── datasets/         # 数据集管理
│   └── monitoring/       # 监控面板
├── app/                   # 应用入口
├── lib/                   # 基础设施
├── store/                 # 全局状态 (Zustand)
└── types/                 # TypeScript 类型定义
```

### 基础设施架构 (CDK Stack 分层)

```
Layer 1: NetworkStack, IamStack (并行部署)
    ↓
Layer 2: DatabaseStack, StorageStack (并行部署)
    ↓
Layer 3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
    ↓
Layer 4: FsxLustreStack
    ↓
Layer 5: AlbStack
```

**HyperPod Add-ons:**

| Add-on | 功能 |
|--------|------|
| **Training Operator** | 分布式训练任务编排，Gang Scheduling |
| **Task Governance (Kueue)** | 资源配额管理，优先级调度，抢占策略 |
| **Observability** | Prometheus + Grafana 监控 |
| **Spaces** | JupyterLab/VS Code 在线开发环境 |
| **Health Check Agent** | 节点健康检查，故障检测 |
| **Elastic Agent** | 检查点管理，Auto-Resume |

## 技术栈

### 后端

| 类别 | 技术 | 版本 |
|------|------|------|
| **运行时** | Python | 3.11 |
| **Web 框架** | FastAPI | 0.109+ |
| **ASGI 服务器** | Uvicorn | 0.27+ |
| **ORM** | SQLAlchemy (async) | 2.0.25 |
| **数据库迁移** | Alembic | 1.13+ |
| **数据验证** | Pydantic | 2.5+ |
| **数据库** | MySQL (dev) / Aurora MySQL (prod) | 8.0 / 3.x |
| **AWS SDK** | boto3 | 1.34+ |
| **HyperPod SDK** | sagemaker-hyperpod | 1.0.0 |
| **认证** | python-jose (JWT), passlib (bcrypt) | - |
| **日志** | structlog | - |

### 前端

| 类别 | 技术 | 版本 |
|------|------|------|
| **语言** | TypeScript | 5.3+ |
| **框架** | React | 18.2 |
| **构建工具** | Vite | 5.0+ |
| **UI 组件库** | AWS Cloudscape Design System | 3.0 |
| **状态管理** | Zustand | 4.4+ |
| **数据获取** | TanStack Query | 5.17+ |
| **路由** | React Router | 6.x |
| **测试** | Vitest | 1.2+ |

### 基础设施

| 类别 | 技术 | 说明 |
|------|------|------|
| **IaC** | AWS CDK (Python) | 基础设施即代码 |
| **容器编排** | EKS | 1.32+ |
| **训练平台** | SageMaker HyperPod | with EKS |
| **高性能存储** | FSx for Lustre | 训练数据存储 |
| **对象存储** | S3 | 模型制品、检查点 |
| **数据库** | Aurora MySQL | 3.x (兼容 MySQL 8.0) |
| **监控** | Prometheus + Grafana | HyperPod Observability |
| **实验追踪** | SageMaker Managed MLflow | - |
| **GitOps** | ArgoCD | 配置自动同步 |

## HyperPod 集成

### SDK-First 原则

项目遵循 SDK-First 开发原则，按功能域选择合适的 SDK：

| 功能域 | 推荐 SDK | 说明 |
|--------|---------|------|
| **训练任务管理** | `sagemaker-hyperpod.training` | 任务提交、状态监控、生命周期管理 |
| **集群管理** | `sagemaker-hyperpod.cluster` | 集群状态查询、节点健康监控 |
| **在线开发环境** | `sagemaker-hyperpod.space` | Space 创建、配置、生命周期管理 |
| **推理服务** | `sagemaker-hyperpod.inference` | 模型端点创建、扩缩容 |
| **模型注册** | boto3 (SageMaker API) | Model Registry 操作 |
| **存储操作** | boto3 (S3 API) | 数据集、检查点存储 |
| **监控指标** | boto3 (CloudWatch API) | 资源利用率查询 |
| **状态监控** | kubernetes-client | Kueue Workload 状态查询（例外场景） |

### Task Governance (Kueue)

HyperPod Task Governance 基于 Kueue 提供企业级资源调度能力：

**资源配额管理:**
- ClusterQueue: 集群级资源池，定义 GPU/CPU/内存配额
- LocalQueue: 命名空间级队列，实现租户隔离

**优先级配置:**

| 优先级 | Kueue Priority | 使用场景 |
|--------|---------------|---------|
| High | 1000 | 紧急任务、关键业务训练 |
| Medium | 500 | 常规生产任务、模型微调 |
| Low | 100 | 基础训练任务、实验性训练 |

**抢占式调度:**
- 高优先级任务可抢占低优先级任务
- 抢占前自动创建检查点（超时 5 分钟强制抢占）
- 被抢占任务自动重新排队恢复

## 快速开始

### 前提条件

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.11+ | 后端运行时 |
| Node.js | 18+ LTS | 前端构建 |
| Docker | 最新稳定版 | 容器化部署 |
| Docker Compose | v2+ | 本地开发环境 |
| AWS CLI | 2.x | AWS 服务交互 |
| kubectl | 与 EKS 版本匹配 | Kubernetes 操作 |

### 本地开发

**1. 克隆仓库**

```bash
git clone <repository-url>
cd ai-studio-project
```

**2. 配置环境变量**

```bash
# 后端
cp backend/.env.example backend/.env
# 编辑 backend/.env 配置数据库连接等

# 前端
cp frontend/.env.example frontend/.env
# 编辑 frontend/.env 配置 API 地址等
```

**3. 使用 Docker Compose 启动**

```bash
# 启动所有服务 (MySQL + 后端 + 前端)
docker-compose up -d

# 查看日志
docker-compose logs -f
```

**4. 或手动启动各服务**

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head  # 数据库迁移
uvicorn src.main:app --reload

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

**5. 访问应用**

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| API 文档 (ReDoc) | http://localhost:8000/redoc |

### 数据库迁移

```bash
cd backend

# 应用所有迁移
alembic upgrade head

# 生成新迁移
alembic revision --autogenerate -m "description"

# 回滚上一个迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

## 开发指南

### TDD 工作流

项目践行测试驱动开发 (TDD)，遵循 **Red-Green-Refactor** 循环：

```
1. 🔴 Red: 先写失败的测试
   pytest tests/unit/domain/test_training_job.py -v

2. 🟢 Green: 编写最少代码使测试通过
   pytest tests/unit/domain/test_training_job.py -v

3. 🔄 Refactor: 重构代码，保持测试通过
   pytest tests/unit/ -v && black src/ && ruff check src/
```

### 测试分层

| 层级 | 位置 | 测试对象 | Mock 策略 |
|------|------|---------|----------|
| **单元测试** | `tests/unit/domain/` | 实体、值对象、域逻辑 | 无依赖，纯函数 |
| **单元测试** | `tests/unit/application/` | 应用服务 | Mock 仓库接口 |
| **集成测试** | `tests/integration/api/` | API 端点 | Mock 外部服务 |
| **集成测试** | `tests/integration/persistence/` | 仓库实现 | 真实数据库 |
| **E2E 测试** | `tests/e2e/` | 完整流程 | 最小化 Mock |

**覆盖率目标:**
- 核心功能 (P1): ≥80%
- 次要功能 (P2): ≥70%
- 辅助功能 (P3): ≥60%

### 代码风格

**Python:**

```bash
cd backend

# 格式化
black src/ tests/

# Lint 检查
ruff check src/ tests/

# 类型检查
mypy src/

# 全部检查
black src/ && ruff check src/ && mypy src/
```

**TypeScript:**

```bash
cd frontend

# 格式化
npm run format

# Lint 检查
npm run lint

# 类型检查
npm run type-check
```

### 测试命令

**后端:**

```bash
cd backend

# 运行全部测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 带覆盖率
pytest --cov=src --cov-report=html

# 运行单个测试
pytest -k "test_name"

# 失败时立即停止
pytest -x

# 显示详细输出
pytest -v --tb=short
```

**前端:**

```bash
cd frontend

# 运行测试
npm test

# 带覆盖率
npm run test:coverage

# 监视模式
npm run test:watch
```

## 术语标准

项目使用统一的术语标准，确保代码、文档和 API 的一致性：

### 核心实体

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 用户 | `User` | `users` | `/users` |
| 审计日志 | `AuditLog` | `audit_logs` | `/audit-logs` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |
| 任务模板 | `JobTemplate` | `job_templates` | `/job-templates` |

### 训练任务状态

| 状态 | 说明 |
|------|------|
| `Submitted` | 已提交，等待资源分配 |
| `Running` | 训练正在执行 |
| `Paused` | 用户主动暂停 |
| `Preempted` | 被高优先级任务抢占 |
| `Completed` | 训练成功完成 |
| `Failed` | 训练失败 |

### 命名规范

| 场景 | 规范 | 示例 |
|------|------|------|
| Python 类 | PascalCase | `TrainingJob` |
| Python 函数/变量 | snake_case | `training_job` |
| Python 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 数据库表 | 小写复数 + 下划线 | `training_jobs` |
| API 路径 | 小写复数 + 短横线 | `/training-jobs` |
| TypeScript 接口 | PascalCase | `TrainingJob` |
| TypeScript 变量 | camelCase | `trainingJob` |
| React 组件 | PascalCase | `TrainingJobList` |

## 项目结构

```
ai-studio-project/
├── backend/                    # 后端服务 (FastAPI)
│   ├── src/                   # 源代码 (Clean Architecture)
│   │   ├── api/              # API 层
│   │   ├── application/      # 应用层
│   │   ├── domain/           # 域层
│   │   ├── infrastructure/   # 基础设施层
│   │   └── core/             # 跨切关注点
│   ├── tests/                # 测试
│   │   ├── unit/            # 单元测试
│   │   ├── integration/     # 集成测试
│   │   └── e2e/             # 端到端测试
│   ├── alembic/             # 数据库迁移
│   ├── CLAUDE.md            # 后端开发指南
│   └── requirements.txt     # Python 依赖
│
├── frontend/                   # 前端应用 (React + Vite)
│   ├── src/                  # 源代码
│   │   ├── features/        # 业务功能模块
│   │   ├── app/             # 应用入口
│   │   ├── lib/             # 基础设施
│   │   └── store/           # 全局状态
│   ├── CLAUDE.md            # 前端开发指南
│   └── package.json         # Node.js 依赖
│
├── infrastructure/             # 基础设施代码
│   ├── cdk/                  # AWS CDK (Python)
│   │   ├── stacks/          # CDK Stack 定义
│   │   └── CLAUDE.md        # 基础设施开发指南
│   └── k8s/                  # Kubernetes 资源
│       ├── base/            # Kustomize 基础配置
│       └── overlays/        # 环境覆盖配置
│
├── specs/                      # 功能规范文档
│   └── 001-ai-training-platform/
│       ├── spec.md          # 功能规范
│       ├── plan.md          # 实施计划
│       ├── data-model.md    # 数据模型
│       ├── tasks.md         # 任务清单
│       └── quickstart.md    # 快速入门
│
├── docker/                     # Docker 配置
├── docker-compose.yml          # 本地开发环境
├── .env.example               # 环境变量模板
├── CLAUDE.md                  # 项目总体指南
├── CONTRIBUTING.md            # 贡献指南
└── README.md                  # 本文件
```

## 部署

### 本地开发环境

使用 Docker Compose 启动完整开发环境：

```bash
docker-compose up -d
```

### Kubernetes 部署

**1. 配置 kubeconfig**

```bash
aws eks update-kubeconfig --name <cluster-name> --region <region>
```

**2. 部署应用**

```bash
cd infrastructure/k8s
kubectl apply -k overlays/dev/  # 开发环境
kubectl apply -k overlays/prod/ # 生产环境
```

### CDK 部署

**1. 安装依赖**

```bash
cd infrastructure/cdk
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. 部署基础设施**

```bash
# 开发环境
cdk deploy --context env=dev --all

# 生产环境
cdk deploy --context env=prod --all
```

## 监控和日志

| 服务 | 说明 | 访问方式 |
|------|------|---------|
| **Prometheus** | 指标采集和存储 | HyperPod Observability Add-on |
| **Grafana** | 监控仪表盘 | Amazon Managed Grafana |
| **MLflow** | 实验追踪和模型管理 | SageMaker Managed MLflow |
| **CloudWatch Logs** | 日志存储和查询 | AWS Console / API |

## 文档

| 文档 | 位置 | 用途 |
|------|------|------|
| **功能规范** | [specs/001-ai-training-platform/spec.md](./specs/001-ai-training-platform/spec.md) | 完整功能需求和术语标准 |
| **实施计划** | [specs/001-ai-training-platform/plan.md](./specs/001-ai-training-platform/plan.md) | 开发里程碑和任务分解 |
| **数据模型** | [specs/001-ai-training-platform/data-model.md](./specs/001-ai-training-platform/data-model.md) | 数据库设计和实体关系 |
| **任务清单** | [specs/001-ai-training-platform/tasks.md](./specs/001-ai-training-platform/tasks.md) | 详细任务列表 |
| **快速入门** | [specs/001-ai-training-platform/quickstart.md](./specs/001-ai-training-platform/quickstart.md) | 新手入门指南 |
| **后端指南** | [backend/CLAUDE.md](./backend/CLAUDE.md) | TDD 流程、SDK 原则、代码风格 |
| **前端指南** | [frontend/CLAUDE.md](./frontend/CLAUDE.md) | React 架构、状态管理、设计规范 |
| **基础设施指南** | [infrastructure/cdk/CLAUDE.md](./infrastructure/cdk/CLAUDE.md) | CDK Stack 分层、HyperPod 部署 |
| **API 文档** | http://localhost:8000/docs | Swagger UI (本地运行时) |

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解贡献流程。

## 联系方式

- **项目维护者**: AI Platform Team
- **问题反馈**: 请通过 GitHub Issues 提交
