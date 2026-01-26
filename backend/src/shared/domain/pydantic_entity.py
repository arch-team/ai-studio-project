"""Pydantic V2 领域实体基类 - 自动化 ORM 转换。"""

from datetime import datetime
from enum import Enum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from src.shared.utils import utc_now


class PydanticEntity(BaseModel):
    """Pydantic V2 领域实体基类。

    所有领域实体继承此类，获得：
    - 自动 ORM 模型转换 (from_attributes=True)
    - 赋值时自动验证 (validate_assignment=True)
    - 字符串自动去空格 (str_strip_whitespace=True)
    - JSON 序列化支持

    使用方式:
    ```python
    class User(PydanticEntity):
        username: str = Field(min_length=3, max_length=64)
        email: str
        status: UserStatus = UserStatus.ACTIVE

    # 从 ORM 模型转换
    user = User.from_orm(user_model)

    # 转换为字典（用于创建 ORM 模型）
    data = user.to_model_dict(exclude={"id"})
    ```
    """

    model_config = ConfigDict(
        from_attributes=True,       # 支持从 ORM 模型转换
        validate_assignment=True,   # 赋值时触发验证
        str_strip_whitespace=True,  # 字符串去空格
        use_enum_values=False,      # 保留枚举对象（不转为值）
        arbitrary_types_allowed=True,  # 允许任意类型
        extra="ignore",             # 忽略额外字段
    )

    # 通用字段 - 子类可选择覆盖
    id: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_orm(cls, model: Any) -> Self:
        """从 ORM 模型创建实体。

        Args:
            model: SQLAlchemy ORM 模型实例

        Returns:
            领域实体实例
        """
        return cls.model_validate(model)

    def to_model_dict(
        self,
        *,
        exclude: set[str] | None = None,
        include: set[str] | None = None,
        exclude_unset: bool = False,
        exclude_none: bool = False,
        convert_enums: bool = True,
    ) -> dict[str, Any]:
        """转换为字典，用于创建/更新 ORM 模型。

        Args:
            exclude: 排除的字段集合
            include: 只包含的字段集合（优先级高于 exclude）
            exclude_unset: 是否排除未设置的字段
            exclude_none: 是否排除 None 值字段
            convert_enums: 是否将枚举转换为值

        Returns:
            可用于 Model(**dict) 的字典
        """
        # 默认排除时间戳字段
        default_exclude = {"created_at", "updated_at"}
        final_exclude = (exclude or set()) | default_exclude

        data = self.model_dump(
            exclude=final_exclude if not include else None,
            include=include,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            mode="python",  # 保留 Python 对象
        )

        # 枚举转换为值（ORM 模型需要）
        if convert_enums:
            data = self._convert_enums_to_values(data)

        return data

    def _convert_enums_to_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """递归将字典中的枚举转换为值。"""
        result = {}
        for key, value in data.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, dict):
                result[key] = self._convert_enums_to_values(value)
            elif isinstance(value, list):
                result[key] = [
                    v.value if isinstance(v, Enum) else v
                    for v in value
                ]
            else:
                result[key] = value
        return result

    def __eq__(self, other: object) -> bool:
        """基于 ID 的相等性比较。"""
        if not isinstance(other, self.__class__):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """基于 ID 的哈希。"""
        return hash((self.__class__.__name__, self.id))

    def touch(self) -> None:
        """更新 updated_at 时间戳。"""
        self.updated_at = utc_now()
