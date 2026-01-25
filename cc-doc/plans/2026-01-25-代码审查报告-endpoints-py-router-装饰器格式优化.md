# 代码审查报告: endpoints.py Router 装饰器格式优化

## 审查标准

**单行格式优先，仅超过 120 字符时使用多行格式。**

## 审查发现

### 📊 分析结果

| 文件 | 可简化为单行 | 需保持多行 (>120) |
|------|:-----------:|:----------------:|
| `datasets/api/endpoints.py` | 13 处 | 1 处 |
| `training/api/endpoints.py` | 9 处 | 0 处 |
| `monitoring/api/endpoints.py` | 6 处 | 0 处 |
| `quotas/api/endpoints.py` | 4 处 | 0 处 |
| `quotas/api/resource_quota_endpoints.py` | 4 处 | 0 处 |
| `audit/api/endpoints.py` | ✅ 已是单行 | - |

### ✅ 符合标准的文件

- `audit/api/endpoints.py` - 已使用单行格式，无需修改

### ⚠️ 需要简化的文件

共 **36 处**多行装饰器可简化为单行（均 ≤120 字符）。

---

## 🛠️ 修改计划

### 1. datasets/api/endpoints.py (13 处可简化，1 处保持)

**可简化为单行**:
```python
# L72 (83字符)
@router.post("", response_model=DatasetDetail, status_code=status.HTTP_201_CREATED)

# L94 (51字符)
@router.get("", response_model=DatasetListResponse)

# L145 (58字符)
@router.get("/{dataset_id}", response_model=DatasetDetail)

# L172 (60字符)
@router.patch("/{dataset_id}", response_model=DatasetDetail)

# L202 (105字符)
@router.post("/{dataset_id}/versions", response_model=DatasetDetail, status_code=status.HTTP_201_CREATED)

# L262 (101字符)
@router.post("/{dataset_id}/upload/{upload_id}/presigned-urls", response_model=PresignedUrlsResponse)

# L315 (95字符)
@router.get("/{dataset_id}/upload/{upload_id}/progress", response_model=UploadProgressResponse)

# L347 (96字符)
@router.post("/{dataset_id}/upload/{upload_id}/complete", response_model=CompleteUploadResponse)

# L393 (107字符)
@router.post("/{dataset_id}/fsx/sync", response_model=FsxSyncResponse, status_code=status.HTTP_201_CREATED)

# L414 (85字符)
@router.get("/{dataset_id}/fsx/sync/{task_id}", response_model=FsxSyncStatusResponse)

# L439 (111字符)
@router.post("/{dataset_id}/fsx/prefetch", response_model=FsxSyncResponse, status_code=status.HTTP_201_CREATED)

# L477 (69字符)
@router.get("/{dataset_id}/fsx/path", response_model=FsxPathResponse)

# L508 (66字符)
@router.get("/fsx/health", response_model=FsxAvailabilityResponse)
```

**需保持多行** (121 字符 > 120):
```python
# L231 - 保持多行格式
@router.post(
    "/{dataset_id}/upload/initiate",
    response_model=InitiateUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
```

### 2. training/api/endpoints.py (9 处)

```python
@router.post("", response_model=TrainingJobDetail, status_code=status.HTTP_201_CREATED)
@router.get("", response_model=TrainingJobListResponse)
@router.get("/{job_id}", response_model=TrainingJobDetail)
@router.put("/{job_id}", response_model=TrainingJobDetail)
@router.post("/{job_id}/pause", response_model=TrainingJobDetail)
@router.post("/{job_id}/resume", response_model=TrainingJobDetail)
@router.post("/{job_id}/cancel", response_model=TrainingJobDetail)
@router.post("/{job_id}/checkpoints", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
@router.post("/from-template/{template_id}", response_model=TrainingJobDetail, status_code=status.HTTP_201_CREATED)
```

### 3. monitoring/api/endpoints.py (6 处)

```python
@router.get("/clusters/{cluster_name}/metrics", response_model=ClusterMetricsResponse)
@router.get("/jobs/{job_id}/gpu-utilization", response_model=GPUUtilizationResponse)
@router.get("/grafana/dashboards", response_model=GrafanaDashboardsResponse)
@router.get("/storage", response_model=StorageMetricsResponse)
@router.get("/network", response_model=NetworkMetricsResponse)
@router.get("/clusters/{cluster_name}/health", response_model=ClusterHealthResponse)
```

### 4. quotas/api/endpoints.py (4 处)

```python
@router.get("", response_model=ResourceLimitConfigListResponse)
@router.post("", response_model=ResourceLimitConfigResponse, status_code=status.HTTP_201_CREATED)
@router.get("/{config_id}", response_model=ResourceLimitConfigResponse)
@router.put("/{config_id}", response_model=ResourceLimitConfigResponse)
```

### 5. quotas/api/resource_quota_endpoints.py (4 处)

```python
@router.get("", response_model=ResourceQuotaListResponse)
@router.post("", response_model=ResourceQuotaResponse, status_code=status.HTTP_201_CREATED)
@router.get("/{quota_id}", response_model=ResourceQuotaResponse)
@router.put("/{quota_id}", response_model=ResourceQuotaResponse)
```

---

## 特殊情况：带 responses 参数的装饰器

`models/api/endpoints.py` 和 `spaces/api/endpoints.py` 中有带 `responses={}` 参数的装饰器，这些通常会超过 120 字符，建议保持多行格式：

```python
# models/api/endpoints.py - 保持多行
@router.post(
    "",
    response_model=ModelDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ModelErrorResponse, "description": "Training job or checkpoint not found"},
        422: {"model": ModelErrorResponse, "description": "Validation error"},
    },
)
```

---

## 验证方式

```bash
# 代码格式检查
black backend/src/modules/*/api/endpoints.py
ruff check backend/src/modules/*/api/endpoints.py

# 运行测试确保无破坏
pytest tests/unit -v --tb=short
pytest tests/integration -v --tb=short
```

---

## 📋 审查结论

| 类型 | 数量 | 描述 |
|------|------|------|
| 可简化为单行 | 36 处 | ≤120 字符，应改为单行 |
| 需保持多行 | 1 处 | >120 字符 |
| 已符合标准 | 4 处 | audit 模块 |
| 特殊情况 | ~10 处 | 带 responses 参数，建议保持多行 |

**建议**: 将 36 处多行装饰器简化为单行格式，提高代码可读性。
