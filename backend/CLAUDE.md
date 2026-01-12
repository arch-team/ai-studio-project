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

## Architecture

### 分层架构
```
src/main.py              → FastAPI 应用入口 + 全局异常处理
src/api/v1/              → API 路由 (版本化，当前 v1)
src/services/            → 业务逻辑层 (无状态服务)
src/clients/             → 外部服务客户端 (AWS SDK 封装)
src/middleware/          → 认证/授权/审计中间件
src/models/              → SQLAlchemy ORM 模型
src/schemas/             → Pydantic 请求/响应模式
src/core/                → 基础设施 (配置、数据库、异常)
```

### 异常处理体系
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

### 认证架构 (双模式)
- **SSO 模式**: IAM Identity Center OIDC (`middleware/sso.py`)
- **本地认证**: JWT + 密码策略 (`middleware/auth.py`)

```python
# 路由保护示例
from src.middleware.auth import RequireAdmin, RequireEngineer

@router.post("/jobs", dependencies=[Depends(RequireEngineer)])
async def create_job(): ...
```

### RBAC 权限系统
四级角色层级：`ADMIN > PROJECT_MANAGER > ENGINEER > VIEWER`

```python
# src/services/rbac_service.py
rbac = get_rbac_service()
result = rbac.check_permission(user_role, ResourceType.TRAINING_JOB, Action.CREATE)
if not result.allowed:
    raise AuthorizationError(result.reason)
```

### 服务单例模式
所有服务使用 `get_xxx_service()` 获取单例实例：

```python
from src.services.rbac_service import get_rbac_service
from src.services.account_service import get_account_service
from src.clients.hyperpod_client import get_hyperpod_client
```

## Key Patterns

### 新增 API 端点
1. 在 `src/api/v1/endpoints/` 创建路由文件
2. 在 `src/api/v1/router.py` 注册路由
3. 使用 `RequireXxx` 依赖进行权限控制
4. 业务异常直接抛出 `AppException` 子类

### 新增业务异常
1. 在 `src/core/exceptions.py` 定义异常类，继承合适的父类
2. 在 `HTTP_STATUS_MAPPING` 中添加状态码映射

### 新增数据模型
1. 在 `src/models/` 创建 SQLAlchemy 模型
2. 运行 `alembic revision --autogenerate -m "description"`
3. 运行 `alembic upgrade head`

## Project Constraints

### HyperPod SDK 使用原则
- **默认使用 HyperPod Task Governance API**: 所有训练任务调度通过 `HyperPodClient`
- **Kueue 直接访问**: 仅在状态监控和故障诊断时使用，需在代码注释中说明理由

### 测试组织
测试文件镜像 `src/` 结构：
```
tests/test_core/       → src/core/ 测试
tests/test_services/   → src/services/ 测试
tests/test_schemas/    → src/schemas/ 测试
```
