"""向后兼容别名 - BaseRepository 已合并到 PydanticRepository。"""

from src.shared.infrastructure.pydantic_repository import PydanticRepository

# 向后兼容：BaseRepository 现在是 PydanticRepository 的别名
BaseRepository = PydanticRepository
