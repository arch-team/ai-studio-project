"""Audit module domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。
"""

from dataclasses import dataclass

from src.shared.domain.problem import Problem, problem


@problem(404, "AUDIT_LOG_NOT_FOUND", "Audit log with id '{audit_log_id}' not found")
@dataclass
class AuditLogNotFoundError(Problem):
    """审计日志未找到."""

    audit_log_id: int


# =============================================================================
# 向后兼容别名 (deprecated)
# =============================================================================

AuditLogError = Problem
"""[DEPRECATED] 使用 Problem 替代."""
