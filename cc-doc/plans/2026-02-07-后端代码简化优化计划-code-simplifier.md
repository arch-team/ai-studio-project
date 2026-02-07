# 后端代码简化优化计划（code-simplifier）

## Context

项目后端（Python/FastAPI，DDD + Modular Monolith）已完成一轮架构优化：
- BaseApplicationService Mixin 模式已实现，ResourceQuotaService 从 157→40 行
- `@problem` 装饰器 + `@dataclass` 异常模式已统一
- EntitySchema 自动枚举推断已优化

但仍存在以下可优化项：
- **两个重复的 Repository 基类**（`base_repository.py` 236 行 + `pydantic_repository.py` 259 行），CRUD 实现高度重复
- **billing 模块架构违规**：`report_service.py` 和 `usage_aggregator.py` 直接导入其他模块 ORM 模型，违反 R3 跨模块隔离规则
- **大文件需拆分**：`hyperpod/client.py`（779 行）混合 3 个职责，`training/endpoints.py`（490 行）11 个端点混杂
- **Service 层 Mixin 可推广**：UserService 等仍有少量 CRUD 样板代码

本计划使用 `code-simplifier:code-simplifier` agent 分步执行后端代码优化。

---

## Step 1: Repository 基类合并（高价值，低风险）

**目标**：将 `BaseRepository` 和 `PydanticRepository` 合并为单一基类

**问题**：两个基类的 CRUD 方法（`get_by_id/create/update/delete/soft_delete/exists/list_with_filters` 等）实现完全一致。`PydanticRepository` 是 `BaseRepository` 的严格超集（自动化 Entity↔Model 转换 vs 手动抽象方法）。当前仅 `UploadSessionRepositoryImpl` 使用 `BaseRepository`。

**修改文件**：
- `backend/src/shared/infrastructure/pydantic_repository.py` — 扩展为支持非 PydanticEntity 子类（当 `_entity_class` 未设置时，fallback 到手动 `_to_entity/_to_model`）
- `backend/src/shared/infrastructure/base_repository.py` — 删除或保留为别名
- `backend/src/shared/infrastructure/__init__.py` — 更新导出
- `backend/src/modules/datasets/infrastructure/repositories/upload_session_repository_impl.py` — 改为继承合并后的基类

**复用**：
- `PydanticRepository` 现有实现（`pydantic_repository.py`）
- `BaseRepository` 的抽象方法签名作为 fallback 模式

**验证**：
```bash
pytest backend/tests/architecture/ -v
pytest backend/tests/ -k "repo or upload_session or dataset" -v
mypy backend/src/shared/infrastructure/
```

**预期收益**：减少 ~230 行代码，消除双基类维护负担

---

## Step 2: billing 模块架构违规修复（高价值，中风险）

**目标**：消除 billing 模块直接导入其他模块 ORM 模型的违规

**问题**：
- `billing/application/services/report_service.py:9-10` 直接 `from src.modules.datasets.infrastructure.models...` 和 `from src.modules.training.infrastructure.models...`
- 违反 R3（模块间通信必须通过事件总线或共享接口）和 Clean Architecture（Application 层不应直接使用 ORM）

**修改文件**：
- `backend/src/modules/billing/application/interfaces.py` — 新增 `IResourceUsageQuery` 接口（定义 `get_training_job_stats()`, `get_dataset_stats()` 等方法，返回纯数据 DTO）
- `backend/src/modules/billing/infrastructure/repositories/` — 新增 `resource_usage_query_impl.py`（实现接口，将 ORM 查询从 Service 下沉到 Infrastructure 层）
- `backend/src/modules/billing/application/services/report_service.py` — 移除 ORM 导入，改为依赖 `IResourceUsageQuery` 接口
- `backend/src/modules/billing/application/services/usage_aggregator.py` — 同上
- `backend/src/modules/billing/api/dependencies.py` — 更新依赖注入链

**复用**：
- 现有的跨模块接口模式（参考 `shared/domain/interfaces/quota_checker.py`）
- 现有的依赖注入 5 层链模板

**验证**：
```bash
pytest backend/tests/architecture/ -v  # 关键：架构合规必须通过
pytest backend/tests/ -k "billing or report" -v
```

**预期收益**：消除 2 处 R3 违规，Service 层更纯粹

---

## Step 3: HyperPod Client 大文件拆分（中价值，中风险）

**目标**：将 779 行的 `client.py` 按职责拆分为多个子模块

**问题**：单文件混合集群管理、训练任务管理、检查点/恢复/抢占 3 个职责。`resume_training_job` 和 `trigger_preemption` 重复了 `submit_training_job` 中的容器构建逻辑。

**修改文件**：
- `backend/src/modules/training/infrastructure/hyperpod/client.py` — 重构为 Facade，委托子模块
- `backend/src/modules/training/infrastructure/hyperpod/config_builder.py` — 新建，提取 `_build_container/_build_replica_spec/_build_kueue_labels` 等共享构建逻辑（~80 行）
- `backend/src/modules/training/infrastructure/hyperpod/cluster_client.py` — 新建，集群 CRUD（~150 行）
- `backend/src/modules/training/infrastructure/hyperpod/job_client.py` — 新建，任务提交/状态/停止（~250 行）
- `backend/src/modules/training/infrastructure/hyperpod/checkpoint_client.py` — 新建，检查点验证/恢复/抢占（~200 行）
- `backend/src/modules/training/infrastructure/hyperpod/__init__.py` — 更新导出

**复用**：
- 现有的 `HyperPodClient` 接口保持不变（Facade 模式）
- 现有的 `@lru_cache(maxsize=1)` Singleton 模式

**验证**：
```bash
pytest backend/tests/ -k "hyperpod or training" -v
mypy backend/src/modules/training/infrastructure/hyperpod/
pytest backend/tests/architecture/ -v
```

**预期收益**：从 779 行单文件拆分为 5 个清晰模块（平均 ~150 行），消除 ~60 行重复构建逻辑

---

## Step 4: training/endpoints.py 拆分（中价值，低风险）

**目标**：将 490 行的 endpoints 按资源类型拆分

**问题**：11 个端点涵盖 TrainingJob CRUD、状态操作、Checkpoint、Template、Logs/Debug、Metrics，全部混杂在一个文件中。

**修改文件**：
- `backend/src/modules/training/api/endpoints.py` — 拆分为子路由目录
- `backend/src/modules/training/api/endpoints/` — 新建目录：
  - `training_jobs.py`：CRUD + 状态操作（~200 行）
  - `checkpoints.py`：检查点端点（~60 行）
  - `metrics.py`：指标和日志端点（~100 行）
  - `__init__.py`：聚合子路由并导出 `router`
- `backend/src/router.py` — 如需更新 include 路径

**复用**：
- FastAPI 的 `APIRouter` + `include_router` 原生支持
- 现有的 `dependencies.py` 和 `schemas/` 无需修改

**验证**：
```bash
pytest backend/tests/ -k "training" -v
pytest backend/tests/architecture/ -v
```

**预期收益**：从 490 行单文件拆分为 3-4 个按资源组织的文件

---

## Step 5: Service 层 Mixin 推广（低价值，低风险，可选）

**目标**：将 `BaseApplicationService` Mixin 推广到 `UserService`

**问题**：`UserService`（~110 行）有标准 CRUD 模式（`get_user/create_user/update_user/list_users`），可通过继承 `BaseApplicationService` 减少样板代码。

**修改文件**：
- `backend/src/modules/auth/application/services/user_service.py` — 改为继承 `BaseApplicationService[User, int]`

**验证**：
```bash
pytest backend/tests/ -k "user" -v
pytest backend/tests/architecture/ -v
```

**预期收益**：减少 ~30 行样板代码，提升代码一致性

---

## 执行策略

使用 `code-simplifier:code-simplifier` agent 分步执行，每步聚焦一个可管理的范围：

1. **Step 1 → Step 2** 为 P1 高优先级，应优先执行
2. **Step 3 → Step 4** 为 P2 中优先级，Step 1/2 完成后执行
3. **Step 5** 为可选项，视时间决定

每步完成后运行验证命令确认无回归，再进入下一步。

## 总体预期收益

| 指标 | 值 |
|------|-----|
| 代码净减少 | ~400-500 行 |
| 架构违规修复 | 2 处 R3 违规 → 0 |
| 最大文件行数 | 779 行 → ~250 行 |
| Repository 基类 | 2 个 → 1 个 |
| 文件职责清晰度 | 显著提升 |
