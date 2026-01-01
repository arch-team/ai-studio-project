# Checkpoint管理服务

提供训练checkpoint的注册、查询、删除和S3迁移功能,支持分层存储策略。

## 功能特性

### CheckpointService

**核心功能**:
1. **注册checkpoint**: 训练脚本保存checkpoint后记录到数据库
2. **列举checkpoint**: 按训练任务查询所有checkpoint
3. **获取最新checkpoint**: 用于恢复训练
4. **删除旧checkpoint**: 清理策略(保留最近N个)
5. **路径生成**: 规范化checkpoint存储路径

### S3MigrationService

**迁移功能**:
1. **迁移到S3**: 将FSx/Local checkpoint迁移到S3长期存储
2. **从S3下载**: 从S3下载checkpoint到本地
3. **S3删除**: 从S3删除checkpoint
4. **存在性检查**: 验证S3对象是否存在

## 存储策略

### 三层存储架构

```
训练Pod → NVMe (热数据) → FSx (温数据) → S3 (冷数据)
   ↓           ↓                ↓              ↓
训练中      训练间隔        近期checkpoint   长期归档
>10GB/s     >5GB/s          <1GB/s         低成本
```

**存储类型**:
- **LOCAL (NVMe)**: 训练节点本地SSD,超高性能,训练期间频繁读写
- **FSX (Lustre)**: 共享高性能文件系统,跨节点访问,近期checkpoint
- **S3**: 对象存储,低成本长期保留,最终checkpoint归档

## API使用示例

### 1. 注册Checkpoint

训练脚本保存checkpoint后调用此接口:

```bash
curl -X POST http://localhost:8000/api/v1/checkpoints/ \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "step": 1000,
    "storage_path": "/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
    "storage_type": "LOCAL",
    "size_bytes": 1048576000,
    "epoch": 5,
    "metadata": {
      "learning_rate": 0.001,
      "optimizer": "AdamW",
      "batch_size": 32
    },
    "metrics": {
      "loss": 0.25,
      "accuracy": 0.92
    }
  }'
```

**响应**:
```json
{
  "id": 123,
  "job_id": 1,
  "step": 1000,
  "epoch": 5,
  "storage_path": "/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
  "storage_type": "LOCAL",
  "size_bytes": 1048576000,
  "checkpoint_metadata": {
    "learning_rate": 0.001,
    "optimizer": "AdamW",
    "batch_size": 32
  },
  "checkpoint_metrics": {
    "loss": 0.25,
    "accuracy": 0.92
  },
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-01T10:00:00Z"
}
```

### 2. 列举训练任务的Checkpoint

```bash
curl -X GET "http://localhost:8000/api/v1/checkpoints/jobs/1?limit=10"
```

**可选参数**:
- `storage_type`: 存储类型过滤 (LOCAL/FSX/S3)
- `limit`: 最大返回数量 (默认100)
- `offset`: 偏移量 (默认0)

**响应**:
```json
{
  "checkpoints": [
    {
      "id": 125,
      "job_id": 1,
      "step": 3000,
      "storage_type": "LOCAL",
      ...
    },
    {
      "id": 124,
      "job_id": 1,
      "step": 2000,
      "storage_type": "LOCAL",
      ...
    }
  ],
  "total": 2
}
```

### 3. 获取最新Checkpoint (恢复训练)

```bash
curl -X GET "http://localhost:8000/api/v1/checkpoints/jobs/1/latest"
```

**响应**:
```json
{
  "id": 125,
  "job_id": 1,
  "step": 3000,
  "storage_path": "/mnt/nvme/checkpoints/1/checkpoint-step-3000.pt",
  "storage_type": "LOCAL",
  ...
}
```

### 4. 清理旧Checkpoint

保留最近5个checkpoint,删除其余:

```bash
curl -X DELETE "http://localhost:8000/api/v1/checkpoints/jobs/1/cleanup?keep_last_n=5"
```

**响应**:
```json
{
  "success": true,
  "message": "清理旧checkpoint完成: deleted=10, kept=5",
  "deleted_count": 10
}
```

### 5. 迁移Checkpoint到S3

```bash
curl -X POST http://localhost:8000/api/v1/checkpoints/migrate \
  -H "Content-Type: application/json" \
  -d '{
    "checkpoint_id": 123,
    "delete_source": false
  }'
```

**响应**:
```json
{
  "success": true,
  "s3_uri": "s3://ai-training-checkpoints/checkpoints/1/step-1000-123.pt",
  "message": "Checkpoint迁移到S3成功: id=123"
}
```

## Python SDK使用

### 基本使用

```python
from sqlalchemy.ext.asyncio import AsyncSession
from services.checkpoint import CheckpointService
from models.training import CheckpointStorageType

async def save_checkpoint_example(session: AsyncSession, job_id: int):
    """注册checkpoint示例"""
    service = CheckpointService(session)

    checkpoint = await service.register_checkpoint(
        job_id=job_id,
        step=1000,
        storage_path="/mnt/nvme/checkpoints/1/checkpoint-step-1000.pt",
        storage_type=CheckpointStorageType.LOCAL,
        size_bytes=1048576000,
        epoch=5,
        metadata={"learning_rate": 0.001},
        metrics={"loss": 0.25}
    )
    print(f"Checkpoint已注册: id={checkpoint.id}, step={checkpoint.step}")


async def list_checkpoints_example(session: AsyncSession, job_id: int):
    """列举checkpoint示例"""
    service = CheckpointService(session)

    checkpoints = await service.list_checkpoints(job_id=job_id, limit=10)
    for ckpt in checkpoints:
        print(f"Checkpoint: step={ckpt.step}, type={ckpt.storage_type.value}")


async def get_latest_checkpoint_example(session: AsyncSession, job_id: int):
    """获取最新checkpoint示例(恢复训练)"""
    service = CheckpointService(session)

    latest = await service.get_latest_checkpoint(job_id=job_id)
    if latest:
        print(f"最新checkpoint: step={latest.step}, path={latest.storage_path}")
    else:
        print("未找到checkpoint")


async def cleanup_example(session: AsyncSession, job_id: int):
    """清理旧checkpoint示例"""
    service = CheckpointService(session)

    deleted_count = await service.delete_old_checkpoints(
        job_id=job_id,
        keep_last_n=5  # 保留最近5个
    )
    print(f"已删除{deleted_count}个旧checkpoint")
```

### S3迁移示例

```python
from services.checkpoint import S3MigrationService

async def migrate_to_s3_example(checkpoint):
    """迁移checkpoint到S3"""
    s3_service = S3MigrationService()

    s3_uri = await s3_service.migrate_to_s3(
        checkpoint=checkpoint,
        delete_source=False  # 保留源文件
    )
    print(f"已迁移到S3: {s3_uri}")


async def download_from_s3_example(checkpoint):
    """从S3下载checkpoint"""
    s3_service = S3MigrationService()

    local_path = await s3_service.download_from_s3(
        checkpoint=checkpoint,
        local_path="/mnt/nvme/restored/checkpoint.pt"
    )
    print(f"已下载到: {local_path}")
```

## 训练脚本集成

### PyTorch训练脚本示例

```python
import os
import torch
import requests
from pathlib import Path

class CheckpointManager:
    """Checkpoint管理器(训练脚本中使用)"""

    def __init__(self, api_base_url: str, job_id: int):
        self.api_base_url = api_base_url
        self.job_id = job_id
        self.checkpoint_dir = Path("/mnt/nvme/checkpoints") / str(job_id)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, model, optimizer, step: int, epoch: int, metrics: dict):
        """保存checkpoint并注册到平台"""
        # 1. 保存checkpoint到本地NVMe
        checkpoint_path = self.checkpoint_dir / f"checkpoint-step-{step}.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'step': step,
            'epoch': epoch,
            'metrics': metrics,
        }, checkpoint_path)

        # 2. 注册到平台API
        size_bytes = checkpoint_path.stat().st_size
        response = requests.post(
            f"{self.api_base_url}/checkpoints/",
            json={
                "job_id": self.job_id,
                "step": step,
                "storage_path": str(checkpoint_path),
                "storage_type": "LOCAL",
                "size_bytes": size_bytes,
                "epoch": epoch,
                "metadata": {
                    "learning_rate": optimizer.param_groups[0]['lr'],
                    "optimizer": type(optimizer).__name__,
                },
                "metrics": metrics
            }
        )

        if response.status_code == 201:
            print(f"✅ Checkpoint已注册: step={step}")
        else:
            print(f"❌ 注册失败: {response.text}")

    def load_latest_checkpoint(self, model, optimizer):
        """加载最新checkpoint(恢复训练)"""
        response = requests.get(
            f"{self.api_base_url}/checkpoints/jobs/{self.job_id}/latest"
        )

        if response.status_code == 404:
            print("未找到checkpoint,从头开始训练")
            return 0, 0  # start_step, start_epoch

        checkpoint_info = response.json()
        checkpoint_path = checkpoint_info['storage_path']

        # 加载checkpoint
        checkpoint = torch.load(checkpoint_path)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        print(f"✅ 已恢复训练: step={checkpoint['step']}, epoch={checkpoint['epoch']}")
        return checkpoint['step'], checkpoint['epoch']


# 训练循环示例
def train():
    # 初始化
    job_id = int(os.environ['JOB_ID'])
    ckpt_manager = CheckpointManager(
        api_base_url="http://platform-api:8000/api/v1",
        job_id=job_id
    )

    model = MyModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)

    # 恢复训练
    start_step, start_epoch = ckpt_manager.load_latest_checkpoint(model, optimizer)

    # 训练循环
    for epoch in range(start_epoch, num_epochs):
        for step, batch in enumerate(dataloader, start=start_step):
            # 训练步骤
            loss = train_step(model, batch, optimizer)

            # 每N步保存checkpoint
            if step % 1000 == 0:
                metrics = {"loss": loss.item(), "epoch": epoch}
                ckpt_manager.save_checkpoint(
                    model, optimizer, step, epoch, metrics
                )
```

## 环境变量配置

在 `.env` 文件中配置:

```bash
# Checkpoint S3存储桶
CHECKPOINT_S3_BUCKET=ai-training-checkpoints

# FSx挂载点
CHECKPOINT_FSX_MOUNT=/mnt/fsx/checkpoints

# NVMe本地存储路径
CHECKPOINT_NVME_PATH=/mnt/nvme/checkpoints

# AWS凭证(S3迁移用)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## 最佳实践

### 1. Checkpoint保存频率

- **频繁训练** (大模型): 每100-500步保存一次到LOCAL
- **长周期训练**: 每1000-5000步保存一次
- **Epoch结束**: 必须保存checkpoint

### 2. 清理策略

- **LOCAL (NVMe)**: 保留最近3-5个checkpoint
- **FSX**: 保留最近10-20个checkpoint
- **S3**: 长期保留(成本低)

推荐定时任务:
```python
# 每小时清理LOCAL,保留最近3个
await service.delete_old_checkpoints(
    job_id=job_id,
    keep_last_n=3,
    storage_type=CheckpointStorageType.LOCAL
)
```

### 3. 迁移策略

- **训练期间**: 保存到LOCAL (最快)
- **训练暂停/完成**: 迁移到FSX (共享访问)
- **7天后**: 自动迁移到S3 (长期归档)

### 4. 恢复训练

```python
# 1. 获取最新checkpoint
latest = await service.get_latest_checkpoint(job_id=job_id)

# 2. 如果在S3,先下载到LOCAL
if latest.storage_type == CheckpointStorageType.S3:
    s3_service = S3MigrationService()
    local_path = await s3_service.download_from_s3(
        checkpoint=latest,
        local_path="/mnt/nvme/restored/checkpoint.pt"
    )
else:
    local_path = latest.storage_path

# 3. 加载checkpoint恢复训练
checkpoint = torch.load(local_path)
model.load_state_dict(checkpoint['model_state_dict'])
```

## 错误处理

### 常见错误

1. **训练任务不存在** (400 Bad Request)
   - 检查 `job_id` 是否正确
   - 确认训练任务已创建

2. **源文件不存在** (400 Bad Request - 迁移时)
   - 检查 `storage_path` 是否正确
   - 确认文件未被删除

3. **S3上传失败** (500 Internal Server Error)
   - 检查AWS凭证配置
   - 检查S3存储桶权限
   - 检查网络连接

### 日志排查

```bash
# 查看checkpoint服务日志
tail -f /var/log/ai-platform/checkpoint-service.log

# 查看S3迁移日志
grep "S3迁移" /var/log/ai-platform/checkpoint-service.log
```

## 性能优化

### 1. 并行保存

训练脚本中使用异步保存:
```python
import threading

def async_save_checkpoint(model, path):
    """异步保存checkpoint(不阻塞训练)"""
    thread = threading.Thread(
        target=lambda: torch.save(model.state_dict(), path)
    )
    thread.start()
```

### 2. 分层存储加速

- **训练中**: 只保存到LOCAL NVMe (>10GB/s)
- **训练结束**: 异步迁移到FSx和S3

### 3. 压缩存储

```python
# 使用压缩减少存储空间
torch.save(checkpoint, path, _use_new_zipfile_serialization=True)
```

## 监控指标

### Checkpoint指标

- `checkpoint_total`: Checkpoint总数
- `checkpoint_size_bytes`: Checkpoint大小
- `checkpoint_save_duration`: 保存耗时
- `checkpoint_migrate_duration`: S3迁移耗时

### 告警规则

- Checkpoint保存失败率 > 5%
- S3迁移失败率 > 10%
- LOCAL存储空间 < 10%

## 分层存储自动迁移 (T041)

### StorageMigrationService

**T041核心实现**: 自动化checkpoint在NVMe/FSx/S3之间的生命周期管理

#### 迁移策略

1. **NVMe → FSx (7天后)**
   - 自动扫描超过7天的LOCAL checkpoint
   - 复制到FSx共享存储
   - 删除NVMe源文件(可配置)

2. **FSx → S3 (30天后)**
   - 自动扫描超过30天的FSX checkpoint
   - 上传到S3长期归档
   - 删除FSx源文件(可配置)

3. **最后checkpoint特殊处理**
   - 训练完成后立即迁移最后checkpoint到S3
   - 确保最终模型快速归档

#### Celery定时任务

**启动命令**:
```bash
cd backend

# 启动worker和beat (自动执行定时任务)
celery -A tasks.checkpoint_migration worker --beat --loglevel=info

# 或分别启动
celery -A tasks.checkpoint_migration worker --loglevel=info  # worker
celery -A tasks.checkpoint_migration beat --loglevel=info    # 调度器
```

**定时配置**:
- 执行时间: 每天凌晨2点
- 任务队列: `checkpoint_migration`
- 超时时间: 1小时

#### 手动迁移API

**执行完整策略**:
```bash
POST /api/v1/checkpoints/migrate/policy

# 响应:
{
  "success": true,
  "stats": {
    "nvme_to_fsx": 5,
    "fsx_to_s3": 3,
    "errors": 0
  }
}
```

**手动迁移到FSx**:
```bash
POST /api/v1/checkpoints/{checkpoint_id}/migrate/fsx?delete_source=true
```

**手动迁移到S3**:
```bash
POST /api/v1/checkpoints/{checkpoint_id}/migrate/s3-from-fsx?delete_source=true
```

#### 配置参数

在 `backend/.env` 中配置:

```bash
# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0

# 迁移策略阈值
CHECKPOINT_MIGRATION_NVME_TO_FSX_DAYS=7   # NVMe → FSx (天数)
CHECKPOINT_MIGRATION_FSX_TO_S3_DAYS=30    # FSx → S3 (天数)
CHECKPOINT_MIGRATION_ENABLED=true         # 是否启用自动迁移
```

#### Python SDK使用

```python
from services.checkpoint.storage_migration_service import StorageMigrationService

async def migration_example(session: AsyncSession):
    service = StorageMigrationService(session)

    # 手动迁移: NVMe → FSx
    success = await service.migrate_nvme_to_fsx(checkpoint, delete_source=True)

    # 手动迁移: FSx → S3
    success = await service.migrate_fsx_to_s3(checkpoint, delete_source=True)

    # 执行完整策略
    stats = await service.run_migration_policy()
    print(f"迁移完成: {stats}")
```

#### 监控和告警

**关键指标**:
- `checkpoint_migration_success_rate`: 迁移成功率
- `checkpoint_migration_latency`: 迁移延迟
- `checkpoint_storage_usage`: 各层存储使用率

**查看任务状态**:
```bash
# 查看活动任务
celery -A tasks.checkpoint_migration inspect active

# 查看统计信息
celery -A tasks.checkpoint_migration inspect stats

# 查看定时任务
celery -A tasks.checkpoint_migration inspect scheduled
```

## 相关文档

- [训练任务管理](../training/README.md)
- [模型存储服务](../storage/README.md)
- [K8s集成文档](../k8s/README.md)
- [T041任务规范](/specs/001-ai-training-platform/plan.md#t041-分层存储策略nvmefsx-s3)
