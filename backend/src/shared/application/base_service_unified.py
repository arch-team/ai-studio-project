"""统一的应用服务基类 - 使用 Mixin 模式实现职责分离."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from src.shared.application.mixins import (
    BatchOperationsMixin,
    CRUDOperationsMixin,
    StateManagementMixin,
    ValidationMixin,
)
from src.shared.utils import EnumMapper

T = TypeVar("T")  # 实体类型
ID = TypeVar("ID")  # ID 类型


class BaseApplicationService(
    Generic[T, ID],
    ValidationMixin,
    CRUDOperationsMixin,
    BatchOperationsMixin,
    StateManagementMixin,
):
    """统一的应用服务基类，通过 Mixin 提供通用业务逻辑模式.

    职责分离的 Mixin 组合：
    - ValidationMixin: 字段唯一性、实体存在性验证
    - CRUDOperationsMixin: 基础 CRUD 操作和列表查询
    - BatchOperationsMixin: 批量创建、批量获取
    - StateManagementMixin: 状态转换验证、终态检查

    子类受益于：
    - 减少样板代码
    - 一致的错误处理
    - 可重用的验证模式
    - 职责清晰的代码结构

    子类可通过以下方式自定义未找到错误：
    1. 类属性: _not_found_error_factory = CustomNotFoundError
    2. 构造函数参数: super().__init__(repo, "Entity", CustomNotFoundError)
    """

    # 默认使用通用的 EntityNotFoundError，子类可覆盖
    _not_found_error_factory: Callable[[str], Exception] | None = None

    def __init__(
        self,
        repository: object,
        entity_type: str,
        not_found_error_factory: Callable[[str], Exception] | None = None,
    ):
        """初始化应用服务.

        Args:
            repository: 具有标准方法的仓库实例
            entity_type: 用于错误消息的实体类型名称
            not_found_error_factory: 可选的自定义未找到错误工厂
        """
        self._repository = repository
        self._entity_type = entity_type
        # 只有在传入参数时才覆盖类属性，保持子类可通过类属性定义 error factory
        if not_found_error_factory is not None:
            self._not_found_error_factory = not_found_error_factory

    # ========== 工具方法 ==========

    def convert_enum(
        self,
        value: str | None,
        enum_class: type,
        default: Any = None,
    ) -> Any:
        """将字符串转换为枚举值."""
        return EnumMapper.from_string(value, enum_class, default)
