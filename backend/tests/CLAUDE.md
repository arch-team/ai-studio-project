# Backend Tests 规范指南

> **版本**: 1.5
> **最后更新**: 2025-01-17
> **架构模式**: 扁平模块 + 类型前缀命名

本文档是后端测试的**规范单一真实源 (Single Source of Truth)**。所有测试相关决策应以本文档为准。

> ⚠️ **过渡说明**: 本文档描述的是**目标结构**。当前存在部分遗留的深层嵌套结构（如 `unit/modules/auth/domain/entities/`），新测试应遵循本规范的扁平结构。

---

## 目录

1. [设计原则](#1-设计原则)
2. [目录结构规范](#2-目录结构规范)
3. [测试分层策略](#3-测试分层策略)
4. [Fixture 使用规范](#4-fixture-使用规范)
5. [测试标记 (Markers)](#5-测试标记-markers)
6. [测试编写规范](#6-测试编写规范)
7. [测试运行命令](#7-测试运行命令)
8. [Mock 使用规范](#8-mock-使用规范)

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **模块自治** | 每个模块的测试独立存放 |
| **扁平优先** | 最大目录深度 ≤ 4 层，避免过度嵌套 |
| **类型前缀** | 文件名使用类型前缀，便于排序和定位 |
| **共享复用** | 通用 fixtures 和工具集中在 `tests/shared/` |
| **测试诚信** | 切勿为让测试通过而伪造结果，测试失败 = 代码有问题 |

---

## 2. 目录结构规范

### 2.1 完整目录结构

```
backend/tests/
├── conftest.py                    # 全局 pytest 配置
├── shared/                        # 共享测试基础设施
│   ├── conftest.py                # 共享 fixtures 导出
│   ├── fixtures/                  # 可复用 fixtures
│   │   ├── database.py            # 数据库 session fixtures
│   │   ├── auth.py                # JWT、用户认证 fixtures
│   │   └── mocks.py               # 通用 mock 对象
│   ├── helpers/                   # 测试辅助函数
│   │   ├── assertions.py          # 自定义断言
│   │   └── async_utils.py         # 异步测试工具
│   └── constants.py               # 测试常量
│
├── unit/                          # 单元测试 (无外部依赖)
│   ├── conftest.py                # 单元测试 fixtures
│   ├── auth/
│   │   ├── conftest.py            # 模块专属 fixtures
│   │   ├── test_entity_user.py    # User 实体
│   │   ├── test_entity_login_attempt.py
│   │   ├── test_vo_token.py       # Token 值对象
│   │   ├── test_event_user_created.py  # UserCreatedEvent
│   │   ├── test_svc_auth.py       # AuthService
│   │   ├── test_dto_user.py       # UserDTO 转换
│   │   └── test_schema_auth.py    # LoginRequest 验证
│   ├── training/
│   │   ├── conftest.py
│   │   ├── test_entity_training_job.py
│   │   ├── test_entity_checkpoint.py
│   │   ├── test_vo_job_status.py
│   │   ├── test_vo_resource_config.py
│   │   ├── test_event_job_completed.py
│   │   ├── test_event_job_failed.py
│   │   ├── test_svc_training.py
│   │   ├── test_dto_training_job.py
│   │   └── test_schema_training.py
│   ├── quotas/
│   ├── models/
│   ├── datasets/
│   ├── spaces/
│   ├── audit/
│   ├── billing/
│   ├── monitoring/
│   └── shared/                    # shared 内核测试
│       ├── test_domain.py
│       └── test_utils.py
│
├── integration/                   # 集成测试 (真实依赖)
│   ├── conftest.py                # 集成测试 fixtures (真实 DB)
│   ├── auth/
│   │   ├── test_api_auth.py       # API 端点集成测试
│   │   └── test_repo_user.py      # 仓库实现测试
│   ├── training/
│   │   ├── test_api_training.py
│   │   └── test_repo_training_job.py
│   ├── cross_module/              # 跨模块集成测试
│   └── database/                  # 数据库集成测试
│
├── e2e/                           # 端到端测试
│   ├── conftest.py
│   ├── scenarios/                 # 用户场景测试
│   │   ├── test_e2e_auth.py       # 认证完整流程
│   │   ├── test_e2e_training.py   # 训练任务流程
│   │   └── test_e2e_model.py      # 模型管理流程
│   └── aws/                       # AWS 集成 E2E
│       ├── test_aws_hyperpod.py   # HyperPod 集成
│       └── test_aws_s3.py         # S3 存储集成
│
├── architecture/                  # 架构合规测试
│   ├── test_arch_dependency.py    # 依赖方向检查
│   ├── test_arch_layer.py         # 分层规则检查
│   ├── test_arch_module.py        # 模块隔离检查
│   └── test_arch_import.py        # 导入规则检查
│
└── performance/                   # 性能测试
    ├── conftest.py
    ├── test_perf_api.py           # API 响应性能
    ├── test_perf_db.py            # 数据库查询性能
    └── test_perf_load.py          # 负载测试
```

### 2.2 目录深度对比

| 层级 | 旧结构 (最深 6 层) | 新结构 (最深 4 层) |
|------|-------------------|-------------------|
| 实体测试 | `unit/modules/auth/domain/entities/` | `unit/auth/` |
| 服务测试 | `unit/modules/auth/application/services/` | `unit/auth/` |
| API 测试 | `integration/modules/auth/api/` | `integration/auth/` |

### 2.3 各目录职责

| 目录 | 职责 | 外部依赖 |
|------|------|---------|
| `shared/` | 共享 fixtures、helpers、constants | 无 |
| `unit/` | 领域逻辑、服务逻辑测试 | 无（全部 mock） |
| `integration/` | API 端点、仓库实现 | 数据库、外部服务 |
| `e2e/` | 完整用户流程 | 完整应用 |
| `architecture/` | 架构规则合规检查 | 无 |
| `performance/` | 性能基准测试 | 完整应用 |

### 2.4 文件命名规范

#### 类型前缀表

**单元测试前缀** (用于 `unit/` 目录):

| 前缀 | 含义 | 测试内容 |
|------|------|---------|
| `test_entity_` | 领域实体 | 状态转换、业务规则、不变条件 |
| `test_vo_` | 值对象 | 不变性、相等性、验证规则 |
| `test_event_` | 域事件 | 事件创建、属性验证、序列化 |
| `test_svc_` | 应用服务 | 用例编排、Mock 仓库调用 |
| `test_dto_` | DTO | Entity ↔ DTO 转换逻辑 |
| `test_schema_` | Pydantic Schema | 请求验证、响应格式、字段约束 |

**集成测试前缀** (用于 `integration/` 目录):

| 前缀 | 含义 | 测试内容 |
|------|------|---------|
| `test_api_` | API 端点 | HTTP 请求/响应、状态码 |
| `test_repo_` | 仓库实现 | CRUD 操作、查询逻辑 |

**特殊测试前缀**:

| 前缀 | 含义 | 适用目录 |
|------|------|---------|
| `test_e2e_` | 端到端场景 | `e2e/scenarios/` |
| `test_aws_` | AWS 集成 | `e2e/aws/` |
| `test_arch_` | 架构合规 | `architecture/` |
| `test_perf_` | 性能测试 | `performance/` |

#### 命名优势

- **可排序**: 同类型文件在文件浏览器中自动分组
- **易定位**: 输入 `test_entity_` 即可补全所有实体测试
- **可扩展**: 新增实体只需新增文件，无需修改现有文件
- **可筛选**: `pytest -k "test_arch_"` 运行所有架构测试

#### 完整示例

```
unit/training/
├── conftest.py
├── test_entity_training_job.py    # TrainingJob 状态机、业务规则
├── test_entity_checkpoint.py      # Checkpoint 生命周期
├── test_vo_job_status.py          # JobStatus 枚举验证
├── test_vo_resource_config.py     # ResourceConfig 不变性
├── test_event_job_completed.py    # TrainingJobCompletedEvent 创建
├── test_event_job_failed.py       # TrainingJobFailedEvent 属性
├── test_svc_training.py           # TrainingJobService 用例
├── test_dto_training_job.py       # TrainingJob ↔ DTO 转换
└── test_schema_training.py        # CreateJobRequest 验证规则

integration/training/
├── test_api_training.py           # /training-jobs 端点
└── test_repo_training_job.py      # TrainingJobRepository 实现

architecture/
├── test_arch_dependency.py        # 依赖方向: Domain 不依赖外部
├── test_arch_layer.py             # 分层规则: API→App→Domain
├── test_arch_module.py            # 模块隔离: 禁止横向依赖
└── test_arch_import.py            # 导入规则: 只允许导入 shared

e2e/scenarios/
├── test_e2e_auth.py               # 注册→登录→Token刷新
├── test_e2e_training.py           # 提交→监控→完成
└── test_e2e_model.py              # 上传→审批→发布

performance/
├── test_perf_api.py               # API 响应时间 < 200ms
├── test_perf_db.py                # 查询时间 < 100ms
└── test_perf_load.py              # 100并发下稳定运行
```

---

## 3. 测试分层策略

### 3.1 测试金字塔

```
        /\
       /  \      E2E Tests (少量)
      /----\
     /      \    Integration Tests (中等)
    /--------\
   /          \  Unit Tests (大量)
  /____________\
```

### 3.2 各层职责

**单元测试 (Unit)**:

| 位置 | 测试对象 | Mock 策略 |
|------|---------|----------|
| `unit/{module}/test_entity_*.py` | 实体、业务规则 | 无依赖，纯函数 |
| `unit/{module}/test_vo_*.py` | 值对象 | 无依赖，纯函数 |
| `unit/{module}/test_event_*.py` | 域事件 | 无依赖，纯函数 |
| `unit/{module}/test_svc_*.py` | 应用服务 | Mock 仓库接口 |
| `unit/{module}/test_dto_*.py` | DTO 转换 | 无依赖 |
| `unit/{module}/test_schema_*.py` | Schema 验证 | 无依赖 |

**集成测试 (Integration)**:

| 位置 | 测试对象 | Mock 策略 |
|------|---------|----------|
| `integration/{module}/test_api_*.py` | API 端点 | Mock 外部服务 |
| `integration/{module}/test_repo_*.py` | 仓库实现 | 真实数据库 |

**其他测试**:

| 位置 | 测试对象 | Mock 策略 |
|------|---------|----------|
| `e2e/scenarios/test_e2e_*.py` | 完整用户流程 | 真实应用 |
| `e2e/aws/test_aws_*.py` | AWS 服务集成 | 真实 AWS |
| `architecture/test_arch_*.py` | 架构规则 | 静态分析 |
| `performance/test_perf_*.py` | 性能指标 | 真实应用 |

### 3.3 测试比例建议

- **Unit Tests**: 70%
- **Integration Tests**: 20%
- **E2E Tests**: 10%

### 3.4 单元测试覆盖范围决策

| 组件 | 是否单测 | 原因 |
|------|---------|------|
| Entity | ✅ 是 | 核心业务逻辑，状态转换复杂 |
| Value Object | ✅ 是 | 验证规则、不变性保证 |
| Domain Event | ✅ 是 | 事件驱动架构核心 |
| Application Service | ✅ 是 | 用例编排，需验证调用顺序 |
| DTO | ✅ 是 | 转换逻辑易出错 |
| Pydantic Schema | ✅ 是 | 复杂验证规则需独立测试 |
| Domain Service | ❌ 否 | 通常逻辑简单，由集成测试覆盖 |
| Specification | ❌ 否 | 与数据库耦合，属集成测试 |
| Repository 接口 | ❌ 否 | 接口无逻辑，测试实现即可 |

---

## 4. Fixture 使用规范

### 4.1 conftest.py 层级职责

```python
# tests/conftest.py - 全局配置
@pytest.fixture(scope="session")
def event_loop():
    """全局事件循环"""

# tests/shared/conftest.py - 共享 fixtures
@pytest.fixture
def mock_session(): ...
@pytest.fixture
def jwt_manager(): ...

# tests/unit/conftest.py - 单元测试配置
# 导入共享 fixtures，添加单元测试专属配置

# tests/unit/{module}/conftest.py - 模块专属
@pytest.fixture
def sample_user(): ...
@pytest.fixture
def mock_user_repository(): ...

# tests/integration/conftest.py - 集成测试配置
@pytest.fixture(scope="module")
def test_database(): ...  # 真实数据库连接
```

### 4.2 Fixture 作用域

| 作用域 | 使用场景 |
|-------|---------|
| `function` (默认) | 每个测试函数独立状态 |
| `class` | 同一测试类共享 |
| `module` | 同一文件共享（数据库连接） |
| `session` | 整个测试会话共享（事件循环） |

### 4.3 共享 Fixtures 使用

```python
# 在模块 conftest.py 中导入共享 fixtures
from tests.shared.fixtures.database import mock_session
from tests.shared.fixtures.auth import jwt_manager, sample_user_data

# 或在测试文件中直接导入
from tests.shared.helpers.assertions import assert_entity_equal
```

---

## 5. 测试标记 (Markers)

### 5.1 可用标记

| 标记 | 说明 | 默认行为 |
|------|------|---------|
| `@pytest.mark.unit` | 单元测试 | 自动添加 |
| `@pytest.mark.integration` | 集成测试 | 自动添加 |
| `@pytest.mark.e2e` | 端到端测试 | 自动添加 |
| `@pytest.mark.architecture` | 架构合规测试 | 自动添加 |
| `@pytest.mark.performance` | 性能测试 | 默认跳过 |
| `@pytest.mark.aws_integration` | AWS 集成测试 | 默认跳过 |
| `@pytest.mark.slow` | 耗时测试 | 默认跳过 |

### 5.2 自动标记规则

测试根据路径自动添加标记：

```python
# tests/conftest.py
def pytest_collection_modifyitems(config, items):
    for item in items:
        test_path = str(item.fspath)
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        # ...
```

---

## 6. 测试编写规范

### 6.1 测试类命名

```python
# 按功能分组
class TestUserCreation:
    def test_create_with_required_fields(self): ...
    def test_create_with_optional_fields(self): ...

class TestUserStateTransitions:
    def test_activate_from_pending(self): ...
    def test_deactivate_active_user(self): ...
```

### 6.2 测试函数命名

```python
# 格式: test_{action}_{condition}_{expected_result}
def test_login_with_valid_credentials_returns_token(self): ...
def test_login_with_invalid_password_raises_error(self): ...
def test_create_user_with_duplicate_email_fails(self): ...
```

### 6.3 断言规范

```python
# ✅ 使用具体断言
assert user.status == UserStatus.ACTIVE
assert response.status_code == 200
assert "error" in response.json()

# ✅ 使用自定义断言
from tests.shared.helpers.assertions import assert_entity_equal
assert_entity_equal(actual_user, expected_user, exclude_fields=["created_at"])

# ❌ 避免过于宽泛的断言
assert user is not None  # 不够具体
assert response.ok      # 不够具体
```

### 6.4 测试结构 (AAA 模式)

```python
def test_submit_training_job_success(self):
    # Arrange - 准备测试数据
    job = TrainingJob(name="test-job", owner_id=1)
    mock_repo.create.return_value = job

    # Act - 执行被测行为
    result = await service.submit_job(job)

    # Assert - 验证结果
    assert result.status == JobStatus.SUBMITTED
    mock_repo.create.assert_called_once_with(job)
```

---

## 7. 测试运行命令

### 7.1 常用命令

```bash
# 运行所有单元测试
pytest tests/unit -v

# 运行特定模块的单元测试
pytest tests/unit/auth -v

# 按类型运行单元测试
pytest -k "test_entity_" -v      # 所有实体测试
pytest -k "test_vo_" -v          # 所有值对象测试
pytest -k "test_event_" -v       # 所有域事件测试
pytest -k "test_svc_" -v         # 所有服务测试
pytest -k "test_dto_" -v         # 所有 DTO 测试
pytest -k "test_schema_" -v      # 所有 Schema 测试

# 运行集成测试
pytest tests/integration -v

# 运行架构合规检查
pytest tests/architecture -v
pytest -k "test_arch_" -v

# 运行 E2E 测试
pytest tests/e2e -v
pytest -k "test_e2e_" -v

# 运行性能测试
pytest tests/performance -v
pytest -k "test_perf_" -v

# 运行 AWS 集成测试（需要凭证）
pytest -k "test_aws_" -v

# 运行完整测试套件（排除默认跳过的测试）
pytest tests/

# 生成覆盖率报告
pytest tests/unit --cov=src --cov-report=html
```

### 7.2 开发常用

```bash
# 监视模式（需要 pytest-watch）
ptw tests/unit/

# 只运行上次失败的测试
pytest --lf

# 失败时立即停止
pytest -x

# 详细输出
pytest -v --tb=short

# 运行匹配名称的测试
pytest -k "test_login"
```

---

## 8. Mock 使用规范

### 8.1 单元测试 Mock 策略

```python
# ✅ Mock 外部依赖接口
@pytest.fixture
def mock_user_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo

# ✅ 使用 Mock 注入服务
async def test_auth_service_login(mock_user_repository, mock_jwt_manager):
    service = AuthService(
        user_repository=mock_user_repository,
        jwt_manager=mock_jwt_manager,
    )
    # ...
```

### 8.2 集成测试 Mock 策略

```python
# ✅ 只 Mock 外部服务，不 Mock 数据库
@pytest.fixture
def mock_hyperpod_client():
    """Mock HyperPod，但使用真实数据库"""
    client = AsyncMock()
    client.submit_job.return_value = {"job_id": "hyperpod-123"}
    return client
```

### 8.3 禁止的 Mock 模式

```python
# ❌ 不要 Mock 被测试的类本身
# ❌ 不要 Mock 简单的数据类
# ❌ 不要在测试中修改生产代码的行为
```

---

## 附录: 快速参考卡片

```
┌─────────────────────────────────────────────────────────────┐
│                     测试规范速查                              │
├─────────────────────────────────────────────────────────────┤
│ 📁 单元测试前缀 (unit/)                                      │
│   • test_entity_  → 领域实体      • test_svc_    → 应用服务 │
│   • test_vo_      → 值对象        • test_dto_    → DTO 转换 │
│   • test_event_   → 域事件        • test_schema_ → Schema   │
│                                                             │
│ 📁 集成测试前缀 (integration/)                               │
│   • test_api_     → API 端点      • test_repo_   → 仓库实现 │
│                                                             │
│ 📁 特殊测试前缀                                              │
│   • test_arch_    → 架构合规      • test_perf_   → 性能测试 │
│   • test_e2e_     → E2E 场景      • test_aws_    → AWS 集成 │
├─────────────────────────────────────────────────────────────┤
│ 📂 文件放置位置                                              │
│   • 实体测试   → unit/{module}/test_entity_{name}.py        │
│   • 事件测试   → unit/{module}/test_event_{name}.py         │
│   • Schema测试 → unit/{module}/test_schema_{name}.py        │
│   • API 测试   → integration/{module}/test_api_{name}.py    │
├─────────────────────────────────────────────────────────────┤
│ 🏃 常用命令                                                  │
│   • pytest tests/unit -v           # 全部单元测试            │
│   • pytest -k "test_entity_"       # 所有实体测试            │
│   • pytest -k "test_event_"        # 所有事件测试            │
│   • pytest -k "test_schema_"       # 所有 Schema 测试        │
│   • pytest -k "test_arch_"         # 所有架构测试            │
│   • pytest --lf                    # 重跑失败               │
└─────────────────────────────────────────────────────────────┘
```
