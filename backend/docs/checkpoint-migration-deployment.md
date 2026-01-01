# Checkpoint分层存储迁移部署指南

T041任务实现: 自动化checkpoint在NVMe/FSx/S3之间的生命周期管理

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     训练Pod (K8s)                            │
│  保存checkpoint → /mnt/nvme/checkpoints (NVMe本地存储)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ 7天后 (Celery定时任务)
┌─────────────────────────────────────────────────────────────┐
│              FSx for Lustre (共享存储)                       │
│       /mnt/fsx/checkpoints (跨节点访问,性能>5GB/s)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ 30天后 (Celery定时任务)
┌─────────────────────────────────────────────────────────────┐
│              S3 (长期归档,无限容量)                          │
│  s3://ai-training-checkpoints/checkpoints/{job_id}/...      │
└─────────────────────────────────────────────────────────────┘
```

## 部署步骤

### 1. 安装依赖

```bash
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 验证Celery安装
celery --version
```

### 2. 配置环境变量

在 `backend/.env` 中添加配置:

```bash
# Redis (Celery broker)
REDIS_URL=redis://redis-server:6379/0

# Checkpoint存储路径
CHECKPOINT_S3_BUCKET=ai-training-checkpoints
CHECKPOINT_FSX_MOUNT=/mnt/fsx/checkpoints
CHECKPOINT_NVME_PATH=/mnt/nvme/checkpoints

# 分层迁移策略阈值
CHECKPOINT_MIGRATION_NVME_TO_FSX_DAYS=7
CHECKPOINT_MIGRATION_FSX_TO_S3_DAYS=30
CHECKPOINT_MIGRATION_ENABLED=true

# AWS凭证 (S3访问)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 3. 启动Redis

```bash
# 使用Docker启动Redis
docker run -d \
  --name redis-checkpoint-migration \
  -p 6379:6379 \
  redis:7-alpine

# 验证Redis运行
redis-cli ping  # 应返回 PONG
```

### 4. 启动Celery服务

#### 方式1: 使用启动脚本

```bash
cd backend
./scripts/start_celery.sh
```

#### 方式2: 手动启动

```bash
cd backend/src

# 启动worker和beat (一条命令)
celery -A tasks.checkpoint_migration worker --beat --loglevel=info

# 或分别启动
celery -A tasks.checkpoint_migration worker --loglevel=info  # 终端1
celery -A tasks.checkpoint_migration beat --loglevel=info    # 终端2
```

### 5. 验证部署

#### 检查Celery状态

```bash
# 检查worker连接
celery -A tasks.checkpoint_migration inspect ping

# 查看定时任务
celery -A tasks.checkpoint_migration inspect scheduled

# 查看活动任务
celery -A tasks.checkpoint_migration inspect active

# 查看统计信息
celery -A tasks.checkpoint_migration inspect stats
```

#### 手动触发迁移任务

```bash
# 通过API触发完整迁移策略
curl -X POST http://localhost:8000/api/v1/checkpoints/migrate/policy

# 预期响应:
{
  "success": true,
  "stats": {
    "nvme_to_fsx": 0,
    "fsx_to_s3": 0,
    "errors": 0
  },
  "message": "分层存储迁移策略执行完成"
}
```

## Kubernetes部署

### 1. 创建ConfigMap

```yaml
# k8s/checkpoint-migration-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: checkpoint-migration-config
  namespace: ai-training-platform
data:
  CHECKPOINT_MIGRATION_NVME_TO_FSX_DAYS: "7"
  CHECKPOINT_MIGRATION_FSX_TO_S3_DAYS: "30"
  CHECKPOINT_MIGRATION_ENABLED: "true"
```

### 2. 创建Secret

```yaml
# k8s/checkpoint-migration-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: checkpoint-migration-secrets
  namespace: ai-training-platform
type: Opaque
stringData:
  REDIS_URL: redis://redis-service:6379/0
  AWS_ACCESS_KEY_ID: your-access-key
  AWS_SECRET_ACCESS_KEY: your-secret-key
```

### 3. 部署Celery Deployment

```yaml
# k8s/checkpoint-migration-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkpoint-migration-celery
  namespace: ai-training-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: checkpoint-migration-celery
  template:
    metadata:
      labels:
        app: checkpoint-migration-celery
    spec:
      containers:
      - name: celery-worker
        image: ai-platform-backend:latest
        command:
          - celery
          - -A
          - tasks.checkpoint_migration
          - worker
          - --beat
          - --loglevel=info
        envFrom:
          - configMapRef:
              name: checkpoint-migration-config
          - secretRef:
              name: checkpoint-migration-secrets
        volumeMounts:
          - name: fsx-volume
            mountPath: /mnt/fsx/checkpoints
          - name: nvme-volume
            mountPath: /mnt/nvme/checkpoints
      volumes:
        - name: fsx-volume
          persistentVolumeClaim:
            claimName: fsx-lustre-pvc
        - name: nvme-volume
          hostPath:
            path: /mnt/nvme/checkpoints
            type: DirectoryOrCreate
```

### 4. 应用配置

```bash
kubectl apply -f k8s/checkpoint-migration-config.yaml
kubectl apply -f k8s/checkpoint-migration-secrets.yaml
kubectl apply -f k8s/checkpoint-migration-deployment.yaml

# 验证部署
kubectl get pods -n ai-training-platform | grep checkpoint-migration
kubectl logs -f deployment/checkpoint-migration-celery -n ai-training-platform
```

## 监控和告警

### 1. Prometheus指标

在FastAPI应用中暴露Celery指标:

```python
from prometheus_client import Counter, Histogram

checkpoint_migration_success = Counter(
    'checkpoint_migration_success_total',
    'Checkpoint迁移成功次数',
    ['source', 'destination']
)

checkpoint_migration_errors = Counter(
    'checkpoint_migration_errors_total',
    'Checkpoint迁移失败次数',
    ['source', 'destination', 'error_type']
)

checkpoint_migration_latency = Histogram(
    'checkpoint_migration_latency_seconds',
    'Checkpoint迁移延迟',
    ['source', 'destination']
)
```

### 2. Grafana仪表盘

创建Grafana仪表盘监控:
- 迁移成功率 (按源/目标分组)
- 迁移延迟 (P50/P95/P99)
- 存储使用率 (NVMe/FSx/S3)
- 迁移错误率

### 3. 告警规则

```yaml
# prometheus-alerts.yaml
groups:
  - name: checkpoint_migration
    rules:
      - alert: CheckpointMigrationHighErrorRate
        expr: |
          rate(checkpoint_migration_errors_total[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Checkpoint迁移错误率过高"
          description: "迁移错误率 {{ $value }} > 10%"

      - alert: CheckpointMigrationStalled
        expr: |
          time() - checkpoint_migration_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Checkpoint迁移任务停滞"
          description: "超过24小时未执行成功"
```

## 故障排查

### 1. Celery无法连接Redis

**症状**: worker启动失败,显示连接错误

**检查**:
```bash
# 测试Redis连接
redis-cli -h redis-server ping

# 检查Redis日志
docker logs redis-checkpoint-migration

# 验证环境变量
echo $REDIS_URL
```

**解决**:
- 确认Redis服务运行正常
- 检查REDIS_URL配置正确
- 确认网络连接(防火墙规则)

### 2. FSx挂载点不存在

**症状**: NVMe→FSx迁移失败,日志显示路径错误

**检查**:
```bash
# 检查FSx挂载
mount | grep fsx
df -h | grep fsx

# 检查权限
ls -la /mnt/fsx/checkpoints
```

**解决**:
```bash
# 创建挂载点
sudo mkdir -p /mnt/fsx/checkpoints

# 挂载FSx
sudo mount -t lustre -o noatime,flock fs-12345678.fsx.us-west-2.amazonaws.com@tcp:/fsx /mnt/fsx

# 设置权限
sudo chown -R app-user:app-group /mnt/fsx/checkpoints
sudo chmod 755 /mnt/fsx/checkpoints
```

### 3. S3上传失败

**症状**: FSx→S3迁移失败,S3上传错误

**检查**:
```bash
# 测试AWS凭证
aws sts get-caller-identity

# 测试S3访问
aws s3 ls s3://ai-training-checkpoints/

# 测试上传
echo "test" > /tmp/test.txt
aws s3 cp /tmp/test.txt s3://ai-training-checkpoints/test.txt
```

**解决**:
- 验证AWS凭证配置
- 检查S3存储桶策略和IAM权限
- 确认网络连接(代理配置)

### 4. 定时任务未执行

**症状**: 凌晨2点任务未运行

**检查**:
```bash
# 检查beat进程
ps aux | grep celery | grep beat

# 查看beat日志
tail -f /var/log/ai-platform/celery-checkpoint-migration.log

# 检查定时任务配置
celery -A tasks.checkpoint_migration inspect scheduled
```

**解决**:
- 确认beat进程运行
- 检查服务器时区设置
- 验证定时任务配置正确

## 性能优化

### 1. 并行迁移

修改迁移策略使用并发:

```python
# 在StorageMigrationService中
import asyncio

async def run_migration_policy(self):
    # 并行迁移多个checkpoint
    nvme_tasks = [
        self.migrate_nvme_to_fsx(ckpt)
        for ckpt in nvme_checkpoints[:10]  # 限制并发数
    ]
    results = await asyncio.gather(*nvme_tasks, return_exceptions=True)
```

### 2. 批量S3上传

使用S3 Transfer Manager:

```python
from boto3.s3.transfer import TransferConfig

config = TransferConfig(
    multipart_threshold=1024 * 25,  # 25MB
    max_concurrency=10,
    num_download_attempts=5,
)

s3_client.upload_file(
    source_path, bucket, key,
    Config=config
)
```

### 3. 压缩Checkpoint

在迁移前压缩:

```python
import tarfile

def compress_checkpoint(source, dest):
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(source, arcname=os.path.basename(source))
```

## 最佳实践

### 1. 渐进式部署

1. 先在测试环境验证
2. 生产环境先禁用自动迁移(`CHECKPOINT_MIGRATION_ENABLED=false`)
3. 手动触发测试几次
4. 监控一周后启用自动迁移

### 2. 备份策略

- S3开启版本控制
- 重要checkpoint保留多个副本
- 定期备份到不同区域

### 3. 成本优化

- 使用S3生命周期策略:
  - 90天后迁移到S3 Glacier
  - 180天后迁移到S3 Deep Archive
- 压缩checkpoint减少存储成本
- 定期清理不需要的checkpoint

## 相关文档

- [Checkpoint服务README](/backend/src/services/checkpoint/README.md)
- [Celery官方文档](https://docs.celeryq.dev/)
- [AWS FSx for Lustre文档](https://docs.aws.amazon.com/fsx/latest/LustreGuide/)
- [T041任务规范](/specs/001-ai-training-platform/plan.md#t041)
