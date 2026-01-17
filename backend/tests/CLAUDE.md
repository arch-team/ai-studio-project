# Backend Tests 规范指南

> **版本**: 1.6 | **更新**: 2025-01-17 | **架构**: 扁平模块 + 类型前缀命名
> **继承**: `backend/CLAUDE.md` (TDD 工作流、代码风格)

本文档是后端测试的**规范单一真实源**。所有测试相关决策应以本文档为准。

---

## AI 指令

> **过渡警告**: 存在遗留嵌套结构 (`unit/modules/auth/domain/`)，新测试**必须**遵循本规范的扁平结构。

### 创建测试时
1. **选前缀**: 根据被测对象类型选择前缀 (见速查表)
2. **放对位置**: 纯逻辑 → `unit/`, 需数据库 → `integration/`
3. **用 AAA**: Arrange (准备) → Act (执行) → Assert (验证)
4. **函数命名**: `test_{action}_{condition}_{expected_result}`
   - `test_login_with_valid_credentials_returns_token`
   - `test_create_user_with_duplicate_email_raises_error`
5. **类命名**: 按功能分组
   - `TestUserCreation`, `TestUserStateTransitions`
6. **复用优先**: 优先使用 `shared/fixtures/` 中的已有 fixture

### Mock 策略
| 测试类型 | Mock 对象 | 真实对象 |
|---------|----------|---------|
| 单元测试 | Repository 实现, JWT Manager, 外部 API Client | Entity, VO, Event |
| 集成测试 | AWS 服务 (HyperPod, S3, SQS) | 数据库, API 端点 |
| E2E 测试 | 无 | 全部 |

### 断言规范
```python
# ✅ 具体断言
assert user.status == UserStatus.ACTIVE
assert response.status_code == 200
assert "email" in error_detail

# ❌ 模糊断言
assert user is not None
assert response.ok
assert result  # bool 转换
```

### 禁止事项
- ❌ 创建无前缀的 `test_*.py` 文件
- ❌ 在 `unit/` 目录使用真实数据库
- ❌ Mock 被测试的类本身
- ❌ Mock 简单的数据类
- ❌ 为让测试通过而伪造结果 (测试失败 = 代码有问题)

---

## 速查表

### 文件前缀 → 测试对象

**单元测试 (unit/)**:
| 前缀 | 测试对象 | 示例 |
|------|---------|------|
| `test_entity_` | 领域实体 (状态转换、业务规则) | `test_entity_training_job.py` |
| `test_vo_` | 值对象 (不变性、验证规则) | `test_vo_job_status.py` |
| `test_event_` | 域事件 (创建、属性、序列化) | `test_event_job_completed.py` |
| `test_svc_` | 应用服务 (用例编排) | `test_svc_training.py` |
| `test_dto_` | DTO (Entity ↔ DTO 转换) | `test_dto_training_job.py` |
| `test_schema_` | Pydantic Schema (请求验证) | `test_schema_training.py` |

**集成测试 (integration/)**:
| 前缀 | 测试对象 | 示例 |
|------|---------|------|
| `test_api_` | API 端点 (HTTP 请求/响应) | `test_api_training.py` |
| `test_repo_` | 仓库实现 (CRUD、查询) | `test_repo_training_job.py` |

**特殊测试**:
| 前缀 | 适用目录 | 测试内容 |
|------|---------|---------|
| `test_arch_` | `architecture/` | 架构合规检查 |
| `test_e2e_` | `e2e/scenarios/` | 端到端用户流程 |
| `test_aws_` | `e2e/aws/` | AWS 服务集成 |
| `test_perf_` | `performance/` | 性能基准测试 |

### 常用命令

```bash
# 按类型运行
pytest tests/unit -v              # 全部单元测试
pytest -k "test_entity_" -v       # 所有实体测试
pytest -k "test_svc_" -v          # 所有服务测试
pytest -k "test_arch_" -v         # 所有架构测试

# 开发常用
pytest --lf                       # 重跑失败
pytest -x                         # 失败即停
pytest tests/unit --cov=src       # 带覆盖率
```

---

## 目录结构

```
backend/tests/
├── conftest.py                   # 全局 pytest 配置
├── shared/                       # 共享测试基础设施
│   ├── fixtures/                 # database.py, auth.py, mocks.py
│   ├── helpers/                  # assertions.py, async_utils.py
│   └── constants.py
├── unit/{module}/                # 单元测试 (无外部依赖)
│   ├── conftest.py
│   ├── test_entity_*.py
│   ├── test_vo_*.py
│   ├── test_event_*.py
│   ├── test_svc_*.py
│   ├── test_dto_*.py
│   └── test_schema_*.py
├── integration/{module}/         # 集成测试 (真实 DB)
│   ├── test_api_*.py
│   └── test_repo_*.py
├── e2e/                          # 端到端测试
│   ├── scenarios/test_e2e_*.py
│   └── aws/test_aws_*.py
├── architecture/test_arch_*.py   # 架构合规
└── performance/test_perf_*.py    # 性能测试
```

**目录深度**: 最大 4 层 (如 `unit/auth/test_entity_user.py`)

---

## 测试分层

### 单元测试覆盖范围

| 组件 | 单测 | 原因 |
|------|:----:|------|
| Entity | ✅ | 核心业务逻辑，状态转换复杂 |
| Value Object | ✅ | 验证规则、不变性保证 |
| Domain Event | ✅ | 事件驱动架构核心 |
| Application Service | ✅ | 用例编排，验证调用顺序 |
| DTO | ✅ | 转换逻辑易出错 |
| Pydantic Schema | ✅ | 复杂验证规则 |
| Domain Service | ❌ | 逻辑简单，集成测试覆盖 |
| Repository 接口 | ❌ | 接口无逻辑，测试实现即可 |

### 测试比例
- **Unit**: 70% | **Integration**: 20% | **E2E**: 10%

---

## Fixture 规范

### conftest.py 层级

| 位置 | 职责 | Scope | 使用场景 |
|------|------|-------|---------|
| `tests/conftest.py` | 全局配置、事件循环 | session | 整个测试会话共享 |
| `tests/shared/conftest.py` | 共享 fixtures | function | 每个测试独立 |
| `tests/unit/{module}/conftest.py` | 模块专属 | function | 模块内复用 |
| `tests/integration/conftest.py` | 真实 DB 连接 | module | 同文件共享连接 |

### 使用方式

```python
# Fixture 通过参数自动注入 (无需手动调用)
async def test_create_user(mock_user_repository, sample_user):
    service = UserService(repository=mock_user_repository)
    result = await service.create(sample_user)
    assert result.id is not None
```

---

## 测试标记

| 标记 | 默认行为 |
|------|---------|
| `@pytest.mark.unit` | 自动添加 (路径含 `/unit/`) |
| `@pytest.mark.integration` | 自动添加 (路径含 `/integration/`) |
| `@pytest.mark.e2e` | 自动添加 |
| `@pytest.mark.architecture` | 自动添加 |
| `@pytest.mark.performance` | 默认跳过 |
| `@pytest.mark.aws_integration` | 默认跳过 |
| `@pytest.mark.slow` | 默认跳过 |
