"""Enhanced Schema - 向后兼容别名.

此文件保留用于向后兼容。新代码请直接使用：
    from src.shared.api.schemas.entity_schema import EntitySchema

迁移指南: 参见 src/shared/MIGRATION_GUIDE.md
"""

# 从新的统一实现导入
from src.shared.api.schemas.entity_schema import EntitySchema

# 向后兼容别名 - 旧代码无需修改即可继续工作
AutoMappingEntitySchema = EntitySchema

# 导出列表
__all__ = ["AutoMappingEntitySchema", "EntitySchema"]
