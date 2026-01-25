# Phase 4 US2 存储集成服务实施计划

**任务**: T047 (S3 上传集成) + T048 (FSx 路径管理)
**日期**: 2026-01-25
**状态**: 待实施

---

## 1. 任务概述

| 任务 | 描述 | 目标文件 |
|------|------|---------|
| **T047** | S3 分片上传、MD5 校验、断点续传 | `dataset_upload_service.py` |
| **T048** | FSx 挂载路径管理、S3→FSx 同步、数据预热 | `fsx_service.py` |

**验收标准**:
- FR-006: 数据集上传速度 ≥100MB/s
- FR-007: 支持 ≥10TB 数据集
- SC-005: S3 到 FSx 同步时间 <10分钟 (1TB 数据集)

---

## 2. 文件结构

### 2.1 T047 S3 上传 - 新建文件

```
backend/
├── alembic/versions/
│   └── 20260126_*_create_upload_sessions.py  # [新建] 数据库迁移
└── src/modules/datasets/
    ├── application/
    │   ├── interfaces/                          # [新建目录]
    │   │   ├── __init__.py
    │   │   └── upload_service.py               # IDatasetUploadService 接口
    │   └── services/
    │       └── dataset_upload_service.py       # [新建] 上传服务实现
    ├── domain/
    │   ├── value_objects/
    │   │   └── upload_state.py                 # [新建] UploadPart, UploadStatus 枚举
    │   └── repositories/
    │       └── upload_session_repository.py    # [新建] IUploadSessionRepository 接口
    ├── infrastructure/
    │   ├── models/
    │   │   └── upload_session_model.py         # [新建] UploadSessionModel ORM
    │   ├── repositories/
    │   │   └── upload_session_repository_impl.py # [新建] 仓库实现
    │   └── s3/                                  # [新建目录]
    │       ├── __init__.py
    │       └── multipart_upload_client.py      # S3 Multipart 客户端
    └── api/
        ├── schemas/
        │   └── upload_schemas.py               # [新建] 上传请求/响应
        ├── endpoints.py                         # [修改] 添加 6 个上传端点
        └── dependencies.py                      # [修改] 添加上传服务依赖

backend/tests/
├── unit/modules/datasets/
│   ├── domain/
│   │   └── test_vo_upload_state.py         # [新建]
│   ├── application/
│   │   └── test_svc_dataset_upload.py      # [新建]
│   └── infrastructure/
│       ├── test_upload_session_model.py    # [新建] ORM 模型测试
│       ├── test_upload_session_repo.py     # [新建] 仓库测试
│       └── test_s3_multipart_client.py     # [新建]
└── integration/datasets/
    └── test_api_upload.py                   # [新建]
```

### 2.2 T048 FSx 服务 - 新建文件

```
backend/src/modules/datasets/
├── application/
│   └── interfaces/
│       └── fsx_service.py                  # [新建] IFsxService 接口
│   └── services/
│       └── fsx_sync_service.py             # [新建] FSx 同步服务
├── domain/
│   └── value_objects/
│       └── fsx_path.py                     # [新建] FsxPath, SyncStatus
└── infrastructure/
    └── fsx/                                 # [新建目录]
        ├── __init__.py
        └── fsx_client.py                   # FSx Data Repository 客户端

backend/tests/
├── unit/modules/datasets/
│   ├── application/
│   │   └── test_svc_fsx_sync.py            # [新建]
│   └── infrastructure/
│       └── test_fsx_client.py              # [新建]
└── integration/datasets/
    └── test_api_fsx_sync.py                # [新建]
```

---

## 3. T047 详细设计

### 3.1 核心接口

```python
# application/interfaces/upload_service.py
class IDatasetUploadService(ABC):
    async def initiate_multipart_upload(dataset_id, filename, content_type, total_size) -> InitiateUploadResponse
    async def generate_presigned_urls(dataset_id, upload_id, part_numbers, expiration) -> list[UploadPartUrl]
    async def register_part_completion(dataset_id, upload_id, part_result) -> None
    async def get_upload_progress(dataset_id, upload_id) -> dict
    async def complete_multipart_upload(dataset_id, upload_id) -> CompleteUploadResult
    async def abort_multipart_upload(dataset_id, upload_id) -> None
```

### 3.2 值对象

```python
# domain/value_objects/upload_state.py
class UploadStatus(Enum):
    INITIATED, IN_PROGRESS, COMPLETING, COMPLETED, ABORTED, FAILED

@dataclass(frozen=True)
class UploadPart:
    part_number: int  # 1-10000
    etag: str
    size_bytes: int
    md5_checksum: str
    uploaded_at: datetime

@dataclass
class UploadSession:
    upload_id: str
    dataset_id: int
    bucket: str
    key: str
    filename: str
    total_size: int
    part_size: int
    status: UploadStatus
    completed_parts: dict[int, UploadPart]

    @property
    def missing_parts(self) -> list[int]  # 断点续传关键
```

### 3.3 API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/{dataset_id}/upload/initiate` | 初始化分片上传 |
| POST | `/{dataset_id}/upload/{upload_id}/presigned-urls` | 获取预签名 URL (批量) |
| POST | `/{dataset_id}/upload/{upload_id}/parts` | 注册分片完成 |
| GET | `/{dataset_id}/upload/{upload_id}/progress` | 获取上传进度 |
| POST | `/{dataset_id}/upload/{upload_id}/complete` | 完成上传 |
| DELETE | `/{dataset_id}/upload/{upload_id}` | 取消上传 |

### 3.4 分片大小策略

```python
DEFAULT_PART_SIZE = 100 * 1024 * 1024  # 100MB (满足 FR-006)
MIN_PART_SIZE = 5 * 1024 * 1024        # 5MB (S3 最小)
MAX_PARTS = 10000                       # S3 限制 → 支持 1PB 文件
```

### 3.5 断点续传 - 数据库持久化方案

**新增数据库表**: `upload_sessions` (支持跨会话断点续传)

```sql
CREATE TABLE upload_sessions (
    -- 主键
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 上传标识
    upload_id VARCHAR(128) NOT NULL UNIQUE COMMENT 'S3 Multipart Upload ID',
    dataset_id BIGINT UNSIGNED NOT NULL COMMENT '关联数据集ID',

    -- S3 存储信息
    bucket VARCHAR(128) NOT NULL COMMENT 'S3 桶名',
    s3_key VARCHAR(512) NOT NULL COMMENT 'S3 对象键',

    -- 文件信息
    filename VARCHAR(256) NOT NULL COMMENT '原始文件名',
    content_type VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
    total_size BIGINT UNSIGNED NOT NULL COMMENT '文件总大小 (字节)',
    part_size INT UNSIGNED NOT NULL COMMENT '分片大小 (字节)',

    -- 状态
    status ENUM('initiated', 'in_progress', 'completing', 'completed', 'aborted', 'failed')
        NOT NULL DEFAULT 'initiated' COMMENT '上传状态',

    -- 分片追踪 (JSON 数组: [{"part_number":1,"etag":"xxx","size":100,"md5":"yyy"},...])
    completed_parts JSON COMMENT '已完成分片列表',

    -- 进度统计
    uploaded_bytes BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已上传字节数',
    completed_part_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已完成分片数',

    -- 所有者
    owner_id BIGINT UNSIGNED NOT NULL COMMENT '上传者用户ID',

    -- 时间戳
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    expires_at DATETIME(3) COMMENT '会话过期时间 (7天后自动清理)',

    -- 索引
    INDEX idx_dataset_id (dataset_id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),

    -- 外键
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据集上传会话表';
```

**新增文件**:
- `backend/alembic/versions/20260126_*_create_upload_sessions.py` - 数据库迁移
- `backend/src/modules/datasets/infrastructure/models/upload_session_model.py` - ORM 模型
- `backend/src/modules/datasets/domain/repositories/upload_session_repository.py` - 仓库接口
- `backend/src/modules/datasets/infrastructure/repositories/upload_session_repository_impl.py` - 仓库实现

**会话清理策略**:
- 过期时间: 7 天 (expires_at = created_at + 7 days)
- 定时任务: 每天清理 `status IN ('completed', 'aborted', 'failed') OR expires_at < NOW()`
- S3 清理: 取消未完成的 Multipart Upload

---

## 4. T048 详细设计

### 4.1 核心接口

```python
# application/interfaces/fsx_service.py
class IFsxService(ABC):
    async def get_dataset_fsx_path(dataset_id) -> FsxPathInfo
    async def initiate_s3_to_fsx_sync(dataset_id, s3_uri, priority) -> FsxSyncTask
    async def get_sync_status(task_id) -> FsxSyncTask
    async def cancel_sync(task_id) -> None
    async def prefetch_dataset(dataset_id, paths) -> FsxSyncTask  # 数据预热
    async def release_dataset(dataset_id) -> None  # 缓存释放
    async def check_fsx_availability() -> dict
```

### 4.2 同步机制

使用 **FSx Data Repository Task API** (boto3):
- `create_data_repository_task(Type="IMPORT_METADATA_FROM_REPOSITORY")` - S3→FSx
- `create_data_repository_task(Type="RELEASE_DATA_FROM_FILESYSTEM")` - FSx→S3

### 4.3 路径映射

```
S3:  s3://bucket/datasets/{dataset_id}/
FSx: /fsx/datasets/{dataset_id}/
```

---

## 5. TDD 实施顺序

### Phase 1: T047 S3 上传 (Day 1-4)

**Day 1**: 数据库迁移和 ORM 模型
```
🔴 test_upload_session_model.py (ORM 模型测试)
🟢 20260126_*_create_upload_sessions.py (Alembic 迁移)
🟢 upload_session_model.py (SQLAlchemy 模型)
🔴 test_upload_session_repository.py (仓库测试)
🟢 upload_session_repository.py (接口) + upload_session_repository_impl.py (实现)
```

**Day 2**: 值对象和接口
```
🔴 test_vo_upload_state.py (UploadPart, UploadSession 验证)
🟢 upload_state.py
🔴 test_svc_dataset_upload.py::test_initiate_* (初始化测试)
🟢 IDatasetUploadService 接口
```

**Day 3**: S3 客户端和服务
```
🔴 test_s3_multipart_client.py (mock boto3)
🟢 multipart_upload_client.py
🔴 test_svc_dataset_upload.py::test_presigned_*, test_register_*
🟢 DatasetUploadService
```

**Day 4**: API 和集成
```
🔴 test_api_upload.py (使用 moto mock S3)
🟢 upload_schemas.py + endpoints.py
🔄 断点续传优化 (数据库持久化)
✅ 完整上传流程验证 (包括跨会话恢复)
```

### Phase 2: T048 FSx 服务 (Day 5-6)

**Day 5**: FSx 客户端
```
🔴 test_fsx_client.py (mock boto3 fsx)
🟢 fsx_client.py
🔴 test_svc_fsx_sync.py
🟢 FsxSyncService
```

**Day 6**: 集成和预热
```
🔴 test_api_fsx_sync.py
🟢 FSx 端点添加
🔄 与 DatasetService 集成
✅ 数据预热流程验证
```

---

## 6. 关键实现细节

### 6.1 断点续传实现

```python
# 1. 客户端上传中断后，调用 progress 端点
GET /datasets/{id}/upload/{upload_id}/progress
→ 返回 {"missing_parts": [3, 5, 7]}

# 2. 仅请求缺失分片的预签名 URL
POST /datasets/{id}/upload/{upload_id}/presigned-urls
{"part_numbers": [3, 5, 7]}

# 3. 上传缺失分片后完成
POST /datasets/{id}/upload/{upload_id}/complete
```

### 6.2 MD5 校验

- **每个分片**: 客户端计算 MD5，注册时上报
- **整体文件**: S3 ETag (分片上传时为 MD5 数组的 MD5)
- **验证时机**: 完成上传时比对

### 6.3 与 DatasetService 集成

```python
# 上传完成后自动更新数据集状态
async def complete_upload(...):
    result = await upload_service.complete_multipart_upload(...)
    await dataset_service.mark_available(dataset_id)  # PREPARING → AVAILABLE
    return result
```

---

## 7. 测试覆盖目标

| 类别 | 测试数量 | 覆盖点 |
|------|---------|-------|
| **值对象** | ~10 | 不可变性、验证、属性计算 |
| **S3 客户端** | ~15 | 初始化/分片/完成/取消、错误处理 |
| **上传服务** | ~20 | 完整流程、断点续传、权限检查 |
| **FSx 客户端** | ~10 | 同步/预热/释放、状态查询 |
| **API 集成** | ~15 | 端点响应、错误码、认证 |
| **总计** | ~70 | 80%+ 覆盖率 |

---

## 8. 验证清单

- [ ] S3 分片上传 100MB 文件成功
- [ ] 断点续传恢复已上传分片
- [ ] MD5 校验和匹配
- [ ] FSx 同步任务创建成功
- [ ] 数据预热触发正常
- [ ] 上传完成后数据集状态更新为 AVAILABLE
- [ ] 所有测试通过
- [ ] tasks.md 更新 T047, T048 为完成状态
