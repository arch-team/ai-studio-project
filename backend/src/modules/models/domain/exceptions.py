"""Model module domain exceptions.

使用 @problem 装饰器和 @dataclass 简化异常定义。
每个异常类通过装饰器注入 http_status 和 error_code。
get_details() 自动返回所有数据字段。
"""

from dataclasses import dataclass
from typing import Union

from src.shared.domain.problem import Problem, problem


@problem(404, "MODEL_NOT_FOUND", "Model not found: {model_id}")
@dataclass
class ModelNotFoundError(Problem):
    """模型未找到."""

    model_id: Union[int, str]


@problem(409, "DUPLICATE_MODEL_VERSION", "Model version already exists: {model_name} {version}")
@dataclass
class DuplicateModelVersionError(Problem):
    """模型版本重复."""

    model_name: str
    version: str


@problem(
    409, "INVALID_MODEL_STATE", "Cannot {operation} model {model_id} in {current_state} state"
)
@dataclass
class InvalidModelStateError(Problem):
    """模型状态无效."""

    model_id: int
    current_state: str
    operation: str


# =============================================================================
# 向后兼容别名 (deprecated)
# =============================================================================

ModelError = Problem
"""[DEPRECATED] 使用 Problem 替代."""
