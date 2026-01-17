# Backend 代码优化计划 (Code-Simplifier)

> **目标**: 优化 backend 项目代码质量，消除重复代码，提高可维护性
> **约束**: 保持 DDD 架构规范 (R1-R4)，不改变 API 接口

---

## 优化摘要

| 优化项 | 优先级 | 影响范围 | 风险 |
|--------|--------|----------|------|
| 消除 API 层重复工具函数 | P0 高 | 3 个模块 | 低 |
| TrainingJob 实体值对象重构 | P1 中 | training 模块 | 中 |
| Enum 转换简化 | P2 低 | 2 个模块 | 低 |

---

## Phase 1: 消除重复工具函数 (P0)

### 问题
3 个模块中存在**完全相同**的函数定义：
- `_get_owner_filter()` - 获取所有者过滤条件
- `_check_resource_owner_or_privileged()` - 权限检查
- `_calculate_total_pages()` - 分页计算

### 重复位置
```
src/modules/training/api/endpoints.py:48-70
src/modules/models/api/endpoints.py:29-49
src/modules/spaces/api/endpoints.py:22-42
```

### 已有解决方案
- `src/modules/auth/api/permissions.py` → `get_owner_filter()`, `check_resource_owner_or_privileged()`
- `src/shared/utils/pagination.py` → `calculate_total_pages()`

### 优化方案

**Step 1.1**: 修改 `training/api/endpoints.py`
```python
# 删除重复函数定义 (lines 48-70)
# 添加导入
from src.modules.auth.api.permissions import (
    get_owner_filter,
    check_resource_owner_or_privileged,
)
from src.shared.utils import calculate_total_pages

# 替换调用
# _get_owner_filter(current_user) → get_owner_filter(current_user)
# _check_resource_owner_or_privileged(...) → check_resource_owner_or_privileged(...)
# _calculate_total_pages(total, page_size) → calculate_total_pages(total, page_size)
```

**Step 1.2**: 修改 `models/api/endpoints.py` (同上)

**Step 1.3**: 修改 `spaces/api/endpoints.py` (同上)

### 关键文件
- `src/modules/training/api/endpoints.py`
- `src/modules/models/api/endpoints.py`
- `src/modules/spaces/api/endpoints.py`
- `src/modules/auth/api/permissions.py` (已有，无需修改)
- `src/shared/utils/pagination.py` (已有，无需修改)

---

## Phase 2: TrainingJob 值对象重构 (P1)

### 问题
`training_job.py` (173 行) 包含 43+ 字段，实体过于庞大。

### 已有值对象
- `TrainingMetrics` - 训练指标 (4 字段)
- `PodStatistics` - Pod 统计 (4 字段)

### 优化方案

**Step 2.1**: 使用 `TrainingMetrics` 封装指标字段
```python
# Before: 4 个独立字段
current_epoch: int | None = None
current_step: int | None = None
latest_loss: Decimal | None = None
latest_accuracy: Decimal | None = None

# After: 1 个值对象
metrics: TrainingMetrics = field(default_factory=TrainingMetrics)
```

**Step 2.2**: 使用 `PodStatistics` 封装 Pod 字段
```python
# Before: 4 个独立字段
total_pods: int | None = None
running_pods: int = 0
failed_pods: int = 0
preemption_count: int = 0

# After: 1 个值对象
pod_stats: PodStatistics = field(default_factory=PodStatistics)
```

**Step 2.3**: 创建 `TimeStatistics` 值对象
```python
@dataclass(frozen=True)
class TimeStatistics:
    """时间统计值对象"""
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None
```

**Step 2.4**: 同步更新
- ORM Model 映射
- Repository `_to_entity()` 方法
- API Schema `from_entity()` 方法

### 关键文件
- `src/modules/training/domain/entities/training_job.py`
- `src/modules/training/domain/value_objects/__init__.py`
- `src/modules/training/infrastructure/models/training_job_model.py`
- `src/modules/training/infrastructure/repositories/training_job_repository_impl.py`
- `src/modules/training/api/schemas/responses.py`

---

## Phase 3: Enum 转换简化 (P2)

### 问题
多处存在相同的 Enum 转换模式：
```python
def _to_domain_status(status: JobStatusEnum | None) -> JobStatus | None:
    if status is None:
        return None
    return JobStatus(status.value)
```

### 优化方案
使用 `EnumMapper.to_domain()` 替代：
```python
from src.shared.utils import EnumMapper

# 调用处直接使用
status=EnumMapper.to_domain(status_enum, JobStatus)
```

### 关键文件
- `src/modules/training/api/endpoints.py`
- `src/modules/quotas/api/endpoints.py`
- `src/shared/utils/enum_mapper.py` (已有)

---

## 验证方法

### 测试命令
```bash
# 1. 单元测试
pytest tests/unit/ -v

# 2. 集成测试
pytest tests/integration/ -v

# 3. 架构合规测试
pytest tests/unit/test_architecture_compliance.py -v

# 4. 代码质量检查
black src/ && ruff check src/ && mypy src/
```

### 验证清单
- [ ] 所有测试通过
- [ ] 架构合规检查通过
- [ ] Lint/Type 检查无错误
- [ ] API 端点功能正常 (手动验证)

---

## 实施顺序

1. **Phase 1** (P0) - 消除重复工具函数
   - 低风险，立即可执行
   - 预计减少 ~60 行重复代码

2. **Phase 2** (P1) - TrainingJob 值对象重构
   - 中等风险，需要同步更新多个文件
   - 可选：根据时间决定是否执行

3. **Phase 3** (P2) - Enum 转换简化
   - 低风险，可快速完成
   - 可选：根据时间决定是否执行
