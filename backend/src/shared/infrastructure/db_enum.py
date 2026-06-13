"""SQLAlchemy Enum 列类型辅助工具。

解决 Python Enum 成员名 (.name) 与数据库 ENUM 列值大小写不一致的问题。
"""

from enum import Enum as PyEnum

from sqlalchemy import Enum as SAEnum


def lowercase_enum(enum_cls: type[PyEnum], **kwargs: object) -> SAEnum:
    """构造按 .value（小写）读写的 SQLAlchemy Enum 列类型。

    SQLAlchemy ``Enum()`` 默认按成员名 (.name, 如 'ACTIVE') 持久化/读回。
    当数据库 ENUM 列定义为小写 .value (如 'active')、而 Python Enum 成员名为
    大写时，读回会抛 ``LookupError: 'active' is not among the defined enum values``。

    本 helper 通过 ``values_callable`` 让 SQLAlchemy 改用 .value 读写，与小写
    数据库列对齐。

    仅用于"成员名 ≠ .value 且数据库存小写 .value"的列；数据库存成员名 (.name)
    的列（如 spaces 的 backend 列存 'STUDIO'）切勿使用，否则反而破坏其一致性。
    """
    return SAEnum(enum_cls, values_callable=lambda members: [m.value for m in members], **kwargs)
