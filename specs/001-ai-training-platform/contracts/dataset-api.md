# API契约: 数据集管理

**版本**: v1.0.0 | **日期**: 2025-12-23 | **特性分支**: `001-ai-training-platform`

## API概述

数据集管理API提供了上传、版本化和管理AI训练数据集的能力。该API支持大文件上传、数据集版本控制、元数据管理和高效数据访问。

## 基本信息

- **基础路径**: `/api/v1/datasets`
- **认证**: Bearer Token (JWT)
- **内容类型**: application/json, multipart/form-data (上传)
- **响应格式**: JSON

## 端点概览

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | / | 创建新数据集 | `dataset:create` |
| GET | / | 获取数据集列表 | `dataset:read` |
| GET | /{id} | 获取特定数据集详情 | `dataset:read` |
| PUT | /{id} | 更新特定数据集 | `dataset:update` |
| DELETE | /{id} | 删除数据集 | `dataset:delete` |
| POST | /{id}/versions | 创建新数据集版本 | `dataset:create` |
| GET | /{id}/versions | 获取数据集版本列表 | `dataset:read` |
| GET | /{id}/versions/{version_id} | 获取特定数据集版本详情 | `dataset:read` |
| POST | /{id}/versions/{version_id}/files | 上传文件到数据集版本 | `dataset:update` |
| GET | /{id}/versions/{version_id}/files | 获取数据集版本文件列表 | `dataset:read` |
| POST | /{id}/versions/{version_id}/actions/finalize | 完成数据集版本创建 | `dataset:update` |
| POST | /{id}/versions/{version_id}/actions/compare | 比较两个数据集版本 | `dataset:read` |

## 详细定义

### 创建数据集 (POST /)

创建新的数据集元数据记录，准备接收数据文件。

#### 请求体

```json
{
  "name": "imagenet-2025",
  "description": "增强版ImageNet数据集，包含1000个类别和200万张高分辨率图像",
  "storage_type": "s3",
  "project_id": "project-456",
  "access_level": "project",
  "estimated_size_bytes": 1099511627776,
  "content_type": "image",
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "none"
  },
  "tags": ["image", "classification", "high-resolution"]
}
```

#### 响应 (201 Created)

```json
{
  "id": "dataset-123",
  "name": "imagenet-2025",
  "description": "增强版ImageNet数据集，包含1000个类别和200万张高分辨率图像",
  "storage_type": "s3",
  "storage_path": "s3://datasets/dataset-123",
  "project_id": "project-456",
  "created_at": "2025-12-23T08:15:30Z",
  "created_by": "user-123",
  "size_bytes": 0,
  "access_level": "project",
  "content_type": "image",
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "none"
  },
  "tags": ["image", "classification", "high-resolution"],
  "links": {
    "self": "/api/v1/datasets/dataset-123",
    "versions": "/api/v1/datasets/dataset-123/versions"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **409 Conflict**: 资源冲突，例如同名数据集已存在
- **413 Request Entity Too Large**: 请求体过大

### 获取数据集列表 (GET /)

获取用户可访问的数据集列表，支持分页和过滤。

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `project_id`: 按项目ID过滤
- `content_type`: 按内容类型过滤（例如"image", "text", "audio", "video", "tabular"）
- `tags`: 按标签过滤，用逗号分隔
- `created_by`: 按创建者ID过滤
- `from_date`: 从此日期开始创建的数据集 (ISO 8601格式)
- `to_date`: 到此日期结束创建的数据集 (ISO 8601格式)
- `name`: 按名称搜索（支持模糊匹配）
- `sort`: 排序字段 (created_at, name, size_bytes)
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "items": [
    {
      "id": "dataset-123",
      "name": "imagenet-2025",
      "description": "增强版ImageNet数据集，包含1000个类别和200万张高分辨率图像",
      "storage_type": "s3",
      "project_id": "project-456",
      "created_at": "2025-12-23T08:15:30Z",
      "created_by": "user-123",
      "size_bytes": 1099511627776,
      "latest_version": "v1.0.0",
      "version_count": 2,
      "content_type": "image",
      "tags": ["image", "classification", "high-resolution"],
      "links": {
        "self": "/api/v1/datasets/dataset-123"
      }
    },
    {
      "id": "dataset-124",
      "name": "wikipedia-zh-2025",
      "description": "中文维基百科文本语料库",
      "storage_type": "s3",
      "project_id": "project-456",
      "created_at": "2025-12-22T10:30:15Z",
      "created_by": "user-123",
      "size_bytes": 21474836480,
      "latest_version": "v2.1.0",
      "version_count": 3,
      "content_type": "text",
      "tags": ["text", "chinese", "corpus"],
      "links": {
        "self": "/api/v1/datasets/dataset-124"
      }
    }
  ],
  "pagination": {
    "total_items": 15,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  }
}
```

### 获取特定数据集详情 (GET /{id})

获取单个数据集的详细信息。

#### 路径参数

- `id`: 数据集ID

#### 响应 (200 OK)

```json
{
  "id": "dataset-123",
  "name": "imagenet-2025",
  "description": "增强版ImageNet数据集，包含1000个类别和200万张高分辨率图像",
  "storage_type": "s3",
  "storage_path": "s3://datasets/dataset-123",
  "project_id": "project-456",
  "access_level": "project",
  "created_at": "2025-12-23T08:15:30Z",
  "updated_at": "2025-12-23T10:45:20Z",
  "created_by": {
    "id": "user-123",
    "username": "zhang.wei",
    "email": "zhang.wei@example.com"
  },
  "size_bytes": 1099511627776,
  "content_type": "image",
  "file_count": 2000000,
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "none"
  },
  "tags": ["image", "classification", "high-resolution"],
  "versions": [
    {
      "id": "v1.0.0",
      "created_at": "2025-12-23T09:30:00Z",
      "size_bytes": 549755813888,
      "status": "ready",
      "file_count": 1000000
    },
    {
      "id": "v1.1.0",
      "created_at": "2025-12-23T10:45:20Z",
      "size_bytes": 549755813888,
      "status": "ready",
      "file_count": 1000000
    }
  ],
  "usage": {
    "training_job_count": 5,
    "last_used_at": "2025-12-23T12:00:00Z"
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123",
    "versions": "/api/v1/datasets/dataset-123/versions",
    "latest_version": "/api/v1/datasets/dataset-123/versions/v1.1.0"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集不存在

### 更新特定数据集 (PUT /{id})

更新现有数据集的元数据信息。

#### 路径参数

- `id`: 数据集ID

#### 请求体

```json
{
  "name": "imagenet-2025-enhanced",
  "description": "增强版ImageNet数据集，更新描述",
  "access_level": "organization",
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "standard",
    "preprocessing": "normalized"
  },
  "tags": ["image", "classification", "high-resolution", "enhanced"]
}
```

#### 响应 (200 OK)

```json
{
  "id": "dataset-123",
  "name": "imagenet-2025-enhanced",
  "updated_at": "2025-12-23T14:20:10Z",
  "links": {
    "self": "/api/v1/datasets/dataset-123"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集不存在
- **409 Conflict**: 资源冲突，例如同名数据集已存在

### 删除数据集 (DELETE /{id})

删除指定的数据集及其所有版本。

#### 路径参数

- `id`: 数据集ID

#### 查询参数

- `force`: 布尔值，是否强制删除（默认false）
- `delete_storage`: 布尔值，是否同时删除存储中的数据文件（默认false）

#### 响应 (204 No Content)

成功删除后无响应体

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集不存在
- **409 Conflict**: 资源正在被使用，无法删除

### 创建新数据集版本 (POST /{id}/versions)

为现有数据集创建新版本，准备接收数据文件。

#### 路径参数

- `id`: 数据集ID

#### 请求体

```json
{
  "version": "v1.1.0",
  "description": "增加100万张新图像，优化类别平衡",
  "based_on_version": "v1.0.0",
  "estimated_size_bytes": 549755813888,
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "standard",
    "class_balance": "improved"
  }
}
```

#### 响应 (201 Created)

```json
{
  "id": "v1.1.0",
  "dataset_id": "dataset-123",
  "version": "v1.1.0",
  "description": "增加100万张新图像，优化类别平衡",
  "based_on_version": "v1.0.0",
  "storage_path": "s3://datasets/dataset-123/v1.1.0",
  "created_at": "2025-12-23T10:45:20Z",
  "created_by": "user-123",
  "status": "creating",
  "size_bytes": 0,
  "file_count": 0,
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "standard",
    "class_balance": "improved"
  },
  "upload_credentials": {
    "upload_id": "upload-789",
    "presigned_url_base": "https://api.example.com/uploads/dataset-123/v1.1.0",
    "expires_at": "2025-12-23T11:45:20Z"
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0",
    "dataset": "/api/v1/datasets/dataset-123",
    "files": "/api/v1/datasets/dataset-123/versions/v1.1.0/files",
    "finalize": "/api/v1/datasets/dataset-123/versions/v1.1.0/actions/finalize"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集不存在
- **409 Conflict**: 版本号已存在

### 获取数据集版本列表 (GET /{id}/versions)

获取数据集的所有版本列表。

#### 路径参数

- `id`: 数据集ID

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为20，最大为100
- `status`: 按状态过滤 (creating, ready, failed)
- `sort`: 排序字段 (created_at, version)，默认为created_at
- `order`: 排序方向 (asc, desc)，默认desc

#### 响应 (200 OK)

```json
{
  "dataset_id": "dataset-123",
  "items": [
    {
      "id": "v1.1.0",
      "version": "v1.1.0",
      "description": "增加100万张新图像，优化类别平衡",
      "created_at": "2025-12-23T10:45:20Z",
      "created_by": "user-123",
      "status": "ready",
      "size_bytes": 549755813888,
      "file_count": 1000000,
      "links": {
        "self": "/api/v1/datasets/dataset-123/versions/v1.1.0"
      }
    },
    {
      "id": "v1.0.0",
      "version": "v1.0.0",
      "description": "初始版本",
      "created_at": "2025-12-23T09:30:00Z",
      "created_by": "user-123",
      "status": "ready",
      "size_bytes": 549755813888,
      "file_count": 1000000,
      "links": {
        "self": "/api/v1/datasets/dataset-123/versions/v1.0.0"
      }
    }
  ],
  "pagination": {
    "total_items": 2,
    "total_pages": 1,
    "current_page": 1,
    "per_page": 20,
    "next": null,
    "prev": null
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions",
    "dataset": "/api/v1/datasets/dataset-123"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集不存在

### 获取特定数据集版本详情 (GET /{id}/versions/{version_id})

获取单个数据集版本的详细信息。

#### 路径参数

- `id`: 数据集ID
- `version_id`: 版本ID

#### 响应 (200 OK)

```json
{
  "id": "v1.1.0",
  "dataset_id": "dataset-123",
  "version": "v1.1.0",
  "description": "增加100万张新图像，优化类别平衡",
  "based_on_version": "v1.0.0",
  "storage_path": "s3://datasets/dataset-123/v1.1.0",
  "created_at": "2025-12-23T10:45:20Z",
  "updated_at": "2025-12-23T11:30:00Z",
  "created_by": {
    "id": "user-123",
    "username": "zhang.wei",
    "email": "zhang.wei@example.com"
  },
  "status": "ready",
  "size_bytes": 549755813888,
  "file_count": 1000000,
  "file_stats": {
    "by_extension": {
      ".jpg": 950000,
      ".png": 50000
    },
    "by_directory": {
      "train": 800000,
      "val": 200000
    }
  },
  "metadata": {
    "image_format": "jpeg",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "augmentation": "standard",
    "class_balance": "improved"
  },
  "validation_results": {
    "status": "passed",
    "checks": [
      {
        "name": "file_integrity",
        "status": "passed",
        "details": "所有文件完整性校验通过"
      },
      {
        "name": "schema_validation",
        "status": "passed",
        "details": "所有元数据符合模式要求"
      }
    ]
  },
  "usage": {
    "training_job_count": 3,
    "last_used_at": "2025-12-23T12:00:00Z"
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0",
    "dataset": "/api/v1/datasets/dataset-123",
    "files": "/api/v1/datasets/dataset-123/versions/v1.1.0/files",
    "download": "/api/v1/datasets/dataset-123/versions/v1.1.0/download"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集或版本不存在

### 上传文件到数据集版本 (POST /{id}/versions/{version_id}/files)

上传文件到数据集版本。支持单文件上传和分片上传。

#### 路径参数

- `id`: 数据集ID
- `version_id`: 版本ID

#### 请求体 (multipart/form-data)

- `file`: 文件内容
- `path`: 文件在数据集中的路径
- `metadata`: JSON格式的文件元数据 (可选)

#### 响应 (201 Created)

```json
{
  "file_id": "file-456",
  "path": "train/cat/image12345.jpg",
  "size_bytes": 2097152,
  "content_type": "image/jpeg",
  "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
  "upload_status": "complete",
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0/files/file-456"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集或版本不存在
- **409 Conflict**: 文件路径已存在
- **413 Request Entity Too Large**: 文件大小超过限制
- **507 Insufficient Storage**: 存储空间不足

### 大文件分片上传 (POST /{id}/versions/{version_id}/files)

对于大文件，支持分片上传机制。

#### 初始化上传 (multipart/form-data)

- `action`: "initiate_multipart"
- `path`: 文件在数据集中的路径
- `size_bytes`: 文件总大小
- `content_type`: 文件MIME类型
- `total_parts`: 分片总数
- `metadata`: JSON格式的文件元数据 (可选)

#### 响应 (202 Accepted)

```json
{
  "file_id": "file-456",
  "path": "train/cat/image12345.jpg",
  "upload_id": "upload-789",
  "size_bytes": 1073741824,
  "content_type": "image/jpeg",
  "total_parts": 100,
  "upload_status": "pending",
  "part_upload_urls": [
    {
      "part_number": 1,
      "presigned_url": "https://api.example.com/uploads/dataset-123/v1.1.0/file-456/1",
      "expires_at": "2025-12-23T11:45:20Z"
    },
    {
      "part_number": 2,
      "presigned_url": "https://api.example.com/uploads/dataset-123/v1.1.0/file-456/2",
      "expires_at": "2025-12-23T11:45:20Z"
    }
  ],
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0/files/file-456",
    "complete": "/api/v1/datasets/dataset-123/versions/v1.1.0/files/file-456/complete"
  }
}
```

#### 完成分片上传 (POST /{id}/versions/{version_id}/files/{file_id}/complete)

```json
{
  "upload_id": "upload-789",
  "parts": [
    {
      "part_number": 1,
      "etag": "7b2270617274223a317d"
    },
    {
      "part_number": 2,
      "etag": "7b2270617274223a327d"
    }
  ]
}
```

#### 响应 (200 OK)

```json
{
  "file_id": "file-456",
  "path": "train/cat/image12345.jpg",
  "size_bytes": 1073741824,
  "content_type": "image/jpeg",
  "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
  "upload_status": "complete",
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0/files/file-456"
  }
}
```

### 获取数据集版本文件列表 (GET /{id}/versions/{version_id}/files)

获取数据集版本包含的文件列表，支持分页和过滤。

#### 路径参数

- `id`: 数据集ID
- `version_id`: 版本ID

#### 查询参数

- `page`: 页码，默认为1
- `per_page`: 每页条目数，默认为100，最大为1000
- `prefix`: 按路径前缀过滤
- `sort`: 排序字段 (path, size_bytes)，默认为path
- `order`: 排序方向 (asc, desc)，默认asc

#### 响应 (200 OK)

```json
{
  "dataset_id": "dataset-123",
  "version_id": "v1.1.0",
  "items": [
    {
      "file_id": "file-456",
      "path": "train/cat/image12345.jpg",
      "size_bytes": 2097152,
      "content_type": "image/jpeg",
      "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
      "last_modified": "2025-12-23T11:00:00Z",
      "metadata": {
        "width": 1024,
        "height": 1024,
        "class": "cat",
        "label": 0
      }
    },
    {
      "file_id": "file-457",
      "path": "train/cat/image12346.jpg",
      "size_bytes": 1835008,
      "content_type": "image/jpeg",
      "md5_hash": "a92c4de3a6e9693e3e5ef15408abed10",
      "last_modified": "2025-12-23T11:05:00Z",
      "metadata": {
        "width": 1024,
        "height": 1024,
        "class": "cat",
        "label": 0
      }
    }
  ],
  "pagination": {
    "total_items": 1000000,
    "total_pages": 10000,
    "current_page": 1,
    "per_page": 100,
    "next": "/api/v1/datasets/dataset-123/versions/v1.1.0/files?page=2&per_page=100",
    "prev": null
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0/files",
    "version": "/api/v1/datasets/dataset-123/versions/v1.1.0",
    "dataset": "/api/v1/datasets/dataset-123"
  }
}
```

#### 错误响应

- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集或版本不存在

### 完成数据集版本创建 (POST /{id}/versions/{version_id}/actions/finalize)

标记数据集版本上传完成，触发验证和索引处理。

#### 路径参数

- `id`: 数据集ID
- `version_id`: 版本ID

#### 请求体

```json
{
  "metadata_update": {
    "image_format": "mixed",
    "min_resolution": "1024x1024",
    "classes": 1000,
    "class_balance": "improved",
    "total_images": 1000000
  },
  "skip_validation": false,
  "make_default": true
}
```

#### 响应 (200 OK)

```json
{
  "id": "v1.1.0",
  "dataset_id": "dataset-123",
  "status": "validating",
  "validation_job_id": "job-567",
  "estimated_completion_time": "2025-12-23T12:00:00Z",
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0",
    "validation_job": "/api/v1/jobs/job-567"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集或版本不存在
- **409 Conflict**: 版本状态不允许完成操作

### 比较两个数据集版本 (POST /{id}/versions/{version_id}/actions/compare)

比较两个数据集版本之间的差异。

#### 路径参数

- `id`: 数据集ID
- `version_id`: 基准版本ID

#### 请求体

```json
{
  "target_version_id": "v1.0.0",
  "comparison_type": "detailed",
  "include_file_list": true,
  "max_differences": 1000
}
```

#### 响应 (200 OK)

```json
{
  "base_version_id": "v1.1.0",
  "target_version_id": "v1.0.0",
  "summary": {
    "added_files_count": 500000,
    "removed_files_count": 0,
    "modified_files_count": 500000,
    "unchanged_files_count": 500000,
    "total_size_difference_bytes": 0
  },
  "metadata_differences": {
    "class_balance": {
      "base": "improved",
      "target": null
    },
    "augmentation": {
      "base": "standard",
      "target": "none"
    }
  },
  "directory_differences": {
    "train/cat": {
      "added_files_count": 5000,
      "removed_files_count": 0,
      "modified_files_count": 0
    },
    "train/dog": {
      "added_files_count": 5000,
      "removed_files_count": 0,
      "modified_files_count": 0
    }
  },
  "file_differences": {
    "added_files": [
      {
        "path": "train/cat/image99999.jpg",
        "size_bytes": 2097152
      },
      {
        "path": "train/cat/image99998.jpg",
        "size_bytes": 2097152
      }
    ],
    "removed_files": [],
    "modified_files": [
      {
        "path": "train/metadata.json",
        "base_size_bytes": 1048576,
        "target_size_bytes": 1045576
      }
    ]
  },
  "links": {
    "self": "/api/v1/datasets/dataset-123/versions/v1.1.0/actions/compare",
    "base_version": "/api/v1/datasets/dataset-123/versions/v1.1.0",
    "target_version": "/api/v1/datasets/dataset-123/versions/v1.0.0"
  }
}
```

#### 错误响应

- **400 Bad Request**: 请求参数无效
- **401 Unauthorized**: 未授权访问
- **403 Forbidden**: 权限不足
- **404 Not Found**: 指定的数据集或版本不存在

## 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 202 | 请求已接受，但处理尚未完成 |
| 204 | 请求成功，无返回内容 |
| 400 | 请求参数无效 |
| 401 | 未提供认证或认证无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 413 | 请求体或上传文件过大 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |
| 507 | 存储空间不足 |

## 错误响应格式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "数据集不存在",
    "details": "找不到ID为dataset-123的数据集",
    "request_id": "req-abc-123"
  }
}
```

## 速率限制

API实施速率限制以防止滥用。限制信息通过HTTP响应头提供：

- `X-RateLimit-Limit`: 时间窗口内允许的请求数
- `X-RateLimit-Remaining`: 当前时间窗口内剩余的请求数
- `X-RateLimit-Reset`: 当前时间窗口重置的时间（Unix时间戳）

超过限制时返回429状态码。

## 数据集上传最佳实践

1. **创建数据集和版本**：首先创建数据集元数据，然后创建版本
2. **大文件分片上传**：对于大于10MB的文件，使用分片上传API
3. **并行上传**：利用多个并行连接同时上传多个文件或文件分片
4. **断点续传**：记录已上传的文件和分片，支持上传中断后继续
5. **验证和索引**：所有文件上传完成后，调用finalize端点触发验证和索引
6. **元数据更新**：完成上传后可以更新数据集和版本的元数据
7. **数据集结构**：遵循约定的目录结构（例如train/val/test分割）
8. **文件命名**：使用有意义且符合约定的文件命名

## 版本控制

API使用语义化版本控制，格式为v{major}.{minor}.{patch}。主要版本号变更表示不向后兼容的更改，客户端应该通过API基础路径中的版本号指定使用的API版本。

## 安全要求

1. 所有API请求必须使用HTTPS
2. 认证使用Bearer Token (JWT)
3. 令牌必须包含适当的权限范围
4. 令牌过期时间不超过12小时
5. 敏感数据（如API密钥、密码）不会记录在日志中