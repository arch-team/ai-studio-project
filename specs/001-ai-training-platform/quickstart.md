# 快速入门指南: 企业级AI训练平台

**版本**: v1.0.0 | **日期**: 2025-12-23 | **特性分支**: `001-ai-training-platform`

## 简介

企业级AI训练平台是基于AWS SageMaker HyperPod和EKS构建的高性能分布式训练平台，专为大规模AI模型训练而设计，支持多租户资源管理、版本化数据集、分布式训练作业调度以及全生命周期监控。

本指南将帮助您快速上手平台的核心功能，包括用户登录、资源配额管理、数据集上传、训练任务提交和监控等基本操作。

## 前提条件

在开始使用AI训练平台之前，请确保您满足以下条件：

1. **访问凭证**：已获取平台访问账号与权限
2. **网络环境**：能够访问平台API端点和用户界面
3. **数据准备**：准备好用于训练的数据集（支持常见格式：图像、文本、音频等）
4. **训练代码**：准备好符合平台规范的训练脚本和配置

## 快速开始

### 1. 用户登录与认证

```bash
# 获取访问令牌
curl -X POST https://api.ai-platform.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 43200
}

# 使用令牌访问API
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

所有后续API调用都需要在请求头中包含`Authorization: Bearer {token}`。

### 2. 浏览您的资源配额

检查您的团队或项目可用资源配额：

```bash
# 获取团队资源配额
curl -X GET https://api.ai-platform.example.com/api/v1/resources/quotas?owner_type=team&owner_id=your-team-id \
  -H "Authorization: Bearer {token}"

# 响应
{
  "items": [
    {
      "id": "quota-456",
      "owner_type": "team",
      "owner_id": "team-123",
      "owner_name": "研发部",
      "gpu_limit": 128,
      "cpu_limit": 1024,
      "memory_limit_gb": 4096,
      "storage_limit_gb": 20480,
      "priority": 80,
      "usage": {
        "gpu_used": 64,
        "cpu_used": 512,
        "memory_used_gb": 2048,
        "storage_used_gb": 10240,
        "usage_percentage": 50
      }
    }
  ]
}
```

### 3. 数据集管理

#### 3.1 创建新数据集

```bash
# 创建数据集元数据
curl -X POST https://api.ai-platform.example.com/api/v1/datasets \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "imagenet-subset",
    "description": "ImageNet子集，包含100个类别和10万张图像",
    "storage_type": "s3",
    "project_id": "project-456",
    "access_level": "project",
    "estimated_size_bytes": 10737418240,
    "content_type": "image",
    "metadata": {
      "image_format": "jpeg",
      "classes": 100
    },
    "tags": ["image", "classification"]
  }'

# 响应
{
  "id": "dataset-123",
  "name": "imagenet-subset",
  "storage_path": "s3://datasets/dataset-123",
  "created_at": "2025-12-23T08:15:30Z",
  "created_by": "user-123",
  "size_bytes": 0,
  "links": {
    "self": "/api/v1/datasets/dataset-123",
    "versions": "/api/v1/datasets/dataset-123/versions"
  }
}
```

#### 3.2 创建数据集版本

```bash
# 创建数据集版本
curl -X POST https://api.ai-platform.example.com/api/v1/datasets/dataset-123/versions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.0.0",
    "description": "初始版本",
    "estimated_size_bytes": 10737418240,
    "metadata": {
      "image_format": "jpeg",
      "min_resolution": "224x224",
      "classes": 100
    }
  }'

# 响应
{
  "id": "v1.0.0",
  "dataset_id": "dataset-123",
  "version": "v1.0.0",
  "description": "初始版本",
  "storage_path": "s3://datasets/dataset-123/v1.0.0",
  "created_at": "2025-12-23T09:30:00Z",
  "status": "creating",
  "upload_credentials": {
    "upload_id": "upload-789",
    "presigned_url_base": "https://api.ai-platform.example.com/uploads/dataset-123/v1.0.0",
    "expires_at": "2025-12-23T10:30:00Z"
  }
}
```

#### 3.3 上传数据文件

```bash
# 上传单个文件
curl -X POST https://api.ai-platform.example.com/api/v1/datasets/dataset-123/versions/v1.0.0/files \
  -H "Authorization: Bearer {token}" \
  -F "file=@/path/to/image001.jpg" \
  -F "path=train/cat/image001.jpg" \
  -F 'metadata={"width":224,"height":224,"label":0}'

# 对于大文件（分片上传）
# 1. 初始化分片上传
curl -X POST https://api.ai-platform.example.com/api/v1/datasets/dataset-123/versions/v1.0.0/files \
  -H "Authorization: Bearer {token}" \
  -F "action=initiate_multipart" \
  -F "path=train/video/video001.mp4" \
  -F "size_bytes=1073741824" \
  -F "content_type=video/mp4" \
  -F "total_parts=100"

# 2. 获取预签名URL后，上传每个分片
# 3. 完成上传
curl -X POST https://api.ai-platform.example.com/api/v1/datasets/dataset-123/versions/v1.0.0/files/file-456/complete \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "upload-789",
    "parts": [
      {"part_number": 1, "etag": "etag1"},
      {"part_number": 2, "etag": "etag2"}
    ]
  }'
```

#### 3.4 完成数据集版本创建

上传所有文件后，完成版本创建：

```bash
curl -X POST https://api.ai-platform.example.com/api/v1/datasets/dataset-123/versions/v1.0.0/actions/finalize \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata_update": {
      "total_images": 100000,
      "class_distribution": "balanced"
    },
    "make_default": true
  }'
```

### 4. 训练任务管理

#### 4.1 创建训练任务

```bash
curl -X POST https://api.ai-platform.example.com/api/v1/training-jobs \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet50-training",
    "description": "使用ImageNet子集训练ResNet-50",
    "job_type": "distributed",
    "framework": "pytorch",
    "distribution_strategy": "ddp",
    "num_nodes": 2,
    "gpus_per_node": 8,
    "container_image": "registry.example.com/pytorch:2.0-cuda11.8",
    "entrypoint": "python /workspace/train.py --config /workspace/configs/resnet.yaml",
    "hyperparameters": {
      "learning_rate": 0.001,
      "batch_size": 64,
      "epochs": 10
    },
    "resource_requirements": {
      "priority": "high",
      "gpu_type": "nvidia-a100-80g",
      "cpu_cores_per_gpu": 8,
      "memory_gb_per_gpu": 128
    },
    "dataset_versions": ["dataset-123/v1.0.0"],
    "project_id": "project-456",
    "timeout_hours": 48,
    "environment_variables": {
      "PYTHONUNBUFFERED": "1"
    },
    "checkpoint_config": {
      "frequency_minutes": 30,
      "storage_type": "tiered"
    }
  }'

# 响应
{
  "id": "job-789",
  "name": "resnet50-training",
  "status": "pending",
  "created_at": "2025-12-23T10:15:30Z",
  "queue_position": 1,
  "estimated_start_time": "2025-12-23T10:30:00Z",
  "links": {
    "self": "/api/v1/training-jobs/job-789",
    "metrics": "/api/v1/training-jobs/job-789/metrics",
    "logs": "/api/v1/training-jobs/job-789/logs"
  }
}
```

#### 4.2 启动训练任务

```bash
curl -X POST https://api.ai-platform.example.com/api/v1/training-jobs/job-789/actions/start \
  -H "Authorization: Bearer {token}"
```

#### 4.3 监控训练进度

```bash
# 获取训练指标
curl -X GET https://api.ai-platform.example.com/api/v1/training-jobs/job-789/metrics \
  -H "Authorization: Bearer {token}" \
  -G --data-urlencode "metric_names=loss,accuracy,learning_rate" \
  --data-urlencode "interval=5m"

# 获取训练日志
curl -X GET https://api.ai-platform.example.com/api/v1/training-jobs/job-789/logs \
  -H "Authorization: Bearer {token}" \
  -G --data-urlencode "limit=100" \
  --data-urlencode "follow=true"
```

#### 4.4 停止或恢复训练

```bash
# 停止训练
curl -X POST https://api.ai-platform.example.com/api/v1/training-jobs/job-789/actions/stop \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "模型已收敛",
    "create_final_checkpoint": true
  }'

# 恢复训练（从特定检查点创建新任务）
curl -X POST https://api.ai-platform.example.com/api/v1/training-jobs/job-789/actions/resume \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "checkpoint_id": "checkpoint-456",
    "hyperparameters_override": {
      "learning_rate": 0.0005
    }
  }'
```

#### 4.5 查看检查点

```bash
curl -X GET https://api.ai-platform.example.com/api/v1/training-jobs/job-789/checkpoints \
  -H "Authorization: Bearer {token}"
```

### 5. 监控与告警

#### 5.1 获取平台级别指标

```bash
curl -X GET https://api.ai-platform.example.com/api/v1/monitoring/metrics \
  -H "Authorization: Bearer {token}" \
  -G --data-urlencode "metric_names=gpu_utilization,job_count,queue_depth" \
  --data-urlencode "interval=1h"
```

#### 5.2 查看活跃告警

```bash
curl -X GET https://api.ai-platform.example.com/api/v1/monitoring/alerts?status=firing \
  -H "Authorization: Bearer {token}"
```

#### 5.3 检查系统健康状态

```bash
curl -X GET https://api.ai-platform.example.com/api/v1/monitoring/health \
  -H "Authorization: Bearer {token}"
```

## 常见工作流程

### 工作流程1：从头开始训练模型

1. 创建新数据集并上传数据
2. 准备训练代码和配置文件
3. 提交训练任务
4. 监控训练进度和指标
5. 完成训练后获取模型制品

### 工作流程2：从检查点恢复训练

1. 查看已有训练任务的检查点列表
2. 选择适合的检查点用于恢复
3. 创建新的恢复训练任务，可选择修改超参数
4. 监控恢复的训练任务进度

### 工作流程3：进行超参数优化

1. 创建多个具有不同超参数的训练任务
2. 使用平台的监控功能比较不同任务的性能
3. 选择表现最佳的超参数配置进行完整训练

## 资源管理最佳实践

### 有效利用资源配额

1. **合理设置任务优先级**：高优先级应仅用于关键任务
2. **利用借用机制**：在资源紧张时可以向其他团队借用资源
3. **设置适当的超时时间**：避免任务无限期运行占用资源
4. **选择合适的节点数量**：根据任务规模和并行度需求选择

### 数据集管理技巧

1. **版本化管理**：为每次重大数据更改创建新版本
2. **利用元数据**：详细记录数据集特征以便追踪
3. **数据集比较**：使用比较功能了解不同版本间的差异
4. **合理组织目录结构**：遵循约定（如train/val/test分割）

### 训练效率提升

1. **分布式策略选择**：根据模型特点选择适合的分布式策略
2. **检查点配置优化**：平衡保存频率与存储开销
3. **资源规格合理配置**：避免过度分配或资源不足
4. **环境变量优化**：针对不同框架设置性能优化参数

## 故障排除

### 常见问题与解决方案

1. **训练任务一直处于pending状态**
   - 检查资源配额是否足够
   - 查看是否有更高优先级任务占用资源
   - 确认节点选择器配置是否有过于严格的限制

2. **训练任务运行失败**
   - 查看任务日志了解具体错误信息
   - 确认容器镜像是否包含所有依赖
   - 检查环境变量配置是否正确

3. **数据集上传失败**
   - 检查存储配额是否充足
   - 对于大文件确保使用分片上传
   - 验证文件路径格式是否符合要求

4. **指标或日志无法获取**
   - 确认训练任务ID是否正确
   - 检查认证令牌是否有效或已过期
   - 验证是否有足够的查看权限

### 联系支持

如遇到无法自行解决的问题，请通过以下方式联系平台支持团队：

- 电子邮件：support@ai-platform.example.com
- 内部工单系统：http://helpdesk.internal/ai-platform
- 技术文档：http://docs.ai-platform.example.com

## 后续步骤

完成快速入门后，建议您进一步了解以下高级功能：

1. **自定义训练模板**：创建和使用标准化训练模板
2. **集成CI/CD流程**：将训练流程集成到持续集成系统
3. **自动化数据预处理**：设置数据预处理流水线
4. **自定义监控仪表板**：创建针对特定项目的监控视图
5. **成本分析与优化**：利用成本分析功能优化资源使用

## 参考资料

- [完整API文档](http://docs.ai-platform.example.com/api)
- [数据集格式规范](http://docs.ai-platform.example.com/datasets)
- [分布式训练最佳实践](http://docs.ai-platform.example.com/distributed-training)
- [AWS SageMaker HyperPod文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html)