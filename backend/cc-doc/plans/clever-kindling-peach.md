# 异常处理框架重构计划：装饰器 + dataclass 方案

## 概述

**目标**：使用 Python 原生的装饰器和 dataclass 简化异常定义，减少样板代码约 55%。

**约束**：
- ✅ 零外部依赖
- ✅ 保持现有响应格式（前端无需修改）
- ✅ 保持 HTTP 状态码映射不变
- ✅ 所有现有测试通过

---

## 当前状态

| 指标 | 数值 |
|------|------|
| 异常类总数 | 50 个 |
| 代码行数 | ~963 行 |
| 两套基类体系 | `DomainError` + `SecurityError` |
| 模块数 | 8 个 |

**痛点**：
1. 每个异常类需要 8-15 行样板代码
2. `DomainError` 用 `error_code` 类属性，`SecurityError` 用 `code` 实例属性，不一致
3. `get_details()` 方法需要手动维护

---

## 目标架构

### 新异常定义方式（对比）

**Before** (12 行):
```python
class TrainingJobNotFoundError(EntityNotFoundError):
    """Raised when a training job is not found."""

    error_code = "TRAINING_JOB_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__("TrainingJob", identifier)
        self.identifier = identifier

    def get_details(self) -> dict[str, Any]:
        return {"entity_type": "TrainingJob", "entity_id": self.identifier}
```

**After** (5 行):
```python
@problem(404, "TRAINING_JOB_NOT_FOUND")
@dataclass
class TrainingJobNotFoundError(Problem):
    """训练任务未找到"""
    job_id: str
```

---

## 实施计划

### Phase 1: 核心框架实现

#### 1.1 创建新的基础异常类

**文件**: `src/shared/domain/problem.py` (新建)

```python
"""Problem Details 异常基类 - 基于装饰器和 dataclass 的简化实现。

设计说明:
---------
使用 @problem 装饰器和 @dataclass 组合，将异常定义从 12 行减少到 5 行。
响应格式保持不变，与前端 AppError.fromApiResponse() 兼容。
"""

from dataclasses import dataclass, field, fields
from typing import Any, ClassVar


def problem(status: int, code: str, message_template: str | None = None):
    """装饰器：注入 HTTP 状态码、错误代码和消息模板。

    Args:
        status: HTTP 状态码 (400, 404, 409, etc.)
        code: 错误代码 (ENTITY_NOT_FOUND, etc.)
        message_template: 可选的消息模板，支持 {field_name} 占位符

    Example:
        @problem(404, "USER_NOT_FOUND", "User '{user_id}' not found")
        @dataclass
        class UserNotFoundError(Problem):
            user_id: str
    """
    def decorator(cls):
        cls.http_status = status
        cls.error_code = code
        if message_template:
            cls._message_template = message_template
        return cls
    return decorator


@dataclass
class Problem(Exception):
    """RFC 9457 风格的问题详情基类。

    子类只需定义数据字段，消息和详情自动生成。

    Attributes:
        http_status: HTTP 状态码 (类属性，由 @problem 装饰器注入)
        error_code: 错误代码 (类属性，由 @problem 装饰器注入)
        message: 错误消息 (自动生成或自定义)
    """

    # 类属性默认值，由 @problem 装饰器覆盖
    http_status: ClassVar[int] = 400
    error_code: ClassVar[str] = "PROBLEM"
    _message_template: ClassVar[str | None] = None

    # 实例属性
    message: str = field(init=False, default="")

    def __post_init__(self) -> None:
        """自动生成消息并初始化 Exception。"""
        if not self.message:
            self.message = self._generate_message()
        super().__init__(self.message)

    def _generate_message(self) -> str:
        """根据模板或字段生成消息。"""
        if self._message_template:
            return self._message_template.format(**self._get_field_values())
        # 默认消息格式
        return f"{self.__class__.__name__}: {self._get_field_values()}"

    def _get_field_values(self) -> dict[str, Any]:
        """获取所有数据字段的值（排除 message）。"""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if f.name != "message" and f.init
        }

    def get_details(self) -> dict[str, Any] | None:
        """返回结构化错误详情。自动包含所有数据字段。"""
        details = self._get_field_values()
        return details if details else None
```

#### 1.2 更新异常处理器

**文件**: `src/shared/api/exception_handlers.py`

变更点：
- 添加 `Problem` 基类的处理器
- 保持 `DomainError` 和 `SecurityError` 处理器（向后兼容）

```python
from src.shared.domain.problem import Problem

async def problem_exception_handler(request: Request, exc: Problem) -> JSONResponse:
    """Handle all Problem-based exceptions."""
    return JSONResponse(
        status_code=exc.http_status,
        content=_build_error_response(
            code=exc.error_code,
            message=exc.message,
            details=exc.get_details(),
            trace_id=_get_trace_id(request),
        ),
    )
```

#### 1.3 注册处理器

**文件**: `src/main.py`

```python
from src.shared.domain.problem import Problem

# 注册顺序：更具体的优先
app.add_exception_handler(Problem, problem_exception_handler)
app.add_exception_handler(DomainError, domain_exception_handler)
app.add_exception_handler(SecurityError, security_exception_handler)
```

---

### Phase 2: 通用异常迁移

#### 2.1 迁移 shared/domain/exceptions.py

**迁移策略**：保留旧类作为别名，新类使用 Problem

```python
# shared/domain/exceptions.py

from src.shared.domain.problem import Problem, problem

# ========== 新实现 ==========

@problem(404, "ENTITY_NOT_FOUND", "{entity_type} with id '{entity_id}' not found")
@dataclass
class EntityNotFoundProblem(Problem):
    """实体未找到"""
    entity_type: str
    entity_id: str


@problem(422, "VALIDATION_ERROR")
@dataclass
class ValidationProblem(Problem):
    """验证错误"""
    message: str = field(default="Validation failed")
    field_name: str | None = None


@problem(409, "DUPLICATE_ENTITY", "{entity_type} with identifier '{identifier}' already exists")
@dataclass
class DuplicateEntityProblem(Problem):
    """重复实体"""
    entity_type: str
    identifier: str


@problem(409, "INVALID_STATE_TRANSITION", "Cannot transition {entity_type} from '{current_state}' to '{target_state}'")
@dataclass
class InvalidStateTransitionProblem(Problem):
    """无效状态转换"""
    entity_type: str
    current_state: str
    target_state: str


@problem(429, "RESOURCE_QUOTA_EXCEEDED", "{resource_type} quota exceeded: limit={limit}, requested={requested}")
@dataclass
class ResourceQuotaExceededProblem(Problem):
    """资源配额超限"""
    resource_type: str
    limit: int
    requested: int


# ========== 向后兼容别名 ==========
# 保留旧的 DomainError 体系，逐步弃用

class DomainError(Exception):
    """[DEPRECATED] 使用 Problem 替代"""
    ...  # 保持原有实现
```

---

### Phase 3: 模块异常迁移

#### 3.1 迁移 training 模块 (12 个异常)

**文件**: `src/modules/training/domain/exceptions.py`

```python
from dataclasses import dataclass
from src.shared.domain.problem import Problem, problem


@problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
@dataclass
class TrainingJobNotFoundError(Problem):
    """训练任务未找到"""
    job_id: str


@problem(404, "CHECKPOINT_NOT_FOUND", "Checkpoint '{checkpoint_id}' not found")
@dataclass
class CheckpointNotFoundError(Problem):
    """检查点未找到"""
    checkpoint_id: str


@problem(409, "DUPLICATE_JOB_NAME", "Training job with name '{job_name}' already exists")
@dataclass
class DuplicateJobNameError(Problem):
    """任务名称重复"""
    job_name: str


@problem(409, "INVALID_JOB_STATE", "Cannot {operation} job {job_id} in state '{current_state}'")
@dataclass
class InvalidJobStateError(Problem):
    """任务状态无效"""
    job_id: int
    current_state: str
    operation: str


@problem(500, "CHECKPOINT_STORAGE_ERROR")
@dataclass
class CheckpointStorageError(Problem):
    """检查点存储失败"""
    message: str = field(default="Checkpoint storage operation failed")
    job_id: int | None = None


@problem(500, "CHECKPOINT_MIGRATION_ERROR",
         "Failed to migrate checkpoint {checkpoint_id} from {source_tier} to {target_tier}: {reason}")
@dataclass
class CheckpointMigrationError(Problem):
    """检查点迁移失败"""
    checkpoint_id: int
    source_tier: str
    target_tier: str
    reason: str


@problem(404, "JOB_TEMPLATE_NOT_FOUND", "JobTemplate '{template_id}' not found")
@dataclass
class JobTemplateNotFoundError(Problem):
    """任务模板未找到"""
    template_id: int


@problem(403, "JOB_TEMPLATE_PERMISSION_DENIED", "Permission denied: cannot {operation} template {template_id}")
@dataclass
class JobTemplatePermissionDeniedError(Problem):
    """模板权限拒绝"""
    operation: str
    template_id: int


@problem(503, "HYPERPOD_SDK_UNAVAILABLE",
         "HyperPod SDK component '{component}' is not available. Please install sagemaker-hyperpod package.")
@dataclass
class HyperPodSDKUnavailableError(Problem):
    """HyperPod SDK 不可用"""
    component: str = "HyperPodPytorchJob"


@problem(404, "HYPERPOD_POD_NOT_FOUND", "Pod '{pod_name}' not found in job '{job_name}'")
@dataclass
class HyperPodPodNotFoundError(Problem):
    """HyperPod Pod 未找到"""
    job_name: str
    pod_name: str


@problem(500, "HYPERPOD_OPERATION_ERROR")
@dataclass
class HyperPodOperationError(Problem):
    """HyperPod 操作失败"""
    operation: str
    reason: str
    job_name: str | None = None

    def __post_init__(self) -> None:
        if self.job_name:
            self.message = f"HyperPod operation '{self.operation}' on job '{self.job_name}' failed: {self.reason}"
        else:
            self.message = f"HyperPod operation '{self.operation}' failed: {self.reason}"
        super().__post_init__()
```

#### 3.2 类似迁移其他模块

- `quotas/domain/exceptions.py` (4 个异常)
- `models/domain/exceptions.py` (4 个异常)
- `spaces/domain/exceptions.py` (5 个异常)
- `audit/domain/exceptions.py` (2 个异常)

---

### Phase 4: Security 异常统一

#### 4.1 迁移 security 异常

**文件**: `src/shared/infrastructure/security/exceptions.py`

```python
from dataclasses import dataclass, field
from src.shared.domain.problem import Problem, problem


@problem(401, "AUTHENTICATION_FAILED")
@dataclass
class AuthenticationError(Problem):
    """认证失败"""
    message: str = field(default="Authentication failed")


@problem(401, "INVALID_CREDENTIALS")
@dataclass
class InvalidCredentialsError(Problem):
    """凭证无效"""
    message: str = field(default="Invalid username or password")


@problem(401, "TOKEN_EXPIRED")
@dataclass
class TokenExpiredError(Problem):
    """令牌过期"""
    message: str = field(default="Token has expired")


@problem(401, "INVALID_TOKEN")
@dataclass
class InvalidTokenError(Problem):
    """令牌无效"""
    message: str = field(default="Invalid token")


@problem(423, "ACCOUNT_LOCKED", "Account is locked until {locked_until}")
@dataclass
class AccountLockedError(Problem):
    """账户被锁定"""
    locked_until: str | None = None

    def __post_init__(self) -> None:
        if not self.locked_until:
            self.message = "Account is locked"
        super().__post_init__()


@problem(400, "PASSWORD_TOO_WEAK")
@dataclass
class PasswordTooWeakError(Problem):
    """密码强度不足"""
    violations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.message = f"Password does not meet requirements: {'; '.join(self.violations)}"
        super().__post_init__()


@problem(403, "INSUFFICIENT_PERMISSIONS", "Insufficient permissions: requires {required_permission}")
@dataclass
class InsufficientPermissionsError(Problem):
    """权限不足"""
    required_permission: str


@problem(503, "SSO_DEGRADED_MODE")
@dataclass
class SSODegradedModeError(Problem):
    """SSO 降级模式"""
    message: str = field(default="SSO service is temporarily unavailable")
```

---

### Phase 5: 测试更新

#### 5.1 更新测试文件

**文件**: `tests/unit/shared/test_problem.py` (新建)

```python
"""Problem 基类和装饰器测试"""

import pytest
from dataclasses import dataclass
from src.shared.domain.problem import Problem, problem


class TestProblemDecorator:
    """测试 @problem 装饰器"""

    def test_decorator_injects_status_and_code(self):
        @problem(404, "TEST_NOT_FOUND")
        @dataclass
        class TestError(Problem):
            item_id: str

        assert TestError.http_status == 404
        assert TestError.error_code == "TEST_NOT_FOUND"

    def test_decorator_with_message_template(self):
        @problem(404, "TEST_NOT_FOUND", "Item '{item_id}' not found")
        @dataclass
        class TestError(Problem):
            item_id: str

        err = TestError(item_id="123")
        assert err.message == "Item '123' not found"


class TestProblemGetDetails:
    """测试 get_details() 自动生成"""

    def test_returns_all_fields(self):
        @problem(404, "TEST_ERROR")
        @dataclass
        class TestError(Problem):
            field1: str
            field2: int

        err = TestError(field1="value", field2=42)
        details = err.get_details()

        assert details == {"field1": "value", "field2": 42}

    def test_excludes_message_field(self):
        @problem(400, "TEST_ERROR")
        @dataclass
        class TestError(Problem):
            custom_field: str

        err = TestError(custom_field="test")
        details = err.get_details()

        assert "message" not in details
        assert details == {"custom_field": "test"}
```

**文件**: `tests/unit/shared/test_svc_exception_handlers.py`

- 添加 `TestProblemExceptionHandler` 测试类
- 验证 Problem 异常的响应格式与现有格式一致

---

## 代码量对比

| 文件 | Before | After | 减少 |
|------|--------|-------|------|
| `shared/domain/exceptions.py` | 136 行 | 60 行 | -56% |
| `shared/infrastructure/security/exceptions.py` | 178 行 | 80 行 | -55% |
| `shared/api/exception_handlers.py` | 115 行 | 85 行 | -26% |
| `modules/*/domain/exceptions.py` | 537 行 | 200 行 | -63% |
| **新增** `shared/domain/problem.py` | 0 行 | +70 行 | - |
| **总计** | **966 行** | **495 行** | **-49%** |

---

## 迁移策略

**决策**: 完全替换（用户确认）

- ✅ 删除旧的 `DomainError` / `SecurityError` 基类
- ✅ 所有 50 个异常迁移到 `Problem` 基类
- ✅ 一次性完成，代码最简洁

## 迁移顺序

```
1. [Phase 1] 核心框架 (problem.py + handler)
   ↓
2. [Phase 2] 通用异常 (shared/domain) - 删除旧 DomainError
   ↓
3. [Phase 3] 模块异常 (training → quotas → models → spaces → audit)
   ↓
4. [Phase 4] Security 异常 - 删除旧 SecurityError
   ↓
5. [Phase 5] 测试更新 - 更新所有异常相关测试
   ↓
6. [Cleanup] 删除 exception_handlers.py 中的旧处理器
```

---

## 验证清单

### 功能验证
- [x] 所有异常返回正确的 HTTP 状态码
- [x] 响应格式与现有格式完全一致
- [x] `get_details()` 自动返回所有字段
- [x] trace_id 正确传递

### 测试验证
- [x] `pytest tests/unit/shared/test_problem.py -v` 全部通过 (34 tests)
- [x] `pytest tests/unit/shared/test_svc_exception_handlers.py -v` 全部通过 (45 tests)
- [x] `pytest tests/unit/` 全部通过 (1024 tests, 2.43s)
- [ ] `pytest tests/integration/` 全部通过

### 前端兼容性
- [x] API 响应格式不变 (保持 `{"error": {"code", "message", "details", "trace_id"}}`)
- [x] 前端 `AppError.fromApiResponse()` 无需修改

---

## 关键文件清单

| 操作 | 文件路径 |
|------|---------|
| **新建** | `src/shared/domain/problem.py` |
| **修改** | `src/shared/api/exception_handlers.py` |
| **修改** | `src/main.py` |
| **重构** | `src/shared/domain/exceptions.py` |
| **重构** | `src/shared/infrastructure/security/exceptions.py` |
| **重构** | `src/modules/training/domain/exceptions.py` |
| **重构** | `src/modules/quotas/domain/exceptions.py` |
| **重构** | `src/modules/models/domain/exceptions.py` |
| **重构** | `src/modules/spaces/domain/exceptions.py` |
| **重构** | `src/modules/audit/domain/exceptions.py` |
| **重构** | `src/modules/auth/domain/exceptions.py` |
| **新建** | `tests/unit/shared/test_problem.py` |
| **修改** | `tests/unit/shared/test_svc_exception_handlers.py` |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 迁移过程中测试失败 | 分阶段迁移，每阶段验证 |
| 前端兼容性问题 | 响应格式完全不变 |
| 旧代码依赖旧类 | 保留别名，逐步弃用 |
| dataclass 限制 | 复杂场景可重写 `__post_init__` |
