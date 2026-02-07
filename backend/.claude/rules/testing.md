# 测试规范 (Testing Standards)

> **职责**: 测试规范，定义 TDD 工作流、测试分层、前缀命名和 Fixture 模式。

---

## 0. 速查卡片

### 命令

```bash
pytest tests/unit -v              # 全部单元测试
pytest tests/integration -v       # 集成测试
pytest tests/architecture -v      # 架构合规检查
pytest --cov=src                  # 带覆盖率

# 按类型筛选
pytest -k "test_entity_" -v      # 所有实体测试
pytest -k "test_svc_" -v         # 所有服务测试
pytest -k "test_api_" -v         # 所有 API 测试

# 开发常用
pytest --lf                       # 重跑失败
pytest -x                         # 失败即停
```

### 文件前缀 → 测试对象

**单元测试 (unit/)**:

| 前缀 | 测试对象 | 示例 |
|------|---------|------|
| `test_entity_` | 领域实体 (状态转换、业务规则) | `test_entity_training_job.py` |
| `test_vo_` | 值对象 (不变性、验证规则) | `test_vo_job_status.py` |
| `test_event_` | 域事件 (创建、属性) | `test_event_job_completed.py` |
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

### 分层

| 层级 | 覆盖 | Mock | 速度 |
|------|------|------|------|
| Unit | Entity/Service | 外部依赖 | ms |
| Integration | API/Repo | 外部服务 | s |
| E2E | 完整流程 | 无 | min |

### 陷阱 ⚠️

- ❌ 创建无前缀的 `test_*.py` 文件
- ❌ 在 `unit/` 目录使用真实数据库
- ❌ Mock 被测对象 → ✅ 只 Mock 外部依赖
- ❌ 测试顺序依赖 → ✅ 每测试独立数据
- ❌ 伪造断言 → ✅ 修复代码

---

## 1. 目录结构

```
tests/
├── conftest.py                   # 全局 pytest 配置
├── shared/                       # 共享测试基础设施
│   ├── fixtures/                 # database.py, auth.py, mocks.py
│   ├── helpers/                  # assertions.py, async_utils.py
│   └── constants.py
├── unit/{module}/                # 单元测试 (无外部依赖)
│   ├── conftest.py
│   ├── test_entity_*.py
│   ├── test_vo_*.py
│   ├── test_svc_*.py
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

**目录深度**: 最大 4 层 (如 `unit/training/test_entity_training_job.py`)

---

## 2. 测试模式

**AAA 模式** (必须):

```python
async def test_create_user_returns_user(self) -> None:
    dto = CreateUserDTO(name="张三", email="a@b.com")  # Arrange
    result = await service.create_user(dto)             # Act
    assert result.name == "张三"                        # Assert
```

**参数化**: `@pytest.mark.parametrize("input,expected", [(val1, exp1), ...])`

**异常**: `with pytest.raises(ValidationError, match="名称不能为空"): ...`

**命名**: `test_{action}_{condition}_{expected_result}`
- `test_login_with_valid_credentials_returns_token`
- `test_create_user_with_duplicate_email_raises_error`

---

## 3. Mock 策略

**原则**: 只 Mock 边界 (Repo/外部 API/文件系统/时间)

| 测试类型 | Mock 对象 | 真实对象 |
|---------|----------|---------|
| 单元测试 | Repository 实现, JWT Manager, 外部 API Client | Entity, VO, Event |
| 集成测试 | AWS 服务 (HyperPod, S3, SQS) | 数据库, API 端点 |
| E2E 测试 | 无 | 全部 |

```python
mock_repo = AsyncMock(spec=IUserRepository)
mock_repo.save.return_value = user
service = UserService(repository=mock_repo)
# 验证: mock_repo.save.assert_called_once()
```

---

## 4. 断言规范

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

---

## 5. Fixture 规范

| 位置 | 职责 | Scope |
|------|------|-------|
| `tests/conftest.py` | 全局配置、事件循环 | session |
| `tests/shared/conftest.py` | 共享 fixtures | function |
| `tests/unit/{module}/conftest.py` | 模块专属 | function |
| `tests/integration/conftest.py` | 真实 DB 连接 | module |

**模式**: `yield` + 清理，Fixture 通过参数自动注入

---

## 6. 测试标记

| 标记 | 默认行为 |
|------|---------|
| `@pytest.mark.unit` | 自动添加 (路径含 `/unit/`) |
| `@pytest.mark.integration` | 自动添加 (路径含 `/integration/`) |
| `@pytest.mark.e2e` | 自动添加 |
| `@pytest.mark.architecture` | 自动添加 |
| `@pytest.mark.performance` | 默认跳过 |
| `@pytest.mark.aws_integration` | 默认跳过 |
| `@pytest.mark.slow` | 默认跳过 |

---

## 7. 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Domain | 95% | 100% |
| Application | 90% | 95% |
| Infrastructure | 80% | 85% |
| API | 80% | 85% |
| **整体** | **85%** | **90%** |

### 测试比例

- **Unit**: 70% | **Integration**: 20% | **E2E**: 10%

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §测试
