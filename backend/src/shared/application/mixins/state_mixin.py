"""状态管理相关的 Mixin 类."""

from collections.abc import Callable
from typing import Any, TypeVar

from src.shared.domain.exceptions import InvalidStateTransitionError

T = TypeVar("T")  # 实体类型
ID = TypeVar("ID")  # ID 类型


class StateManagementMixin:
    """提供状态管理功能的 Mixin 类.

    提供的功能：
    - 状态转换验证
    - 终态检查
    - 带状态验证的实体获取
    """

    # 这些属性由主类提供
    _entity_type: str
    _not_found_error_factory: Callable[[str], Exception] | None

    def _create_invalid_transition_error(self, current_state: str, target_state: str) -> Exception:
        """创建无效状态转换错误."""
        return InvalidStateTransitionError(self._entity_type, current_state, target_state)

    def _validate_state_transition(
        self,
        entity: Any,
        target_state: Any,
        allowed_from_states: list[Any] | None = None,
    ) -> None:
        """验证状态转换是否允许.

        优先使用实体自身的 can_transition_to 方法，
        否则检查 allowed_from_states 列表.
        """
        current_state = getattr(entity, "status", None) or getattr(entity, "state", None)

        if current_state is None:
            return

        # 检查实体是否有 can_transition_to 方法
        if hasattr(entity, "can_transition_to"):
            if not entity.can_transition_to(target_state):
                raise self._create_invalid_transition_error(str(current_state), str(target_state))
        # 否则检查 allowed_from_states
        elif allowed_from_states and current_state not in allowed_from_states:
            raise self._create_invalid_transition_error(str(current_state), str(target_state))

    def _ensure_not_terminal(self, entity: Any, action: str = "update") -> None:
        """确保实体不在终态，否则抛出无效状态转换错误."""
        if hasattr(entity, "is_terminal") and entity.is_terminal():
            current_state = getattr(entity, "status", None) or getattr(entity, "state", "unknown")
            raise self._create_invalid_transition_error(str(current_state), action)

    async def _with_validation(
        self,
        entity_id: ID,
        allowed_states: list[Any] | None = None,
        require_non_terminal: bool = False,
    ) -> T:
        """获取实体并验证其状态.

        常用于状态转换操作.

        Args:
            entity_id: 实体 ID
            allowed_states: 允许的当前状态列表
            require_non_terminal: 是否要求实体不在终态

        Returns:
            验证通过的实体

        注意: 需要主类有 _get_or_raise 方法 (来自 CRUDOperationsMixin).
        """
        if not hasattr(self, "_get_or_raise"):
            raise AttributeError("StateManagementMixin requires CRUDOperationsMixin")

        entity = await self._get_or_raise(entity_id)

        if require_non_terminal:
            self._ensure_not_terminal(entity)

        if allowed_states:
            current_state = getattr(entity, "status", None) or getattr(entity, "state", None)
            if current_state and current_state not in allowed_states:
                raise self._create_invalid_transition_error(str(current_state), "operation")

        return entity  # type: ignore[no-any-return]
