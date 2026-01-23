# ARCHITECTURE.md 与 Spec-Kit 文件一致性分析

## 分析目标

对比 `backend/docs/ARCHITECTURE.md` 架构规范与 spec-kit 生成的 `plan.md` 和 `tasks.md` 之间的不一致之处。

---

## Spec-Kit 文件职责定义

根据 `CLAUDE.md` 中的定义：

| 文件 | 职责 |
|------|------|
| `plan.md` | **实施计划 (HOW)** - 技术选型、架构设计、里程碑 |
| `tasks.md` | **任务清单 (DO)** - 可执行的原子任务清单 (0.5-2人日/任务) |

---

## 不一致性分析

### 1. 🔴 **严重不一致：模块化目录结构**

#### ARCHITECTURE.md 定义（第5.1节）
```
modules/{name}/
├── api/
│   ├── endpoints.py
│   ├── dependencies.py
│   └── schemas/
├── application/
│   ├── dto/
│   ├── services/
│   └── interfaces/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── repositories/
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── models/
    └── repositories/
```

#### tasks.md 中的路径定义
许多任务使用**扁平结构**而非模块化结构：

| 任务 | tasks.md 路径 | ARCHITECTURE.md 应为 |
|------|--------------|---------------------|
| T011 | `backend/src/domain/entities/user.py` | `backend/src/modules/auth/domain/entities/user.py` |
| T014 | `backend/src/application/interfaces/hyperpod_client.py` | `backend/src/modules/training/application/interfaces/hyperpod_client.py` |
| T016b | `backend/src/api/middleware/audit.py` | `backend/src/shared/api/middleware/audit.py` |
| T023 | `backend/src/domain/entities/training_job.py` | `backend/src/modules/training/domain/entities/training_job.py` |

**影响**: 违反 Modular Monolith 架构原则，模块边界不清晰。

---

### 2. 🔴 **严重不一致：Application 层结构**

#### ARCHITECTURE.md 定义（第2.1节）
```
application/
├── dto/                # 数据传输对象 (跨层传输)
├── services/           # 业务用例实现
└── interfaces/         # 端口接口 (外部服务抽象)
```

#### plan.md 定义
```
application/
└── services/       # AuthService
```

**缺失**: `plan.md` 未包含 `dto/` 和 `interfaces/` 子目录定义。

**影响**: 开发人员可能遗漏 DTO 和接口层的实现。

---

### 3. 🟡 **中等不一致：共享模块命名**

#### ARCHITECTURE.md 定义
使用 `shared/` 作为共享内核目录：
```python
from src.shared.domain import BaseEntity, DomainEvent
from src.shared.infrastructure import get_db, get_settings
from src.shared.api import domain_exception_handler
```

#### plan.md 定义
在设计原则部分使用了 `core/`：
```
core/: 共享核心 - 跨层工具 (配置、安全、日志)
```

**影响**: 命名不一致可能导致混淆。

**实际状态**: plan.md 项目结构部分使用 `shared/`，与 ARCHITECTURE.md 一致。但设计原则部分提到 `core/`，需要统一。

---

### 4. 🟡 **中等不一致：API 层依赖规则描述**

#### ARCHITECTURE.md 定义（第2.2节）
> **API 层约束**:
> - API 层只能通过 Application Services 执行业务操作（创建、修改、删除）
> - **API 层可以导入 Domain 层的类型定义**（实体类、值对象、枚举）用于类型标注和响应映射
> - API 层禁止直接访问 Infrastructure 实现

#### plan.md 定义
```
api/: API 层 - 包含 REST 端点、Pydantic Schema、FastAPI 依赖注入，**依赖 application 层**
```

**缺失**: plan.md 未明确说明 API 层可以导入 Domain 层类型定义这一重要例外。

---

### 5. 🟡 **中等不一致：Infrastructure 层双重实现职责**

#### ARCHITECTURE.md 定义（第2.2节）
> **Infrastructure 双重实现**: Infrastructure 层同时实现 Domain 层的 Repository 接口和 Application 层的外部服务接口 (interfaces/)

#### plan.md 定义
```
infrastructure/: 基础设施层 - 包含 ORM 模型、仓储实现、外部服务适配器，**实现 domain/application 接口**
```

**影响**: plan.md 描述过于简化，未强调"双重实现"的职责。

---

### 6. 🟢 **轻微不一致：模块核心实体定义**

#### ARCHITECTURE.md 模块划分（第1.4节）

| 模块 | 核心实体 |
|------|---------|
| `training` | TrainingJob, Checkpoint |
| `models` | Model |
| `quotas` | ResourceQuota, ResourceLimitConfig |

#### tasks.md 任务分配

- T022a（models 表迁移）被放在 **Phase 3: US1 训练任务管理** 下
- 但 `models` 是独立模块，应有独立的 Phase 或明确标注跨模块依赖

**影响**: 模块边界划分与任务组织不完全对应。

---

### 7. 🟢 **轻微不一致：文件命名规范覆盖**

#### ARCHITECTURE.md 定义（第5.2节）

| 类型 | 命名规范 |
|------|---------|
| 实体 | `{entity}.py` |
| 仓库接口 | `{entity}_repository.py` |
| 仓库实现 | `{entity}_repository_impl.py` |
| ORM 模型 | `{entity}_model.py` |
| 服务 | `{entity}_service.py` |

#### plan.md/tasks.md 状态

- tasks.md 遵循此命名规范
- plan.md 未显式定义后端文件命名规范（仅定义了前端命名规范）

---

## 一致性汇总表

| 维度 | ARCHITECTURE.md | plan.md | tasks.md | 状态 |
|------|----------------|---------|----------|------|
| 模块化目录结构 | ✅ 完整定义 | ✅ 定义 | ❌ 使用扁平路径 | 🔴 严重不一致 |
| Application 层结构 | ✅ dto/services/interfaces | ⚠️ 仅 services | N/A | 🔴 严重不一致 |
| 共享模块命名 | shared/ | 混用 core/shared | shared/ | 🟡 中等不一致 |
| API 层依赖规则 | ✅ 详细定义 | ⚠️ 简化描述 | N/A | 🟡 中等不一致 |
| Infrastructure 双重实现 | ✅ 明确说明 | ⚠️ 简化描述 | N/A | 🟡 中等不一致 |
| 模块核心实体 | ✅ 完整定义 | N/A | ⚠️ Phase 组织不对应 | 🟢 轻微不一致 |
| 文件命名规范 | ✅ 后端完整 | ⚠️ 仅前端 | ✅ 遵循 | 🟢 轻微不一致 |

---

## 修复建议

### 优先级 1（必须修复）

1. **tasks.md 路径规范化**
   - 将所有任务路径从扁平结构改为模块化结构
   - 例：`backend/src/domain/entities/user.py` → `backend/src/modules/auth/domain/entities/user.py`

2. **plan.md 补充 Application 层完整结构**
   - 在项目结构中明确包含 `dto/` 和 `interfaces/` 子目录

### 优先级 2（建议修复）

3. **plan.md 统一共享模块命名**
   - 将设计原则部分的 `core/` 改为 `shared/`

4. **plan.md 补充 API 层依赖规则**
   - 明确说明 API 层可导入 Domain 层类型定义

5. **plan.md 补充 Infrastructure 双重实现职责**
   - 强调 Infrastructure 同时实现 Domain 和 Application 层接口

### 优先级 3（可选修复）

6. **tasks.md 模块边界标注**
   - 对跨模块任务（如 T022a）添加模块归属说明

---

## 结论

ARCHITECTURE.md 作为"单一真实源"定义了完整的架构规范，但 **plan.md** 和 **tasks.md** 存在以下主要问题：

1. **tasks.md 的路径定义违反模块化架构**（最严重）
2. **plan.md 对 Application 层结构描述不完整**
3. **命名和描述的细节不一致**

---

## 实施计划

### Phase 1: 修复 plan.md（优先）

#### 1.1 补充 Application 层完整结构

**目标文件**: `specs/001-ai-training-platform/plan.md`

**修改位置**: Project Structure 部分的后端模块结构示例

**修改内容**:
```
├── application/
│   ├── dto/                # 数据传输对象 (跨层传输)
│   ├── services/           # 业务用例实现
│   └── interfaces/         # 端口接口 (外部服务抽象)
```

#### 1.2 统一共享模块命名

**修改位置**: Project Structure 设计原则部分

**修改内容**: 将 `core/` 改为 `shared/`

#### 1.3 补充 API 层依赖规则

**修改位置**: 后端目录结构设计原则部分

**添加内容**:
- API 层可以导入 Domain 层的类型定义（实体类、值对象、枚举）用于类型标注
- API 层禁止直接访问 Infrastructure 实现

#### 1.4 补充 Infrastructure 双重实现职责

**修改位置**: 后端目录结构设计原则部分

**添加内容**: Infrastructure 层同时实现 Domain 层的 Repository 接口和 Application 层的外部服务接口

---

### Phase 2: 修复 tasks.md 路径

#### 2.1 路径替换规则

| 原路径前缀 | 新路径前缀 | 适用模块 |
|-----------|----------|---------|
| `backend/src/domain/entities/user.py` | `backend/src/modules/auth/domain/entities/user.py` | auth |
| `backend/src/domain/entities/space.py` | `backend/src/modules/spaces/domain/entities/space.py` | spaces |
| `backend/src/domain/entities/training_job.py` | `backend/src/modules/training/domain/entities/training_job.py` | training |
| `backend/src/domain/entities/checkpoint.py` | `backend/src/modules/training/domain/entities/checkpoint.py` | training |
| `backend/src/domain/entities/model.py` | `backend/src/modules/models/domain/entities/model.py` | models |
| `backend/src/domain/entities/dataset.py` | `backend/src/modules/datasets/domain/entities/dataset.py` | datasets |
| `backend/src/domain/entities/resource_quota.py` | `backend/src/modules/quotas/domain/entities/resource_quota.py` | quotas |
| `backend/src/domain/entities/audit_log.py` | `backend/src/modules/audit/domain/entities/audit_log.py` | audit |
| `backend/src/application/interfaces/*_client.py` | `backend/src/modules/{module}/application/interfaces/*_client.py` | 对应模块 |
| `backend/src/api/middleware/` | `backend/src/shared/api/middleware/` | shared |
| `backend/src/api/v1/endpoints/` | `backend/src/modules/{module}/api/endpoints.py` | 对应模块 |

#### 2.2 需要修改的任务列表

**Phase 2 任务**:
- T011: User 模型路径
- T011c: Space 模型路径
- T012: ResourceQuota 模型路径
- T012a: AuditLog 模型路径
- T012b: ResourceLimitConfig 模型路径
- T013: 认证中间件路径
- T014: HyperPod SDK 客户端路径
- T015: S3 客户端路径
- T016: FastAPI 应用入口路径
- T016b: 审计日志中间件路径

**Phase 3 任务**:
- T023: TrainingJob 模型路径
- T024: Checkpoint 模型路径
- T024a: Model 模型路径
- T025-T031: 训练任务 API 端点路径
- T036-T038: HyperPod 集成服务路径

**Phase 4-7 任务**: 类似修复

---

### 验证步骤

修复完成后验证：

1. **路径格式检查**: 确认所有 `backend/src/` 路径都包含 `modules/{name}/` 或 `shared/`
2. **模块归属检查**: 确认每个文件路径对应正确的业务模块
3. **依赖规则检查**: 确认 plan.md 中的依赖规则描述与 ARCHITECTURE.md 一致

---

### 预计工作量

- **Phase 1 (plan.md)**: 约 15 分钟
- **Phase 2 (tasks.md)**: 约 30-45 分钟（大量路径替换）
- **验证**: 约 10 分钟

**总计**: 约 1 小时
