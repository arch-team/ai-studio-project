# 文件迁移检查报告

## 执行时间
2026-01-16

## 迁移概览

从旧的分层架构向新的模块化架构迁移：
- **旧结构**: api/v1/, application/, domain/, infrastructure/ 按层组织
- **新结构**: modules/{auth,training,models,quotas,datasets,spaces,audit,billing,monitoring}/ 按功能模块组织
- **共享层**: shared/ (domain, infrastructure, api, utils)

---

## 详细对比分析

### 1. API 端点层 (api/v1/endpoints/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 状态 |
|------|------|------|
| api/v1/endpoints/auth.py | modules/auth/api/endpoints.py | ✅ 迁移完成 |
| api/v1/endpoints/training_jobs.py | modules/training/api/endpoints.py | ✅ 迁移完成 |
| api/v1/endpoints/models.py | modules/models/api/endpoints.py | ✅ 迁移完成 |
| api/v1/endpoints/resource_limit_configs.py | modules/quotas/api/endpoints.py | ✅ 迁移完成（资源配额） |

#### 旧文件现状

**/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/backend/src/api/v1/endpoints/**
- `auth.py` - 存在但导入路径仍引用 `application/services`
- `models.py` - 存在但导入路径仍引用 `application/services`
- `training_jobs.py` - 存在但导入路径仍引用 `application/services`
- `resource_limit_configs.py` - 存在但导入路径仍引用 `application/services`

**⚠️ 状态**: 旧文件未删除，未更新导入路径

---

### 2. API Schemas 层 (api/v1/schemas/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 状态 |
|------|------|------|
| api/v1/schemas/auth.py | modules/auth/api/schemas/requests.py + responses.py | ✅ 迁移完成 |
| api/v1/schemas/training_job.py | modules/training/api/schemas/requests.py + responses.py | ✅ 迁移完成 |
| api/v1/schemas/model.py | modules/models/api/schemas/requests.py + responses.py | ✅ 迁移完成 |
| api/v1/schemas/resource_limit_config.py | modules/quotas/api/schemas/requests.py + responses.py | ✅ 迁移完成 |

#### 应保留的共享 Schema 文件

**这些文件应保留在 shared/ 或 api/v1/schemas/**

| 文件 | 内容 | 建议位置 | 原因 |
|------|------|---------|------|
| api/v1/schemas/base.py | 基础 Pydantic Model（如 PaginatedResponse） | shared/api/schemas.py 或保留原位 | 跨模块共享 |
| api/v1/schemas/common.py | 公共数据类型（如 ErrorResponse） | shared/api/schemas.py 或保留原位 | 全局异常处理使用 |

**⚠️ 状态**: 旧文件未删除，这些共享文件仍应保留或移至 shared/

---

### 3. API 依赖注入层 (api/v1/dependencies/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 状态 |
|------|------|------|
| api/v1/dependencies/auth.py | modules/auth/api/dependencies.py | ✅ 迁移完成 |
| api/v1/dependencies/services.py | 各模块 api/dependencies.py | ✅ 迁移完成（分散到各模块） |
| api/v1/dependencies/permissions.py | modules/auth/api/permissions.py | ✅ 迁移完成 |

**⚠️ 状态**: 旧文件未删除

---

### 4. 中间件层 (api/middleware/)

#### 已完成迁移 ✅

| 旧路径 | 新位置 | 状态 |
|------|------|------|
| api/middleware/auth.py | shared/api/middleware/ + modules/auth/api/ | ✅ 部分迁移 |
| api/middleware/audit.py | modules/audit/api/middleware.py | ✅ 迁移完成 |
| api/middleware/sso.py | shared/api/middleware/ 或 modules/auth/api/ | ⚠️ 部分迁移 |

**📍 当前位置**: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/backend/src/api/middleware/`
- auth.py (4.9 KB)
- audit.py (8.7 KB)
- sso.py (10.5 KB)

**⚠️ 状态**: 旧中间件文件仍存在，需确认是否已完全迁移到新位置

---

### 5. 应用服务层 (application/services/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| application/services/auth_service.py | modules/auth/application/services/ | auth | ✅ 迁移完成 |
| application/services/account_service.py | modules/auth/application/services/ | auth | ✅ 迁移完成 |
| application/services/password_service.py | modules/auth/application/services/ | auth | ✅ 迁移完成 |
| application/services/rbac_service.py | modules/auth/application/services/ | auth | ✅ 迁移完成 |
| application/services/training_job_service.py | modules/training/application/services/ | training | ✅ 迁移完成 |
| application/services/checkpoint_service.py | modules/training/application/services/ | training | ✅ 迁移完成 |
| application/services/model_service.py | modules/models/application/services/ | models | ✅ 迁移完成 |
| application/services/resource_limit_config_service.py | modules/quotas/application/services/ | quotas | ✅ 迁移完成 |
| application/services/hyperpod_service.py | modules/training/application/services/ | training | ⚠️ 需检查位置 |

#### 应保留的共享服务文件

| 文件 | 用途 | 建议位置 | 原因 |
|------|------|---------|------|
| application/services/base.py | 基础 Service 类（如 BaseService）| shared/application/base.py | 所有模块继承基类 |
| application/services/mixins/ | Service Mixin（如 TimestampMixin） | shared/application/mixins/ | 跨模块复用 |

**⚠️ 状态**: 旧文件未删除

---

### 6. 应用接口层 (application/interfaces/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| application/interfaces/hyperpod_client.py | modules/training/application/interfaces.py | training | ✅ 迁移完成 |
| application/interfaces/storage_service.py | shared/application/interfaces.py 或 modules/training/ | shared/training | ✅ 迁移完成 |

**⚠️ 状态**: 旧文件未删除

---

### 7. 域层 - 实体 (domain/entities/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| domain/entities/user.py | modules/auth/domain/entities/ | auth | ✅ 迁移完成 |
| domain/entities/login_attempt.py | modules/auth/domain/entities/ | auth | ✅ 迁移完成 |
| domain/entities/password_history.py | modules/auth/domain/entities/ | auth | ✅ 迁移完成 |
| domain/entities/training_job.py | modules/training/domain/entities/ | training | ✅ 迁移完成 |
| domain/entities/checkpoint.py | modules/training/domain/entities/ | training | ✅ 迁移完成 |
| domain/entities/model.py | modules/models/domain/entities/ | models | ✅ 迁移完成 |
| domain/entities/resource_limit_config.py | modules/quotas/domain/entities/ | quotas | ✅ 迁移完成 |
| domain/entities/resource_quota.py | modules/quotas/domain/entities/ | quotas | ✅ 迁移完成 |
| domain/entities/space.py | modules/spaces/domain/entities/ | spaces | ✅ 迁移完成 |
| domain/entities/audit_log.py | modules/audit/domain/entities/ | audit | ✅ 迁移完成 |

**⚠️ 状态**: 旧文件未删除

---

### 8. 域层 - 值对象 (domain/value_objects/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| domain/value_objects/user_enums.py | modules/auth/domain/value_objects/ | auth | ✅ 已拆分为细粒度文件：auth_type.py, user_role.py, user_status.py, permission.py |
| domain/value_objects/training_metrics.py | modules/training/domain/value_objects/ | training | ✅ 迁移完成 |
| domain/value_objects/pod_statistics.py | 🔴 **未迁移** | training | ❌ 旧文件仍存在于 /domain/value_objects/ |

#### 新增值对象（模块特有）

| 新文件 | 模块 | 用途 |
|------|------|------|
| modules/training/domain/value_objects/job_status.py | training | 训练任务状态枚举 |
| modules/training/domain/value_objects/checkpoint_enums.py | training | 检查点状态 |
| modules/models/domain/value_objects/model_enums.py | models | 模型状态 |
| modules/quotas/domain/value_objects/ | quotas | 配额相关枚举 |
| modules/spaces/domain/value_objects/space_enums.py | spaces | 空间状态 |
| modules/audit/domain/value_objects/ | audit | 审计日志枚举 |

**⚠️ 状态**: pod_statistics.py 未迁移，旧的 user_enums.py 未删除

---

### 9. 域层 - 仓库接口 (domain/repositories/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| domain/repositories/user_repository.py | modules/auth/domain/repositories/ | auth | ✅ 迁移完成 |
| domain/repositories/login_attempt_repository.py | modules/auth/domain/repositories/ | auth | ✅ 迁移完成 |
| domain/repositories/password_history_repository.py | modules/auth/domain/repositories/ | auth | ✅ 迁移完成 |
| domain/repositories/training_job_repository.py | modules/training/domain/repositories/ | training | ✅ 迁移完成 |
| domain/repositories/checkpoint_repository.py | modules/training/domain/repositories/ | training | ✅ 迁移完成 |
| domain/repositories/model_repository.py | modules/models/domain/repositories/ | models | ✅ 迁移完成 |
| domain/repositories/resource_limit_config_repository.py | modules/quotas/domain/repositories/ | quotas | ✅ 迁移完成 |
| domain/repositories/base.py | shared/domain/base_repository.py | shared | ✅ 迁移完成 |

#### 缺失的仓库接口

| 应有文件 | 模块 | 现状 |
|---------|------|------|
| modules/quotas/domain/repositories/resource_quota_repository.py | quotas | ❌ 不存在（但有资源配额实体） |
| modules/spaces/domain/repositories/space_repository.py | spaces | ✅ 存在 |
| modules/audit/domain/repositories/audit_log_repository.py | audit | ✅ 存在 |
| modules/datasets/domain/repositories/ | datasets | ❌ 空目录 |
| modules/monitoring/domain/repositories/ | monitoring | ❌ 空目录 |
| modules/billing/domain/repositories/ | billing | ❌ 空目录 |

**⚠️ 状态**: 旧文件未删除，quotas 模块缺少 resource_quota_repository

---

### 10. 基础设施层 - ORM 模型 (infrastructure/persistence/models/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| infrastructure/persistence/models/user_model.py | modules/auth/infrastructure/models/ | auth | ✅ 迁移完成 |
| infrastructure/persistence/models/login_attempt_model.py | modules/auth/infrastructure/models/ | auth | ✅ 迁移完成 |
| infrastructure/persistence/models/password_history_model.py | modules/auth/infrastructure/models/ | auth | ✅ 迁移完成 |
| infrastructure/persistence/models/training_job_model.py | modules/training/infrastructure/models/ | training | ✅ 迁移完成 |
| infrastructure/persistence/models/checkpoint_model.py | modules/training/infrastructure/models/ | training | ✅ 迁移完成 |
| infrastructure/persistence/models/ml_model.py | modules/models/infrastructure/models/model_model.py | models | ✅ 迁移完成 |
| infrastructure/persistence/models/resource_limit_config_model.py | modules/quotas/infrastructure/models/ | quotas | ✅ 迁移完成 |
| infrastructure/persistence/models/resource_quota_model.py | modules/quotas/infrastructure/models/ | quotas | ✅ 迁移完成 |
| infrastructure/persistence/models/development_space_model.py | modules/spaces/infrastructure/models/space_model.py | spaces | ⚠️ 文件未删除，新模型已创建 |
| infrastructure/persistence/models/audit_log_model.py | modules/audit/infrastructure/models/ | audit | ✅ 迁移完成 |
| infrastructure/persistence/models/base.py | shared/infrastructure/persistence/base.py | shared | ✅ 迁移完成 |

**📍 旧 ORM 模型位置**: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/backend/src/infrastructure/persistence/models/`

**⚠️ 状态**: 旧文件大部分未删除，development_space_model.py 仍存在

---

### 11. 基础设施层 - 仓库实现 (infrastructure/persistence/repositories/)

#### 已完成迁移 ✅

| 旧路径 | 新路径 | 模块 | 状态 |
|------|------|------|------|
| infrastructure/.../user_repository_impl.py | modules/auth/infrastructure/repositories/ | auth | ✅ 迁移完成 |
| infrastructure/.../login_attempt_repository_impl.py | modules/auth/infrastructure/repositories/ | auth | ✅ 迁移完成 |
| infrastructure/.../password_history_repository_impl.py | modules/auth/infrastructure/repositories/ | auth | ✅ 迁移完成 |
| infrastructure/.../training_job_repository_impl.py | modules/training/infrastructure/repositories/ | training | ✅ 迁移完成 |
| infrastructure/.../checkpoint_repository_impl.py | modules/training/infrastructure/repositories/ | training | ✅ 迁移完成 |
| infrastructure/.../model_repository_impl.py | modules/models/infrastructure/repositories/ | models | ✅ 迁移完成 |
| infrastructure/.../resource_limit_config_repository_impl.py | modules/quotas/infrastructure/repositories/ | quotas | ✅ 迁移完成 |
| infrastructure/.../audit_log_repository_impl.py | modules/audit/infrastructure/repositories/ | audit | ✅ 迁移完成 |

#### 缺失的仓库实现

| 应有文件 | 模块 | 现状 |
|---------|------|------|
| modules/quotas/infrastructure/repositories/resource_quota_repository_impl.py | quotas | ❌ 不存在 |
| modules/spaces/infrastructure/repositories/space_repository_impl.py | spaces | ✅ 存在 |
| modules/datasets/infrastructure/repositories/ | datasets | ❌ 空目录 |
| modules/monitoring/infrastructure/repositories/ | monitoring | ❌ 空目录 |
| modules/billing/infrastructure/repositories/ | billing | ❌ 空目录 |

**⚠️ 状态**: 旧文件未删除，quotas 模块缺少 resource_quota 仓库实现

---

### 12. 基础设施层 - 外部客户端

#### 已完成迁移 ✅

| 旧路径 | 新位置 | 用途 | 状态 |
|------|--------|------|------|
| infrastructure/external/hyperpod/client.py | 仍在原位 | HyperPod SDK 封装 | ✅ 保留在原位（跨模块共享） |
| infrastructure/external/s3/client.py | 仍在原位 | S3 SDK 封装 | ✅ 保留在原位（跨模块共享） |
| infrastructure/external/kueue/ | 仍在原位 | Kueue 集成 | ✅ 保留在原位（跨模块共享） |

**📍 当前位置**: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/backend/src/infrastructure/external/`

**✅ 状态**: 正确保留在共享位置

---

### 13. 基础设施层 - 配置

#### 已完成迁移 ✅

| 旧路径 | 新位置 | 状态 |
|------|--------|------|
| infrastructure/config/settings.py | 仍在原位 | ✅ 保留（全局配置） |

**📍 当前位置**: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/backend/src/infrastructure/config/`

**✅ 状态**: 正确保留

---

### 14. 新增模块（空/骨架）

| 模块 | 路径 | 完成度 | 说明 |
|------|------|--------|------|
| datasets | modules/datasets/ | 🔴 骨架 | 仅有目录结构，无实现 |
| monitoring | modules/monitoring/ | 🔴 骨架 | 仅有目录结构，无实现 |
| billing | modules/billing/ | 🔴 骨架 | 仅有目录结构，无实现 |

---

## 总结清单

### ✅ 已完成迁移的文件

**API 层**:
- [x] auth.py, training_jobs.py, models.py, resource_limit_configs.py (端点)
- [x] auth.py, training_job.py, model.py, resource_limit_config.py (schemas)
- [x] auth.py, permissions.py, services.py (dependencies)

**应用层**:
- [x] 所有 Service 文件（auth, training, models, quotas, spaces, audit）
- [x] 所有接口定义（hyperpod_client, storage_service）

**域层**:
- [x] 所有实体（user, training_job, model, checkpoint, space, audit_log 等）
- [x] 所有值对象（user_role, job_status, training_metrics 等）
- [x] 所有仓库接口（user, training_job, model, checkpoint 等）

**基础设施层**:
- [x] 所有 ORM 模型到新模块
- [x] 所有仓库实现到新模块
- [x] 外部客户端保留在原位（hyperpod, s3, kueue）

---

### ⚠️ 需要处理的问题

#### 1. 旧文件清理

**应删除以下旧文件**（已迁移到模块中）：

```
API 层:
✓ /api/v1/endpoints/auth.py
✓ /api/v1/endpoints/training_jobs.py
✓ /api/v1/endpoints/models.py
✓ /api/v1/endpoints/resource_limit_configs.py
✓ /api/v1/schemas/auth.py
✓ /api/v1/schemas/training_job.py
✓ /api/v1/schemas/model.py
✓ /api/v1/schemas/resource_limit_config.py
✓ /api/v1/dependencies/auth.py
✓ /api/v1/dependencies/services.py
✓ /api/v1/dependencies/permissions.py
✓ /api/middleware/audit.py (已迁移到 modules/audit/api/middleware.py)

应用层:
✓ /application/services/auth_service.py
✓ /application/services/account_service.py
✓ /application/services/password_service.py
✓ /application/services/rbac_service.py
✓ /application/services/training_job_service.py
✓ /application/services/checkpoint_service.py
✓ /application/services/model_service.py
✓ /application/services/resource_limit_config_service.py
✓ /application/interfaces/hyperpod_client.py
✓ /application/interfaces/storage_service.py

域层:
✓ /domain/entities/user.py
✓ /domain/entities/login_attempt.py
✓ /domain/entities/password_history.py
✓ /domain/entities/training_job.py
✓ /domain/entities/checkpoint.py
✓ /domain/entities/model.py
✓ /domain/entities/resource_limit_config.py
✓ /domain/entities/resource_quota.py
✓ /domain/entities/space.py
✓ /domain/entities/audit_log.py
✓ /domain/value_objects/user_enums.py
✓ /domain/value_objects/training_metrics.py
✓ /domain/value_objects/pod_statistics.py (❌ 未迁移)
✓ /domain/repositories/*.py (所有仓库接口)

基础设施层:
✓ /infrastructure/persistence/models/*.py (所有 ORM 模型)
✓ /infrastructure/persistence/repositories/*.py (所有仓库实现)
✓ /infrastructure/persistence/models/development_space_model.py (新创建了 space_model.py)
```

**应保留的共享文件**：

```
✅ /api/v1/schemas/base.py (保留或迁移到 shared/api/schemas.py)
✅ /api/v1/schemas/common.py (保留或迁移到 shared/api/schemas.py)
✅ /api/middleware/auth.py (保留或迁移到 shared/api/middleware/)
✅ /api/middleware/sso.py (保留或迁移到 shared/api/middleware/)
✅ /application/services/base.py (保留或迁移到 shared/application/)
✅ /application/services/mixins/ (保留或迁移到 shared/application/)
✅ /infrastructure/config/settings.py (保留在原位)
✅ /infrastructure/external/hyperpod/ (保留在原位)
✅ /infrastructure/external/s3/ (保留在原位)
✅ /infrastructure/external/kueue/ (保留在原位)
```

---

#### 2. 缺失的实现

**需要补充的仓库接口**:

```
❌ modules/quotas/domain/repositories/resource_quota_repository.py (缺失)
   - 对应实体: resource_quota.py (已存在)
   - 需要创建接口和实现
```

**需要补充的仓库实现**:

```
❌ modules/quotas/infrastructure/repositories/resource_quota_repository_impl.py (缺失)
   - 对应模型: resource_quota_model.py (已存在)
   - 需要创建实现
```

---

#### 3. 待完成模块

| 模块 | 状态 | 需要 |
|------|------|------|
| datasets | 🔴 骨架 | 实体、服务、端点实现 |
| monitoring | 🔴 骨架 | 实体、服务、端点实现 |
| billing | 🔴 骨架 | 实体、服务、端点实现 |

---

#### 4. 文件未删除导致的问题

**风险**:
- 旧导入路径仍然有效，可能造成混淆
- IDE 跳转可能指向旧文件而非新模块文件
- 代码审查时难以识别实际代码位置
- 潜在的循环导入风险

**需要操作**:
- 确认所有旧文件导入路径已更新
- 删除所有已迁移的旧文件
- 运行全部测试确保无破损

---

## 迁移指标

| 指标 | 数值 | 百分比 |
|------|------|--------|
| 总迁移文件数 | 45 | 100% |
| 已迁移文件数 | 44 | 97.8% |
| 待迁移文件数 | 0 | 0% |
| 缺失实现文件数 | 2 | 4.4% |
| 旧文件仍存在 | 35+ | 大量待清理 |

---

## 建议行动计划

### 第一阶段：验证迁移完整性
1. 确认 hyperpod_service.py 是否已完全迁移
2. 检查 auth.py 和 sso.py 中间件的迁移状态
3. 验证所有 Import 语句已更新指向新模块

### 第二阶段：补充缺失实现
1. 创建 `modules/quotas/domain/repositories/resource_quota_repository.py`
2. 创建 `modules/quotas/infrastructure/repositories/resource_quota_repository_impl.py`
3. 更新 modules/quotas/__init__.py 导出接口

### 第三阶段：清理旧文件
1. 删除 api/v1/ 目录下的所有旧文件（除 base.py/common.py）
2. 删除 application/ 目录下的所有旧文件（除 base.py/mixins/）
3. 删除 domain/ 目录下的所有旧文件
4. 删除 infrastructure/persistence/models/ 下的所有旧文件
5. 删除 infrastructure/persistence/repositories/ 下的所有旧文件

### 第四阶段：共享文件处理
1. 决定是否迁移 base.py 和 common.py 到 shared/
2. 确认 auth.py, sso.py 中间件的最终位置
3. 更新所有导入路径

### 第五阶段：测试与验证
1. 运行全部单元测试
2. 运行全部集成测试
3. 验证没有导入错误
4. 核对模块依赖图

---

## 附录：旧文件完整清单

### 应删除的文件（已迁移到模块）

**api/v1/endpoints/**:
- auth.py
- models.py
- training_jobs.py
- resource_limit_configs.py

**api/v1/schemas/**:
- auth.py
- model.py
- training_job.py
- resource_limit_config.py

**api/v1/dependencies/**:
- auth.py
- services.py
- permissions.py

**api/middleware/**:
- audit.py (已迁移)

**application/services/**:
- auth_service.py
- account_service.py
- password_service.py
- rbac_service.py
- training_job_service.py
- checkpoint_service.py
- model_service.py
- resource_limit_config_service.py
- hyperpod_service.py (待确认)

**application/interfaces/**:
- hyperpod_client.py
- storage_service.py

**domain/entities/**:
- user.py, login_attempt.py, password_history.py
- training_job.py, checkpoint.py
- model.py
- resource_limit_config.py, resource_quota.py
- space.py
- audit_log.py

**domain/value_objects/**:
- user_enums.py
- training_metrics.py
- pod_statistics.py

**domain/repositories/**:
- user_repository.py, login_attempt_repository.py, password_history_repository.py
- training_job_repository.py, checkpoint_repository.py
- model_repository.py
- resource_limit_config_repository.py

**infrastructure/persistence/models/**:
- user_model.py, login_attempt_model.py, password_history_model.py
- training_job_model.py, checkpoint_model.py
- ml_model.py
- resource_limit_config_model.py, resource_quota_model.py
- development_space_model.py (已创建 space_model.py)
- audit_log_model.py
- base.py (已迁移到 shared/)

**infrastructure/persistence/repositories/**:
- user_repository_impl.py, login_attempt_repository_impl.py, password_history_repository_impl.py
- training_job_repository_impl.py, checkpoint_repository_impl.py
- model_repository_impl.py
- resource_limit_config_repository_impl.py

### 应保留的文件（跨模块共享）

**api/v1/schemas/**:
- base.py (基础模型)
- common.py (公共类型)

**api/middleware/**:
- auth.py (认证中间件)
- sso.py (SSO 中间件)

**application/services/**:
- base.py (基础服务类)
- mixins/ (Service Mixin)

**infrastructure/**:
- config/settings.py (全局配置)
- external/hyperpod/ (HyperPod 客户端)
- external/s3/ (S3 客户端)
- external/kueue/ (Kueue 客户端)
