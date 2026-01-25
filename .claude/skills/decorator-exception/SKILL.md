---
name: decorator-exception
description: 使用 @problem 装饰器 + @dataclass 简化 FastAPI/DDD 异常定义，减少 60% 代码量
---

# 基于装饰器的异常定义框架

**提取日期:** 2025-01-25
**来源:** backend/src/shared/domain/problem.py
**上下文:** FastAPI + DDD 架构中需要统一的异常处理和 HTTP 状态码映射

## 问题

传统的异常定义方式冗长且容易出错：

```python
# ❌ 传统方式：12+ 行代码
class UserNotFoundError(DomainError):
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.http_status = 404
        self.error_code = "USER_NOT_FOUND"
        super().__init__(f"User '{user_id}' not found")

    def get_details(self) -> dict:
        return {"user_id": self.user_id}
```

问题：
- 每个异常类都要重复定义 `__init__`、`http_status`、`error_code`、`get_details()`
- 容易忘记某个字段
- 消息模板和字段不同步时难以发现

## 解决方案

使用 `@problem` 装饰器 + `@dataclass` 组合：

```python
# ✅ 新方式：5 行代码
from dataclasses import dataclass
from src.shared.domain.problem import Problem, problem

@problem(404, "USER_NOT_FOUND", "User '{user_id}' not found")
@dataclass
class UserNotFoundError(Problem):
    """用户未找到."""
    user_id: str
```

### 装饰器实现

```python
def problem(status: int, code: str, message_template: str | None = None):
    """装饰器：注入 HTTP 状态码、错误代码和消息模板。"""
    def decorator(cls):
        cls.http_status = status
        cls.error_code = code
        if message_template:
            cls._message_template = message_template
        return cls
    return decorator


@dataclass(kw_only=True)
class Problem(Exception):
    """RFC 9457 风格的问题详情基类。"""

    http_status: ClassVar[int] = 400
    error_code: ClassVar[str] = "PROBLEM"
    _message_template: ClassVar[str | None] = None
    message: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if not self.message:
            self.message = self._generate_message()
        super().__init__(self.message)

    def _generate_message(self) -> str:
        if self._message_template:
            return self._message_template.format(**self._get_field_values())
        # 默认：类名 + 字段值
        field_values = self._get_field_values()
        if field_values:
            return f"{self.__class__.__name__}: {', '.join(f'{k}={v!r}' for k, v in field_values.items())}"
        return self.__class__.__name__

    def get_details(self) -> dict[str, Any] | None:
        """自动返回所有数据字段。"""
        details = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "message"}
        return details if details else None
```

### 使用示例

```python
# 定义异常
@problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
@dataclass
class TrainingJobNotFoundError(Problem):
    job_id: str

@problem(409, "INVALID_STATE_TRANSITION",
         "Cannot transition {entity_type} from '{current_state}' to '{target_state}'")
@dataclass
class InvalidStateTransitionError(Problem):
    entity_type: str
    current_state: str
    target_state: str

# 使用异常
raise TrainingJobNotFoundError(job_id="job-123")
# → message: "TrainingJob 'job-123' not found"
# → http_status: 404
# → error_code: "TRAINING_JOB_NOT_FOUND"
# → get_details(): {"job_id": "job-123"}
```

### 异常处理器集成

```python
# FastAPI 异常处理器
@app.exception_handler(Problem)
async def problem_exception_handler(request: Request, exc: Problem):
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.get_details(),
            }
        }
    )
```

## 何时使用

**适用场景:**
- FastAPI/Flask 等 Web 框架的异常处理
- DDD 架构中的领域异常定义
- 需要统一 HTTP 状态码映射的 API 项目
- 需要结构化错误响应（RFC 9457 Problem Details）

**关键优势:**
1. 代码量减少 60%（12 行 → 5 行）
2. 消息模板与字段自动同步
3. `get_details()` 自动生成，无需手动维护
4. 类型安全（dataclass 提供类型检查）
5. 符合 RFC 9457 Problem Details 标准

**注意事项:**
- 基类必须使用 `kw_only=True`，否则子类的非默认字段会报错
- 消息模板中的占位符必须与字段名匹配
