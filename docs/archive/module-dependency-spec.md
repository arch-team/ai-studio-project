# Modular Monolith 模块间依赖规范

> **版本**: 1.0
> **更新日期**: 2025-01-16
> **适用范围**: AI 训练平台后端 (`backend/src/`)

本规范定义模块间的依赖关系、通信方式和架构约束，确保系统的可维护性和可扩展性。

---

## 1. 核心原则

### 1.1 依赖方向规则

```
┌─────────────────────────────────────────────────────────┐
│                    模块内部分层                          │
│                                                         │
│   API 层 ──────────► Application 层 ──────► Domain 层   │
│                           ▲                             │
│                           │                             │
│                    Infrastructure 层                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                    跨模块依赖                            │
│                                                         │
│   modules/A  ───X───►  modules/B   (禁止横向依赖)       │
│       │                    │                            │
│       └────────┬───────────┘                            │
│                ▼                                        │
│           shared/  (唯一允许的共享依赖)                  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 黄金法则

| 规则 | 说明 | 强制级别 |
|------|------|----------|
| **R1** | 模块的 Domain 层**绝对不能**导入任何其他模块代码 | 强制 |
| **R2** | 模块的 Application 层只能依赖**接口**，不能依赖具体实现 | 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享接口** | 强制 |
| **R4** | `auth` 模块的认证依赖是**唯一例外**，可被其他模块 API 层导入 | 例外 |

---

## 2. 依赖分类与规则

### 2.1 允许的依赖

#### 2.1.1 共享内核依赖

所有模块可以导入 `shared/` 下的内容：

```python
# Domain 层共享
from src.shared.domain import (
    BaseEntity,
    IRepository,
    DomainError,
    EntityNotFoundError,
    ValidationError,
    DuplicateEntityError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    DomainEvent,
    event_bus,
    event_handler,
)

# Infrastructure 层共享
from src.shared.infrastructure import get_db, get_settings
from src.shared.infrastructure.security import hash_password, verify_password

# API 层共享
from src.shared.api import domain_exception_handler
from src.shared.api.schemas import EntitySchema, PaginatedResponse

# 工具共享
from src.shared.utils import utc_now, paginate
```

#### 2.1.2 Auth 模块特殊依赖（唯一例外）

其他模块的 **API 层** 可以导入 auth 的认证依赖：

```python
# 仅允许在 API 层导入
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
    require_engineer,
    require_viewer,
)
from src.modules.auth.api.current_user import CurrentUser
```

### 2.2 禁止的依赖

```python
# 禁止：直接导入其他模块的服务
from src.modules.training.application.services import TrainingJobService

# 禁止：直接导入其他模块的实体
from src.modules.quotas.domain.entities import ResourceQuota

# 禁止：直接导入其他模块的仓库实现
from src.modules.models.infrastructure.repositories import ModelRepositoryImpl

# 禁止：Domain 层导入任何外部模块
# modules/training/domain/entities/training_job.py
from src.modules.quotas.domain import QuotaError  # 绝对禁止！
```

---

## 3. 模块间通信方式

### 3.1 事件驱动通信（推荐）

#### 定义域事件

```python
# modules/training/domain/events.py
from dataclasses import dataclass
from src.shared.domain import DomainEvent

@dataclass
class TrainingJobCompletedEvent(DomainEvent):
    """训练任务完成事件"""
    job_id: int
    owner_id: int
    duration_seconds: int
    final_metrics: dict

@dataclass
class TrainingJobFailedEvent(DomainEvent):
    """训练任务失败事件"""
    job_id: int
    owner_id: int
    error_message: str
```

#### 发布事件

```python
# modules/training/application/services/training_job_service.py
from src.shared.domain import event_bus

class TrainingJobService:
    async def complete_job(self, job_id: int) -> TrainingJob:
        job = await self._repository.get_by_id(job_id)
        job.mark_completed()

        # 发布事件，解耦其他模块
        await event_bus.publish_async(
            TrainingJobCompletedEvent(
                job_id=job.id,
                owner_id=job.owner_id,
                duration_seconds=job.duration,
                final_metrics=job.metrics,
            )
        )

        return await self._repository.update(job)
```

#### 订阅事件

```python
# modules/billing/application/services/billing_service.py
from src.shared.domain import event_handler
from src.modules.training.domain.events import TrainingJobCompletedEvent

class BillingService:
    @event_handler(TrainingJobCompletedEvent)
    async def on_training_completed(self, event: TrainingJobCompletedEvent):
        """监听训练完成，计算成本"""
        await self._calculate_training_cost(
            job_id=event.job_id,
            duration=event.duration_seconds,
        )
```

### 3.2 共享接口通信（必要时）

当需要同步调用时，通过 `shared/` 定义接口：

```python
# shared/domain/interfaces/quota_checker.py
from abc import ABC, abstractmethod

class IQuotaChecker(ABC):
    """配额检查接口 - 供其他模块使用"""

    @abstractmethod
    async def check_quota(self, user_id: int, resource_type: str, amount: int) -> bool:
        """检查用户配额是否足够"""
        pass

    @abstractmethod
    async def consume_quota(self, user_id: int, resource_type: str, amount: int) -> None:
        """消费配额"""
        pass
```

```python
# modules/quotas/infrastructure/quota_checker_impl.py
from src.shared.domain.interfaces import IQuotaChecker

class QuotaCheckerImpl(IQuotaChecker):
    async def check_quota(self, user_id: int, resource_type: str, amount: int) -> bool:
        # 具体实现
        pass
```

```python
# modules/training/application/services/training_job_service.py
from src.shared.domain.interfaces import IQuotaChecker

class TrainingJobService:
    def __init__(
        self,
        repository: ITrainingJobRepository,
        quota_checker: IQuotaChecker,  # 依赖接口，不依赖实现
    ):
        self._repository = repository
        self._quota_checker = quota_checker
```

### 3.3 通信方式选择指南

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 状态变更通知 | EventBus | 发布者不关心订阅者，完全解耦 |
| 需要返回值 | 共享接口 | 同步调用，获取结果 |
| 跨模块查询 | 共享接口 | 数据聚合，需要实时数据 |
| 审计日志 | EventBus | 审计模块订阅所有关键事件 |
| 配额检查 | 共享接口 | 同步校验，阻塞操作 |

---

## 4. 依赖注入规范

### 4.1 依赖注入层级

```
Layer 1: Database Session (get_db)
    ↓
Layer 2: Repository (get_xxx_repository)
    ↓
Layer 3: External Client (get_xxx_client) - 推荐 Singleton
    ↓
Layer 4: Application Service (get_xxx_service)
    ↓
Layer 5: Permission Check (require_xxx)
```

### 4.2 标准依赖函数模板

```python
# modules/{name}/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db, get_settings
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

### 4.3 外部客户端 Singleton 模式

```python
# modules/training/infrastructure/hyperpod/client.py
from functools import lru_cache

@lru_cache(maxsize=1)
def get_hyperpod_client() -> HyperPodClient:
    """单例模式，避免重复创建 AWS 客户端"""
    settings = get_settings()
    return HyperPodClient(region=settings.aws_region)
```

---

## 5. 异常处理规范

### 5.1 模块异常继承体系

```python
# modules/{name}/domain/exceptions.py
from src.shared.domain import (
    DomainError,
    EntityNotFoundError,
    ValidationError,
    DuplicateEntityError,
)

class {Module}Error(DomainError):
    """模块基础异常"""
    pass

class {Entity}NotFoundError(EntityNotFoundError):
    """实体未找到 - 自动映射到 HTTP 404"""
    def __init__(self, entity_id: int):
        super().__init__(entity_type="{Entity}", entity_id=str(entity_id))

class Invalid{Entity}StateError(DomainError):
    """无效状态 - 自动映射到 HTTP 409"""
    pass
```

### 5.2 异常到 HTTP 状态码映射

| 异常类型 | HTTP 状态码 | 使用场景 |
|---------|-------------|---------|
| `EntityNotFoundError` | 404 | 实体不存在 |
| `DuplicateEntityError` | 409 | 唯一约束冲突 |
| `InvalidStateTransitionError` | 409 | 状态机转换非法 |
| `ValidationError` | 422 | 业务规则校验失败 |
| `ResourceQuotaExceededError` | 429 | 配额超限 |

---

## 6. 模块公开 API 规范

### 6.1 `__init__.py` 导出规则

每个模块必须在 `__init__.py` 明确定义公开 API：

```python
# modules/training/__init__.py
from .api.endpoints import router
from .api.dependencies import get_training_job_service
from .application.services import TrainingJobService
from .domain.entities import TrainingJob, Checkpoint
from .domain.events import TrainingJobCompletedEvent, TrainingJobFailedEvent

__all__ = [
    # API
    "router",
    "get_training_job_service",
    # Application
    "TrainingJobService",
    # Domain
    "TrainingJob",
    "Checkpoint",
    # Events (供其他模块订阅)
    "TrainingJobCompletedEvent",
    "TrainingJobFailedEvent",
]
```

### 6.2 禁止导出内容

以下内容**不应**出现在 `__all__` 中：

- ORM 模型 (`*Model`)
- 仓库实现 (`*RepositoryImpl`)
- 外部客户端实现 (`*Client`)
- 内部工具函数

---

## 7. 核心域事件清单

### 7.1 推荐实现的事件

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| **training** | `TrainingJobSubmittedEvent` | 任务提交 | quotas, audit |
| **training** | `TrainingJobCompletedEvent` | 任务完成 | billing, monitoring |
| **training** | `TrainingJobFailedEvent` | 任务失败 | monitoring, audit |
| **quotas** | `QuotaExceededEvent` | 配额超限 | monitoring |
| **auth** | `UserCreatedEvent` | 用户创建 | quotas (初始化配额) |
| **models** | `ModelPublishedEvent` | 模型发布 | audit |

---

## 8. 快速参考

```
┌────────────────────────────────────────────────────────┐
│            Modular Monolith 依赖速查                    │
├────────────────────────────────────────────────────────┤
│ ✅ 允许                                                │
│   • 导入 shared/* 任意内容                              │
│   • API 层导入 auth 的认证依赖                          │
│   • 通过 EventBus 发布/订阅事件                         │
│   • 依赖 shared 中定义的接口                            │
├────────────────────────────────────────────────────────┤
│ ❌ 禁止                                                │
│   • Domain 层导入任何外部模块                           │
│   • 直接导入其他模块的 Service                          │
│   • 直接导入其他模块的 Repository 实现                  │
│   • 导入其他模块的 ORM Model                            │
├────────────────────────────────────────────────────────┤
│ 🔄 模块间通信                                          │
│   • 优先: EventBus (异步解耦)                          │
│   • 备选: shared 接口 (同步调用)                        │
│   • 禁止: 直接依赖其他模块实现                          │
└────────────────────────────────────────────────────────┘
```

---

## 9. 架构合规检查

本规范通过自动化测试强制执行，详见 `tests/unit/test_architecture_compliance.py`。

CI 流程会在每次提交时检查：
- Domain 层无外部模块导入
- 无跨模块 Service 直接依赖
- API 层不使用 ORM 模型
- 中间件执行顺序正确

---

## 附录 A: 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 模块架构设计 | `docs/module-architecture-design.md` | 架构决策记录 |
| 后端开发指南 | `backend/CLAUDE.md` | 开发规范和 TDD 流程 |
| 功能规范 | `specs/001-ai-training-platform/spec.md` | 业务需求定义 |
