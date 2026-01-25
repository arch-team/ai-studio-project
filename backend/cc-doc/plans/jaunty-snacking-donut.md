# 修复计划：API 响应 Schema 添加抢占相关字段

## 问题描述

API 响应 schema (`TrainingJobDetail` 和 `TrainingJobSummary`) 中缺少以下字段：
- `preemption_count`: 累计被抢占次数
- `kueue_status`: Kueue 状态

这些字段在实体和数据库模型中已存在，但未暴露给 API 响应。

## 修复范围

### 文件修改

**文件**: `backend/src/modules/training/api/schemas/responses.py`

### 修改内容

#### 1. 在 `TrainingJobSummary` 中添加字段

```python
class TrainingJobSummary(AutoMappingEntitySchema["TrainingJob"]):
    """Training job summary for list view."""

    id: int
    job_name: str
    display_name: str | None = None
    status: JobStatusEnum
    priority: JobPriorityEnum
    instance_type: str
    node_count: int
    current_epoch: int | None = None
    latest_loss: Decimal | None = None
    preemption_count: int = 0                    # 新增
    created_at: datetime
    started_at: datetime | None = None

    # ... existing _enum_mappings
```

#### 2. 在 `TrainingJobDetail` 中添加字段

```python
class TrainingJobDetail(TrainingJobSummary):
    """Training job detailed view."""

    # ... existing fields
    kueue_status: str | None = None              # 新增
    kueue_workload_name: str | None = None       # 新增
    # ... rest of fields
```

## 验证步骤

1. 运行集成测试确保无破坏性变更:
   ```bash
   cd backend && source .venv/bin/activate && pytest tests/integration/training/test_api_training_job.py -v
   ```

2. 手动验证 API 响应:
   ```bash
   # 启动服务后调用 GET /api/v1/training-jobs/{id}
   # 验证响应包含 preemption_count 和 kueue_status 字段
   ```

3. 更新评估文件标记 CE-07.4 为通过

## 风险评估

- **低风险**: 仅添加可选字段，向后兼容
- **无破坏性**: AutoMappingEntitySchema 会自动从实体映射字段
