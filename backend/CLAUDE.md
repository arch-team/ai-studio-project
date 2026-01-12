# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**

## Project Overview
AI Training Platform 后端服务 - 基于 FastAPI 构建的异步 API，集成 AWS SageMaker HyperPod 进行分布式训练任务管理。

## Common Commands

```bash
# 启动开发服务器
uvicorn src.main:app --reload

# 数据库迁移
alembic upgrade head                              # 应用迁移
alembic revision --autogenerate -m "description"  # 创建迁移

# 测试
pytest                                    # 运行所有测试
pytest tests/test_services/test_rbac_service.py -v  # 单个测试文件
pytest tests/test_core/test_exceptions.py::test_func -v  # 单个测试函数
pytest --cov=src --cov-report=html        # 测试覆盖率

# 代码检查
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Clean Architecture 整洁架构

本项目遵循**领域驱动设计（DDD）+ 整洁架构（Clean Architecture）**原则。

### 依赖规则（The Dependency Rule）
```
外层 → 内层（依赖方向）
内层绝不能引用外层的任何内容
```

### 四层架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Frameworks & Drivers（框架层）             │
│  FastAPI, SQLAlchemy, boto3, aiomysql                      │
├─────────────────────────────────────────────────────────────┤
│                Interface Adapters（接口适配层）             │
│  api/           → HTTP Controllers（路由处理器）            │
│  infrastructure/repositories/ → Repository 实现            │
│  infrastructure/external/     → 外部服务适配器             │
├─────────────────────────────────────────────────────────────┤
│                   Use Cases（应用层）                       │
│  application/use_cases/  → 业务用例                        │
│  application/services/   → 应用服务（编排多个用例）        │
│  application/dto/        → 数据传输对象                    │
├─────────────────────────────────────────────────────────────┤
│                    Entities（领域层）                       │
│  domain/entities/        → 领域实体（纯 Python 类）        │
│  domain/value_objects/   → 值对象（不可变）                │
│  domain/repositories/    → 仓储接口（抽象基类）            │
│  domain/services/        → 领域服务                        │
│  domain/events/          → 领域事件                        │
└─────────────────────────────────────────────────────────────┘
```

### 目标目录结构

```
src/
├── domain/                      # 领域层（最内层，无外部依赖）
│   ├── entities/               # 领域实体（纯 Python dataclass）
│   ├── value_objects/          # 值对象
│   ├── repositories/           # 仓储接口（ABC）
│   ├── services/               # 领域服务
│   └── events/                 # 领域事件
│
├── application/                # 应用层（用例编排）
│   ├── use_cases/             # 用例（单一职责）
│   ├── services/              # 应用服务
│   └── dto/                   # 数据传输对象
│
├── infrastructure/            # 基础设施层
│   ├── persistence/           # 持久化
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── repositories/     # 仓储实现
│   │   └── database.py
│   ├── external/             # 外部服务适配器
│   │   ├── hyperpod/         # HyperPod SDK 封装
│   │   └── s3/               # S3 客户端
│   └── config/               # 配置
│
├── api/                       # 接口适配层
│   ├── v1/endpoints/         # 路由处理器
│   ├── middleware/           # 中间件
│   └── schemas/              # Pydantic 请求/响应
│
└── main.py                    # 应用入口
```

### 当前架构（演进中）

```
src/
├── main.py              → FastAPI 应用入口 + 全局异常处理
├── api/v1/              → API 路由（版本化）
├── services/            → 业务逻辑层（待迁移到 application/）
├── clients/             → 外部服务客户端（待迁移到 infrastructure/）
├── middleware/          → 认证/授权/审计中间件
├── models/              → SQLAlchemy ORM 模型（待迁移到 infrastructure/）
├── schemas/             → Pydantic 请求/响应（待迁移到 api/）
└── core/                → 基础设施（配置、数据库、异常）
```

## Key Patterns 关键模式

### 领域实体（Domain Entity）
```python
# domain/entities/training_job.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class TrainingJob:
    """领域实体 - 纯 Python，无 ORM 依赖"""
    id: str
    name: str
    status: JobStatus
    owner_id: str

    def can_be_cancelled(self) -> bool:
        """领域逻辑封装在实体内"""
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING]

    def cancel(self) -> None:
        if not self.can_be_cancelled():
            raise DomainError("Job cannot be cancelled in current state")
        self.status = JobStatus.CANCELLED
```

### 仓储接口（Repository Interface）
```python
# domain/repositories/job_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

class IJobRepository(ABC):
    """仓储接口 - 定义在领域层，实现在基础设施层"""

    @abstractmethod
    async def find_by_id(self, job_id: str) -> Optional[TrainingJob]:
        pass

    @abstractmethod
    async def save(self, job: TrainingJob) -> None:
        pass

    @abstractmethod
    async def find_by_owner(self, owner_id: str) -> List[TrainingJob]:
        pass
```

### 仓储实现（Repository Implementation）
```python
# infrastructure/persistence/repositories/job_repository.py
from domain.repositories.job_repository import IJobRepository
from infrastructure.persistence.models.job import JobModel

class SQLAlchemyJobRepository(IJobRepository):
    """仓储实现 - ORM 与领域实体转换"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, job_id: str) -> Optional[TrainingJob]:
        model = await self._session.get(JobModel, job_id)
        return self._to_entity(model) if model else None

    def _to_entity(self, model: JobModel) -> TrainingJob:
        """ORM 模型 → 领域实体"""
        return TrainingJob(
            id=model.id,
            name=model.name,
            status=JobStatus(model.status),
            owner_id=model.owner_id,
        )
```

### 用例（Use Case）
```python
# application/use_cases/create_training_job.py
from dataclasses import dataclass

@dataclass
class CreateTrainingJobRequest:
    name: str
    owner_id: str
    instance_type: str
    node_count: int

class CreateTrainingJobUseCase:
    """用例 - 编排领域服务和仓储，单一职责"""

    def __init__(
        self,
        job_repository: IJobRepository,
        hyperpod_service: IHyperPodService,
    ):
        self._job_repo = job_repository
        self._hyperpod = hyperpod_service

    async def execute(self, request: CreateTrainingJobRequest) -> TrainingJob:
        # 1. 创建领域实体
        job = TrainingJob.create(
            name=request.name,
            owner_id=request.owner_id,
        )
        # 2. 调用外部服务
        await self._hyperpod.submit_job(job, request.instance_type)
        # 3. 持久化
        await self._job_repo.save(job)
        return job
```

### 依赖注入（Dependency Injection）
```python
# api/v1/endpoints/jobs.py
from fastapi import Depends

async def get_job_repository(
    session: AsyncSession = Depends(get_db),
) -> IJobRepository:
    return SQLAlchemyJobRepository(session)

async def get_create_job_use_case(
    job_repo: IJobRepository = Depends(get_job_repository),
    hyperpod: IHyperPodService = Depends(get_hyperpod_service),
) -> CreateTrainingJobUseCase:
    return CreateTrainingJobUseCase(job_repo, hyperpod)

@router.post("/jobs")
async def create_job(
    request: CreateJobRequest,
    use_case: CreateTrainingJobUseCase = Depends(get_create_job_use_case),
):
    job = await use_case.execute(request.to_domain())
    return JobResponse.from_entity(job)
```

## 异常处理体系

所有业务异常继承 `AppException`，系统自动映射到 HTTP 状态码：

```python
# src/core/exceptions.py
AppException           → 基类
├── AuthenticationError   → 401
├── AuthorizationError    → 403
├── ResourceNotFoundError → 404
├── ResourceConflictError → 409
├── ValidationError       → 400
├── HyperPodError         → 500
└── SSOError              → 502
```

在 `main.py` 中 `app_exception_handler` 自动处理所有 `AppException` 子类，无需手动捕获。

### 新增业务异常
1. 在 `src/core/exceptions.py` 定义异常类，继承合适的父类
2. 在 `HTTP_STATUS_MAPPING` 中添加状态码映射

## 认证架构（双模式）

- **SSO 模式**: IAM Identity Center OIDC (`middleware/sso.py`)
- **本地认证**: JWT + 密码策略 (`middleware/auth.py`)

```python
# 路由保护示例
from src.middleware.auth import RequireAdmin, RequireEngineer

@router.post("/jobs", dependencies=[Depends(RequireEngineer)])
async def create_job(): ...
```

## RBAC 权限系统

四级角色层级：`ADMIN > PROJECT_MANAGER > ENGINEER > VIEWER`

```python
# src/services/rbac_service.py
rbac = get_rbac_service()
result = rbac.check_permission(user_role, ResourceType.TRAINING_JOB, Action.CREATE)
if not result.allowed:
    raise AuthorizationError(result.reason)
```

## Project Constraints 项目约束

### HyperPod SDK 使用原则
- **默认使用 HyperPod Task Governance API**: 所有训练任务调度通过 `HyperPodClient`
- **Kueue 直接访问**: 仅在状态监控和故障诊断时使用，需在代码注释中说明理由

### 整洁架构约束
- **领域层零依赖**: `domain/` 目录下的代码不能 import 任何外部库（除标准库）
- **仓储接口在领域层**: `IXxxRepository` 定义在 `domain/repositories/`
- **仓储实现在基础设施层**: `SQLAlchemyXxxRepository` 实现在 `infrastructure/persistence/repositories/`
- **用例单一职责**: 每个用例类只处理一个业务场景
- **依赖注入**: 使用 FastAPI `Depends()` 注入依赖，便于测试

### 测试组织
```
tests/
├── unit/                  # 单元测试
│   ├── domain/           # 领域层测试（无 mock）
│   ├── application/      # 用例测试（mock 仓储）
│   └── infrastructure/   # 基础设施测试
├── integration/          # 集成测试
└── e2e/                  # 端到端测试
```

## 演进策略

### Phase 1: 当前（保持兼容）
- 继续使用现有 `services/` 作为业务逻辑层
- 新功能逐步采用整洁架构模式

### Phase 2: 引入领域层
- 创建 `domain/` 目录结构
- 新增领域实体和仓储接口
- `models/` 仅作为 ORM 映射

### Phase 3: 分离应用层
- 创建 `application/use_cases/`
- 现有 `services/` 逐步迁移到用例模式
- 完成目录结构重组
