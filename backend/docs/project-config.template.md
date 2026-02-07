# 项目配置模板 (Project Configuration Template)

> **职责**: 项目配置模板，供新项目复制并填充占位符。

<!--
使用说明：
1. 复制此模板到新项目的 .claude/ 目录
2. 替换所有 {{PLACEHOLDER}} 占位符
3. 删除不适用的章节
4. 保持与 CLAUDE.md 的单向引用（CLAUDE.md → project-config.md）
-->

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

<!-- 替换为实际项目信息 -->
| 配置项 | 值 |
|--------|-----|
| **项目名称** | {{PROJECT_NAME}} |
| **项目描述** | {{PROJECT_DESCRIPTION}} |
| **架构模式** | {{ARCHITECTURE_PATTERN}} |
| **源码根路径** | `{{SRC_ROOT}}` |
| **模块路径** | `{{SRC_ROOT}}/modules` |
| **共享路径** | `{{SRC_ROOT}}/shared` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处仅列出**项目特有**的技术选型。

| 类别 | 技术选型 | 用途说明 |
|------|---------|---------|
| **数据库** | {{DATABASE}} | {{DATABASE_PURPOSE}} |
| **外部服务** | {{EXTERNAL_SERVICE}} | {{SERVICE_PURPOSE}} |
<!-- 添加其他项目特有技术，示例:
| **资源调度** | Kueue | K8s 资源调度和优先级管理 |
| **实验追踪** | MLflow | 训练指标和实验记录 |
-->

---

## 业务模块

> **维护提示**: 新增模块时同步更新此表和 `{{SRC_ROOT}}/modules/` 目录。

| 模块 | 职责 | 核心实体 | 外部依赖 |
|------|------|---------|---------|
| `auth` | 用户认证与授权 | `User` | SSO Provider |
| `{{MODULE_1}}` | {{MODULE_1_DESC}} | `{{ENTITY_1}}` | {{EXT_DEP_1}} |
| `{{MODULE_2}}` | {{MODULE_2_DESC}} | `{{ENTITY_2}}` | {{EXT_DEP_2}} |
| `shared` | 共享内核 (必须保留) | `BaseEntity`, `DomainEvent` | - |

<!-- 示例 (参考实际项目):
| `training` | 训练任务生命周期管理 | TrainingJob, Checkpoint | HyperPod, Kueue |
| `models` | 模型版本控制、审批 | Model, ModelVersion | Model Registry |
| `quotas` | 资源配额配置与管理 | ResourceQuota, ResourceLimitConfig | Kueue ClusterQueue |
| `datasets` | 数据集版本管理与存储 | Dataset, DatasetVersion | S3, FSx |
| `billing` | 成本统计与计费分析 | CostRecord, UsageReport | - |
| `monitoring` | 训练监控与告警 | Metric, Alert | CloudWatch |
| `audit` | 审计日志记录与查询 | AuditLog | - |
-->

---

## 核心域事件

> **设计原则**: 事件用于模块间解耦通信，订阅者不应直接依赖发布者的实现。

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| `{{MODULE}}` | `{{Entity}}SubmittedEvent` | 任务/流程提交 | quotas, audit |
| `{{MODULE}}` | `{{Entity}}CompletedEvent` | 流程完成 | audit, monitoring |
| `{{MODULE}}` | `{{Entity}}FailedEvent` | 流程失败 | audit, monitoring |
| `auth` | `UserCreatedEvent` | 用户创建 | quotas (初始化配额) |

<!-- 示例 (参考实际项目):
| training | TrainingJobSubmittedEvent | 任务提交 | quotas, audit |
| training | TrainingJobCompletedEvent | 任务完成 | audit, monitoring |
| training | TrainingJobFailedEvent | 任务失败 | audit, monitoring |
| quotas | QuotaExceededEvent | 配额超限 | monitoring |
| models | ModelPublishedEvent | 模型发布 | audit |
-->

---

## 导入路径配置

> **原则**: 参考 [rules/architecture.md](rules/architecture.md) 模块隔离章节。

### 共享内核导入

```python
# Domain 层共享
from {{SRC_ROOT}}.shared.domain import (
    BaseEntity, PydanticEntity,
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DomainEvent, event_bus, event_handler,
    # 跨模块接口 (按需添加)
)

# Problem 异常体系 (推荐使用 @problem 装饰器定义异常)
from {{SRC_ROOT}}.shared.domain.problem import problem, Problem
# 示例: @problem(404, "ENTITY_NOT_FOUND", "Entity '{id}' not found")

# Infrastructure 层共享
from {{SRC_ROOT}}.shared.infrastructure import get_db, get_settings, PydanticRepository

# API 层共享
from {{SRC_ROOT}}.shared.api import domain_exception_handler
from {{SRC_ROOT}}.shared.api.schemas import EntitySchema, PaginatedResponse
```

### 认证依赖 (唯一跨模块例外)

```python
# 仅允许在 API 层导入
from {{SRC_ROOT}}.modules.auth.api.dependencies import (
    get_current_active_user,
    # 按需添加角色检查函数: require_admin, require_engineer, require_viewer
)
```

---

## 外部服务配置

> **位置约定**: 外部服务适配器放在对应模块的 `infrastructure/` 下，或共享的放在 `shared/infrastructure/` 下。

| 服务 | 用途 | 适配器位置 |
|------|------|-----------|
| {{SERVICE_1}} | {{SERVICE_1_PURPOSE}} | `modules/{{module_1}}/infrastructure/{{service_1}}/` |
| {{SERVICE_2}} | {{SERVICE_2_PURPOSE}} | `shared/infrastructure/{{service_2}}/` |

<!-- 示例 (参考实际项目):
| AWS SageMaker HyperPod | 分布式训练管理 | modules/training/infrastructure/hyperpod/ |
| AWS S3 | 数据集和模型存储 | shared/infrastructure/storage/s3_client.py |
| AWS S3 (分片上传) | 大文件断点续传 | modules/datasets/infrastructure/s3/ |
| Kueue | 资源调度和优先级管理 | modules/training/infrastructure/ |
-->

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵。

### 违规检测 (Claude 自动检查)

| 违规类型 | 模式 | 严重级别 |
|---------|------|---------|
| 跨模块 Service 导入 | `from {{SRC_ROOT}}.modules.X.application.services` | 🔴 阻止 |
| 跨模块 Entity 导入 | `from {{SRC_ROOT}}.modules.X.domain.entities` | 🔴 阻止 |
| Domain 层导入外部框架 | `domain/` 文件中 `from fastapi/sqlalchemy` | 🔴 阻止 |
| 跨模块 Repository 实现导入 | `from {{SRC_ROOT}}.modules.X.infrastructure.repositories` | 🟡 警告 |

### 允许的例外

- **ORM 外键关系**: `*_model.py` 中可导入其他模块的 ORM Model
- **Auth 认证**: API 层可导入 `auth.api.dependencies`

---

## 架构合规测试

> **测试位置**: `tests/architecture/test_architecture_compliance.py`

| 测试类 | 验证规则 |
|--------|---------|
| `TestApplicationLayerDoesNotImportInfrastructure` | Application 不导入 Infrastructure |
| `TestDomainLayerIndependence` | Domain 不依赖 Infrastructure/API |
| `TestApiLayerDoesNotImportInfrastructureModels` | API 不直接使用 ORM |
| `TestDomainExceptionUsage` | Entity 用域异常，非 ValueError |
| `TestModuleDomainLayerIsolation` | R1: Domain 零跨模块导入 |
| `TestModuleApplicationLayerDependencies` | R2/R3: Application 跨模块隔离 |
| `TestModuleApiLayerAuthDependency` | R4: Auth 依赖例外验证 |
| `TestModuleInfrastructureLayerIsolation` | Infrastructure 跨模块隔离 |
| `TestModulePublicApiExports` | `__init__.py` 定义 `__all__` |

```bash
# 运行架构合规测试
pytest tests/architecture -v
```

---

## 待解决问题

<!-- 记录项目中尚未解决的架构或数据模型问题 -->

### {{ISSUE_TITLE_1}}

| 项目 | 说明 |
|------|------|
| **现状** | {{CURRENT_STATE}} |
| **问题** | {{PROBLEM_DESCRIPTION}} |
| **待确认** | {{PENDING_DECISION}} |

<!-- 示例 (参考实际项目):
### 数据模型一致性问题

#### 问题1: resource_quotas 表与 Kueue 配额重复
| 项目 | 说明 |
|------|------|
| **现状** | 应用层存储 max_gpu_count, max_cpu_cores, max_memory_gb |
| **问题** | Kueue ClusterQueue 已管理这些配额值，存在数据不一致风险 |
| **待确认** | 应用层是"配置源"同步到 Kueue，还是只存业务元数据？ |
-->

---

## 外部系统集成

<!-- 记录与外部系统集成的关键信息、踩坑记录和诊断清单 -->

> **踩坑记录和诊断清单参见**: 对应的 `.claude/skills/` 目录

<!-- 示例 (参考实际项目):
已解决的关键问题:
- TAS 配置问题（Workload Pending）
- 抢占不生效（Cohort 配置）
- PriorityClass 双重资源（WorkloadPriorityClass vs PriorityClass）
-->

---

## 模板使用检查清单

在使用此模板创建新项目配置时：

- [ ] 替换所有 `{{PLACEHOLDER}}` 占位符
- [ ] 删除不适用的章节和注释
- [ ] 确保 CLAUDE.md 引用此文件
- [ ] 运行架构合规测试验证配置正确
- [ ] 补充"待解决问题"和"外部系统集成"章节
