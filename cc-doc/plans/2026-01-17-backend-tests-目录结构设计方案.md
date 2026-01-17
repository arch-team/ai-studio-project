# Backend Tests 目录结构设计方案

## 背景分析

### 现有项目架构
- **架构模式**: DDD + Modular Monolith + Clean Architecture
- **9 个业务模块**: auth, training, quotas, models, datasets, spaces, audit, billing, monitoring
- **每模块 4 层**: api → application → domain ← infrastructure
- **共享内核**: `src/shared/` (domain, infrastructure, api, utils)

### 当前测试结构问题

```
tests/
├── unit/
│   ├── domain/entities/      # ❌ 按层组织，不知道属于哪个模块
│   ├── domain/value_objects/
│   ├── application/services/
│   └── ...
```

**问题**:
1. 按层组织而非按模块 → 难以定位特定模块的测试
2. 违背 Modular Monolith 原则 → 模块边界不清晰
3. 测试文件增长后难以维护

---

## 推荐方案：模块优先 + 层级分离

### 设计原则

| 原则 | 说明 |
|------|------|
| **模块自治** | 每个模块的测试独立存放，与 `src/modules/` 结构镜像 |
| **层级对应** | 测试文件结构与源代码层级一一对应 |
| **共享复用** | 通用 fixtures 和工具集中在 `tests/shared/` |
| **级别分离** | unit/integration/e2e 在模块内部或根级别明确区分 |

### 推荐目录结构

```
backend/tests/
├── conftest.py                      # 全局 pytest 配置
├── pytest.ini                       # pytest 标记和路径配置 (可选，已有 pyproject.toml)
│
├── shared/                          # 📦 共享测试基础设施
│   ├── __init__.py
│   ├── conftest.py                 # 共享 fixtures 导出
│   ├── fixtures/                   # 可复用 fixtures
│   │   ├── __init__.py
│   │   ├── database.py             # 数据库 session fixtures
│   │   ├── auth.py                 # JWT、用户认证 fixtures
│   │   ├── factories.py            # 测试数据工厂 (Factory Boy)
│   │   └── mocks.py                # 通用 mock 对象
│   ├── helpers/                    # 测试辅助函数
│   │   ├── __init__.py
│   │   ├── assertions.py           # 自定义断言
│   │   ├── api_client.py           # API 测试客户端封装
│   │   └── async_utils.py          # 异步测试工具
│   └── constants.py                # 测试常量
│
├── unit/                            # 🧪 单元测试 (无外部依赖)
│   ├── conftest.py                 # 单元测试级别 fixtures
│   │
│   ├── modules/                    # 按模块组织
│   │   ├── auth/                   # auth 模块测试
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py         # auth 模块专属 fixtures
│   │   │   ├── domain/             # 领域层测试
│   │   │   │   ├── entities/
│   │   │   │   │   ├── test_user.py
│   │   │   │   │   └── test_login_attempt.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── test_user_role.py
│   │   │   │   │   └── test_permission.py
│   │   │   │   └── test_exceptions.py
│   │   │   ├── application/        # 应用层测试
│   │   │   │   └── services/
│   │   │   │       ├── test_auth_service.py
│   │   │   │       ├── test_password_service.py
│   │   │   │       └── test_rbac_service.py
│   │   │   └── api/                # API 层单元测试 (mock deps)
│   │   │       ├── test_endpoints.py
│   │   │       └── test_schemas.py
│   │   │
│   │   ├── training/               # training 模块测试
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── test_training_job.py
│   │   │   │   │   └── test_checkpoint.py
│   │   │   │   └── value_objects/
│   │   │   │       ├── test_job_status.py
│   │   │   │       └── test_distribution_strategy.py
│   │   │   ├── application/
│   │   │   │   └── services/
│   │   │   │       ├── test_training_job_service.py
│   │   │   │       └── test_checkpoint_service.py
│   │   │   └── api/
│   │   │       └── test_endpoints.py
│   │   │
│   │   ├── quotas/                 # quotas 模块测试
│   │   │   └── ...                 # 同上结构
│   │   │
│   │   ├── models/                 # models 模块测试
│   │   │   └── ...
│   │   │
│   │   ├── datasets/               # datasets 模块测试
│   │   │   └── ...
│   │   │
│   │   ├── spaces/                 # spaces 模块测试
│   │   │   └── ...
│   │   │
│   │   ├── audit/                  # audit 模块测试
│   │   │   └── ...
│   │   │
│   │   ├── billing/                # billing 模块测试
│   │   │   └── ...
│   │   │
│   │   └── monitoring/             # monitoring 模块测试
│   │       └── ...
│   │
│   └── shared/                     # shared 内核测试
│       ├── __init__.py
│       ├── domain/
│       │   ├── test_base_entity.py
│       │   ├── test_exceptions.py
│       │   └── test_events.py
│       ├── infrastructure/
│       │   ├── test_query_builder.py
│       │   └── security/
│       │       ├── test_jwt_manager.py
│       │       └── test_password_hasher.py
│       └── utils/
│           └── test_datetime_utils.py
│
├── integration/                     # 🔗 集成测试 (真实依赖)
│   ├── conftest.py                 # 集成测试 fixtures (真实 DB)
│   │
│   ├── modules/                    # 按模块组织
│   │   ├── auth/
│   │   │   ├── api/                # API 端点集成测试
│   │   │   │   └── test_auth_endpoints.py
│   │   │   └── persistence/        # 仓库实现测试
│   │   │       ├── test_user_repository.py
│   │   │       └── test_login_attempt_repository.py
│   │   │
│   │   ├── training/
│   │   │   ├── api/
│   │   │   │   └── test_training_job_endpoints.py
│   │   │   ├── persistence/
│   │   │   │   └── test_training_job_repository.py
│   │   │   └── external/           # 外部服务集成
│   │   │       └── test_hyperpod_client.py
│   │   │
│   │   └── ...                     # 其他模块
│   │
│   ├── cross_module/               # 跨模块集成测试
│   │   ├── test_quota_enforcement.py    # quotas ↔ training
│   │   ├── test_audit_logging.py        # audit ↔ all modules
│   │   └── test_event_propagation.py    # EventBus 集成
│   │
│   ├── middleware/                 # 中间件集成测试
│   │   ├── test_authentication_middleware.py
│   │   └── test_audit_middleware.py
│   │
│   └── database/                   # 数据库集成测试
│       ├── test_migrations.py
│       └── test_transaction_rollback.py
│
├── e2e/                             # 🎯 端到端测试
│   ├── conftest.py                 # E2E fixtures (完整应用)
│   │
│   ├── scenarios/                  # 用户场景测试
│   │   ├── test_user_registration_flow.py
│   │   ├── test_training_job_lifecycle.py
│   │   ├── test_dataset_upload_flow.py
│   │   └── test_checkpoint_recovery.py
│   │
│   └── aws/                        # AWS 集成 E2E
│       ├── README.md               # AWS 测试说明
│       ├── test_hyperpod_integration.py
│       └── test_s3_storage.py
│
├── performance/                     # ⚡ 性能测试 (可选)
│   ├── conftest.py
│   ├── test_api_latency.py
│   └── test_concurrent_training_jobs.py
│
└── architecture/                    # 🏗️ 架构合规测试
    └── test_architecture_compliance.py  # 分层依赖检查
```

---

## 核心设计详解

### 1. 测试文件命名规范

| 类型 | 命名模式 | 示例 |
|------|---------|------|
| 实体测试 | `test_{entity}.py` | `test_user.py`, `test_training_job.py` |
| 值对象测试 | `test_{value_object}.py` | `test_job_status.py` |
| 服务测试 | `test_{service}_service.py` | `test_auth_service.py` |
| API 端点测试 | `test_{feature}_endpoints.py` | `test_auth_endpoints.py` |
| 仓库测试 | `test_{entity}_repository.py` | `test_user_repository.py` |
| 场景测试 | `test_{scenario}_flow.py` | `test_training_job_lifecycle.py` |

### 2. conftest.py 层级职责

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

# tests/unit/modules/auth/conftest.py - 模块专属
@pytest.fixture
def sample_user(): ...
@pytest.fixture
def mock_user_repository(): ...

# tests/integration/conftest.py - 集成测试配置
@pytest.fixture(scope="module")
def test_database(): ...  # 真实数据库连接

# tests/e2e/conftest.py - E2E 配置
@pytest.fixture(scope="session")
def app_client(): ...  # 完整应用客户端
```

### 3. 测试工厂模式 (Factory Boy)

```python
# tests/shared/fixtures/factories.py
import factory
from src.modules.auth.domain.entities import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    username = factory.Faker('user_name')
    email = factory.Faker('email')
    role = UserRole.ENGINEER
    status = UserStatus.ACTIVE

class TrainingJobFactory(factory.Factory):
    class Meta:
        model = TrainingJob

    id = factory.Sequence(lambda n: n)
    name = factory.Faker('sentence', nb_words=3)
    status = JobStatus.SUBMITTED
    # ...
```

### 4. pytest 标记配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: 单元测试 (无外部依赖)",
    "integration: 集成测试 (需要数据库)",
    "e2e: 端到端测试 (完整应用)",
    "aws_integration: AWS 集成测试 (需要 AWS 凭证)",
    "slow: 耗时测试",
    "performance: 性能测试",
]
addopts = "-m 'not aws_integration and not slow'"
```

### 5. 测试运行命令

```bash
# 运行所有单元测试
pytest tests/unit -v

# 运行特定模块的单元测试
pytest tests/unit/modules/auth -v

# 运行集成测试
pytest tests/integration -v -m integration

# 运行 E2E 测试
pytest tests/e2e -v -m e2e

# 运行架构合规检查
pytest tests/architecture -v

# 运行完整测试套件 (排除 AWS 和慢速测试)
pytest tests/

# 运行 AWS 集成测试 (需要凭证)
pytest tests/ -m aws_integration

# 生成覆盖率报告
pytest tests/unit --cov=src --cov-report=html
```

---

## 迁移计划

### Phase 1: 创建新结构

1. 创建 `tests/shared/` 目录和基础 fixtures
2. 创建 `tests/unit/modules/` 和 `tests/integration/modules/` 骨架
3. 创建 `tests/architecture/` 并移动架构合规测试

### Phase 2: 迁移现有测试

1. 将 `tests/unit/domain/` 下的测试按模块拆分
2. 将 `tests/unit/application/` 下的测试按模块拆分
3. 将 `tests/integration/` 下的测试按模块重组
4. 更新所有 conftest.py 的 import 路径

### Phase 3: 验证和清理

1. 运行完整测试套件确保无回归
2. 删除旧目录结构
3. 更新 CI/CD 配置

---

## 关键文件清单

| 文件 | 用途 |
|------|------|
| `tests/conftest.py` | 全局 pytest 配置 |
| `tests/shared/fixtures/database.py` | 数据库 fixtures |
| `tests/shared/fixtures/auth.py` | 认证 fixtures |
| `tests/shared/fixtures/factories.py` | 测试数据工厂 |
| `tests/unit/modules/{module}/conftest.py` | 模块专属 fixtures |
| `tests/integration/conftest.py` | 集成测试数据库配置 |
| `tests/architecture/test_architecture_compliance.py` | 架构合规检查 |

---

## 验证方式

1. **测试发现**: `pytest --collect-only` 确认所有测试被发现
2. **模块隔离**: 单独运行各模块测试确认无交叉依赖
3. **CI 集成**: 更新 GitHub Actions 配置运行分层测试
4. **覆盖率**: 确保迁移后覆盖率不下降
