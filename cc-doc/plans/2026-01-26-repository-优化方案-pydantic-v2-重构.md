# Repository 优化方案：Pydantic V2 重构

> **最终选择**: Pydantic V2 作为 Entity 基类
> **目标**: 减少 ~780 行 Repository 样板代码，统一验证能力

---

## 现状分析

### 当前问题

| 问题 | 影响 | 统计 |
|------|------|------|
| 逐字段映射冗长 | 每个 Repository 约 52 行转换代码 | 15 个实现 × 52 行 = 780 行 |
| 枚举转换重复 | Model→Entity 和 Entity→Model 都要手工转换 | 每个枚举字段 2 次转换 |
| 验证逻辑分散 | Entity、Service、API 多层验证 | 维护困难 |
| 无字段排除机制 | id, created_at 等只读字段也被包含 | 容易误更新 |

---

## 方案概述

### 核心改动

1. **Entity 层**: `@dataclass` → `BaseModel` (Pydantic V2)
2. **Repository 层**: 使用 `model_validate(model, from_attributes=True)` 自动转换
3. **验证逻辑**: 集中在 Entity 层，统一验证规则

### 架构变化

```
当前架构:
Entity (@dataclass)  ←[手工转换 52 行]→  Model (SQLAlchemy)
        ↓
   API Schema (Pydantic)  # 单独定义

重构后架构:
Entity (Pydantic BaseModel)  ←[model_validate 1 行]→  Model (SQLAlchemy)
        ↓
   API Schema  # 可复用 Entity 或继承
```

---

## 实施计划

### 阶段 1：创建 Pydantic Entity 基类

**文件**: `backend/src/shared/domain/base_entity.py`

```python
"""Pydantic V2 领域实体基类。"""

from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from src.shared.utils import utc_now


class DomainEntity(BaseModel):
    """领域实体基类。

    所有领域实体继承此类，获得：
    - 自动 ORM 模型转换 (from_attributes=True)
    - 赋值时自动验证 (validate_assignment=True)
    - 字符串自动去空格 (str_strip_whitespace=True)
    - JSON 序列化支持
    """

    model_config = ConfigDict(
        from_attributes=True,       # 支持从 ORM 模型转换
        validate_assignment=True,   # 赋值时触发验证
        str_strip_whitespace=True,  # 字符串去空格
        use_enum_values=False,      # 保留枚举对象（不转为值）
        arbitrary_types_allowed=True,  # 允许任意类型
    )

    id: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_orm(cls, model: Any) -> Self:
        """从 ORM 模型创建实体。"""
        return cls.model_validate(model)

    def to_dict(
        self,
        exclude: set[str] | None = None,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        """转换为字典，用于创建/更新 ORM 模型。"""
        default_exclude = {"created_at", "updated_at"}
        final_exclude = (exclude or set()) | default_exclude

        return self.model_dump(
            exclude=final_exclude,
            exclude_unset=exclude_unset,
            mode="python",  # 保留 Python 对象（如 Enum）
        )

    def __eq__(self, other: object) -> bool:
        """基于 ID 的相等性比较。"""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """基于 ID 的哈希。"""
        return hash((self.__class__.__name__, self.id))
```

### 阶段 2：重构 Entity 示例

**文件**: `backend/src/modules/auth/domain/entities/user.py`

**重构前** (@dataclass, 60 行):

```python
@dataclass
class User:
    id: int
    username: str
    email: str
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.ENGINEER
    # ... 30 个字段

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
```

**重构后** (Pydantic, 45 行):

```python
from pydantic import Field, field_validator, EmailStr

from src.shared.domain import DomainEntity


class User(DomainEntity):
    """用户领域实体。"""

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr  # 自动验证邮箱格式
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.ENGINEER

    # 内置验证
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("username must be alphanumeric")
        return v.lower()

    # 业务方法保持不变
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def suspend(self) -> None:
        if self.status == UserStatus.SUSPENDED:
            raise InvalidStateTransitionError(...)
        self.status = UserStatus.SUSPENDED
        self.updated_at = utc_now()
```

### 阶段 3：简化 Repository 基类

**文件**: `backend/src/shared/infrastructure/base_repository.py`

```python
"""Pydantic V2 优化的基础仓库实现。"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain import DomainEntity
from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.utils import utc_now

EntityT = TypeVar("EntityT", bound=DomainEntity)
ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT", int, str)


class BaseRepository(Generic[EntityT, ModelT, IdT]):
    """Pydantic V2 优化的基础仓库。

    利用 Pydantic 的 from_attributes=True 自动转换。
    子类只需定义：
    - _entity_class: 实体类型
    - _updatable_fields: 允许更新的字段列表（可选）
    """

    _entity_class: type[EntityT]
    _updatable_fields: list[str] | None = None

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        self._session = session
        self._model_class = model_class

    def _to_entity(self, model: ModelT) -> EntityT:
        """ORM 模型 → 领域实体（自动转换）。"""
        return self._entity_class.model_validate(model)

    def _to_model(self, entity: EntityT) -> ModelT:
        """领域实体 → ORM 模型（新建时）。"""
        data = entity.to_dict(exclude={"id"} if entity.id is None else None)
        return self._model_class(**data)

    def _update_model(self, model: ModelT, entity: EntityT) -> None:
        """更新 ORM 模型（只更新指定字段）。"""
        if self._updatable_fields:
            fields = self._updatable_fields
        else:
            # 默认更新所有非只读字段
            fields = [
                f for f in entity.model_fields.keys()
                if f not in {"id", "created_at", "owner_id"}
            ]

        for field_name in fields:
            if hasattr(entity, field_name):
                value = getattr(entity, field_name)
                # 枚举转换为值
                if hasattr(value, "value"):
                    setattr(model, field_name, value.value)
                else:
                    setattr(model, field_name, value)

    # ========== CRUD 操作（保持不变）==========

    async def get_by_id(self, id: IdT) -> EntityT | None:
        """根据主键获取实体。"""
        result = await self._session.execute(
            select(self._model_class).where(self._model_class.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, entity: EntityT) -> EntityT:
        """创建新实体。"""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: EntityT) -> EntityT:
        """更新现有实体。"""
        result = await self._session.execute(
            select(self._model_class).where(self._model_class.id == entity.id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            raise EntityNotFoundError(self._entity_class.__name__, str(entity.id))

        self._update_model(model, entity)
        model.updated_at = utc_now()

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    # ... 其他方法保持不变
```

### 阶段 4：简化具体 Repository 实现

**优化前** (56 行):

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
    # ... _to_model, _update_model 类似
```

**优化后** (8 行):

```python
class TrainingJobRepositoryImpl(BaseRepository[TrainingJob, TrainingJobModel, int]):
    _entity_class = TrainingJob
    _updatable_fields = [
        "status", "hyperpod_status", "hyperpod_job_arn",
        "error_message", "started_at", "completed_at",
    ]

    def __init__(self, session: AsyncSession):
        super().__init__(session, TrainingJobModel)
```

**代码量**: 56 行 → 8 行 (**减少 86%**)

---

## 迁移清单

### 需要修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `shared/domain/base_entity.py` | 新建 | Pydantic DomainEntity 基类 |
| `shared/infrastructure/base_repository.py` | 重写 | 使用 model_validate 自动转换 |
| **Entity 文件 (15 个)** | | |
| `modules/auth/domain/entities/user.py` | 重构 | @dataclass → BaseModel |
| `modules/training/domain/entities/training_job.py` | 重构 | @dataclass → BaseModel |
| `modules/training/domain/entities/checkpoint.py` | 重构 | @dataclass → BaseModel |
| `modules/datasets/domain/entities/dataset.py` | 重构 | @dataclass → BaseModel |
| `modules/quotas/domain/entities/resource_quota.py` | 重构 | @dataclass → BaseModel |
| `modules/spaces/domain/entities/space.py` | 重构 | @dataclass → BaseModel |
| ... | | 其他 Entity |
| **Repository 实现 (15 个)** | | |
| `modules/*/infrastructure/repositories/*_impl.py` | 简化 | 删除手写转换方法 |

### 迁移顺序（渐进式）

1. **第一批 (低风险)**
   - auth 模块：User（字段简单）
   - 预计工作量：1-2 小时

2. **第二批 (中等)**
   - datasets 模块：Dataset, DatasetVersion
   - quotas 模块：ResourceQuota
   - 预计工作量：2-3 小时

3. **第三批 (复杂)**
   - training 模块：TrainingJob, Checkpoint（字段最多）
   - spaces 模块：Space
   - 预计工作量：3-4 小时

4. **第四批 (收尾)**
   - 其他模块
   - 清理旧代码
   - 预计工作量：1-2 小时

---

## 验证计划

### 测试策略

```bash
# 每个模块迁移后运行
pytest tests/unit/modules/{module}/ -v
pytest tests/integration/modules/{module}/ -v

# 全量测试
pytest tests/ -v --cov=src

# 类型检查
mypy src/
```

### 验收标准

- [ ] 所有现有测试通过
- [ ] 枚举字段正确转换（双向）
- [ ] 验证逻辑在 Entity 层生效
- [ ] _update_model 只更新指定字段
- [ ] 类型检查无新错误
- [ ] 代码量减少 > 70%

---

## 预期收益

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| Repository 样板代码 | 780 行 | ~120 行 | **-85%** |
| 新增 Repository 工作量 | 52 行/个 | 8 行/个 | **-85%** |
| 枚举转换代码 | 手工两次 | 自动 | **消除** |
| 验证逻辑位置 | 分散 | Entity 层集中 | **统一** |
| Entity + Repository 总代码 | ~2500 行 | ~1500 行 | **-40%** |

---

## 注意事项

### Pydantic V2 vs @dataclass 差异

| 特性 | @dataclass | Pydantic V2 |
|------|-----------|-------------|
| 默认值 | `field(default_factory=...)` | `Field(default_factory=...)` |
| 可变默认值 | 需要 factory | 需要 factory |
| 验证时机 | 无 | 初始化 + 赋值 |
| 序列化 | 手动 | `.model_dump()` |
| 类型强制 | 无 | 自动转换 |

### 迁移时易错点

1. **枚举处理**: Pydantic 默认保留枚举对象，ORM 需要值
   ```python
   # Entity 中使用枚举
   status: JobStatus = JobStatus.PENDING

   # to_dict 时枚举已是 Python 对象，需要 ORM 接受
   # 或在 _update_model 中转换 value.value
   ```

2. **Optional 字段**: Pydantic V2 更严格
   ```python
   # 正确
   description: str | None = None

   # 错误（V2 会报错）
   description: str = None
   ```

3. **业务方法中修改字段**: `validate_assignment=True` 会触发验证
   ```python
   def suspend(self) -> None:
       # 这会触发 status 的验证器
       self.status = UserStatus.SUSPENDED
   ```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 验证逻辑变化导致回归 | 高 | 渐进式迁移 + 充分测试 |
| 性能影响 | 低 | Pydantic V2 Rust 核心性能优秀 |
| 学习曲线 | 中 | 团队已熟悉 Pydantic（API Schema） |
| 第三方库兼容性 | 低 | Pydantic V2 是主流选择 |
