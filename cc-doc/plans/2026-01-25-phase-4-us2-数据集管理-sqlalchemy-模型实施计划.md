# Phase 4: US2 数据集管理 - SQLAlchemy 模型实施计划

**任务**: T040 - 创建 Dataset 模型
**Branch**: `001-ai-training-platform-ddd-mm`
**Date**: 2026-01-25

## 概述

本计划涵盖 Phase 4 中 SQLAlchemy 模型子阶段的实施，按照 TDD 工作流完成 T040 任务。

### 前置条件

- [x] T039 - datasets 表迁移已完成 (`20260125_100100_9a1b2c3d4e5f_create_datasets.py`)
- [x] datasets 模块目录结构已创建

### Checklist 状态

| Checklist | 状态 | 说明 |
|-----------|------|------|
| architecture-review.md | N/A | 架构检查清单，非功能检查项 |
| ddd-modular-clean-architecture.md | N/A | DDD 架构规范参考 |
| task-governance.md | N/A | Task Governance 检查清单 |

> 无阻塞性检查项，可继续实施。

---

## T040 任务分解

### 任务目标

创建 Dataset 领域实体 + ORM 模型，遵循 DDD + Clean Architecture 架构模式：
1. **领域实体**: `backend/src/modules/datasets/domain/entities/dataset.py`
2. **值对象**: `backend/src/modules/datasets/domain/value_objects/` (枚举类型)
3. **ORM 模型**: `backend/src/modules/datasets/infrastructure/models/dataset_model.py`
4. **仓库接口**: `backend/src/modules/datasets/domain/repositories/dataset_repository.py`

### TDD 实施步骤

#### Step 1: 创建值对象 (枚举类型)

**文件**: `backend/src/modules/datasets/domain/value_objects/`

需要创建的枚举:
- `DatasetStorageType`: FSX, S3, EFS
- `DatasetType`: IMAGE, TEXT, AUDIO, VIDEO, TABULAR, CUSTOM
- `DatasetVisibility`: PUBLIC, PRIVATE, RESTRICTED
- `DatasetStatus`: AVAILABLE, PREPARING, ARCHIVED, ERROR

**测试文件**: `backend/tests/unit/modules/datasets/domain/test_value_objects.py`

#### Step 2: 创建领域实体

**文件**: `backend/src/modules/datasets/domain/entities/dataset.py`

领域实体职责:
- 封装数据集业务逻辑
- 版本控制逻辑 (名称+版本唯一)
- 状态转换验证
- 访问权限检查

**测试文件**: `backend/tests/unit/modules/datasets/domain/test_dataset_entity.py`

测试用例:
- 创建有效数据集
- 验证必填字段
- 状态转换规则
- 版本比较逻辑

#### Step 3: 创建仓库接口

**文件**: `backend/src/modules/datasets/domain/repositories/dataset_repository.py`

接口方法:
- `get_by_id(id: int) -> Optional[Dataset]`
- `get_by_name_and_version(name: str, version: str) -> Optional[Dataset]`
- `list_by_owner(owner_id: int, ...) -> list[Dataset]`
- `add(entity: Dataset) -> Dataset`
- `update(entity: Dataset) -> Dataset`
- `delete(id: int) -> bool`
- `exists(id: int) -> bool`

#### Step 4: 创建 ORM 模型

**文件**: `backend/src/modules/datasets/infrastructure/models/dataset_model.py`

模型字段 (基于 data-model.md):
- `id`: BigInteger, PK
- `name`: String(128), NOT NULL
- `description`: Text, nullable
- `version`: String(32), default 'v1'
- `storage_type`: Enum (FSX/S3/EFS), default FSX
- `storage_uri`: String(512), NOT NULL
- `total_size_bytes`: BigInteger, nullable
- `file_count`: Integer, nullable
- `dataset_type`: Enum, NOT NULL
- `data_format`: String(64), nullable
- `tags`: JSON, nullable
- `visibility`: Enum, default PRIVATE
- `owner_id`: BigInteger, FK -> users.id
- `status`: Enum, default PREPARING
- `created_at`, `updated_at`, `last_accessed_at`: DateTime

关系:
- `owner`: relationship -> UserModel

**测试文件**: `backend/tests/unit/modules/datasets/infrastructure/test_dataset_model.py`

#### Step 5: 创建仓库实现

**文件**: `backend/src/modules/datasets/infrastructure/repositories/dataset_repository_impl.py`

---

## 关键文件清单

### 新建文件

| 路径 | 类型 | 说明 |
|------|------|------|
| `backend/src/modules/datasets/domain/value_objects/__init__.py` | 代码 | 值对象导出 |
| `backend/src/modules/datasets/domain/value_objects/storage_type.py` | 代码 | DatasetStorageType 枚举 |
| `backend/src/modules/datasets/domain/value_objects/dataset_type.py` | 代码 | DatasetType 枚举 |
| `backend/src/modules/datasets/domain/value_objects/visibility.py` | 代码 | DatasetVisibility 枚举 |
| `backend/src/modules/datasets/domain/value_objects/status.py` | 代码 | DatasetStatus 枚举 |
| `backend/src/modules/datasets/domain/entities/dataset.py` | 代码 | Dataset 领域实体 |
| `backend/src/modules/datasets/domain/repositories/dataset_repository.py` | 代码 | IDatasetRepository 接口 |
| `backend/src/modules/datasets/infrastructure/models/dataset_model.py` | 代码 | DatasetModel ORM |
| `backend/src/modules/datasets/infrastructure/repositories/dataset_repository_impl.py` | 代码 | 仓库实现 |
| `backend/tests/unit/modules/datasets/domain/test_value_objects.py` | 测试 | 值对象测试 |
| `backend/tests/unit/modules/datasets/domain/test_dataset_entity.py` | 测试 | 领域实体测试 |
| `backend/tests/unit/modules/datasets/infrastructure/test_dataset_model.py` | 测试 | ORM 模型测试 |

### 修改文件

| 路径 | 修改内容 |
|------|---------|
| `backend/src/modules/datasets/domain/__init__.py` | 导出 Dataset 实体 |
| `backend/src/modules/datasets/domain/entities/__init__.py` | 导出 Dataset |
| `backend/src/modules/datasets/domain/repositories/__init__.py` | 导出 IDatasetRepository |
| `backend/src/modules/datasets/infrastructure/models/__init__.py` | 导出 DatasetModel |
| `backend/src/modules/datasets/infrastructure/repositories/__init__.py` | 导出 DatasetRepositoryImpl |
| `specs/001-ai-training-platform/tasks.md` | 标记 T040 完成 |

---

## 架构合规性要点

### DDD + Clean Architecture 规则

1. **Domain 层隔离**: Dataset 实体不依赖任何外部模块
2. **依赖倒置**: ORM 模型实现 Domain 层定义的仓库接口
3. **值对象不可变**: 枚举类型继承自 Python Enum
4. **ORM FK 例外**: 允许导入 UserModel 定义外键关系

### 参考实现

- 领域实体模式: `modules/training/domain/entities/training_job.py`
- ORM 模型模式: `modules/training/infrastructure/models/training_job_model.py`
- 值对象模式: `modules/training/domain/value_objects/`

---

## 验证方法

```bash
# 运行单元测试
pytest backend/tests/unit/modules/datasets/ -v

# 架构合规检查
pytest backend/tests/architecture/ -v

# 类型检查
mypy backend/src/modules/datasets/

# 代码格式
black backend/src/modules/datasets/ && ruff check backend/src/modules/datasets/
```

---

## 时间估算

| 步骤 | 预估时间 |
|------|---------|
| Step 1: 值对象 + 测试 | 0.5h |
| Step 2: 领域实体 + 测试 | 1h |
| Step 3: 仓库接口 | 0.5h |
| Step 4: ORM 模型 + 测试 | 1h |
| Step 5: 仓库实现 | 0.5h |
| 代码审查/修复 | 0.5h |
| **总计** | **4h** |
