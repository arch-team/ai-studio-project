"""统一的应用服务基类 - 合并 BaseService 和 EnhancedBaseService."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from src.shared.domain.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from src.shared.domain.interfaces import IEntityExistenceChecker
from src.shared.utils import EnumMapper

T = TypeVar("T")  # 实体类型
ID = TypeVar("ID")  # ID 类型


class BaseApplicationService(Generic[T, ID]):
    """统一的应用服务基类，提供通用业务逻辑模式。

    合并了原来的 BaseService 和 EnhancedBaseService，
    消除重复代码，提供一致的接口。

    提供的功能：
    - CRUD 操作与验证
    - 状态转换管理
    - 实体存在性验证
    - 枚举转换工具
    - 分页支持
    - 批量操作

    子类受益于：
    - 减少样板代码
    - 一致的错误处理
    - 可重用的验证模式

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
        """初始化应用服务。

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

    # ========== 错误创建 ==========

    def _create_not_found_error(self, entity_id: str) -> Exception:
        """创建未找到错误。可通过 _not_found_error_factory 自定义。"""
        if self._not_found_error_factory is not None:
            return self._not_found_error_factory(entity_id)
        return EntityNotFoundError(self._entity_type, entity_id)

    def _create_duplicate_error(self, field: str, value: str) -> Exception:
        """创建重复实体错误。"""
        return DuplicateEntityError(self._entity_type, f"{field}={value}")

    def _create_invalid_transition_error(
        self, current_state: str, target_state: str
    ) -> Exception:
        """创建无效状态转换错误。"""
        return InvalidStateTransitionError(
            self._entity_type, current_state, target_state
        )

    # ========== 实体检索 ==========

    async def _get_or_raise(self, entity_id: ID) -> T:
        """根据 ID 获取实体或抛出未找到错误。"""
        entity = await self._repository.get_by_id(entity_id)  # type: ignore
        if entity is None:
            raise self._create_not_found_error(str(entity_id))
        return entity  # type: ignore

    async def _get_by_field_or_none(self, field_name: str, field_value: Any) -> T | None:
        """根据任意字段获取实体。"""
        method_name = f"get_by_{field_name}"
        if hasattr(self._repository, method_name):
            method = getattr(self._repository, method_name)
            return await method(field_value)
        return None

    # ========== 验证工具 ==========

    async def _validate_unique_field(self, field_name: str, field_value: Any) -> None:
        """验证字段值唯一性。"""
        # 尝试特定的 exists_by_xxx 方法
        method_name = f"exists_by_{field_name}"
        if hasattr(self._repository, method_name):
            exists_method = getattr(self._repository, method_name)
            if await exists_method(field_value):
                raise self._create_duplicate_error(field_name, str(field_value))
        # 回退到通用的 exists_by 方法
        elif hasattr(self._repository, "exists_by"):
            if await self._repository.exists_by(field_name, field_value):  # type: ignore
                raise self._create_duplicate_error(field_name, str(field_value))

    async def _validate_entity_exists(
        self,
        checker: IEntityExistenceChecker | None,
        entity_type: str,
        entity_id: ID,
    ) -> None:
        """验证相关实体存在。"""
        if checker and not await checker.exists(entity_id):  # type: ignore
            raise EntityNotFoundError(entity_type, str(entity_id))

    async def _validate_entities_exist(
        self,
        validations: list[tuple[IEntityExistenceChecker | None, str, ID]],
    ) -> None:
        """验证多个相关实体存在。"""
        for checker, entity_type, entity_id in validations:
            await self._validate_entity_exists(checker, entity_type, entity_id)

    # ========== 状态管理 ==========

    def _validate_state_transition(
        self,
        entity: Any,
        target_state: Any,
        allowed_from_states: list[Any] | None = None,
    ) -> None:
        """验证状态转换是否允许。"""
        current_state = getattr(entity, "status", None) or getattr(entity, "state", None)

        if current_state is None:
            return

        # 检查实体是否有 can_transition_to 方法
        if hasattr(entity, "can_transition_to"):
            if not entity.can_transition_to(target_state):
                raise self._create_invalid_transition_error(
                    str(current_state), str(target_state)
                )
        # 否则检查 allowed_from_states
        elif allowed_from_states and current_state not in allowed_from_states:
            raise self._create_invalid_transition_error(
                str(current_state), str(target_state)
            )

    # ========== CRUD 操作 ==========

    async def get_by_id(self, entity_id: ID) -> T:
        """根据 ID 获取实体。"""
        return await self._get_or_raise(entity_id)

    async def list_entities(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[T], int]:
        """列出带过滤和分页的实体。"""
        # 尝试使用仓库的 list_with_filters 方法
        if hasattr(self._repository, "list_with_filters"):
            return await self._repository.list_with_filters(  # type: ignore
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        # 回退到通用的 list 方法
        elif hasattr(self._repository, "list"):
            return await self._repository.list(  # type: ignore
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        else:
            # 如果没有可用的列表方法，返回空列表
            return [], 0

    async def create_entity(
        self,
        data: dict[str, Any],
        unique_fields: list[str] | None = None,
    ) -> T:
        """创建带验证的新实体。"""
        # 验证唯一字段
        if unique_fields:
            for field in unique_fields:
                if field in data:
                    await self._validate_unique_field(field, data[field])

        # 创建实体（假设仓库有 create 方法）
        return await self._repository.create(data)  # type: ignore

    async def update_entity(
        self,
        entity_id: ID,
        data: dict[str, Any],
    ) -> T:
        """更新现有实体。"""
        entity = await self._get_or_raise(entity_id)

        # 更新实体属性
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # 保存更改
        return await self._repository.update(entity)  # type: ignore

    async def delete_entity(
        self,
        entity_id: ID,
        soft_delete: bool = True,
    ) -> None:
        """删除实体。"""
        await self._get_or_raise(entity_id)  # 验证存在

        if soft_delete and hasattr(self._repository, "soft_delete"):
            await self._repository.soft_delete(entity_id)  # type: ignore
        else:
            await self._repository.delete(entity_id)  # type: ignore

    # ========== 批量操作 ==========

    async def create_many(
        self,
        items: list[dict[str, Any]],
        unique_fields: list[str] | None = None,
    ) -> list[T]:
        """创建多个实体。"""
        # 验证所有项目的唯一字段
        if unique_fields:
            for item in items:
                for field in unique_fields:
                    if field in item:
                        await self._validate_unique_field(field, item[field])

        # 创建所有实体
        if hasattr(self._repository, "create_many"):
            return await self._repository.create_many(items)  # type: ignore
        else:
            # 回退到单独创建
            results = []
            for item in items:
                result = await self._repository.create(item)  # type: ignore
                results.append(result)
            return results

    async def get_by_ids(self, entity_ids: list[ID]) -> list[T]:
        """根据多个 ID 获取实体。"""
        if hasattr(self._repository, "get_by_ids"):
            return await self._repository.get_by_ids(entity_ids)  # type: ignore
        else:
            # 回退到单独获取
            results = []
            for entity_id in entity_ids:
                entity = await self._repository.get_by_id(entity_id)  # type: ignore
                if entity:
                    results.append(entity)
            return results

    # ========== 工具方法 ==========

    def convert_enum(
        self,
        value: str | None,
        enum_class: type,
        default: Any = None,
    ) -> Any:
        """将字符串转换为枚举值。"""
        return EnumMapper.from_string(value, enum_class, default)