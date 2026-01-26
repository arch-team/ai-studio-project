# Repository 样板代码优化方案

> **目标**: 减少 ~780 行重复的 `_to_entity()` / `_to_model()` / `_update_model()` 样板代码

---

## 现状分析

### 当前问题

| 问题 | 影响 | 统计 |
|------|------|------|
| 逐字段映射冗长 | 每个 Repository 约 52 行转换代码 | 15 个实现 × 52 行 = 780 行 |
| 枚举转换重复 | Model→Entity 和 Entity→Model 都要手工转换 | 每个枚举字段 2 次转换 |
| 字段列表不一致 | Dataset 用字段列表模式，其他逐字段 | 14/15 实现未优化 |
| 无字段排除机制 | id, created_at 等只读字段也被包含 | 容易误更新 |

### 当前模式示例

```python
# 56 行的 _to_entity()
def _to_entity(self, model: TrainingJobModel) -> TrainingJob:
    return TrainingJob(
        id=model.id,
        job_name=model.job_name,
        status=JobStatus(model.status.value),  # 枚举转换
        # ... 53 个字段逐一映射
    )
```

---

## 方案对比：cattrs vs Pydantic V2

### 概览对比

| 维度 | cattrs | Pydantic V2 |
|------|--------|-------------|
| **核心理念** | 结构化/非结构化工具 | 数据验证框架 |
| **Entity 改动** | 无需改动 (保持 @dataclass) | 需改为 BaseModel |
| **学习曲线** | 中等 (hook 机制) | 低 (API 直观) |
| **性能** | 高 (简单转换) | 高 (Rust 核心) |
| **验证能力** | 无内置验证 | 强大的字段验证 |
| **项目侵入性** | 低 | 高 |

---

### 方案 A：cattrs 自动转换

#### 优点

1. **零侵入性** - 现有 15 个 `@dataclass` Entity 完全不用改
2. **轻量级** - 只做转换，不引入复杂概念
3. **灵活 Hook** - 自定义枚举、嵌套对象转换规则
4. **保持 DDD 纯净** - Entity 仍是纯 Python dataclass

#### 缺点

1. **无内置验证** - 验证逻辑仍需在 Entity 或 Service 层
2. **Hook 学习曲线** - 需要理解 structure/unstructure 概念
3. **社区较小** - 文档和示例不如 Pydantic 丰富

#### 代码示例

```python
# Entity 保持不变
@dataclass
class TrainingJob:
    id: int
    job_name: str
    status: JobStatus  # 枚举

# Repository 简化为配置
class TrainingJobRepositoryImpl(BaseRepository[TrainingJob, TrainingJobModel, int]):
    _entity_class = TrainingJob
    _updatable_fields = ["status", "error_message", "completed_at"]

    # 无需手写 _to_entity(), _to_model(), _update_model()
```

#### 适用场景

- ✅ 现有 @dataclass Entity 不想改动
- ✅ 只需要减少转换样板代码
- ✅ 验证逻辑已在其他层处理

---

### 方案 B：Pydantic V2 重构

#### 优点

1. **强大验证** - 字段级验证、自定义验证器、模式验证
2. **from_attributes** - 原生支持从 ORM 模型转换
3. **序列化控制** - JSON 序列化/反序列化一体化
4. **IDE 支持** - 更好的类型推断和自动补全
5. **广泛使用** - 社区大，文档丰富，FastAPI 原生集成

#### 缺点

1. **需要重构 Entity** - 15 个 @dataclass → BaseModel
2. **混淆领域概念** - Pydantic 更像 DTO，不是纯领域实体
3. **额外功能开销** - 引入验证/序列化，可能不需要
4. **DDD 纯净性** - Entity 依赖 pydantic，不再是纯 Python

#### 代码示例

```python
# Entity 需要改为 BaseModel
from pydantic import BaseModel, ConfigDict, field_validator

class TrainingJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 转换

    id: int
    job_name: str
    status: JobStatus

    # 内置验证能力
    @field_validator("job_name")
    @classmethod
    def validate_job_name(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("job_name must be at least 3 characters")
        return v

# Repository 转换
class TrainingJobRepositoryImpl:
    def _to_entity(self, model: TrainingJobModel) -> TrainingJob:
        return TrainingJob.model_validate(model)  # 一行搞定！

    def _to_model(self, entity: TrainingJob) -> TrainingJobModel:
        return TrainingJobModel(**entity.model_dump(exclude={"created_at"}))
```

#### 适用场景

- ✅ 需要在 Entity 层统一验证逻辑
- ✅ 愿意接受较大改动
- ✅ 希望 Entity 和 API Schema 共享定义
- ⚠️ 会模糊 DDD 中 Entity 和 DTO 的边界

---

### 详细对比表

| 维度 | cattrs | Pydantic V2 | 评价 |
|------|--------|-------------|------|
| **Entity 改动量** | 0 行 | ~1500 行 (15 个 Entity) | cattrs 胜 |
| **新增依赖** | cattrs ~50KB | pydantic 已有 | 平手 |
| **转换代码减少** | 74% | 80% | Pydantic 略胜 |
| **验证能力** | 无 | 强 | Pydantic 胜 |
| **DDD 纯净性** | 高 | 中 | cattrs 胜 |
| **学习成本** | 中 | 低 | Pydantic 胜 |
| **社区支持** | 中 | 高 | Pydantic 胜 |
| **迁移风险** | 低 | 高 | cattrs 胜 |

---

### 混合方案（可选）

保持 Entity 为 @dataclass，但在 API Schema 层使用 Pydantic：

```
Entity (@dataclass)  ←→  Repository (cattrs)  ←→  Model (SQLAlchemy)
        ↓
   API Schema (Pydantic)  # 已有
```

**优势**：
- Entity 保持纯领域逻辑（@dataclass）
- Repository 用 cattrs 减少样板
- API Schema 用 Pydantic（已有，无需改动）
- 职责分离最清晰

---

### 推荐结论

| 你的情况 | 推荐方案 |
|---------|---------|
| 只想减少样板代码，不改 Entity | **cattrs** |
| 需要在 Entity 层加入验证逻辑 | **Pydantic V2** |
| 追求 DDD 架构纯净性 | **cattrs** |
| 团队对 Pydantic 更熟悉 | **Pydantic V2** |
| 想最小化迁移风险 | **cattrs** |

**本项目推荐**: cattrs（现有 @dataclass Entity + Clean Architecture，改动最小）

---

## 实施计划

### 阶段 1：添加依赖 + 创建 Converter 工具类

**文件**: `backend/src/shared/infrastructure/entity_converter.py`

```python
"""统一的实体转换器 - 减少 Repository 样板代码。"""

from typing import Any, TypeVar, get_type_hints
from dataclasses import fields, is_dataclass
from enum import Enum

import cattrs
from cattrs import Converter

EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")


class EntityConverter:
    """基于 cattrs 的实体转换器。

    自动处理：
    - 简单字段映射
    - 枚举类型转换 (SQLAlchemy Enum → Python Enum)
    - 嵌套对象转换
    - 可选字段 (None 处理)
    """

    def __init__(self) -> None:
        self._converter = Converter()
        self._register_enum_hooks()

    def _register_enum_hooks(self) -> None:
        """注册枚举类型的自定义 hook。"""

        # SQLAlchemy Enum → Python Enum
        def structure_enum(value: Any, enum_class: type[Enum]) -> Enum:
            if isinstance(value, enum_class):
                return value
            if hasattr(value, "value"):  # SQLAlchemy Enum
                return enum_class(value.value)
            return enum_class(value)

        # Python Enum → str/value (用于 Model)
        def unstructure_enum(value: Enum) -> str:
            return value.value if hasattr(value, "value") else str(value)

        # 注册所有 Enum 子类
        self._converter.register_structure_hook_factory(
            lambda t: issubclass(t, Enum) if isinstance(t, type) else False,
            lambda t: lambda v, _: structure_enum(v, t)
        )
        self._converter.register_unstructure_hook_factory(
            lambda t: issubclass(t, Enum) if isinstance(t, type) else False,
            lambda t: unstructure_enum
        )

    def to_entity(
        self,
        model: ModelT,
        entity_class: type[EntityT],
        field_mapping: dict[str, str] | None = None,
        exclude_fields: set[str] | None = None,
    ) -> EntityT:
        """将 ORM Model 转换为领域实体。

        Args:
            model: SQLAlchemy ORM 模型实例
            entity_class: 目标实体类 (dataclass)
            field_mapping: 字段名映射 {"model_field": "entity_field"}
            exclude_fields: 排除的字段

        Returns:
            领域实体实例
        """
        exclude = exclude_fields or set()
        mapping = field_mapping or {}

        # 从 model 提取数据
        data = {}
        for field in fields(entity_class):
            if field.name in exclude:
                continue

            # 检查是否有字段映射
            model_field_name = mapping.get(field.name, field.name)

            if hasattr(model, model_field_name):
                data[field.name] = getattr(model, model_field_name)

        return self._converter.structure(data, entity_class)

    def to_model_dict(
        self,
        entity: EntityT,
        include_fields: list[str] | None = None,
        exclude_fields: set[str] | None = None,
    ) -> dict[str, Any]:
        """将领域实体转换为字典，用于创建/更新 ORM Model。

        Args:
            entity: 领域实体实例
            include_fields: 只包含这些字段（优先级高）
            exclude_fields: 排除这些字段

        Returns:
            可用于 Model(**dict) 的字典
        """
        exclude = exclude_fields or {"created_at", "updated_at"}

        if include_fields:
            field_names = include_fields
        else:
            field_names = [f.name for f in fields(entity) if f.name not in exclude]

        data = {}
        for name in field_names:
            value = getattr(entity, name)
            # 枚举转换为值
            if isinstance(value, Enum):
                data[name] = value.value
            else:
                data[name] = value

        return data

    def update_model(
        self,
        model: ModelT,
        entity: EntityT,
        updatable_fields: list[str],
    ) -> None:
        """从实体更新 ORM 模型的指定字段。

        Args:
            model: 要更新的 ORM 模型
            entity: 数据来源实体
            updatable_fields: 允许更新的字段列表
        """
        for field_name in updatable_fields:
            if hasattr(entity, field_name):
                value = getattr(entity, field_name)
                # 枚举转换为值
                if isinstance(value, Enum):
                    setattr(model, field_name, value.value)
                else:
                    setattr(model, field_name, value)


# 全局单例
entity_converter = EntityConverter()
```

### 阶段 2：优化 BaseRepository

**文件**: `backend/src/shared/infrastructure/base_repository.py`

```python
from src.shared.infrastructure.entity_converter import entity_converter

class BaseRepository(ABC, Generic[EntityT, ModelT, IdT]):
    """统一的基础仓库实现。

    子类只需定义：
    - _entity_class: 实体类型
    - _field_mapping: 字段名映射（可选）
    - _updatable_fields: 允许更新的字段列表
    """

    # 子类配置
    _entity_class: type[EntityT]
    _field_mapping: dict[str, str] = {}
    _exclude_from_model: set[str] = {"created_at", "updated_at"}
    _updatable_fields: list[str] = []

    def _to_entity(self, model: ModelT) -> EntityT:
        """默认实现：使用 EntityConverter 自动转换。"""
        return entity_converter.to_entity(
            model,
            self._entity_class,
            field_mapping=self._field_mapping,
        )

    def _to_model(self, entity: EntityT) -> ModelT:
        """默认实现：使用 EntityConverter 自动转换。"""
        data = entity_converter.to_model_dict(
            entity,
            exclude_fields=self._exclude_from_model,
        )
        return self._model_class(**data)

    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """默认实现：只更新指定的可变字段。"""
        if not self._updatable_fields:
            raise NotImplementedError(
                f"{self.__class__.__name__} 必须定义 _updatable_fields"
            )
        entity_converter.update_model(model, entity, self._updatable_fields)
```

### 阶段 3：简化具体 Repository 实现

**优化前** (56 行)：

```python
class TrainingJobRepositoryImpl(BaseRepository[TrainingJob, TrainingJobModel, int]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TrainingJobModel)

    def _to_entity(self, model: TrainingJobModel) -> TrainingJob:
        return TrainingJob(
            id=model.id,
            job_name=model.job_name,
            status=JobStatus(model.status.value),
            # ... 53 行
        )

    def _to_model(self, entity: TrainingJob) -> TrainingJobModel:
        return TrainingJobModel(
            id=entity.id,
            # ... 类似的重复
        )

    def _update_model(self, model: TrainingJobModel, entity: TrainingJob) -> None:
        model.status = entity.status.value
        # ... 11 行
```

**优化后** (15 行)：

```python
class TrainingJobRepositoryImpl(BaseRepository[TrainingJob, TrainingJobModel, int]):
    _entity_class = TrainingJob
    _updatable_fields = [
        "status", "hyperpod_status", "hyperpod_job_arn",
        "error_message", "started_at", "completed_at",
        "metrics", "exit_code", "preemption_count",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, TrainingJobModel)
```

**代码量**: 56 行 → 15 行 (**减少 73%**)

---

## 关键文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `pyproject.toml` | 修改 | 添加 `cattrs` 依赖 |
| `shared/infrastructure/entity_converter.py` | 新建 | EntityConverter 工具类 |
| `shared/infrastructure/base_repository.py` | 修改 | 添加默认转换实现 |
| `modules/*/infrastructure/repositories/*_impl.py` | 修改 | 简化为配置式 |

---

## 迁移策略

### 渐进式迁移

1. **第一批**: auth 模块 (User 简单，低风险)
2. **第二批**: datasets 模块 (已有字段列表模式)
3. **第三批**: training 模块 (字段最多，收益最大)
4. **第四批**: quotas, spaces 等其他模块

### 兼容性保证

- 旧的 `_to_entity()` 覆盖仍然生效
- 单元测试必须全部通过
- 渐进式迁移，不一次性改完

---

## 验证计划

### 测试覆盖

```bash
# 1. 运行现有单元测试
pytest tests/unit/modules/ -v

# 2. 运行 Repository 集成测试
pytest tests/integration/ -k "repository" -v

# 3. 验证枚举转换
pytest tests/unit/ -k "enum" -v
```

### 验收标准

- [ ] 所有现有测试通过
- [ ] 枚举字段正确转换（双向）
- [ ] 可选字段 None 处理正确
- [ ] _update_model 只更新指定字段
- [ ] 代码量减少 > 50%

---

## 预期收益

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| Repository 样板代码 | 780 行 | ~200 行 | **-74%** |
| 新增 Repository 工作量 | 52 行/个 | 15 行/个 | **-71%** |
| 枚举转换代码 | 手工两次 | 自动 | **消除** |
| 字段更新控制 | 不明确 | 显式列表 | **更安全** |
