"""Problem Details 异常基类 - 基于装饰器和 dataclass 的简化实现。

设计说明:
---------
使用 @problem 装饰器和 @dataclass 组合，将异常定义从 12 行减少到 5 行。
响应格式保持不变，与前端 AppError.fromApiResponse() 兼容。

使用示例:
--------
@problem(404, "USER_NOT_FOUND", "User '{user_id}' not found")
@dataclass
class UserNotFoundError(Problem):
    user_id: str

# 创建异常
raise UserNotFoundError(user_id="123")
# message: "User '123' not found"
# get_details(): {"user_id": "123"}

迁移策略:
--------
完全替换旧的 DomainError / SecurityError 体系，所有异常迁移到 Problem 基类。
"""

from dataclasses import dataclass, field, fields
from typing import Any, ClassVar


def problem(status: int, code: str, message_template: str | None = None):
    """装饰器：注入 HTTP 状态码、错误代码和消息模板。

    Args:
        status: HTTP 状态码 (400, 401, 403, 404, 409, 422, 429, 500, 503, etc.)
        code: 错误代码 (ENTITY_NOT_FOUND, VALIDATION_ERROR, etc.)
        message_template: 可选的消息模板，支持 {field_name} 占位符

    Example:
        @problem(404, "USER_NOT_FOUND", "User '{user_id}' not found")
        @dataclass
        class UserNotFoundError(Problem):
            user_id: str

        err = UserNotFoundError(user_id="123")
        # err.message == "User '123' not found"
        # err.http_status == 404
        # err.error_code == "USER_NOT_FOUND"
    """
    def decorator(cls):
        cls.http_status = status
        cls.error_code = code
        if message_template:
            cls._message_template = message_template
        return cls
    return decorator


@dataclass(kw_only=True)
class Problem(Exception):
    """RFC 9457 风格的问题详情基类。

    子类只需定义数据字段，消息和详情自动生成。

    Attributes:
        http_status: HTTP 状态码 (类属性，由 @problem 装饰器注入)
        error_code: 错误代码 (类属性，由 @problem 装饰器注入)
        message: 错误消息 (自动生成或自定义)

    Example:
        @problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
        @dataclass
        class TrainingJobNotFoundError(Problem):
            job_id: str

        # 使用时:
        raise TrainingJobNotFoundError(job_id="job-123")

    Note:
        基类使用 kw_only=True，确保子类可以定义非默认字段。
        子类在使用 @dataclass 装饰器时不需要指定 kw_only。
    """

    # 类属性默认值，由 @problem 装饰器覆盖
    http_status: ClassVar[int] = 400
    error_code: ClassVar[str] = "PROBLEM"
    _message_template: ClassVar[str | None] = None

    # 实例属性：允许手动传入 message 覆盖自动生成的消息
    # 使用 kw_only=True 确保这个默认字段不影响子类的非默认字段
    message: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        """自动生成消息并初始化 Exception。"""
        if not self.message:
            self.message = self._generate_message()
        super().__init__(self.message)

    def _generate_message(self) -> str:
        """根据模板或字段生成消息。"""
        if self._message_template:
            try:
                return self._message_template.format(**self._get_field_values())
            except KeyError:
                # 模板中的占位符在字段中找不到，使用默认格式
                pass
        # 默认消息格式：类名 + 字段值
        field_values = self._get_field_values()
        if field_values:
            field_str = ", ".join(f"{k}={v!r}" for k, v in field_values.items())
            return f"{self.__class__.__name__}: {field_str}"
        return self.__class__.__name__

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
