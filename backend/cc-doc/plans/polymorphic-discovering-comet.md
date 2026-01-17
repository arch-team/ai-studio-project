# 测试规范文档制定计划

## 目标

创建 `backend/tests/CLAUDE.md` 测试规范文档。

## 输出文件

`backend/tests/CLAUDE.md`

---

# 以下为规范文档完整内容

```markdown
# Backend Tests 规范指南

> **版本**: 1.0
> **最后更新**: 2025-01-17
> **架构模式**: 模块优先 + 层级分离

本文档是后端测试的**规范单一真实源 (Single Source of Truth)**。所有测试相关决策应以本文档为准。

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
| **模块自治** | 每个模块的测试独立存放，与 `src/modules/` 结构镜像 |
| **层级对应** | 测试文件结构与源代码层级一一对应 |
| **共享复用** | 通用 fixtures 和工具集中在 `tests/shared/` |
| **级别分离** | unit/integration/e2e 在模块内部或根级别明确区分 |
| **测试诚信** | 切勿为让测试通过而伪造结果，测试失败 = 代码有问题 |

---

## 2. 目录结构规范

### 2.1 完整目录结构

```
backend/tests/
├── conftest.py                      # 全局 pytest 配置
│
├── shared/                          # 📦 共享测试基础设施
│   ├── conftest.py                 # 共享 fixtures 导出
│   ├── fixtures/                   # 可复用 fixtures
│   │   ├── database.py             # 数据库 session fixtures
│   │   ├── auth.py                 # JWT、用户认证 fixtures
│   │   └── mocks.py                # 通用 mock 对象
│   ├── helpers/                    # 测试辅助函数
│   │   ├── assertions.py           # 自定义断言
│   │   ├── api_client.py           # API 测试客户端封装
│   │   └── async_utils.py          # 异步测试工具
│   └── constants.py                # 测试常量
│
├── unit/                            # 🧪 单元测试 (无外部依赖)
│   ├── conftest.py                 # 单元测试级别 fixtures
│   ├── modules/                    # 按模块组织
│   │   ├── auth/
│   │   │   ├── conftest.py         # auth 模块专属 fixtures
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   └── value_objects/
│   │   │   ├── application/
│   │   │   │   └── services/
│   │   │   └── api/
│   │   ├── training/
│   │   ├── quotas/
│   │   ├── models/
│   │   ├── datasets/
│   │   ├── spaces/
│   │   ├── audit/
│   │   ├── billing/
│   │   └── monitoring/
│   └── shared/                     # shared 内核测试
│       ├── domain/
│       ├── infrastructure/
│       └── utils/
│
├── integration/                     # 🔗 集成测试 (真实依赖)
│   ├── conftest.py                 # 集成测试 fixtures (真实 DB)
│   ├── modules/                    # 按模块组织
│   │   ├── auth/
│   │   │   ├── api/                # API 端点集成测试
│   │   │   ├── persistence/        # 仓库实现测试
│   │   │   └── external/           # 外部服务集成
│   │   └── ...
│   ├── cross_module/               # 跨模块集成测试
│   ├── middleware/                 # 中间件集成测试
│   └── database/                   # 数据库集成测试
│
├── e2e/                             # 🎯 端到端测试
│   ├── conftest.py                 # E2E fixtures (完整应用)
│   ├── scenarios/                  # 用户场景测试
│   └── aws/                        # AWS 集成 E2E
│
├── architecture/                    # 🏗️ 架构合规测试
│   └── test_architecture_compliance.py
│
└── performance/                     # ⚡ 性能测试
    └── conftest.py
```

### 2.2 各目录职责

| 目录 | 职责 | 外部依赖 |
|------|------|---------|
| `shared/` | 共享 fixtures、helpers、constants | 无 |
| `unit/` | 领域逻辑、服务逻辑测试 | 无（全部 mock） |
| `integration/` | API 端点、仓库实现、中间件 | 数据库、外部服务 |
| `e2e/` | 完整用户流程 | 完整应用 |
| `architecture/` | 架构规则合规检查 | 无 |
| `performance/` | 性能基准测试 | 完整应用 |

### 2.3 文件命名规范

| 类型 | 命名模式 | 示例 |
|------|---------|------|
| 实体测试 | `test_{entity}.py` | `test_user.py`, `test_training_job.py` |
| 值对象测试 | `test_{value_object}.py` | `test_job_status.py` |
| 服务测试 | `test_{service}_service.py` | `test_auth_service.py` |
| API 端点测试 | `test_{feature}_endpoints.py` | `test_auth_endpoints.py` |
| 仓库测试 | `test_{entity}_repository.py` | `test_user_repository.py` |
| 场景测试 | `test_{scenario}_flow.py` | `test_training_job_lifecycle.py` |

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

| 层级 | 位置 | 测试对象 | Mock 策略 |
|------|------|---------|----------|
| **Unit** | `tests/unit/modules/{module}/domain/` | 实体、值对象、域逻辑 | 无依赖，纯函数 |
| **Unit** | `tests/unit/modules/{module}/application/` | 应用服务 | Mock 仓库接口 |
| **Integration** | `tests/integration/modules/{module}/api/` | API 端点 | Mock 外部服务 |
| **Integration** | `tests/integration/modules/{module}/persistence/` | 仓库实现 | 真实数据库 |
| **E2E** | `tests/e2e/scenarios/` | 完整用户流程 | 真实应用 |
| **Architecture** | `tests/architecture/` | 架构规则 | 静态分析 |

### 3.3 测试比例建议

- **Unit Tests**: 70%
- **Integration Tests**: 20%
- **E2E Tests**: 10%

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

# tests/unit/modules/{module}/conftest.py - 模块专属
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
pytest tests/unit/modules/auth -v

# 运行集成测试
pytest tests/integration -v

# 运行架构合规检查
pytest tests/architecture -v

# 运行 E2E 测试
pytest tests/e2e -v

# 运行完整测试套件（排除默认跳过的测试）
pytest tests/

# 运行 AWS 集成测试（需要凭证）
pytest tests/ -m aws_integration

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
┌────────────────────────────────────────────────────────┐
│                  测试规范速查                           │
├────────────────────────────────────────────────────────┤
│ 📁 新测试文件放置位置                                   │
│   • 领域实体测试 → unit/modules/{module}/domain/entities/│
│   • 服务测试 → unit/modules/{module}/application/services/│
│   • API 测试 → integration/modules/{module}/api/        │
│   • 仓库测试 → integration/modules/{module}/persistence/ │
├────────────────────────────────────────────────────────┤
│ 📝 命名规范                                            │
│   • 文件: test_{feature}.py                            │
│   • 类: Test{Feature}{Aspect}                          │
│   • 函数: test_{action}_{condition}_{result}           │
├────────────────────────────────────────────────────────┤
│ 🔧 Fixture 使用                                        │
│   • 共享 fixtures → tests/shared/fixtures/              │
│   • 模块 fixtures → tests/unit/modules/{module}/conftest.py │
│   • 数据库 fixtures → tests/integration/conftest.py     │
├────────────────────────────────────────────────────────┤
│ 🏃 常用命令                                            │
│   • pytest tests/unit -v           # 单元测试          │
│   • pytest tests/unit/modules/auth # 模块测试          │
│   • pytest -k "test_login"         # 名称匹配          │
│   • pytest --lf                    # 重跑失败          │
│   • pytest -x                      # 失败即停          │
└────────────────────────────────────────────────────────┘
```
```
