# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **回复语言要求参见根目录 `CLAUDE.md`**

## Project Overview

AI Training Platform 后端服务 - 基于 AWS SageMaker HyperPod 的企业级 AI 训练平台 API。

## Tech Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.109.0 + Uvicorn 0.27.0
- **ORM**: SQLAlchemy 2.0.25 (async) + Alembic 1.13.1
- **Database**: MySQL 8.0 (aiomysql 异步驱动)
- **Validation**: Pydantic 2.5.3 + pydantic-settings
- **AWS**: boto3 1.34.14, sagemaker-hyperpod 1.0.0
- **Auth**: python-jose (JWT), passlib (bcrypt)

## Common Commands

```bash
# 启动开发服务器
uvicorn src.main:app --reload

# 数据库迁移
alembic upgrade head                    # 应用所有迁移
alembic revision --autogenerate -m "xxx" # 生成迁移

# 运行测试
pytest                                  # 全部测试
pytest tests/unit/                      # 单元测试
pytest tests/integration/               # 集成测试
pytest -k "test_name"                   # 运行单个测试
pytest --cov=src                        # 带覆盖率

# 代码质量
black src/ tests/                       # 格式化
ruff check src/ tests/                  # Lint
mypy src/                               # 类型检查
black src/ && ruff check src/ && mypy src/  # 全部检查

# Docker
docker build --target development -t backend:dev .
docker build --target production -t backend:prod .

# 架构合规检查
pytest tests/unit/test_architecture_compliance.py -v
```

## Architecture

> **核心架构规范请参见**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

@docs/ARCHITECTURE.md

项目采用 **DDD + Modular Monolith + Clean Architecture** 架构模式。

### 目录结构概览

```
src/
├── modules/                           # 功能模块 (auth, training, models, quotas, ...)
│   └── <module>/
│       ├── api/                       # HTTP 端点、Schema、依赖
│       ├── application/               # 业务服务
│       ├── domain/                    # 实体、值对象、仓库接口
│       └── infrastructure/            # ORM 模型、仓库实现
├── shared/                            # 共享内核
│   ├── domain/                        # 基础实体、仓库接口、域事件、跨模块接口
│   ├── infrastructure/                # 数据库、配置、安全
│   ├── api/                           # 中间件、异常处理、分页
│   └── utils/                         # 工具函数
├── main.py                            # 应用入口
└── router.py                          # 路由聚合
```

### 关键规范（详见 docs/ARCHITECTURE.md）

- **黄金法则 R1-R4**: 模块间依赖规则
- **模块间通信**: 事件驱动 + 共享接口
- **异常处理**: 全局异常处理器自动映射 HTTP 状态码
- **依赖注入**: 5 层依赖注入链

## Environment Variables

通过 `.env` 文件或环境变量配置:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://...` | 数据库连接串 |
| `AWS_REGION` | `us-east-1` | AWS 区域 |
| `S3_BUCKET_NAME` | `ai-training-platform` | S3 桶名称 |
| `SECRET_KEY` | `change-me-in-production` | JWT 密钥 |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | 允许的 CORS 源 |

## Testing

```
tests/
├── conftest.py            # 共享 fixtures (AsyncClient)
├── unit/                  # 单元测试 (domain, application)
├── integration/           # 集成测试 (api, persistence)
└── e2e/                   # 端到端测试
```

测试使用 `pytest-asyncio` 进行异步测试，`httpx.AsyncClient` + `ASGITransport` 测试 API 端点。

### 测试规范

> TDD 核心原则和测试诚信原则请参见根目录 `CLAUDE.md`

**后端测试分层**:

| 层级 | 位置 | 测试对象 | Mock 策略 |
|------|------|---------|----------|
| **Unit** | `tests/unit/domain/` | 实体、值对象、域逻辑 | 无依赖，纯函数 |
| **Unit** | `tests/unit/application/` | 应用服务 | Mock 仓库接口 |
| **Integration** | `tests/integration/api/` | API 端点 | Mock 外部服务 |
| **Integration** | `tests/integration/persistence/` | 仓库实现 | 真实数据库 |

**命令速查**:

```bash
pytest tests/unit/ --watch    # 监视模式
pytest --lf                   # 只运行上次失败
pytest -x                     # 失败时立即停止
pytest -v --tb=short          # 详细输出
```

## Code Style

### Docstring 规范

**原则**: 类型签名即文档，注释解释"为什么"而非"做什么"。

| 场景 | 规则 | 示例行数 |
|------|------|---------|
| Module docstring | 单行，说明模块职责 | 1 行 |
| Class docstring | 1-2 行，不重复模块信息 | 1-2 行 |
| Method docstring | 1 行 + 类型签名 | 1 行 |
| Args/Returns | 仅当类型签名不够清晰时 | 按需 |

**示例**:

```python
# ❌ 冗余
async def get_by_id(self, id: UUID) -> Optional[T]:
    """Retrieve an entity by its unique identifier.

    Args:
        id: The unique identifier of the entity.

    Returns:
        The entity if found, None otherwise.
    """

# ✅ 简洁
async def get_by_id(self, id: UUID) -> Optional[T]:
    """Get entity by ID."""
```

### 行内注释规范

```python
# ❌ 多余 - 代码已自解释
app.add_middleware(CORSMiddleware, ...)  # Configure CORS

# ✅ 有价值 - 解释"为什么"
# Burst decay prevents resource hoarding while allowing spikes
burst_factor = math.exp(-elapsed / TAU)
```

### 何时需要详细注释

- 复杂算法或公式
- 非显而易见的业务规则
- 临时解决方案 (需包含 TODO + issue 编号)
- 性能优化的权衡说明

## Design Principles

### 模块化设计

```python
# ❌ 功能混杂在一起
class UserService:
    def authenticate(self, username, password): ...
    def hash_password(self, password): ...
    def send_email(self, user, subject, body): ...

# ✅ 按职责拆分模块
class AuthService:          # 认证逻辑
    def authenticate(self, credentials: Credentials) -> AuthResult: ...

class PasswordService:      # 密码处理
    def hash(self, password: str) -> str: ...
```

**模块边界检查清单**：
- 每个模块文件 < 300 行（超过则考虑拆分）
- 每个类 < 10 个公开方法
- 模块间通过接口通信，不直接依赖实现

### 职责单一

| 层级 | 职责 | 禁止 |
|------|------|------|
| **Entity** | 业务规则、状态转换 | 数据库访问、外部调用 |
| **Service** | 用例编排、事务协调 | HTTP 处理、SQL 语句 |
| **Repository** | 数据持久化 | 业务逻辑、验证规则 |
| **Endpoint** | HTTP 转换、参数验证 | 业务逻辑、直接数据库访问 |

## SDK 优先原则

优先使用成熟 SDK，避免重复造轮子。

### 推荐 SDK

| 领域 | 推荐方案 | 替代 | 原因 |
|------|---------|------|------|
| **后台任务** | K8s CronJob + Watch API | Celery + Redis | 利用现有 EKS，无需额外组件 |
| **认证** | Authlib | python-jose 手写 | 完整 OAuth2/OIDC，支持 AWS IAM |
| **日志** | structlog | 标准 logging | 结构化 JSON，上下文绑定 |
| **监控** | OpenTelemetry | 厂商特定 SDK | CNCF 标准，可切换后端 |

### 后台任务实现指南

**定时任务 → Kubernetes CronJob**
- 训练卡住检测（每30分钟）
- 存储容量告警（每5分钟）
- 检查点迁移（每30分钟）

**事件驱动 → Kubernetes Watch API**
- HyperPod/Kueue 状态变化监控
- 抢占事件检测

### 实现前检查清单

1. 搜索 PyPI 是否有现成方案
2. 检查 FastAPI 生态集成 (awesome-fastapi)
3. AWS 功能优先用 boto3 官方 SDK
4. 复杂功能找专业库，简单功能用标准库

## Module Responsibility Matrix

| 模块 | 职责 | 核心实体 | 外部依赖 |
|------|------|---------|---------|
| **auth** | 用户认证、授权、RBAC | User, LoginAttempt | SSO Provider |
| **training** | 训练任务生命周期管理 | TrainingJob, Checkpoint | HyperPod, Kueue |
| **models** | 模型版本控制、审批 | Model, ModelVersion | Model Registry |
| **quotas** | 资源配额配置与管理 | ResourceQuota, ResourceLimitConfig | Kueue ClusterQueue |
| **spaces** | 在线开发环境管理 | Space | SageMaker Spaces |
| **audit** | 审计日志记录与查询 | AuditLog | - |

## 待解决问题

### 数据模型一致性问题

#### 问题1: resource_quotas 表与 Kueue 配额重复

| 项目 | 说明 |
|------|------|
| **现状** | 应用层存储 `max_gpu_count`, `max_cpu_cores`, `max_memory_gb` |
| **问题** | Kueue ClusterQueue 已管理这些配额值，存在数据不一致风险 |
| **待确认** | 应用层是"配置源"同步到 Kueue，还是只存业务元数据？ |

#### 问题2: development_spaces 表与 SageMaker Spaces 状态同步

| 项目 | 说明 |
|------|------|
| **现状** | 应用层缓存 `status`, `instance_type` 等字段 |
| **问题** | SageMaker Spaces API 已提供这些信息，需要同步策略 |
| **待确认** | 缓存更新机制（轮询/事件驱动） |

## Related Documentation

| 文档 | 位置 | 说明 |
|------|------|------|
| **核心架构规范** | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 模块依赖、通信方式、异常处理等 |
| **功能规范** | `specs/001-ai-training-platform/spec.md` | 术语标准、功能需求 |
| **数据模型** | `specs/001-ai-training-platform/data-model.md` | 数据库设计 |
| **架构合规测试** | `tests/unit/test_architecture_compliance.py` | 自动化验证 |
