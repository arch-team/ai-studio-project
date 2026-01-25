# Phase 4 US2 - 数据集管理 API 实施计划

## 实施范围

**用户请求**: Phase 4 US2 数据集管理的数据表迁移、SQLAlchemy 模型、后端 API 端点

**涉及任务**:
- [X] T039 - datasets 表迁移 (已完成)
- [ ] T040 - Dataset 模型 (部分完成，需验证)
- [ ] T041 - POST /datasets 端点
- [ ] T042 - GET /datasets 端点
- [ ] T043 - GET /datasets/{id} 端点
- [ ] T044 - PUT/PATCH /datasets/{id} 端点
- [ ] T045 - DELETE /datasets/{id} 端点
- [ ] T046 - POST /datasets/{id}/versions 端点

**不包括** (后续阶段):
- T047-T048 存储集成服务
- T049-T052 前端页面

---

## 现有实现状态

### 已完成 ✅

| 组件 | 文件路径 | 状态 |
|------|---------|------|
| 领域实体 | `domain/entities/dataset.py` | ✅ 完整 (状态转换、访问控制) |
| 值对象/枚举 | `domain/value_objects/dataset_enums.py` | ✅ 完整 |
| Repository 接口 | `domain/repositories/dataset_repository.py` | ✅ 完整 |
| ORM 模型 | `infrastructure/models/dataset_model.py` | ✅ 完整 |
| Repository 实现 | `infrastructure/repositories/dataset_repository_impl.py` | ✅ 完整 |
| 单元测试 | `tests/unit/modules/datasets/` | ✅ 存在 (entity, model, value_objects) |

### 待实现 ❌

| 组件 | 文件路径 | 状态 |
|------|---------|------|
| API Schemas | `api/schemas/requests.py`, `responses.py` | ❌ 不存在 |
| Application Service | `application/services/dataset_service.py` | ❌ 不存在 |
| API Dependencies | `api/dependencies.py` | ❌ 不存在 |
| API Endpoints | `api/endpoints.py` | ❌ 只有 health_check |
| 集成测试 | `tests/integration/datasets/` | ❌ 不存在 |

---

## TDD 实施步骤

### Step 1: API Schemas (T040 补充)

**目标**: 基于 `contracts/datasets-api.yaml` 创建 Pydantic 请求/响应模型

**TDD 流程**:

1. **🔴 Red**: 编写 schema 测试
   - 文件: `backend/tests/unit/modules/datasets/api/test_schemas.py`
   - 测试: 验证字段、枚举映射、from_entity 方法

2. **🟢 Green**: 实现 schemas
   - `backend/src/modules/datasets/api/schemas/__init__.py`
   - `backend/src/modules/datasets/api/schemas/requests.py`
     - `CreateDatasetRequest` (name, storage_type, storage_uri, dataset_type, ...)
     - `UpdateDatasetRequest` (description, tags, visibility)
   - `backend/src/modules/datasets/api/schemas/responses.py`
     - `DatasetSummary` (列表视图)
     - `DatasetDetail` (详情视图)
     - `DatasetListResponse` (分页响应)
     - 枚举: `DatasetStorageTypeEnum`, `DatasetTypeEnum`, `DatasetStatusEnum`, `DatasetVisibilityEnum`

3. **🔄 Refactor**: 确保符合 `AutoMappingEntitySchema` 模式

### Step 2: Application Service (T040 补充)

**目标**: 创建 DatasetService 封装业务逻辑

**TDD 流程**:

1. **🔴 Red**: 编写 service 单元测试
   - 文件: `backend/tests/unit/modules/datasets/application/test_dataset_service.py`
   - 测试: create, get, list, update, delete, create_version

2. **🟢 Green**: 实现 service
   - `backend/src/modules/datasets/application/services/dataset_service.py`
   - 继承 `EnhancedBaseService[Dataset, int]`
   - 方法:
     - `create_dataset(owner_id, data)` - 校验唯一性，创建实体
     - `get_dataset(dataset_id)` - 获取详情
     - `list_datasets(filters, pagination)` - 分页列表
     - `update_dataset(dataset_id, data)` - 更新元数据
     - `delete_dataset(dataset_id)` - 软删除
     - `create_version(dataset_id, version)` - 创建新版本

3. **🔄 Refactor**: 提取公共逻辑

### Step 3: API Dependencies

**目标**: 创建依赖注入函数

**文件**: `backend/src/modules/datasets/api/dependencies.py`

```python
async def get_dataset_repository(session: AsyncSession = Depends(get_db)) -> IDatasetRepository:
    return DatasetRepositoryImpl(session)

async def get_dataset_service(
    repository: IDatasetRepository = Depends(get_dataset_repository),
) -> DatasetService:
    return DatasetService(repository=repository)
```

### Step 4: API Endpoints (T041-T046)

**目标**: 实现 REST 端点

**TDD 流程**:

1. **🔴 Red**: 编写集成测试
   - 文件: `backend/tests/integration/datasets/test_datasets_api.py`
   - 测试覆盖:
     - T041: POST /datasets - 创建数据集
     - T042: GET /datasets - 查询列表 (分页、过滤)
     - T043: GET /datasets/{id} - 查询详情
     - T044: PATCH /datasets/{id} - 更新元数据
     - T045: DELETE /datasets/{id} - 删除数据集
     - T046: POST /datasets/{id}/versions - 创建版本
     - 权限测试: 仅 owner 或 admin 可修改/删除

2. **🟢 Green**: 实现 endpoints
   - `backend/src/modules/datasets/api/endpoints.py`
   - 遵循 training 模块的实现模式

3. **🔄 Refactor**: 统一错误处理

### Step 5: 路由注册

**文件**: `backend/src/router.py`

```python
from src.modules.datasets.api.endpoints import router as datasets_router
api_router.include_router(datasets_router, prefix="/datasets", tags=["Datasets"])
```

---

## 关键文件清单

### 需要创建的文件

```
backend/src/modules/datasets/
├── api/
│   ├── dependencies.py        # 依赖注入
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py        # 请求模型
│       └── responses.py       # 响应模型
└── application/
    └── services/
        └── dataset_service.py # 业务服务

backend/tests/
├── unit/modules/datasets/
│   ├── api/
│   │   └── test_schemas.py
│   └── application/
│       └── test_dataset_service.py
└── integration/datasets/
    └── test_datasets_api.py
```

### 需要修改的文件

```
backend/src/modules/datasets/api/endpoints.py  # 添加业务端点
backend/src/modules/datasets/api/schemas/__init__.py  # 导出
backend/src/modules/datasets/application/services/__init__.py  # 导出
backend/src/router.py  # 注册路由
specs/001-ai-training-platform/tasks.md  # 标记完成状态
```

---

## 验证步骤

### 单元测试

```bash
# Schema 测试
pytest backend/tests/unit/modules/datasets/api/test_schemas.py -v

# Service 测试
pytest backend/tests/unit/modules/datasets/application/test_dataset_service.py -v
```

### 集成测试

```bash
# API 端点测试
pytest backend/tests/integration/datasets/test_datasets_api.py -v
```

### 全部测试

```bash
pytest backend/tests/unit/modules/datasets/ -v
pytest backend/tests/integration/datasets/ -v
```

### 代码质量

```bash
cd backend && black src/modules/datasets/ tests/ && ruff check src/modules/datasets/ tests/ && mypy src/modules/datasets/
```

---

## API 契约参考

基于 `contracts/datasets-api.yaml`:

| 端点 | 方法 | 请求体 | 响应 |
|------|------|-------|------|
| `/datasets` | GET | Query: page, page_size, dataset_type, storage_type, owner_id, visibility | `DatasetListResponse` |
| `/datasets` | POST | `CreateDatasetRequest` | `DatasetDetail` (201) |
| `/datasets/{id}` | GET | - | `DatasetDetail` |
| `/datasets/{id}` | PATCH | `UpdateDatasetRequest` | `DatasetDetail` |
| `/datasets/{id}` | DELETE | - | 204 No Content |

**注意**: API 契约中没有 `/datasets/{id}/versions` 端点，但 tasks.md T046 要求实现，将按 task 描述补充实现。

---

## 实施顺序

```
Step 1: API Schemas (TDD)
    ↓
Step 2: Application Service (TDD)
    ↓
Step 3: API Dependencies
    ↓
Step 4: API Endpoints (TDD)
    ↓
Step 5: 路由注册 + 验证
    ↓
更新 tasks.md 标记完成
```

---

## 完成标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码质量检查通过 (black, ruff, mypy)
- [ ] API 响应符合 `contracts/datasets-api.yaml`
- [ ] tasks.md 中 T040-T046 标记为 [X]
