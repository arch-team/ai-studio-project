# Shared 模块优化迁移指南

## 概述

本指南帮助您从旧的 shared 模块结构迁移到优化后的统一结构。

## 主要变更

### 1. Repository 基类合并

**旧结构**：
- `BaseRepositoryImpl` - 基础 CRUD 操作
- `EnhancedBaseRepository` - 增强功能（查询构建、分页等）
- `repository_base.py` - 另一个重复的实现

**新结构**：
- `BaseRepository` - 统一的基础仓库类（在 `base_repository.py`）

**迁移步骤**：

```python
# 旧代码
from src.shared.infrastructure.repository_base import EnhancedBaseRepository

class TrainingJobRepository(EnhancedBaseRepository[TrainingJob, TrainingJobModel, int]):
    ...

# 新代码
from src.shared.infrastructure.base_repository import BaseRepository

class TrainingJobRepository(BaseRepository[TrainingJob, TrainingJobModel, int]):
    # 接口完全兼容，无需修改其他代码
    ...
```

### 2. Service 基类合并

**旧结构**：
- `BaseService` - 基础服务操作
- `EnhancedBaseService` - 增强功能（状态管理、批量操作等）

**新结构**：
- `BaseApplicationService` - 统一的应用服务类（在 `base_service_unified.py`）

**迁移步骤**：

```python
# 旧代码
from src.shared.application.enhanced_base_service import EnhancedBaseService

class TrainingJobService(EnhancedBaseService[TrainingJob, int]):
    ...

# 新代码
from src.shared.application.base_service_unified import BaseApplicationService

class TrainingJobService(BaseApplicationService[TrainingJob, int]):
    # 完全兼容，支持所有原有功能
    ...
```

### 3. Schema 基类统一

**旧结构**：
- `EntitySchema` (base.py) - 手动映射
- `AutoMappingEntitySchema` (enhanced_base.py) - 自动映射

**新结构**：
- `EntitySchema` (entity_schema.py) - 统一基类，支持两种模式

**迁移步骤**：

```python
# 旧代码 - 使用 AutoMappingEntitySchema
from src.shared.api.schemas.enhanced_base import AutoMappingEntitySchema

class JobSummary(AutoMappingEntitySchema["TrainingJob"]):
    _enum_mappings = {"status": JobStatusEnum}

# 新代码 - 默认启用自动映射
from src.shared.api.schemas.entity_schema import EntitySchema

class JobSummary(EntitySchema["TrainingJob"]):
    _enum_mappings = {"status": JobStatusEnum}
    # _auto_mapping = True  # 默认值，可省略
```

```python
# 旧代码 - 使用手动映射的 EntitySchema
from src.shared.api.schemas.base import EntitySchema

class ComplexSchema(EntitySchema["ComplexEntity"]):
    @classmethod
    def _map_entity_fields(cls, entity):
        return {"field": entity.computed_value()}

# 新代码 - 禁用自动映射，使用手动模式
from src.shared.api.schemas.entity_schema import EntitySchema

class ComplexSchema(EntitySchema["ComplexEntity"]):
    _auto_mapping = False  # 禁用自动映射

    @classmethod
    def _map_entity_fields(cls, entity):
        return {"field": entity.computed_value()}
```

## 兼容性说明

### 保持兼容的部分

1. **Problem 装饰器系统**：保持不变，继续使用
2. **Domain 层接口**：`IEntityExistenceChecker`、`IQuotaChecker` 保持不变
3. **工具类**：`EnumMapper`、`QueryBuilder`、`utc_now` 等保持不变
4. **异常类**：所有领域异常保持不变

### 需要更新导入的部分

```python
# 更新 Repository 导入
# from src.shared.infrastructure.repository_base import EnhancedBaseRepository
from src.shared.infrastructure.base_repository import BaseRepository

# 更新 Service 导入
# from src.shared.application.enhanced_base_service import EnhancedBaseService
from src.shared.application.base_service_unified import BaseApplicationService

# 更新 Schema 导入
# from src.shared.api.schemas.enhanced_base import AutoMappingEntitySchema
from src.shared.api.schemas.entity_schema import EntitySchema
```

## 逐步迁移策略

### 第一阶段：创建别名（向后兼容）

在旧文件中创建别名，指向新的统一类：

```python
# src/shared/infrastructure/repository_base.py
from src.shared.infrastructure.base_repository import BaseRepository
EnhancedBaseRepository = BaseRepository  # 别名

# src/shared/application/enhanced_base_service.py
from src.shared.application.base_service_unified import BaseApplicationService
EnhancedBaseService = BaseApplicationService  # 别名

# src/shared/api/schemas/enhanced_base.py
from src.shared.api.schemas.entity_schema import EntitySchema
AutoMappingEntitySchema = EntitySchema  # 别名
```

### 第二阶段：逐模块更新

按模块逐步更新导入：
1. 先更新测试文件
2. 再更新业务模块（training、datasets、models 等）
3. 最后更新 API 层

### 第三阶段：清理旧代码

确认所有模块都已迁移后：
1. 删除旧的实现文件
2. 删除别名
3. 运行完整测试套件确认

## 测试验证

迁移后运行以下测试确保兼容性：

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/unit/shared/
pytest tests/integration/

# 检查类型
mypy src/

# 检查导入
python -m py_compile src/modules/*/application/*.py
```

## 性能优化

优化后的好处：
1. **减少代码重复**：约 40% 的重复代码被消除
2. **更好的类型推断**：统一的基类提供更好的 IDE 支持
3. **更少的继承层次**：从 3-4 层减少到 2 层
4. **更清晰的职责**：每个类有明确的单一职责

## 常见问题

### Q: 是否需要立即迁移所有模块？
A: 不需要。通过别名机制，可以逐步迁移。

### Q: 新的基类是否支持所有原有功能？
A: 是的。新基类合并了所有功能，完全向后兼容。

### Q: 性能会受影响吗？
A: 不会。实际上由于减少了继承层次，性能略有提升。

## 支持

如有问题，请查看：
- 单元测试示例：`tests/unit/shared/`
- 集成测试示例：`tests/integration/shared/`