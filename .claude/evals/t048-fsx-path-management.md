## EVAL: T048 - FSx for Lustre 路径管理

Created: 2025-01-25
Task: `backend/src/modules/datasets/application/services/fsx_sync_service.py`
Requirements: SC-005 (S3 到 FSx 同步时间 <10分钟 for 1TB), ≥5GB/s 吞吐量

---

### 能力评估 (Capability Evals) - 使用真实 AWS 环境

#### FSx 文件系统连接

- [ ] **C1.1 文件系统可用性检查**: `check_fsx_availability()` 正确返回 FSx 状态
  - 验证命令: `aws fsx describe-file-systems --file-system-ids ${FSX_ID} | jq '.FileSystems[0].Lifecycle'`
  - 通过条件: 返回 `available=True`，`lifecycle=AVAILABLE`

- [ ] **C1.2 文件系统信息查询**: `FsxClient.describe_filesystem()` 返回完整信息
  - 验证字段: FileSystemId, StorageCapacity, LustreConfiguration
  - 通过条件: 信息与 AWS 控制台一致

#### S3 → FSx 同步

- [ ] **C2.1 同步任务创建**: `initiate_s3_to_fsx_sync()` 成功创建 Data Repository Task
  - 验证命令: `aws fsx describe-data-repository-tasks --task-ids ${TASK_ID}`
  - 通过条件: Task 状态为 PENDING 或 EXECUTING

- [ ] **C2.2 同步任务状态查询**: `get_sync_status()` 返回准确的任务进度
  - 验证字段: status, progress.total, progress.succeeded, progress.failed
  - 通过条件: 进度数据与 AWS API 一致

- [ ] **C2.3 同步任务完成等待**: `FsxClient.wait_for_task_completion()` 正确等待任务完成
  - 通过条件: 任务成功返回 SUCCEEDED 状态；任务失败抛出 `FsxClientError`

- [ ] **C2.4 同步类型验证**: 使用 `IMPORT_METADATA_FROM_REPOSITORY` 类型
  - 验证: 仅导入元数据，实际数据按需加载 (Lazy Loading)
  - 通过条件: 同步完成后 FSx 仅包含元数据，首次访问时加载数据

#### 数据预热

- [ ] **C3.1 整数据集预热**: `prefetch_dataset()` 预加载整个数据集到 FSx 缓存
  - 验证方法: 同步后在 HyperPod 节点访问数据，测量首次访问延迟
  - 通过条件: 预热后访问延迟显著降低 (<100ms vs 首次 >1s)

- [ ] **C3.2 部分路径预热**: 支持指定子路径预热
  - 测试: `prefetch_dataset(dataset_id, paths=["train/", "valid/"])`
  - 通过条件: 仅指定路径被预热，其他路径保持惰性加载

#### 缓存释放

- [ ] **C4.1 缓存释放任务**: `release_dataset()` 创建 RELEASE_DATA_FROM_FILESYSTEM 任务
  - 验证命令: `aws fsx describe-data-repository-tasks --task-ids ${TASK_ID} | jq '.DataRepositoryTasks[0].Type'`
  - 通过条件: Type 为 `RELEASE_DATA_FROM_FILESYSTEM`

- [ ] **C4.2 释放后数据可重新加载**: 释放缓存后，数据仍可从 S3 重新加载
  - 测试流程: 释放 → 访问数据 → 验证自动从 S3 加载
  - 通过条件: 数据访问正常，无数据丢失

#### 路径管理

- [ ] **C5.1 FSx 路径映射**: `get_dataset_fsx_path()` 返回正确的 FSx 挂载路径
  - 格式: `/fsx/datasets/{dataset_id}`
  - 通过条件: 路径在 HyperPod 节点上可访问

- [ ] **C5.2 S3 路径映射**: `get_s3_path_for_dataset()` 返回正确的 S3 URI
  - 格式: `s3://{bucket}/datasets/{dataset_id}`
  - 通过条件: 路径与 Data Repository Association 配置一致

#### 错误处理

- [ ] **C6.1 数据集不存在**: 对不存在的 dataset_id 抛出 `DatasetNotFoundError`
- [ ] **C6.2 任务不存在**: 对无效 task_id 抛出 `FsxSyncTaskNotFoundError`
- [ ] **C6.3 文件系统不可用**: 文件系统状态非 AVAILABLE 时返回 `available=False`
- [ ] **C6.4 任务超时**: `wait_for_task_completion()` 超时后抛出 `FsxClientError`
- [ ] **C6.5 任务失败**: 任务失败时抛出包含失败详情的 `FsxClientError`

---

### 性能评估 (SC-005)

#### 同步性能基准

- [ ] **P1 小数据集同步 (100GB)**: 同步时间 <1分钟
  - 测试方法: 创建 100GB 测试数据集，测量同步耗时
  - 注意: IMPORT_METADATA_FROM_REPOSITORY 仅同步元数据，速度极快

- [ ] **P2 中数据集同步 (500GB)**: 同步时间 <3分钟
- [ ] **P3 大数据集同步 (1TB)**: 同步时间 <10分钟 (SC-005 要求)

#### 吞吐量验证 (≥5GB/s)

- [ ] **P4 单客户端读取吞吐量**: 使用 fio 测试顺序读 ≥5GB/s
  ```bash
  # 在 HyperPod 节点上执行
  fio --name=sequential_read --directory=/fsx/datasets/1 \
      --rw=read --bs=1M --direct=1 --numjobs=8 --iodepth=64 \
      --size=10G --runtime=60 --time_based --group_reporting
  ```
  - 通过条件: READ: bw ≥ 5GB/s

- [ ] **P5 多客户端聚合吞吐量**: 4-8 个客户端并发读取 ≥20GB/s
  - 测试方法: 在多个 HyperPod 节点并发执行 fio
  - 通过条件: 聚合带宽 ≥20GB/s

---

### 回归评估 (Regression Evals)

- [ ] **R1 现有单元测试通过**: `pytest tests/unit/modules/datasets/ -v` 全部通过
- [ ] **R2 FsxClient 封装**: 所有 boto3 调用正确封装为异步方法
- [ ] **R3 数据集仓库**: 数据集状态更新正常
- [ ] **R4 服务依赖注入**: `FsxSyncService` 依赖注入链正常

---

### 集成测试场景 (真实 AWS 环境)

#### 环境要求

```bash
# 环境变量
export AWS_REGION=us-west-2
export FSX_FILESYSTEM_ID=fs-0123456789abcdef0
export FSX_MOUNT_PATH=/fsx
export S3_BUCKET_NAME=ai-training-platform-datasets-dev

# 测试脚本位置
# tests/integration/datasets/test_fsx_sync_integration.py
pytest tests/integration/datasets/test_fsx_sync_integration.py -v
```

#### 测试场景列表

| 场景 | 描述 | 验证方法 |
|------|------|----------|
| **E2E-1** | 元数据同步 | 同步后验证 FSx 路径存在 (仅元数据) |
| **E2E-2** | 数据预热 | 预热后测量访问延迟 |
| **E2E-3** | 缓存释放 | 释放后验证 FSx 空间回收 |
| **E2E-4** | 同步进度监控 | 大数据集同步时查询进度 |
| **E2E-5** | 任务等待超时 | 设置短超时，验证超时处理 |
| **E2E-6** | 并发同步任务 | 多数据集同时同步，验证任务隔离 |

#### HyperPod 节点验证

```bash
# 在 HyperPod 节点上执行验证脚本
kubectl exec -it training-pod-xxx -- bash

# 验证 FSx 挂载
df -h /fsx
ls -la /fsx/datasets/

# 验证数据可访问
time head -c 1M /fsx/datasets/1/train/file.bin

# 验证吞吐量
dd if=/fsx/datasets/1/train/large_file.bin of=/dev/null bs=1M count=1000
```

---

### 成功标准

- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- SC-005: 1TB 数据集同步时间 <10分钟
- 吞吐量: 单客户端 ≥5GB/s，多客户端聚合 ≥20GB/s

---

### AWS 资源要求

| 资源 | 要求 | 用途 |
|------|------|------|
| **FSx for Lustre** | Persistent_2, 500 MB/s/TiB | 高性能文件系统 |
| **Data Repository Association** | 关联 S3 Bucket | S3 ↔ FSx 同步 |
| **S3 Bucket** | 与 FSx DRA 关联 | 数据集持久化存储 |
| **HyperPod 节点** | FSx CSI Driver 已安装 | 验证数据访问 |
| **IAM Role** | fsx:CreateDataRepositoryTask, fsx:DescribeFileSystems | API 调用权限 |

---

### FSx 配置验证

| 配置项 | 预期值 | 验证命令 |
|--------|--------|----------|
| 部署类型 | PERSISTENT_2 | `aws fsx describe-file-systems --file-system-ids ${FSX_ID} | jq '.FileSystems[0].LustreConfiguration.DeploymentType'` |
| 吞吐量级别 | 500 MB/s/TiB | `jq '.FileSystems[0].LustreConfiguration.PerUnitStorageThroughput'` |
| 存储容量 | ≥10 TiB | `jq '.FileSystems[0].StorageCapacity'` |
| DRA 关联 | 已配置 | `aws fsx describe-data-repository-associations --file-system-id ${FSX_ID}` |

---

### 手动验证检查清单

- [ ] FSx 文件系统状态为 AVAILABLE
- [ ] Data Repository Association 已正确配置
- [ ] HyperPod 节点可挂载 FSx 路径
- [ ] 同步任务在 AWS 控制台可见
- [ ] 预热数据在 HyperPod 节点可访问
- [ ] 释放后 FSx 存储空间回收
- [ ] CloudWatch 日志记录同步事件

---

### 故障排查指南

#### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 同步任务 FAILED | DRA 配置错误 | 检查 S3 路径前缀匹配 |
| 任务超时 | 数据量过大或网络问题 | 增加 max_wait_time 或分批同步 |
| 挂载失败 | FSx CSI Driver 未安装 | 验证 EKS Add-on 状态 |
| 吞吐量低 | FSx 吞吐量级别不足 | 升级到 1000 MB/s/TiB |
| 数据不可见 | AutoImport 未配置 | 检查 DRA AutoImportPolicy |

#### 调试命令

```bash
# 查看 FSx 事件日志
aws fsx describe-file-system-events --file-system-id ${FSX_ID}

# 查看 Data Repository Task 详情
aws fsx describe-data-repository-tasks --task-ids ${TASK_ID}

# 检查 DRA 配置
aws fsx describe-data-repository-associations --file-system-id ${FSX_ID}

# HyperPod 节点 FSx 挂载状态
kubectl exec -it pod-name -- mount | grep lustre
```
