# 后端架构规范 (Backend Architecture Standards)

> **职责**: 后端架构规范的**单一真实源 (SSOT)**，定义分层规则、模块隔离和 DDD 模式。
>
> **架构模式**: DDD + Modular Monolith + Clean Architecture

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 0.1 依赖合法性速查矩阵

> **模块间通信**: 优先 EventBus (异步解耦)，备选 shared/interfaces (同步调用)，禁止直接依赖其他模块实现。

| 从 ↓ 导入 → | `shared/*` | `auth.api.dependencies` | 其他模块 Domain | 其他模块 Service | 其他模块 ORM Model |
|-------------|:----------:|:-----------------------:|:--------------:|:---------------:|:-----------------:|
| **Domain** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Application** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Infrastructure** | ✅ | ❌ | ❌ | ❌ | ⚠️ 仅外键 |
| **API** | ✅ | ✅ | ❌ | ❌ | ❌ |

> **Composition Root 例外**: API 层 `dependencies.py` 作为依赖组装点，允许导入其他模块 Infrastructure 实现来注入跨模块依赖。Service 层本身仍通过 shared 接口依赖。

### 0.2 数据模型选择速查

| 层级 | 组件类型 | 推荐方案 | 理由 |
|------|---------|---------|------|
| **Domain** | Entity | PydanticEntity | 业务规则验证、状态可变 |
| **Domain** | Value Object | dataclass(frozen) | 不可变、相等性基于值 |
| **Application** | DTO | dataclass | 内部传输、已验证数据 |
| **Infrastructure** | ORM Model | SQLAlchemy | 持久化专用 |
| **API** | Request/Response | Pydantic | 外部输入验证、FastAPI 集成 |

**决策流程**:
```
数据来自外部？ ──是──► Pydantic
      │
     否
      ↓
需要业务验证？ ──是──► PydanticEntity
      │
     否
      ↓
需要不可变？ ──是──► dataclass(frozen=True)
      │
     否
      ↓
dataclass
```

---

## 1. 核心原则与分层规则

### 架构核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **模块自治** | 每个模块拥有独立的领域模型和业务逻辑 | 模块内 CRUD 完全独立 |
| **显式依赖** | 模块间依赖必须显式声明 | 通过接口定义依赖 |
| **最小知识** | 模块只暴露必要的接口 | 内部实现对外不可见 |
| **单向依赖** | 禁止循环依赖 | 使用事件解耦 |
| **高内聚低耦合** | 相关功能聚合在同一模块 | 按业务领域划分 |

### 模块内部四层结构

```
API 层 (endpoints, schemas)
    ↓
Application 层 (services, dto, interfaces)
    ↓
Domain 层 (entities, value_objects, repositories)
    ↑
Infrastructure 层 (persistence, external adapters)
```

### 依赖规则

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| **Domain** | Pydantic (数据验证), shared/domain | FastAPI, SQLAlchemy, boto3 |
| **Application** | Domain | FastAPI, SQLAlchemy, boto3 |
| **Infrastructure** | Domain, Application | - |
| **API** | Application, Domain (类型) | Infrastructure (通过 DI) |

---

## 2. 模块隔离黄金法则

| 规则 | 说明 | 强制性 |
|------|------|--------|
| **R1** | 模块的 Domain 层**绝对不能**导入任何其他模块代码 | 🔴 强制 |
| **R2** | 模块的 Application 层只能依赖**接口**，不能依赖具体实现 | 🔴 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享接口** | 🔴 强制 |
| **R4** | `auth` 模块的认证依赖是**唯一例外**，可被其他模块 API 层导入 | 🟡 例外 |
| **R5** | Domain Events 作为模块公开契约，其他模块 Application 层可导入用于事件订阅 | 🟡 例外 |

### 允许的共享内核依赖

```python
# ✅ 所有模块可导入 shared/
from src.shared.domain import PydanticEntity, IRepository, DomainError, DomainEvent, event_bus
from src.shared.infrastructure import get_db, get_settings, PydanticRepository
from src.shared.api import domain_exception_handler
```

### 禁止的依赖

```python
# ❌ 禁止：跨模块直接导入
from src.modules.training.application.services import TrainingJobService       # ❌
from src.modules.quotas.domain.entities import ResourceQuota                   # ❌
from src.modules.quotas.infrastructure.repositories import QuotaRepoImpl       # ❌
```

**Infrastructure 跨模块例外**:
- ORM 模型文件 (`*_model.py`): 允许导入其他模块 ORM Model 定义外键关系
- 跨模块查询实现 (`*_query_impl.py`): 允许导入其他模块 ORM Model 用于聚合查询

---

## 3. 模块间通信

### 集成模式决策

| 场景 | 推荐模式 | 实现方式 |
|------|---------|---------|
| 实时同步调用 (配额检查) | Open Host Service | `shared/domain/interfaces/` |
| 异步通知 (任务完成) | Published Language | Domain Events + EventBus |
| 复杂外部系统 (HyperPod) | Anti-Corruption Layer | Infrastructure 适配器 |

### 事件驱动通信（推荐）

```python
# 定义 → 发布 → 订阅
@dataclass
class TrainingJobCompletedEvent(DomainEvent):
    job_id: int
    owner_id: int

# 发布: await event_bus.publish_async(TrainingJobCompletedEvent(...))
# 订阅: @event_handler(TrainingJobCompletedEvent)
```

### 事件可靠性要求

| 要求 | 说明 | 实现方式 |
|------|------|---------|
| **幂等性** | 处理器必须能安全重复执行 | 通过 `event_id` 去重 |
| **重试策略** | 失败时指数退避重试 | `max_retries=3`, 退避 `1s → 2s → 4s` |
| **Outbox Pattern** | 事件与业务操作原子性提交 | 事件先写入 outbox 表，后台轮询发布 |
| **顺序保证** | 同一聚合根的事件需有序处理 | 按 `aggregate_id` 分区 |

### 接口位置区分

- `shared/domain/interfaces/`: **跨模块能力接口**（如 `IQuotaChecker`）
- `modules/{module}/application/interfaces/`: **模块内外部服务抽象**（如 `IS3Client`）

---

## 4. DDD 战术模式

### Entity 实体

继承 `PydanticEntity`，自动获得 `id`, `created_at`, `updated_at`。

**规范**: 配置 `ConfigDict(validate_assignment=True)` | 状态转换在 Entity 内部（调用 `self.touch()` 更新时间戳） | 禁止依赖外部服务 | 只抛 Domain 异常

### Value Object 值对象

使用 `@dataclass(frozen=True)` 确保不可变，相等性基于值。

### Repository 仓库

接口在 Domain 层，实现在 Infrastructure 层。推荐使用 `PydanticRepository`，内置 CRUD，通过 `_updatable_fields` 白名单控制可更新字段。

---

## 5. 异常处理

使用 `@problem` 装饰器 + `@dataclass` 简化异常定义：

```python
from src.shared.domain.problem import problem, Problem

# 定义异常 - 每个仅需 5 行
@problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
@dataclass
class TrainingJobNotFoundError(Problem):
    job_id: str

# 使用: raise TrainingJobNotFoundError(job_id="job-123")
# 自动生成: message, http_status, error_code, get_details()
```

### HTTP 状态码映射

异常由 `shared/api/exception_handlers.py` 自动映射：

| 异常类型 | HTTP 状态码 | 场景 |
|---------|-------------|------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换非法 |
| `ValidationError` | 422 | 参数验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额不足 |

> 详细实现参见 `.claude/skills/decorator-exception/SKILL.md`

---

## 6. 依赖注入

```
Layer 1: Database Session (get_db)
    → Layer 2: Repository (get_xxx_repository)
    → Layer 3: External Client (get_xxx_client) - 推荐 @lru_cache Singleton
    → Layer 4: Application Service (get_xxx_service)
    → Layer 5: Permission Check (require_xxx)
```

### 标准依赖函数模板

```python
# modules/{name}/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db
from src.modules.{name}.domain.repositories import I{Entity}Repository
from src.modules.{name}.infrastructure.repositories import {Entity}RepositoryImpl
from src.modules.{name}.application.services import {Entity}Service

# Layer 2: Repository
async def get_{entity}_repository(
    session: AsyncSession = Depends(get_db),
) -> I{Entity}Repository:
    return {Entity}RepositoryImpl(session)

# Layer 4: Service
async def get_{entity}_service(
    repository: I{Entity}Repository = Depends(get_{entity}_repository),
) -> {Entity}Service:
    return {Entity}Service(repository=repository)
```

### 跨模块依赖注入

跨模块依赖在**消费方 API 层** `dependencies.py` 中组装，Service 只依赖 shared 接口:

```python
# training/api/dependencies.py — 注入 quotas 模块的 IQuotaChecker
from src.modules.quotas.infrastructure import QuotaCheckerImpl, ResourceQuotaRepository
from src.shared.domain.interfaces import IQuotaChecker

async def get_quota_checker(session = Depends(get_db)) -> IQuotaChecker:
    return QuotaCheckerImpl(ResourceQuotaRepository(session))
```

**规则**: Service 层通过接口依赖，API 层 `dependencies.py` 负责实例化具体实现。

---

## 7. 模块结构模板

```
modules/{module}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── endpoints/          # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   └── schemas/            # Pydantic 请求/响应模型
├── application/
│   ├── dto/                # 数据传输对象
│   ├── interfaces/         # 模块内外部服务抽象
│   └── services/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── repositories/       # 仓库接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── models/             # ORM 模型
    ├── repositories/       # 仓库实现
    └── {external}/         # 外部服务客户端
```

导出: `router`, Service, Entity, Domain Events | 禁止导出: ORM Model, RepositoryImpl, 外部客户端实现

### 文件命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 实体 | `{entity}.py` | `training_job.py` |
| 仓库接口 | `{entity}_repository.py` | `training_job_repository.py` |
| 仓库实现 | `{entity}_repository_impl.py` | `training_job_repository_impl.py` |
| ORM 模型 | `{entity}_model.py` | `training_job_model.py` |
| 服务 | `{entity}_service.py` | `training_job_service.py` |

---

## 8. 架构合规测试

> **测试文件**: `tests/architecture/test_architecture_compliance.py`

```bash
pytest tests/architecture -v
```

**Clean Architecture 层级测试**:

| 测试类 | 验证规则 |
|--------|---------|
| `TestApplicationLayerDoesNotImportInfrastructure` | Application 不导入 Infrastructure |
| `TestDomainLayerIndependence` | Domain 不依赖 Infrastructure/API |
| `TestApiLayerDoesNotImportInfrastructureModels` | API 不直接使用 ORM |
| `TestDomainExceptionUsage` | Entity 用域异常，非 ValueError |

**Modular Monolith 模块隔离测试**:

| 测试类 | 验证规则 |
|--------|---------|
| `TestModuleDomainLayerIsolation` | R1: Domain 零跨模块导入 |
| `TestModuleApplicationLayerDependencies` | R2/R3: Application 跨模块隔离 |
| `TestModuleApiLayerAuthDependency` | R4: Auth 依赖例外验证 |
| `TestModuleInfrastructureLayerIsolation` | Infrastructure 跨模块隔离 |
| `TestModulePublicApiExports` | `__init__.py` 定义 `__all__` |
