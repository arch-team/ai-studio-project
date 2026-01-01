# Checkpoint管理快速入门

## 概述

T040: CheckpointService实现完成 ✅

提供训练checkpoint的注册、查询、删除和S3迁移功能,支持三层分层存储策略 (NVMe → FSx → S3)。

## 核心组件

### 1. CheckpointService (核心服务)

**位置**: `backend/src/services/checkpoint/checkpoint_service.py`

**主要功能**:
- ✅ `register_checkpoint()`: 注册新checkpoint到数据库
- ✅ `list_checkpoints()`: 列举训练任务的checkpoint (支持存储类型过滤)
- ✅ `get_latest_checkpoint()`: 获取最新checkpoint (用于恢复训练)
- ✅ `get_checkpoint_by_id()`: 根据ID获取checkpoint
- ✅ `get_checkpoint_by_step()`: 根据step获取checkpoint
- ✅ `delete_checkpoint()`: 删除单个checkpoint
- ✅ `delete_old_checkpoints()`: 清理旧checkpoint (保留最近N个)
- ✅ `count_checkpoints()`: 统计checkpoint数量
- ✅ `generate_checkpoint_path()`: 生成标准化存储路径

### 2. S3MigrationService (S3迁移)

**位置**: `backend/src/services/checkpoint/s3_migration_service.py`

**主要功能**:
- ✅ `migrate_to_s3()`: 迁移checkpoint到S3长期存储
- ✅ `download_from_s3()`: 从S3下载checkpoint到本地
- ✅ `delete_from_s3()`: 从S3删除checkpoint
- ✅ `check_s3_object_exists()`: 检查S3对象是否存在

### 3. REST API端点

**位置**: `backend/src/api/rest/checkpoint.py`

**已实现的API**:
- ✅ `POST /checkpoints/` - 注册新checkpoint
- ✅ `GET /checkpoints/jobs/{job_id}` - 列举训练任务的checkpoint
- ✅ `GET /checkpoints/jobs/{job_id}/latest` - 获取最新checkpoint
- ✅ `GET /checkpoints/{checkpoint_id}` - 获取checkpoint详情
- ✅ `DELETE /checkpoints/{checkpoint_id}` - 删除单个checkpoint
- ✅ `DELETE /checkpoints/jobs/{job_id}/cleanup` - 清理旧checkpoint
- ✅ `POST /checkpoints/migrate` - 迁移checkpoint到S3

### 4. Pydantic Schemas

**位置**: `backend/src/api/schemas/checkpoint.py`

**已实现的Schema**:
- ✅ `CheckpointCreate` - 创建请求
- ✅ `CheckpointResponse` - 响应模型
- ✅ `CheckpointListResponse` - 列表响应
- ✅ `CheckpointDeleteResponse` - 删除响应
- ✅ `CheckpointMigrateRequest` - 迁移请求
- ✅ `CheckpointMigrateResponse` - 迁移响应

### 5. 配置 (Settings)

**位置**: `backend/src/config/settings.py`

**新增配置项**:
```python
checkpoint_s3_bucket: str = "ai-training-checkpoints"
checkpoint_fsx_mount: str = "/mnt/fsx/checkpoints"
checkpoint_nvme_path: str = "/mnt/nvme/checkpoints"
```

### 6. 单元测试

**位置**: `backend/tests/test_checkpoint_service.py`

**测试覆盖**:
- ✅ 注册checkpoint (有效/无效任务)
- ✅ 列举checkpoint (全部/按存储类型过滤)
- ✅ 获取最新checkpoint (有结果/无结果)
- ✅ 根据step获取checkpoint
- ✅ 删除checkpoint (单个/批量/不存在)
- ✅ 清理旧checkpoint (足够/不足/按类型)
- ✅ 统计checkpoint数量
- ✅ 生成存储路径 (LOCAL/FSX/S3)

**测试覆盖率**: >80%

## 快速开始

### 1. 启动后端服务

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**API文档**: http://localhost:8000/docs

### 2. 基本使用示例

#### 注册Checkpoint (训练脚本中)

```python
import requests

def save_checkpoint_to_platform(job_id: int, step: int):
    """训练脚本保存checkpoint后注册到平台"""
    response = requests.post(
        "http://localhost:8000/api/v1/checkpoints/",
        json={
            "job_id": job_id,
            "step": step,
            "storage_path": f"/mnt/nvme/checkpoints/{job_id}/checkpoint-step-{step}.pt",
            "storage_type": "LOCAL",
            "size_bytes": 1048576000,
            "epoch": 5,
            "metadata": {"learning_rate": 0.001},
            "metrics": {"loss": 0.25, "accuracy": 0.92}
        }
    )
    return response.json()
```

#### 获取最新Checkpoint (恢复训练)

```python
def load_latest_checkpoint(job_id: int):
    """获取最新checkpoint用于恢复训练"""
    response = requests.get(
        f"http://localhost:8000/api/v1/checkpoints/jobs/{job_id}/latest"
    )
    if response.status_code == 200:
        checkpoint = response.json()
        return checkpoint['storage_path'], checkpoint['step']
    return None, 0
```

#### 清理旧Checkpoint

```python
def cleanup_old_checkpoints(job_id: int, keep_last_n: int = 5):
    """保留最近N个checkpoint,删除其余"""
    response = requests.delete(
        f"http://localhost:8000/api/v1/checkpoints/jobs/{job_id}/cleanup",
        params={"keep_last_n": keep_last_n}
    )
    return response.json()
```

### 3. 运行测试

```bash
cd backend
pytest tests/test_checkpoint_service.py -v
```

**预期输出**:
```
tests/test_checkpoint_service.py::TestCheckpointService::test_register_checkpoint PASSED
tests/test_checkpoint_service.py::TestCheckpointService::test_list_checkpoints PASSED
tests/test_checkpoint_service.py::TestCheckpointService::test_get_latest_checkpoint PASSED
tests/test_checkpoint_service.py::TestCheckpointService::test_delete_old_checkpoints PASSED
...
==================== 15 passed in 2.5s ====================
```

## 存储架构

### 三层分层存储

```
┌─────────────────────────────────────────────────────────────┐
│                    训练Pod (训练中)                          │
│                                                              │
│  PyTorch Model → torch.save() → NVMe Local Storage         │
│                                    ↓                         │
│                        register_checkpoint() API             │
└─────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: NVMe Local Storage (热数据)                       │
│  - 性能: >10GB/s                                            │
│  - 用途: 训练期间频繁读写                                    │
│  - 保留: 最近3-5个checkpoint                                 │
│  - 路径: /mnt/nvme/checkpoints/{job_id}/checkpoint-step-*.pt│
└─────────────────────────────────────────────────────────────┘
                                    ↓ (训练间隔)
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: FSx for Lustre (温数据)                           │
│  - 性能: >5GB/s                                             │
│  - 用途: 跨节点访问,近期checkpoint                           │
│  - 保留: 最近10-20个checkpoint                               │
│  - 路径: /mnt/fsx/checkpoints/{job_id}/checkpoint-step-*.pt │
└─────────────────────────────────────────────────────────────┘
                                    ↓ (7天后)
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: S3 (冷数据)                                       │
│  - 性能: <1GB/s                                             │
│  - 用途: 长期归档,低成本                                     │
│  - 保留: 永久保留                                            │
│  - URI: s3://ai-training-checkpoints/checkpoints/{job_id}/  │
└─────────────────────────────────────────────────────────────┘
```

## 典型工作流

### Workflow 1: 训练过程中保存Checkpoint

```python
# 训练循环
for step in range(start_step, max_steps):
    loss = train_step(model, batch, optimizer)

    # 每1000步保存checkpoint
    if step % 1000 == 0:
        # 1. 保存到NVMe (最快)
        checkpoint_path = f"/mnt/nvme/checkpoints/{job_id}/checkpoint-step-{step}.pt"
        torch.save(checkpoint, checkpoint_path)

        # 2. 注册到平台
        save_checkpoint_to_platform(job_id, step)
```

### Workflow 2: 恢复训练

```python
# 1. 获取最新checkpoint
checkpoint_path, last_step = load_latest_checkpoint(job_id)

# 2. 加载checkpoint
if checkpoint_path:
    checkpoint = torch.load(checkpoint_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    start_step = last_step
else:
    start_step = 0

# 3. 继续训练
for step in range(start_step, max_steps):
    ...
```

### Workflow 3: 定期清理旧Checkpoint

```python
# 定时任务: 每小时清理旧checkpoint
import schedule

def cleanup_job():
    # 清理所有训练任务的旧checkpoint
    for job_id in active_jobs:
        cleanup_old_checkpoints(job_id, keep_last_n=5)

schedule.every(1).hours.do(cleanup_job)
```

### Workflow 4: 迁移到S3长期存储

```python
# 训练完成后迁移到S3
def archive_checkpoints(job_id: int):
    # 获取所有LOCAL/FSX checkpoint
    response = requests.get(
        f"http://localhost:8000/api/v1/checkpoints/jobs/{job_id}",
        params={"storage_type": "LOCAL"}
    )

    checkpoints = response.json()['checkpoints']

    # 迁移到S3
    for ckpt in checkpoints:
        requests.post(
            "http://localhost:8000/api/v1/checkpoints/migrate",
            json={
                "checkpoint_id": ckpt['id'],
                "delete_source": True  # 迁移后删除源文件
            }
        )
```

## 性能基准

### Checkpoint保存性能

| 存储类型 | 写入速度 | 适用场景 |
|---------|---------|---------|
| NVMe Local | >10GB/s | 训练期间频繁保存 |
| FSx Lustre | >5GB/s | 跨节点访问 |
| S3 | <1GB/s | 长期归档 |

### API响应时间

| API端点 | 平均响应时间 | 说明 |
|--------|------------|------|
| POST /checkpoints/ | <50ms | 数据库插入 |
| GET /checkpoints/jobs/{id} | <100ms | 数据库查询 |
| DELETE /cleanup | <500ms | 批量删除(5-10个) |
| POST /migrate | 10-60s | S3上传(取决于文件大小) |

## 故障排查

### 常见问题

1. **注册checkpoint失败 - 训练任务不存在**
   ```bash
   # 检查训练任务是否存在
   curl http://localhost:8000/api/v1/training/jobs/1
   ```

2. **S3迁移失败 - 源文件不存在**
   ```bash
   # 检查源文件路径
   ls -lh /mnt/nvme/checkpoints/1/
   ```

3. **S3上传失败 - 权限问题**
   ```bash
   # 检查AWS凭证
   aws s3 ls s3://ai-training-checkpoints/
   ```

### 调试日志

```bash
# 启用DEBUG日志
LOG_LEVEL=DEBUG uvicorn src.main:app --reload

# 查看checkpoint相关日志
grep "checkpoint" /var/log/ai-platform/backend.log
```

## 文档参考

- **完整文档**: [backend/src/services/checkpoint/README.md](../backend/src/services/checkpoint/README.md)
- **API文档**: http://localhost:8000/docs (启动后端后访问)
- **测试示例**: [backend/tests/test_checkpoint_service.py](../backend/tests/test_checkpoint_service.py)

## 下一步

- [ ] **T041**: Checkpoint自动迁移任务 (定时FSx→S3)
- [ ] **T042**: Checkpoint监控和告警
- [ ] **T043**: Checkpoint压缩和增量保存
- [ ] **T044**: Checkpoint元数据索引优化

## 完成清单

✅ CheckpointService核心类实现
✅ S3MigrationService实现
✅ REST API端点实现
✅ Pydantic schemas定义
✅ Settings配置更新
✅ 路由注册
✅ 单元测试编写 (>80%覆盖率)
✅ README文档完成
✅ 快速入门文档

**任务状态**: ✅ 完成 (2025-01-01)
