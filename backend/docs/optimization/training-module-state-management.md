# Training 模块状态管理优化总结

## 优化时间
2026-01-27

## 优化文件
- `/src/modules/training/application/services/training_job_service.py`
- `/src/modules/training/domain/value_objects/job_status.py`

## 优化内容

### 1. 提取通用方法 `_stop_job_if_running()`

**优化前**: 停止任务的逻辑在 `cancel_job()` 和 `delete_job()` 中重复
```python
# cancel_job 中
if job.status in (JobStatus.RUNNING, JobStatus.SUBMITTED):
    await self._hyperpod_client.stop_training_job(...)

# delete_job 中
if job.status in (JobStatus.RUNNING, JobStatus.SUBMITTED):
    await self._hyperpod_client.stop_training_job(...)
```

**优化后**: 提取为独立方法
```python
async def _stop_job_if_running(self, job: TrainingJob) -> None:
    """如果任务正在运行，则停止它。"""
    if job.status in (JobStatus.RUNNING, JobStatus.SUBMITTED):
        await self._hyperpod_client.stop_training_job(
            cluster_name=self._cluster_name,
            job_name=job.job_name,
        )
```

### 2. 简化字段更新逻辑 `_apply_updates()`

**优化前**: 在 `update_job()` 中逐个判断和更新字段
```python
if "priority" in data and data["priority"] is not None:
    new_priority = EnumMapper.from_string(...)
    if new_priority is not None:
        job.priority = new_priority
if "description" in data:
    job.description = data["description"]
# ... 重复模式
```

**优化后**: 使用字典映射和循环
```python
UPDATABLE_FIELDS = ["priority", "description", "max_epochs", "checkpoint_interval"]

def _apply_updates(self, job: TrainingJob, updates: dict) -> None:
    """应用更新到任务。"""
    for field in self.UPDATABLE_FIELDS:
        if field not in updates:
            continue
        value = updates[field]
        if field == "priority" and value is not None:
            # 特殊处理枚举类型
            new_priority = EnumMapper.from_string(value, JobPriority, job.priority)
            if new_priority is not None:
                job.priority = new_priority
        elif value is not None or field == "description":
            setattr(job, field, value)
```

### 3. 添加状态转换辅助类 `JobStateTransition`

**新增功能**: 在 Domain 层添加状态转换策略类
```python
class JobStateTransition:
    """任务状态转换策略辅助类。"""

    TERMINAL_STATES = {JobStatus.COMPLETED, JobStatus.FAILED}
    RUNNING_STATES = {JobStatus.RUNNING, JobStatus.SUBMITTED}

    @classmethod
    def can_transition(cls, from_status: JobStatus, to_status: JobStatus) -> bool:
        """检查状态转换是否有效。"""
        return to_status in TRAINING_JOB_STATE_TRANSITIONS.get(from_status, set())

    @classmethod
    def is_terminal(cls, status: JobStatus) -> bool:
        """检查是否为终止状态。"""
        return status in cls.TERMINAL_STATES
```

## 优化效果

### 代码质量提升
- ✅ **重复代码减少**: 提取 `_stop_job_if_running()` 消除重复
- ✅ **维护性增强**: 使用 `UPDATABLE_FIELDS` 集中管理可更新字段
- ✅ **可读性提升**: 状态转换逻辑更清晰
- ✅ **职责单一**: 每个方法职责更明确

### 测试验证
- ✅ 所有单元测试通过 (15/15)
- ✅ 所有 training 模块测试通过 (241/241)
- ✅ 代码格式化检查通过 (black)
- ✅ 代码质量检查通过 (ruff)

### 架构合规
- ✅ 遵循 DDD 原则：状态转换逻辑在 Domain 层
- ✅ 保持 API 兼容性：无接口变更
- ✅ 符合单一职责原则：方法职责明确

## 未来改进建议

1. **状态机模式**: 如果状态转换变得更复杂，可以考虑引入完整的状态机模式
2. **事件驱动**: 状态变更时发布域事件，实现更好的解耦
3. **策略模式**: 不同优先级的任务可能有不同的调度策略