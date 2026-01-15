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
```

## Architecture

项目采用 **Modular Monolith** 架构模式，结合 Clean Architecture 原则：

```
src/
├── modules/                           # 功能模块 (Feature Modules)
│   ├── auth/                          # 认证授权模块
│   │   ├── api/                       # HTTP 端点、Schema、依赖
│   │   ├── application/               # 业务服务
│   │   ├── domain/                    # 实体、值对象、仓库接口
│   │   └── infrastructure/            # ORM 模型、仓库实现
│   ├── training/                      # 训练任务模块
│   ├── models/                        # 模型管理模块
│   ├── quotas/                        # 资源配额模块
│   ├── datasets/                      # 数据集管理模块
│   ├── spaces/                        # 开发空间模块
│   ├── monitoring/                    # 监控告警模块
│   ├── billing/                       # 成本分析模块
│   └── audit/                         # 审计日志模块
│
├── shared/                            # 共享内核 (Shared Kernel)
│   ├── domain/                        # 基础实体、仓库接口、域事件
│   ├── infrastructure/                # 数据库、配置、安全
│   ├── api/                           # 中间件、异常处理、分页
│   └── utils/                         # 工具函数
│
├── main.py                            # 应用入口
└── router.py                          # 路由聚合
```

### 模块结构规范

每个功能模块遵循统一的内部结构（按实体分文件）：

```
modules/<module_name>/
├── __init__.py                        # 模块公开 API
├── api/
│   ├── __init__.py
│   ├── endpoints.py                   # REST 端点 (FastAPI Router)
│   ├── schemas/                       # Pydantic 请求/响应模型
│   │   ├── __init__.py               # 导出所有 Schema
│   │   ├── requests.py               # 请求模型
│   │   └── responses.py              # 响应模型
│   └── dependencies.py                # 模块专属依赖注入
├── application/
│   ├── __init__.py
│   ├── services/                      # 业务用例实现
│   │   ├── __init__.py
│   │   ├── <entity>_service.py       # 每个聚合根一个服务
│   │   └── ...
│   └── interfaces.py                  # 端口定义 (可选)
├── domain/
│   ├── __init__.py
│   ├── entities/                      # 业务实体
│   │   ├── __init__.py               # 导出所有实体
│   │   ├── <entity>.py               # 每个实体一个文件
│   │   └── ...
│   ├── value_objects/                 # 值对象
│   │   ├── __init__.py
│   │   ├── <value_object>.py
│   │   └── ...
│   ├── repositories/                  # 仓库接口
│   │   ├── __init__.py
│   │   ├── <entity>_repository.py    # 每个聚合根一个仓库接口
│   │   └── ...
│   └── exceptions.py                  # 模块专属异常
└── infrastructure/
    ├── __init__.py
    ├── models/                        # SQLAlchemy ORM 模型
    │   ├── __init__.py
    │   ├── <entity>_model.py
    │   └── ...
    └── repositories/                  # 仓库实现
        ├── __init__.py
        ├── <entity>_repository_impl.py
        └── ...
```

### 示例：training 模块

```
modules/training/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── endpoints.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py               # CreateJobRequest, UpdateJobRequest
│   │   └── responses.py              # JobResponse, JobListResponse
│   └── dependencies.py
├── application/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── training_job_service.py
│   │   ├── checkpoint_service.py
│   │   └── hyperpod_service.py
│   └── interfaces.py                  # IHyperPodClient
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py               # from .training_job import TrainingJob
│   │   ├── training_job.py
│   │   └── checkpoint.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── job_status.py
│   │   ├── training_config.py
│   │   └── training_metrics.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── training_job_repository.py
│   │   └── checkpoint_repository.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    ├── models/
    │   ├── __init__.py
    │   ├── training_job_model.py
    │   └── checkpoint_model.py
    ├── repositories/
    │   ├── __init__.py
    │   ├── training_job_repository_impl.py
    │   └── checkpoint_repository_impl.py
    └── hyperpod_client.py             # IHyperPodClient 实现
```

### 文件命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 实体 | `<entity>.py` | `training_job.py`, `user.py` |
| 值对象 | `<value_object>.py` | `job_status.py`, `training_metrics.py` |
| 仓库接口 | `<entity>_repository.py` | `training_job_repository.py` |
| 仓库实现 | `<entity>_repository_impl.py` | `training_job_repository_impl.py` |
| ORM 模型 | `<entity>_model.py` | `training_job_model.py` |
| 服务 | `<entity>_service.py` | `training_job_service.py` |

### `__init__.py` 导出规范

每个目录的 `__init__.py` 应导出该目录下的所有公开 API：

```python
# modules/training/domain/entities/__init__.py
from .training_job import TrainingJob
from .checkpoint import Checkpoint

__all__ = ["TrainingJob", "Checkpoint"]
```

这样可以保持导入路径简洁：

```python
# ✅ 推荐
from modules.training.domain.entities import TrainingJob

# ❌ 避免
from modules.training.domain.entities.training_job import TrainingJob
```

### 模块依赖规则

```
┌─────────────────────────────────────────────────────┐
│                    modules/                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │  auth   │  │training │  │ models  │  ...         │
│  └────┬────┘  └────┬────┘  └────┬────┘              │
│       │            │            │                    │
│       └────────────┼────────────┘                    │
│                    ↓                                 │
│              ┌──────────┐                            │
│              │  shared/ │                            │
│              └──────────┘                            │
└─────────────────────────────────────────────────────┘

规则:
1. 模块只能依赖 shared/，禁止横向依赖
2. 模块间通信通过 shared/domain/events.py 中的域事件
3. shared/ 不依赖任何模块
```

### 模块间通信

**禁止**: 模块 A 直接调用模块 B 的服务

```python
# ❌ 禁止：training 模块直接调用 auth 模块
from modules.auth.application.services import AuthService

class TrainingJobService:
    def __init__(self, auth_service: AuthService):  # 禁止
        ...
```

**推荐**: 通过域事件解耦

```python
# ✅ 推荐：通过事件解耦
# shared/domain/events.py
@dataclass
class TrainingJobCompletedEvent:
    job_id: UUID
    user_id: UUID
    completed_at: datetime

# modules/training/application/services.py
class TrainingJobService:
    def complete_job(self, job_id: UUID):
        job.complete()
        self._event_bus.publish(TrainingJobCompletedEvent(...))

# modules/billing/application/services.py
class BillingService:
    @event_handler(TrainingJobCompletedEvent)
    async def on_job_completed(self, event: TrainingJobCompletedEvent):
        await self._calculate_cost(event.job_id)
```

### 路由聚合

```python
# src/router.py
from fastapi import APIRouter
from modules.auth.api.endpoints import router as auth_router
from modules.training.api.endpoints import router as training_router
from modules.models.api.endpoints import router as models_router
from modules.quotas.api.endpoints import router as quotas_router
from modules.datasets.api.endpoints import router as datasets_router
from modules.spaces.api.endpoints import router as spaces_router
from modules.audit.api.endpoints import router as audit_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(training_router, prefix="/training-jobs", tags=["训练任务"])
api_router.include_router(models_router, prefix="/models", tags=["模型"])
api_router.include_router(quotas_router, prefix="/resource-quotas", tags=["资源配额"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["数据集"])
api_router.include_router(spaces_router, prefix="/spaces", tags=["开发空间"])
api_router.include_router(audit_router, prefix="/audit-logs", tags=["审计日志"])
```

## Key Interfaces

共享内核中的关键接口：

- `IRepository<T>`: 通用仓库接口 (`shared/domain/base_repository.py`)
- `IEventBus`: 域事件发布接口 (`shared/domain/events.py`)
- `IHyperPodClient`: SageMaker HyperPod 操作 (`modules/training/application/interfaces.py`)
- `IStorageService`: S3/FSx 存储操作 (`shared/infrastructure/storage.py`)

## Environment Variables

通过 `.env` 文件或环境变量配置 (参见 `src/infrastructure/config/settings.py`):

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

## Code Style

### Docstring 规范

**原则**: 类型签名即文档，注释解释"为什么"而非"做什么"。

| 场景 | 规则 | 示例行数 |
|------|------|---------|
| Module docstring | 单行，说明模块职责 | 1 行 |
| Class docstring | 1-2 行，不重复模块信息 | 1-2 行 |
| Method docstring | 1 行 + 类型签名 | 1 行 |
| Args/Returns | 仅当类型签名不够清晰时 | 按需 |

**示例对比**:

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

遵循以下核心设计原则，确保代码的可维护性和可扩展性。

### 模块化设计 (Modular Design)

```python
# ❌ 功能混杂在一起
class UserService:
    def authenticate(self, username, password): ...
    def hash_password(self, password): ...
    def send_email(self, user, subject, body): ...
    def generate_report(self, user_id): ...

# ✅ 按职责拆分模块
class AuthService:          # 认证逻辑
    def authenticate(self, credentials: Credentials) -> AuthResult: ...

class PasswordService:      # 密码处理
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, hash: str) -> bool: ...
```

**模块边界检查清单**：
- 每个模块文件 < 300 行（超过则考虑拆分）
- 每个类 < 10 个公开方法
- 模块间通过接口通信，不直接依赖实现

### 简明逻辑 (Simple Logic)
**简明逻辑检查清单**：
- 函数圈复杂度 ≤ 10
- 嵌套层级 ≤ 3
- 每个函数只做一件事

### 清晰接口 (Clear Interfaces)

```python
# ❌ 参数模糊、返回值不明确
def create_job(data, flags, options=None):
    ...  # 调用者不知道传什么、返回什么

# ✅ 类型明确、契约清晰
async def create_job(
    request: CreateJobRequest,
    user_id: UUID,
) -> TrainingJob:
    """创建训练任务。

    Raises:
        ResourceQuotaExceeded: 配额不足
        ValidationError: 请求参数无效
    """
```

**接口设计检查清单**：
- 所有公开方法有完整类型标注
- 可能抛出的异常在 docstring 中声明
- 避免 `dict`/`Any` 作为参数或返回值类型

### 职责单一 (Single Responsibility)

| 层级 | 职责 | 禁止 |
|------|------|------|
| **Entity** | 业务规则、状态转换 | 数据库访问、外部调用 |
| **Service** | 用例编排、事务协调 | HTTP 处理、SQL 语句 |
| **Repository** | 数据持久化 | 业务逻辑、验证规则 |
| **Endpoint** | HTTP 转换、参数验证 | 业务逻辑、直接数据库访问 |

```python
# ❌ 职责混乱 - Service 包含 HTTP 逻辑
class TrainingJobService:
    async def create(self, request: Request):  # 不应接收 HTTP Request
        data = await request.json()            # 不应解析 HTTP
        job = TrainingJob(**data)
        await self.db.execute(...)             # 不应直接操作数据库

# ✅ 职责清晰
class TrainingJobService:
    def __init__(self, repository: ITrainingJobRepository):
        self._repository = repository

    async def create(self, command: CreateJobCommand) -> TrainingJob:
        job = TrainingJob.create(command)      # 实体负责创建逻辑
        return await self._repository.save(job) # 仓库负责持久化
```

## Exception Handling

本项目采用 **全局异常处理器** 模式，将异常到 HTTP 响应的映射集中管理。

### 架构概述

```
┌─────────────────────────────────────────────────┐
│ API 端点 - 无需 try-except                       │
│ (异常自动传播到全局处理器)                        │
├─────────────────────────────────────────────────┤
│ 全局异常处理器 (src/api/exception_handlers.py)  │
│ - domain_exception_handler: DomainError → HTTP  │
│ - security_exception_handler: SecurityError → HTTP │
└─────────────────────────────────────────────────┘
```

### 异常映射表

**Domain 异常** (`src/domain/exceptions/`):

| 异常类型 | HTTP 状态码 | 场景 |
|---------|------------|------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换无效 |
| `ValidationError` | 422 | 业务验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额超限 |

**Security 异常** (`src/core/security/exceptions.py`):

| 异常类型 | HTTP 状态码 | 场景 |
|---------|------------|------|
| `AuthenticationError` | 401 | 认证失败 |
| `InvalidCredentialsError` | 401 | 凭证无效 |
| `TokenExpiredError` | 401 | Token 过期 |
| `UserNotFoundError` | 404 | 用户不存在 |
| `AccountLockedError` | 423 | 账户锁定 |
| `InsufficientPermissionsError` | 403 | 权限不足 |
| `SSODegradedModeError` | 503 | SSO 服务降级 |

### 端点代码规范

```python
# ❌ 禁止：手动转换异常
@router.post("")
async def create_job(data: CreateRequest, service: Service = Depends(...)):
    try:
        job = await service.create_job(data)
        return job
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))

# ✅ 正确：让异常自动传播
@router.post("")
async def create_job(data: CreateRequest, service: Service = Depends(...)):
    job = await service.create_job(data)
    return job
```

**例外情况**：仅在需要自定义响应格式（如 SSO 降级消息）时保留 try-except。

### 新增异常指南

1. **定义异常类**：
   - Domain 异常 → `src/domain/exceptions/__init__.py`
   - Security 异常 → `src/core/security/exceptions.py`

2. **添加映射**：在 `src/api/exception_handlers.py` 的映射表中添加一行：
   ```python
   DOMAIN_EXCEPTION_MAP: dict[type[DomainError], int] = {
       # ... 现有映射
       NewCustomError: status.HTTP_4XX_XXX,  # 新增
   }
   ```

3. **测试**：在 `tests/unit/api/test_exception_handlers.py` 添加映射测试。

## Test-Driven Development (TDD)

本项目践行 TDD 实践，遵循 **Red-Green-Refactor** 循环。

### 测试诚信原则

**🚫 切勿为了让测试用例通过而制造虚假的测试用例通过**

禁止行为：
- 硬编码预期值以匹配错误的实现
- 删除或跳过失败的测试而不修复代码
- 修改测试断言使其匹配错误行为
- 使用过度宽松的断言掩盖问题

正确做法：
- 测试失败时，修复代码而非测试
- 如果测试本身有问题，先理解后再修改
- 保持测试的严格性和准确性

### TDD 工作流

```
1. 🔴 Red: 先写失败的测试
   pytest tests/unit/domain/test_training_job.py -v

2. 🟢 Green: 编写最少代码使测试通过
   pytest tests/unit/domain/test_training_job.py -v

3. 🔄 Refactor: 重构代码，保持测试通过
   pytest tests/unit/ -v && black src/ && ruff check src/
```

### 测试分层策略

| 层级 | 位置 | 测试对象 | Mock 策略 |
|------|------|---------|----------|
| **Unit** | `tests/unit/domain/` | 实体、值对象、域逻辑 | 无依赖，纯函数 |
| **Unit** | `tests/unit/application/` | 应用服务 | Mock 仓库接口 |
| **Integration** | `tests/integration/api/` | API 端点 | Mock 外部服务 |
| **Integration** | `tests/integration/persistence/` | 仓库实现 | 真实数据库 |
| **E2E** | `tests/e2e/` | 完整流程 | 最小化 Mock |

### TDD 命令速查

```bash
# 监视模式 - 文件变更自动运行测试
pytest tests/unit/ --watch              # 需安装 pytest-watch

# 只运行上次失败的测试
pytest --lf

# 失败时立即停止
pytest -x

# 显示详细输出
pytest -v --tb=short

# 运行标记的测试
pytest -m "unit and not slow"
```

### 测试命名规范

```python
# 文件命名: test_<module>.py
tests/unit/domain/test_training_job.py

# 测试函数命名: test_<method>_<scenario>_<expected>
def test_submit_with_invalid_config_raises_validation_error():
    ...

def test_cancel_when_running_transitions_to_cancelled():
    ...
```

### Fixture 组织

```python
# tests/conftest.py - 全局共享
@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """异步 HTTP 测试客户端。"""
    ...

# tests/unit/conftest.py - 单元测试专用
@pytest.fixture
def mock_job_repository() -> Mock:
    """Mock 训练作业仓库。"""
    ...

# tests/integration/conftest.py - 集成测试专用
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """真实数据库会话（事务回滚）。"""
    ...
```

### 编写新功能的 TDD 流程

1. **Domain 层优先**: 先为实体/值对象写测试
2. **Application 层次之**: 测试业务用例（Mock 仓库）
3. **API 层最后**: 测试 HTTP 接口（Mock 服务）
4. **Integration 补充**: 验证真实数据库交互

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

基于 spec.md 需求，后台任务按触发方式分类：

**定时任务 → Kubernetes CronJob**
```yaml
# 示例：训练卡住检测（FR-022）
apiVersion: batch/v1
kind: CronJob
metadata:
  name: stall-detection
spec:
  schedule: "*/30 * * * *"  # 每30分钟
```
- 训练卡住检测（每30分钟）
- 存储容量告警（每5分钟）
- 检查点迁移（每30分钟）

**事件驱动 → Kubernetes Watch API**
- HyperPod/Kueue 状态变化监控
- 抢占事件检测
- 使用 `kubernetes-client` 的 Watch 接口

**同步检查 → API 请求时处理**
- 预算预警（在资源使用 API 中同步检查）

### 实现前检查清单

1. 搜索 PyPI 是否有现成方案
2. 检查 FastAPI 生态集成 (awesome-fastapi)
3. AWS 功能优先用 boto3 官方 SDK
4. 复杂功能找专业库，简单功能用标准库

## 待解决问题

以下问题需要后续统一检查处理。

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

### 待实现表（根据 spec.md）

| 表名 | 所属模块 | 用途 | 备注 |
|------|---------|------|------|
| `training_jobs` | training | 训练任务业务元数据 | HyperPod 管理运行时状态 |
| `datasets` | datasets | 数据集版本和权限管理 | - |
| `checkpoints` | training | 检查点元数据索引 | S3/FSx 存储实际数据 |
| `models` | models | 模型元数据 | 可选，评估 Model Registry 能力是否足够 |

## Module Responsibility Matrix

| 模块 | 职责 | 核心实体 | 外部依赖 |
|------|------|---------|---------|
| **auth** | 用户认证、授权、RBAC | User, LoginAttempt, PasswordHistory | SSO Provider |
| **training** | 训练任务生命周期管理 | TrainingJob, Checkpoint | HyperPod, Kueue |
| **models** | 模型版本控制、审批 | Model, ModelVersion | Model Registry |
| **quotas** | 资源配额配置与管理 | ResourceQuota, ResourceLimitConfig | Kueue ClusterQueue |
| **datasets** | 数据集上传、版本控制 | Dataset, DatasetVersion | S3, FSx |
| **spaces** | 在线开发环境管理 | Space | SageMaker Spaces |
| **monitoring** | 集群监控、告警 | Alert, Metric | CloudWatch, Prometheus |
| **billing** | 成本分析、预算管理 | CostRecord, Budget | Cost Explorer |
| **audit** | 审计日志记录与查询 | AuditLog | - |

## Migration Notes

### 从 Layered Architecture 迁移

当前代码库正在从按层划分迁移到 Modular Monolith。迁移期间：

1. **新功能**: 直接在 `modules/` 下对应模块中开发
2. **现有代码**: 按计划逐步迁移到对应模块
3. **共享代码**: 提取到 `shared/` 中

### 迁移检查清单

迁移单个模块时的检查项：

- [ ] 创建模块目录结构 (`api/`, `application/`, `domain/`, `infrastructure/`)
- [ ] 迁移端点到 `api/endpoints.py`
- [ ] 迁移 Schema 到 `api/schemas.py`
- [ ] 迁移服务到 `application/services.py`
- [ ] 迁移实体到 `domain/entities.py`
- [ ] 迁移仓库接口到 `domain/repositories.py`
- [ ] 迁移 ORM 模型到 `infrastructure/models.py`
- [ ] 迁移仓库实现到 `infrastructure/repositories.py`
- [ ] 更新导入路径
- [ ] 运行单元测试和集成测试
- [ ] 更新 `router.py` 路由注册
