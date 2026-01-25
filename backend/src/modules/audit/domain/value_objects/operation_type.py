"""Operation type value object for audit logging."""

from enum import Enum


class OperationType(Enum):
    """Operation type for audit logging."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
