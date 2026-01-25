# Datasets 模块 Docstring 精简计划

## 问题描述

datasets 模块中存在大量冗余 docstring，违反了 `backend/CLAUDE.md` 的规范：
- **规范要求**: Method docstring 1 行，Args/Returns 仅当类型签名不够清晰时才添加
- **实际情况**: 大量方法使用 10-36 行的详细 docstring，即使类型签名已完全清晰

## 改进目标

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 总代码行数 | ~4173 | ~3950 |
| 精简比例 | - | 5.3% ↓ |
| 规范符合度 | 部分 | 完全 |

---

## 修改清单

### 1. `domain/repositories/dataset_repository.py` (减少 ~26 行)

**文件路径**: `backend/src/modules/datasets/domain/repositories/dataset_repository.py`

| 方法 | 行号 | 改进前 | 改进后 |
|------|------|--------|--------|
| `list_by_owner()` | 21-46 | 15 行 | 1 行 |
| `list_public()` | 49-59 | 11 行 | 1 行 |

**改进示例**:
```python
# ❌ 改进前 (15 行)
async def list_by_owner(
    self,
    owner_id: int,
    status: DatasetStatus | None = None,
    ...
) -> tuple[list[Dataset], int]:
    """获取用户的数据集列表。

    Args:
        owner_id: 用户 ID
        status: 可选的状态过滤
        dataset_type: 可选的类型过滤
        visibility: 可选的可见性过滤
        page: 页码 (从 1 开始)
        page_size: 每页数量
        sort_by: 排序字段
        sort_order: 排序方向

    Returns:
        (数据集列表, 总数) 元组
    """

# ✅ 改进后 (1 行)
async def list_by_owner(...) -> tuple[list[Dataset], int]:
    """按所有者分页查询数据集。"""
```

---

### 2. `application/services/dataset_service.py` (减少 ~77 行)

**文件路径**: `backend/src/modules/datasets/application/services/dataset_service.py`

| 方法 | 行号 | 改进前 | 改进后 | 备注 |
|------|------|--------|--------|------|
| `create_dataset()` | 29-41 | 12 行 | 3 行 | 保留 Raises |
| `list_datasets()` | 94-129 | 36 行 | 2 行 | **最大改进** |
| `get_dataset()` | 137-147 | 11 行 | 2 行 | 保留 Raises |
| `update_dataset()` | 158-169 | 12 行 | 2 行 | 保留 Raises |
| `mark_available()` | 200-207 | 8 行 | 2 行 | 保留 Raises |
| `mark_error()` | 222-229 | 8 行 | 2 行 | 保留 Raises |

**改进示例 (list_datasets)**:
```python
# ❌ 改进前 (36 行)
async def list_datasets(
    self,
    owner_id: int | None = None,
    is_public: bool = False,
    status: DatasetStatus | None = None,
    dataset_type: DatasetType | None = None,
    visibility: DatasetVisibility | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Dataset], int]:
    """列出数据集 (支持分页和过滤)。

    根据 owner_id 和 is_public 参数决定查询范围:
    - owner_id 指定时: 查询该用户的数据集
    - is_public=True 时: 查询公开数据集
    - 两者都未指定时: 返回空列表

    Args:
        owner_id: 用户 ID (查询特定用户的数据集)
        is_public: 是否查询公开数据集
        status: 可选的状态过滤
        dataset_type: 可选的类型过滤
        visibility: 可选的可见性过滤
        page: 页码 (从 1 开始)
        page_size: 每页数量
        sort_by: 排序字段
        sort_order: 排序方向 (asc/desc)

    Returns:
        (数据集列表, 总数) 元组
    """

# ✅ 改进后 (2 行)
async def list_datasets(...) -> tuple[list[Dataset], int]:
    """列出数据集，支持按 owner_id 或公开状态查询，带分页和过滤。"""
```

---

### 3. `domain/entities/dataset.py` (减少 ~14 行)

**文件路径**: `backend/src/modules/datasets/domain/entities/dataset.py`

| 方法 | 行号 | 改进前 | 改进后 |
|------|------|--------|--------|
| `transition_to()` | 58-67 | 9 行 | 2 行 |
| `is_accessible_by()` | 110-118 | 8 行 | 1 行 |

---

## 不修改的文件

以下文件已符合规范，无需修改：

- `infrastructure/repositories/dataset_repository_impl.py` - 已使用简洁 docstring
- `infrastructure/s3/multipart_upload_client.py` - 外部接口需保留详细文档
- `infrastructure/fsx/fsx_client.py` - 外部接口需保留详细文档

---

## 参数换行说明

**结论**: 当前参数换行已符合 Black 88 字符标准，无需调整。

原因：
- 多参数方法（如 9 个参数的 `list_by_owner`）无法在 88 字符内单行
- FastAPI `Depends()` 注入代码较长，换行是合理的
- 强制单行会违反 Black 格式规范

---

## 验证方式

```bash
# 1. 格式检查
cd backend && black src/modules/datasets/ --check

# 2. Lint 检查
ruff check src/modules/datasets/

# 3. 类型检查
mypy src/modules/datasets/

# 4. 运行测试
pytest tests/unit/modules/datasets/ -v
```

---

## 执行顺序

1. 修改 `domain/repositories/dataset_repository.py`
2. 修改 `application/services/dataset_service.py`
3. 修改 `domain/entities/dataset.py`
4. 运行验证命令
