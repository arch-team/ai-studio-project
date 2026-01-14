# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**

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

项目采用 **Clean Architecture + Ports & Adapters** 模式：

```
src/
├── api/                    # API 层 (最外层)
│   ├── v1/endpoints/      # REST 端点
│   ├── v1/schemas/        # Pydantic 请求/响应模型
│   └── v1/dependencies/   # FastAPI 依赖注入
├── application/            # 应用层
│   ├── services/          # 业务用例实现
│   ├── dto/               # 数据传输对象
│   └── interfaces/        # 端口定义 (HyperPod, Storage)
├── domain/                 # 域层 (核心业务)
│   ├── entities/          # 业务实体
│   ├── value_objects/     # 值对象
│   ├── repositories/      # 仓库接口 (IRepository)
│   ├── exceptions/        # 域异常
│   └── events/            # 域事件
├── infrastructure/         # 基础设施层
│   ├── config/            # Settings (Pydantic BaseSettings)
│   ├── persistence/       # ORM 模型和仓库实现
│   └── external/          # 外部适配器 (hyperpod/, s3/, kueue/)
└── core/                   # 跨切关注点
    ├── logging/           # structlog 配置
    ├── security/          # 认证/授权
    └── utils/             # 工具函数
```

**依赖方向**: API → Application → Domain ← Infrastructure

## Key Interfaces

- `IRepository<T>`: 通用仓库接口 (`src/domain/repositories/base.py`)
- `IHyperPodClient`: SageMaker HyperPod 操作 (`src/application/interfaces/hyperpod_client.py`)
- `IStorageService`: S3/FSx 存储操作 (`src/application/interfaces/storage_service.py`)

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

## Test-Driven Development (TDD)

本项目践行 TDD 实践，遵循 **Red-Green-Refactor** 循环。

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
