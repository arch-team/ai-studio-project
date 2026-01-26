# 后端架构 (DDD + Clean Architecture)

**更新时间**: 2026-01-26 10:30
**版本**: 1.0.0

## 模块清单 (9个)

| 模块 | 导出数 | 核心实体 | 状态 |
|------|--------|---------|------|
| `auth` | 19 | User, Role | ✅ 完整 |
| `training` | 24 | TrainingJob, Checkpoint | ✅ 完整 |
| `models` | 11 | Model, ModelVersion | ✅ 完整 |
| `quotas` | 13 | ResourceQuota, ResourceLimitConfig | ✅ 完整 |
| `spaces` | 14 | Space, SpaceType | ✅ 完整 |
| `audit` | 8 | AuditLog | ✅ 完整 |
| `datasets` | 5 | Dataset, DatasetVersion | 🔄 部分 |
| `monitoring` | 0 | Metric, Alert | 📋 骨架 |
| `billing` | 0 | CostRecord, UsageReport | 📋 空 |

## 分层结构

```
modules/{module}/
├── api/                    # API 层 (HTTP 入口适配器)
│   ├── endpoints.py        # FastAPI routes
│   ├── dependencies.py     # 依赖注入
│   └── schemas/
│       ├── requests.py     # 请求模型 (Pydantic)
│       └── responses.py    # 响应模型 (Pydantic)
│
├── application/            # Application 层 (业务用例编排)
│   └── services/
│       └── {entity}_service.py
│
├── domain/                 # Domain 层 (核心业务逻辑)
│   ├── entities/
│   │   └── {entity}.py     # DDD 实体 (BaseEntity)
│   ├── value_objects/      # 值对象
│   ├── repositories/
│   │   └── {entity}_repository.py  # 仓库接口 (IRepository)
│   ├── events.py           # 域事件 (DomainEvent)
│   └── exceptions.py       # 域异常 (Problem)
│
└── infrastructure/         # Infrastructure 层 (技术实现)
    ├── models/
    │   └── {entity}_model.py  # ORM 模型 (SQLAlchemy)
    ├── repositories/
    │   └── {entity}_repository_impl.py  # 仓库实现
    └── {client}.py         # 外部服务客户端
```

### 依赖方向 (黄金规则)

```
    API
     │
     ▼
Application
     │
     ▼
  Domain  ←───── Infrastructure
```

| 规则 | 说明 | 状态 |
|------|------|------|
| **R1** | Domain 层绝不依赖任何外部模块 | ✅ |
| **R2** | Application 层仅依赖接口，不依赖实现 | ✅ |
| **R3** | 模块间通信使用 EventBus 或共享接口 | ✅ |
| **R4** | Auth 认证依赖可被其他模块 API 层导入 | ✅ |

## 共享内核

### shared/domain/

```python
# 基础类
BaseEntity          # 领域实体基类 (id, created_at, updated_at)
PydanticEntity      # Pydantic 实体基类
IRepository[T]      # 仓库接口 (泛型)

# 事件系统
DomainEvent         # 域事件基类
EventBus            # 事件总线 (发布-订阅)
event_handler       # 事件处理装饰器

# 异常框架
Problem             # 结构化异常基类
problem             # 异常装饰器

# 跨模块接口
IQuotaChecker       # 配额检查接口
IEntityExistenceChecker  # 实体存在检查接口
```

### shared/infrastructure/

```python
# 数据库
Base                # SQLAlchemy 声明基类
engine              # 异步引擎
AsyncSessionLocal   # 异步会话工厂
get_db              # 依赖注入

# 仓库
BaseRepository[T, M]    # 通用仓库基类
PydanticRepository      # Pydantic 实体仓库

# 配置
Settings            # Pydantic Settings
get_settings        # 依赖注入

# 存储
S3StorageClient     # S3 客户端封装
FsxClient           # FSx 客户端封装

# 工具
LoggingConfig       # 日志配置
QueryBuilder        # 查询构建器
```

### shared/api/

```python
# 异常处理
exception_handlers  # FastAPI 异常处理器

# 中间件
AuthMiddleware      # JWT 认证
TracingMiddleware   # 请求追踪

# 模式
EntitySchema        # 基础响应模型
PaginationParams    # 分页参数
PaginatedResponse   # 分页响应
```

## 跨模块通信

### 1. 共享接口 (同步)

```python
# quotas 模块实现
class QuotaCheckerImpl(IQuotaChecker):
    async def check_quota(self, user_id, resource_type) -> bool: ...

# training 模块使用
class TrainingJobService:
    def __init__(self, quota_checker: IQuotaChecker):
        self.quota_checker = quota_checker

    async def create_job(self, ...):
        if not await self.quota_checker.check_quota(...):
            raise QuotaExceededError()
```

### 2. 事件总线 (异步)

```python
# training 模块发布
from shared.domain import EventBus

class TrainingJobService:
    async def complete_job(self, job_id):
        # ... 业务逻辑
        await EventBus.publish(TrainingJobCompletedEvent(job_id=job_id))

# audit 模块订阅
from shared.domain import event_handler

@event_handler(TrainingJobCompletedEvent)
async def on_job_completed(event: TrainingJobCompletedEvent):
    await AuditService.log_event(event)
```

### 3. ORM 外键 (TYPE_CHECKING)

```python
# training/infrastructure/models/training_job_model.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import UserModel
    from src.modules.models.infrastructure.models import ModelModel

class TrainingJobModel(Base):
    owner_id = mapped_column(ForeignKey("users.id"))
    model_id = mapped_column(ForeignKey("models.id"))
```

## 模块依赖矩阵

| 模块 | 依赖 | 被依赖 |
|------|------|--------|
| `auth` | - | all |
| `training` | auth, quotas (interface), models (FK) | monitoring |
| `models` | auth | training |
| `quotas` | auth | training (interface) |
| `spaces` | auth | - |
| `datasets` | auth | training |
| `audit` | auth | - (EventBus) |
| `monitoring` | auth | - |
| `billing` | auth | - |

## 关键文件路径

| 用途 | 路径 |
|------|------|
| 应用入口 | `backend/src/main.py` |
| 路由聚合 | `backend/src/router.py` |
| 数据库配置 | `backend/src/shared/infrastructure/database.py` |
| 设置管理 | `backend/src/shared/infrastructure/config.py` |
| 架构合规测试 | `backend/tests/architecture/test_architecture_compliance.py` |
| 迁移脚本 | `backend/alembic/versions/` |

## 命令参考

```bash
# 开发服务器
uvicorn src.main:app --reload

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "message"

# 测试
pytest                          # 全部
pytest tests/unit/              # 单元测试
pytest tests/architecture/      # 架构合规
pytest --cov=src               # 覆盖率

# 代码质量
black src/ tests/
ruff check src/
mypy src/
```

## 技术栈详情

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11+ |
| 框架 | FastAPI | 0.109+ |
| ORM | SQLAlchemy (Async) | 2.0.25 |
| 验证 | Pydantic | 2.5.3 |
| 迁移 | Alembic | 1.13.1 |
| 认证 | python-jose (JWT) | - |
| 密码 | passlib (bcrypt) | - |
| AWS | boto3, aioboto3 | 1.34.14 |
| 测试 | pytest, pytest-asyncio | - |
