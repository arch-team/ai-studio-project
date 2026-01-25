# 代码审查报告: endpoints.py 文件 Router 装饰器格式

## 审查范围

审查了 `backend/src/modules/` 下所有 `endpoints.py` 文件中 `@router.xxx` 装饰器的注释和格式规范。

## 审查发现

### 📊 格式统计

| 模块 | 端点数量 | 格式风格 | 一致性 |
|------|----------|----------|--------|
| `datasets/api/endpoints.py` | 聚合入口 | - | ✅ |
| `datasets/api/dataset_endpoints.py` | 8 | 多行 | ✅ |
| `datasets/api/upload_endpoints.py` | 7 | 多行 | ✅ |
| `datasets/api/fsx_endpoints.py` | 7 | 多行 | ✅ |
| `training/api/endpoints.py` | 14 | 多行 | ✅ |
| `models/api/endpoints.py` | 7 | 多行（含 responses） | ✅ |
| `quotas/api/endpoints.py` | 5 | 多行 | ✅ |
| `spaces/api/endpoints.py` | 5 | 多行（含 responses） | ✅ |
| `audit/api/endpoints.py` | 4 | **单行** | ⚠️ |
| `monitoring/api/endpoints.py` | 6 | 多行 | ✅ |

### 🔍 两种 Router 装饰器格式

#### 格式 A: 多行格式 (主流，10 个文件使用)
```python
@router.post(
    "",
    response_model=DatasetDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(...):
```

#### 格式 B: 单行格式 (仅 audit 模块)
```python
@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(...):
```

### ⚠️ 不一致问题

**audit/api/endpoints.py** 使用单行格式，与其他所有模块不一致：

| 行号 | 当前格式 | 建议统一为 |
|------|---------|-----------|
| 101 | `@router.get("", response_model=AuditLogListResponse)` | 多行 |
| 150 | `@router.get("/{audit_log_id}", response_model=AuditLogResponse)` | 多行 |
| 163 | `@router.get("/count/total", response_model=AuditLogCountResponse)` | 多行 |
| 172 | `@router.delete("/cleanup", response_model=CleanupResultResponse)` | 多行 |

### ✅ 质量亮点

1. **response_model 规范** - 所有端点都正确指定了 `response_model`
2. **status_code 规范** - POST 创建端点正确使用 `status_code=status.HTTP_201_CREATED`
3. **responses 文档** - models 和 spaces 模块提供了完整的错误响应文档
4. **DELETE 规范** - 统一使用 `status_code=status.HTTP_204_NO_CONTENT`

### 🚨 安全检查结果

| 检查项 | 状态 |
|--------|------|
| 硬编码凭证 | ✅ 未发现 |
| SQL 注入风险 | ✅ 使用 SQLAlchemy ORM |
| XSS 漏洞 | ✅ 使用 Pydantic 验证 |
| 缺少输入验证 | ✅ 已使用 Pydantic Schema |
| 权限检查 | ✅ 统一使用 `check_resource_owner_or_privileged` |

---

## 🛠️ 修改计划

### 目标

将 `audit/api/endpoints.py` 中的 4 个 router 装饰器从单行格式改为多行格式，以保持项目一致性。

### 待修改文件

- `backend/src/modules/audit/api/endpoints.py`

### 具体修改

#### 修改 1: 第 101 行
```python
# 当前
@router.get("", response_model=AuditLogListResponse)

# 改为
@router.get(
    "",
    response_model=AuditLogListResponse,
)
```

#### 修改 2: 第 150 行
```python
# 当前
@router.get("/{audit_log_id}", response_model=AuditLogResponse)

# 改为
@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
```

#### 修改 3: 第 163 行
```python
# 当前
@router.get("/count/total", response_model=AuditLogCountResponse)

# 改为
@router.get(
    "/count/total",
    response_model=AuditLogCountResponse,
)
```

#### 修改 4: 第 172 行
```python
# 当前
@router.delete("/cleanup", response_model=CleanupResultResponse)

# 改为
@router.delete(
    "/cleanup",
    response_model=CleanupResultResponse,
)
```

### 验证方式

```bash
# 运行 audit 模块测试
pytest tests/unit/modules/audit -v

# 代码格式检查
black backend/src/modules/audit/api/endpoints.py
ruff check backend/src/modules/audit/api/endpoints.py
```

---

## 📋 审查结论

| 严重性 | 数量 | 描述 |
|--------|------|------|
| 🔴 CRITICAL | 0 | 无安全问题 |
| 🟡 MEDIUM | 1 | audit 模块格式不一致 |
| 🟢 LOW | 0 | - |

**建议**: 修改 audit 模块的 4 处装饰器格式以保持一致性。这是一个低风险的格式统一变更。
