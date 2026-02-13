# 代码风格规范 (Code Style)

> **职责**: Python 代码风格规范，定义类型提示、命名和 Docstring 原则。

---

## 0. 速查卡片

### 类型提示速查

| 规则 | 示例 |
|------|------|
| ✅ 所有公共接口必须有类型提示 | `def get_user(user_id: int) -> User \| None:` |
| ✅ 使用 `X \| None` 代替 `Optional[X]` | `name: str \| None = None` |
| ✅ 使用内置泛型 (Python 3.9+) | `list[str]`, `dict[str, int]` |
| ❌ 禁止使用 `Any` | 使用 `TypeVar` 或具体类型替代 |

### 命名速查

| 元素 | 样式 | 示例 |
|------|------|------|
| 函数/变量 | `snake_case` | `get_user_by_id` |
| 类 | `PascalCase` | `UserRepository` |
| 常量 | `UPPER_SNAKE` | `MAX_RETRY` |
| 私有 | `_prefix` | `_cache` |
| 类型变量 | `PascalCase` + T | `EntityT` |
| 模块/包 | `snake_case` | `user_repository.py` |
| Problem 异常 | `PascalCase` + Error | `TrainingJobNotFoundError` |

### Docstring 速查

```
类型自解释 → 省略 Docstring | 有副作用/异常 → 说明行为
```

### 异步代码速查

```python
# ✅ 正确 - 并发执行独立任务
results = await asyncio.gather(task1(), task2())

# ✅ 正确 - 上下文管理
async with get_db_session() as session: ...

# ❌ 错误 - 可并行时顺序执行
user = await fetch_user(user_id)
permissions = await fetch_permissions(user_id)
```

### 自动检查项 (无需人工关注)

导入排序 (ruff isort) | 行长度 120 字符 (black) | 空行规范 | 格式化风格

---

## 1. 行长度规范

**规则**: 单行不超过 120 字符才换行。由 black 自动处理。

```python
# ✅ 120 字符内保持单行
response = await client.post("/api/v1/training-jobs", json={"name": "test", "config": config, "owner_id": user.id})

# ✅ 超过 120 字符时换行
response = await client.post(
    "/api/v1/training-jobs",
    json={"name": "very-long-training-job-name", "description": "A detailed description", "config": complex_config},
)
```

---

## 2. 类型提示 (Type Hints)

```python
# 泛型类模式
T = TypeVar("T")
class Repository(Generic[T]):
    def get(self, id: int) -> T | None: ...
```

---

## 3. 命名规范

### 命名原则

1. **清晰优于简洁**: `get_user_by_email()` 优于 `get_user()`
2. **动词开头的方法**: `create_user()`, `validate_input()`, `calculate_total()`
3. **布尔值命名**: `is_active`, `has_permission`, `can_edit`
4. **集合命名使用复数**: `users`, `items`, `training_jobs`

---

## 4. Docstring 规范

> **类型即文档**: 类型提示 + 好命名 = 自解释代码。Docstring 只写类型无法表达的内容。

| 场景 | 要求 |
|------|------|
| 类/模块 | ✅ 一句话描述职责 |
| 方法 - 类型自解释 | ❌ 省略 |
| 方法 - 有副作用/异常 | ✅ 说明行为 |
| 私有方法 | ❌ 省略 |
| `__init__` | ❌ 无需文档 |

```python
# ❌ 冗余 - 类型已自解释
async def get_by_id(self, id: int) -> Dataset | None:
    """根据 ID 获取数据集。
    Args: id: Dataset ID
    Returns: Dataset if found
    """

# ✅ 简洁
async def get_by_id(self, id: int) -> Dataset | None:
    """根据 ID 获取数据集。"""

# ✅ 保留 Raises
async def create(self, data: dict) -> Dataset:
    """创建数据集。

    Raises:
        DuplicateEntityError: 如果 name+version 已存在
    """
```

---

## 5. 行内注释规范

```python
# ❌ 多余 - 代码已自解释
app.add_middleware(CORSMiddleware, ...)  # Configure CORS

# ✅ 有价值 - 解释"为什么"
# Burst decay prevents resource hoarding while allowing spikes
burst_factor = math.exp(-elapsed / TAU)
```

### 何时需要详细注释

- 复杂算法或公式
- 非显而易见的业务规则
- 临时解决方案 (需包含 TODO + issue 编号)
- 性能优化的权衡说明

---

## 6. 异步代码规范

```python
# ✅ 正确 - asyncio.gather 并发执行独立任务
user, permissions = await asyncio.gather(
    fetch_user(user_id),
    fetch_permissions(user_id),
)

# ❌ 错误 - 可并行时顺序执行，浪费时间
user = await fetch_user(user_id)
permissions = await fetch_permissions(user_id)

# ❌ 错误 - 在已有事件循环中使用 asyncio.run
def get_user(user_id: int) -> User | None:
    return asyncio.run(self._fetch_user(user_id))  # 禁止
```

---

## 7. 导入规范

> 导入分组排序由 Ruff (isort) 自动处理，以下为人工需关注的规则。

- ✅ 具体导入: `from src.shared.domain import PydanticEntity`
- ❌ 通配符导入: `from src.shared.domain import *`
- ✅ 长路径别名: `import sagemaker_client as sagemaker`

---

## 检查清单

完整检查清单见 [checklist.md](checklist.md) §代码风格
