"""Space module domain exceptions.

设计说明:
---------
每个异常类包含以下类属性：
- http_status: 对应的 HTTP 状态码
- error_code: 错误代码，供前端程序化处理

异常处理器会自动读取这些属性，无需维护映射表。
"""

from src.shared.domain.exceptions import DomainError


class SpaceError(DomainError):
    """Base exception for space-related errors."""

    error_code = "SPACE_ERROR"


class SpaceNotFoundError(SpaceError):
    """Space not found exception."""

    http_status = 404
    error_code = "SPACE_NOT_FOUND"

    def __init__(self, space_id: str):
        super().__init__(f"Space not found: {space_id}")
        self.space_id = space_id


class DuplicateSpaceNameError(SpaceError):
    """Space name already exists for owner exception."""

    http_status = 409
    error_code = "DUPLICATE_SPACE_NAME"

    def __init__(self, space_name: str, owner_id: int):
        super().__init__(f"Space name already exists: {space_name} for owner {owner_id}")
        self.space_name = space_name
        self.owner_id = owner_id


class InvalidSpaceStateError(SpaceError):
    """Invalid space state for operation exception."""

    http_status = 409
    error_code = "INVALID_SPACE_STATE"

    def __init__(self, space_id: str, current_state: str, operation: str):
        super().__init__(
            f"Cannot {operation} space {space_id} in {current_state} state"
        )
        self.space_id = space_id
        self.current_state = current_state
        self.operation = operation


class SpaceQuotaExceededError(SpaceError):
    """Space resource quota exceeded exception."""

    http_status = 429
    error_code = "SPACE_QUOTA_EXCEEDED"

    def __init__(self, resource: str, required: int, available: int):
        super().__init__(
            f"Insufficient {resource}: need {required}, have {available}"
        )
        self.resource = resource
        self.required = required
        self.available = available
