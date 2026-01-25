"""Model module domain exceptions.

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
"""

from src.shared.domain.exceptions import DomainError


class ModelError(DomainError):
    """Base exception for model-related errors."""

    error_code = "MODEL_ERROR"


class ModelNotFoundError(ModelError):
    """Model not found exception."""

    http_status = 404
    error_code = "MODEL_NOT_FOUND"

    def __init__(self, model_id: int | str):
        super().__init__(f"Model not found: {model_id}")
        self.model_id = model_id


class DuplicateModelVersionError(ModelError):
    """Model version already exists exception."""

    http_status = 409
    error_code = "DUPLICATE_MODEL_VERSION"

    def __init__(self, model_name: str, version: str):
        super().__init__(f"Model version already exists: {model_name} {version}")
        self.model_name = model_name
        self.version = version


class InvalidModelStateError(ModelError):
    """Invalid model state for operation exception."""

    http_status = 409
    error_code = "INVALID_MODEL_STATE"

    def __init__(self, model_id: int, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} model {model_id} in {current_state} state"
        )
        self.model_id = model_id
        self.current_state = current_state
        self.operation = operation
