# Backend Tests 重构计划

> **目标**: 将 `backend/tests` 目录重构为符合 `backend/tests/CLAUDE.md` v1.6 规范的扁平结构
> **预计工作量**: 5 个阶段

---

## 一、问题分析

### 当前状态
- **目录结构**: 混合新旧两种结构，嵌套深度 5-6 层
- **文件命名**: 缺少类型前缀（`test_entity_`, `test_svc_` 等）
- **重复文件**: 多处遗留文件与新模块文件重复

### 规范要求
- **扁平结构**: `unit/{module}/test_{prefix}_{name}.py`（最大 4 层）
- **文件前缀**: `test_entity_`, `test_vo_`, `test_svc_`, `test_api_` 等

---

## 二、重构阶段

### Phase 1: 准备工作
1. 运行全部测试记录基线: `pytest tests/ -v --tb=short`
2. 创建目标目录骨架:
   - `unit/shared/`, `unit/auth/`, `unit/training/`, `unit/models/`, `unit/quotas/`, `unit/audit/`
   - `integration/shared/`, `integration/auth/`, `integration/training/`, `integration/models/`, `integration/quotas/`

### Phase 2: Unit Tests 迁移

#### 2.1 shared 模块 (从 unit/core/, unit/shared/infrastructure/)
| 源路径 | 目标路径 |
|-------|---------|
| `unit/core/security/test_jwt.py` | `unit/shared/test_svc_jwt.py` |
| `unit/core/security/test_password.py` | `unit/shared/test_svc_password.py` |
| `unit/core/security/test_exceptions.py` | `unit/shared/test_svc_auth_exceptions.py` |
| `unit/core/mapping/test_enum_mapper.py` | `unit/shared/test_svc_enum_mapper.py` |
| `unit/infrastructure/test_s3_client.py` | `unit/shared/test_svc_s3_client.py` |
| `unit/api/test_exception_handlers.py` | `unit/shared/test_svc_exception_handlers.py` |

**删除重复**:
- `unit/shared/infrastructure/security/` 整个目录
- `unit/shared/utils/` 整个目录

#### 2.2 training 模块 (从 unit/modules/training/)
| 源路径 | 目标路径 |
|-------|---------|
| `unit/modules/training/domain/entities/test_training_job.py` | `unit/training/test_entity_training_job.py` |
| `unit/modules/training/domain/entities/test_checkpoint.py` | `unit/training/test_entity_checkpoint.py` |
| `unit/modules/training/domain/value_objects/test_training_metrics.py` | `unit/training/test_vo_training_metrics.py` |
| `unit/modules/training/domain/value_objects/test_pod_statistics.py` | `unit/training/test_vo_pod_statistics.py` |
| `unit/modules/training/application/services/test_training_job_service.py` | `unit/training/test_svc_training_job.py` |
| `unit/modules/training/application/services/test_hyperpod_service.py` | `unit/training/test_svc_hyperpod.py` |
| `unit/modules/training/application/services/test_hyperpod_client.py` | `unit/training/test_svc_hyperpod_client.py` |
| `unit/modules/training/conftest.py` | `unit/training/conftest.py` |

**删除重复**:
- `unit/domain/entities/test_training_job.py`
- `unit/domain/entities/test_checkpoint.py`
- `unit/domain/value_objects/test_training_metrics.py`
- `unit/domain/value_objects/test_pod_statistics.py`
- `unit/infrastructure/test_hyperpod_client.py`

#### 2.3 auth 模块 (从 unit/modules/auth/)
| 源路径 | 目标路径 |
|-------|---------|
| `unit/modules/auth/application/services/test_auth_service.py` | `unit/auth/test_svc_auth.py` |
| `unit/modules/auth/application/services/test_account_service.py` | `unit/auth/test_svc_account.py` |
| `unit/modules/auth/application/services/test_password_service.py` | `unit/auth/test_svc_password.py` |
| `unit/modules/auth/application/services/test_rbac_service.py` | `unit/auth/test_svc_rbac.py` |
| `unit/modules/auth/conftest.py` | `unit/auth/conftest.py` |

**删除重复**:
- `unit/application/services/test_auth_service.py`
- `unit/application/services/test_account_service.py`
- `unit/application/services/test_password_service.py`
- `unit/application/services/test_rbac_service.py`

#### 2.4 models 模块 (从 unit/modules/models/)
| 源路径 | 目标路径 |
|-------|---------|
| `unit/modules/models/domain/entities/test_model.py` | `unit/models/test_entity_model.py` |
| `unit/modules/models/application/services/test_model_service.py` | `unit/models/test_svc_model.py` |
| `unit/modules/models/conftest.py` | `unit/models/conftest.py` |

**删除重复**:
- `unit/domain/entities/test_model.py`
- `unit/application/services/test_model_service.py`

#### 2.5 quotas 模块 (从 unit/modules/quotas/)
| 源路径 | 目标路径 |
|-------|---------|
| `unit/modules/quotas/application/services/test_resource_limit_config_service.py` | `unit/quotas/test_svc_resource_limit_config.py` |
| `unit/modules/quotas/conftest.py` | `unit/quotas/conftest.py` |

**删除重复**:
- `unit/application/services/test_resource_limit_config_service.py`

#### 2.6 audit 模块
| 源路径 | 目标路径 |
|-------|---------|
| `unit/api/middleware/test_audit_middleware.py` | `unit/audit/test_svc_audit_middleware.py` |

### Phase 3: Integration Tests 迁移

| 源路径 | 目标路径 |
|-------|---------|
| `integration/api/test_auth_endpoints.py` | `integration/auth/test_api_auth.py` |
| `integration/api/test_training_job_endpoints.py` | `integration/training/test_api_training_job.py` |
| `integration/api/test_models_endpoints.py` | `integration/models/test_api_models.py` |
| `integration/api/test_resource_limit_configs_endpoints.py` | `integration/quotas/test_api_resource_limit_configs.py` |
| `integration/middleware/test_auth_middleware.py` | `integration/auth/test_api_auth_middleware.py` |
| `integration/middleware/test_sso_middleware.py` | `integration/auth/test_api_sso_middleware.py` |
| `integration/aws/test_hyperpod_integration.py` | `integration/training/test_aws_hyperpod.py` |
| `integration/aws/test_hyperpod_service_integration.py` | `integration/training/test_aws_hyperpod_service.py` |
| `integration/aws/test_s3_integration.py` | `integration/shared/test_aws_s3.py` |
| `integration/test_gang_scheduling.py` | `integration/training/test_api_gang_scheduling.py` |

**删除重复** (`integration/modules/` 整个目录)

### Phase 4: 清理遗留目录

**删除空目录**:
- `unit/core/`
- `unit/domain/`
- `unit/application/`
- `unit/infrastructure/`
- `unit/api/`
- `unit/modules/`
- `integration/api/`
- `integration/middleware/`
- `integration/aws/`
- `integration/modules/`

### Phase 5: 验证与收尾

1. 运行全部测试验证: `pytest tests/ -v --tb=short`
2. 对比测试数量与基线一致
3. 运行覆盖率: `pytest tests/ --cov=src`
4. 更新 `tests/CLAUDE.md` 中的目录结构说明（移除过渡警告）

---

## 三、关键文件

### 保留不变
- `tests/conftest.py` - 全局配置和自动标记（已实现）
- `tests/unit/conftest.py` - 全局 fixtures（JWT、密码、用户数据）
- `tests/shared/` - 共享 fixtures 和 helpers
- `tests/architecture/` - 架构合规测试
- `tests/e2e/` - E2E 测试骨架
- `tests/performance/` - 性能测试骨架

### 需迁移的 conftest.py
- `unit/modules/training/conftest.py` → `unit/training/conftest.py`
- `unit/modules/auth/conftest.py` → `unit/auth/conftest.py`
- `unit/modules/models/conftest.py` → `unit/models/conftest.py`
- `unit/modules/quotas/conftest.py` → `unit/quotas/conftest.py`
- `integration/aws/conftest.py` → `integration/training/conftest.py`

---

## 四、最终目录结构

```
backend/tests/
├── conftest.py
├── CLAUDE.md
├── shared/
│   ├── fixtures/
│   ├── helpers/
│   └── constants.py
├── unit/
│   ├── conftest.py
│   ├── shared/
│   │   ├── test_svc_jwt.py
│   │   ├── test_svc_password.py
│   │   ├── test_svc_auth_exceptions.py
│   │   ├── test_svc_enum_mapper.py
│   │   ├── test_svc_s3_client.py
│   │   └── test_svc_exception_handlers.py
│   ├── auth/
│   │   ├── conftest.py
│   │   ├── test_svc_auth.py
│   │   ├── test_svc_account.py
│   │   ├── test_svc_password.py
│   │   └── test_svc_rbac.py
│   ├── training/
│   │   ├── conftest.py
│   │   ├── test_entity_training_job.py
│   │   ├── test_entity_checkpoint.py
│   │   ├── test_vo_training_metrics.py
│   │   ├── test_vo_pod_statistics.py
│   │   ├── test_svc_training_job.py
│   │   ├── test_svc_hyperpod.py
│   │   └── test_svc_hyperpod_client.py
│   ├── models/
│   │   ├── conftest.py
│   │   ├── test_entity_model.py
│   │   └── test_svc_model.py
│   ├── quotas/
│   │   ├── conftest.py
│   │   └── test_svc_resource_limit_config.py
│   └── audit/
│       └── test_svc_audit_middleware.py
├── integration/
│   ├── conftest.py
│   ├── shared/
│   │   └── test_aws_s3.py
│   ├── auth/
│   │   ├── test_api_auth.py
│   │   ├── test_api_auth_middleware.py
│   │   └── test_api_sso_middleware.py
│   ├── training/
│   │   ├── conftest.py
│   │   ├── test_api_training_job.py
│   │   ├── test_api_gang_scheduling.py
│   │   ├── test_aws_hyperpod.py
│   │   └── test_aws_hyperpod_service.py
│   ├── models/
│   │   └── test_api_models.py
│   └── quotas/
│       └── test_api_resource_limit_configs.py
├── e2e/
├── architecture/
└── performance/
```

---

## 五、验证策略

### 每阶段验证
```bash
# Phase 1 后
pytest tests/ --co -q | wc -l  # 记录测试数量基线

# Phase 2/3 每个模块迁移后
pytest tests/unit/{module}/ -v
pytest tests/integration/{module}/ -v

# Phase 5 最终验证
pytest tests/ -v --tb=short
pytest tests/ --cov=src --cov-report=term-missing
```

### 回滚策略
每个 Phase 完成后创建 git commit，如需回滚:
```bash
git revert HEAD  # 回滚单个阶段
```

---

## 六、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 重复文件内容不一致 | 迁移前 diff 比较，保留最新版本 |
| Fixture 依赖断裂 | 逐阶段迁移，每阶段运行测试验证 |
| Import 路径错误 | 文件内容无需修改（仅移动和重命名） |
| 遗漏测试文件 | 迁移前后对比测试数量 |
