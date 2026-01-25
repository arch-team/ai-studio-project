"""Quotas domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。
"""

from dataclasses import dataclass

from src.shared.domain.problem import Problem, problem


@problem(404, "QUOTA_NOT_FOUND", "ResourceLimitConfig '{identifier}' not found")
@dataclass
class QuotaNotFoundError(Problem):
    """配额配置未找到."""

    identifier: str


@problem(429, "QUOTA_EXCEEDED", "{resource} quota exceeded: requested {requested}, limit {limit}")
@dataclass
class QuotaExceededError(Problem):
    """资源配额超限."""

    resource: str
    requested: int
    limit: int


@problem(
    409,
    "DUPLICATE_CONFIG",
    "ResourceLimitConfig with role='{role}', scope='{scope}' already exists",
)
@dataclass
class DuplicateConfigError(Problem):
    """配额配置重复."""

    role: str
    scope: str


# =============================================================================
# 向后兼容别名 (deprecated)
# =============================================================================

QuotaError = Problem
"""[DEPRECATED] 使用 Problem 替代."""
