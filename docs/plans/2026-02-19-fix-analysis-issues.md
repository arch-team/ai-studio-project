# Fix All Analysis Issues Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复代码分析发现的所有安全、架构、代码质量问题，覆盖后端(Python/FastAPI)和前端(React/TypeScript)。

**Architecture:** 按优先级分组：P0 安全修复 → P1 后端架构修复 → P2 代码质量 → P3 前端修复。每个 Task 独立可验证。

**Tech Stack:** Python 3.11 + FastAPI + Pydantic v2 | React + TypeScript + Cloudscape

---

## Task 1: [CRITICAL] 移除 .env.aws-integration 出 Git 追踪

**Files:**
- Modify: `backend/.gitignore` (或根目录 `.gitignore`)
- Delete from tracking: `backend/.env.aws-integration`

**Step 1: 从 Git 追踪中移除文件（保留本地文件）**

```bash
cd /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project
git rm --cached backend/.env.aws-integration
```

**Step 2: 验证文件已从 staging 中移除**

```bash
git status
```

Expected: `backend/.env.aws-integration` 出现在 "Untracked files" 或被 .gitignore 忽略。

**Step 3: 检查根目录 .gitignore 是否有覆盖规则**

```bash
cat .gitignore | grep -i env
```

**Step 4: 在根 .gitignore 中添加规则（如没有覆盖）**

在 `.gitignore` 中添加：
```
backend/.env.aws-integration
```

**Step 5: Commit**

```bash
git add .gitignore
git commit -m "security: 从 Git 追踪中移除 .env.aws-integration 环境配置文件"
```

---

## Task 2: [CRITICAL] 敏感配置字段改用 SecretStr + 生产环境校验

**Files:**
- Modify: `backend/src/shared/infrastructure/config.py`

**Step 1: 读取当前 config.py**

检查文件内容（已读）。需要修改字段：
- `secret_key: str` → `secret_key: SecretStr`
- `database_url: str` → `database_url: SecretStr`
- `aws_secret_access_key: str | None` → `aws_secret_access_key: SecretStr | None`

**Step 2: 修改 config.py**

```python
"""Application Settings - Pydantic settings configuration."""

from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Training Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: SecretStr = SecretStr("mysql+aiomysql://ai_training:ai_training_pass@localhost:3306/ai_training")
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: SecretStr | None = None

    # S3
    s3_bucket_name: str = "ai-training-platform"
    s3_prefix: str = "data"

    # HyperPod
    hyperpod_cluster_name: str | None = None

    # FSx for Lustre
    fsx_filesystem_id: str = "fs-placeholder"
    fsx_mount_path: str = "/fsx"

    # MLflow (T037a)
    mlflow_tracking_uri: str = "http://mlflow.kubeflow.svc.cluster.local:5000"
    mlflow_experiment_prefix: str = "ai-training-platform"
    mlflow_request_timeout: int = 30
    mlflow_max_retries: int = 3

    # Security
    secret_key: SecretStr = SecretStr("change-me-in-production")
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """生产环境强制校验敏感配置不使用默认值."""
        if self.environment == "production":
            if self.secret_key.get_secret_value() == "change-me-in-production":
                raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Step 3: 修复 JWTManager 对 secret_key 的使用**

因为 `secret_key` 现在是 `SecretStr`，`jwt.py` 中所有使用 `self.settings.secret_key` 的地方需要改为 `self.settings.secret_key.get_secret_value()`。

修改 `backend/src/shared/infrastructure/security/jwt.py`：
- 第 88 行：`self.settings.secret_key` → `self.settings.secret_key.get_secret_value()`
- 第 147 行：同上
- 第 167 行：同上

**Step 4: 修复 database.py 对 database_url 的使用**

搜索所有使用 `settings.database_url` 的地方：

```bash
grep -rn "settings.database_url\|get_settings().database_url" backend/src/
```

所有引用改为 `.get_secret_value()` 调用。

**Step 5: 运行类型检查**

```bash
cd backend && mypy src/shared/infrastructure/config.py src/shared/infrastructure/security/jwt.py
```

Expected: 无错误。

**Step 6: 运行相关测试**

```bash
cd backend && pytest tests/unit/shared/ tests/integration/auth/ -v
```

Expected: PASS。

**Step 7: Commit**

```bash
git add backend/src/shared/infrastructure/config.py backend/src/shared/infrastructure/security/jwt.py
git commit -m "security(backend): 敏感配置字段改用 SecretStr，添加生产环境校验"
```

---

## Task 3: [HIGH] 禁用生产环境 API 文档端点

**Files:**
- Modify: `backend/src/main.py`

**Step 1: 读取 main.py 的 FastAPI 初始化部分**

查找创建 FastAPI 实例的代码（约第 66-72 行）。

**Step 2: 根据环境条件禁用文档**

将：
```python
return FastAPI(
    title=settings.app_name,
    ...
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

改为：
```python
# 非开发环境禁用 API 文档，防止 API 结构信息泄露
is_dev = settings.environment == "development"

return FastAPI(
    title=settings.app_name,
    ...
    docs_url="/docs" if is_dev else None,
    redoc_url="/redoc" if is_dev else None,
    openapi_url="/openapi.json" if is_dev else None,
)
```

**Step 3: 同时修复健康检查信息泄露**

将 `/health` 端点改为按环境返回不同内容：
```python
@app.get("/health", tags=["Health"])
async def _health_check() -> dict:
    base = {"status": "healthy"}
    if settings.environment == "development":
        base.update({"version": settings.app_version, "environment": settings.environment})
    return base
```

**Step 4: 运行测试**

```bash
cd backend && pytest tests/integration/ -k "health" -v
```

**Step 5: Commit**

```bash
git add backend/src/main.py
git commit -m "security(backend): 生产环境禁用 API 文档端点，健康检查不暴露版本信息"
```

---

## Task 4: [HIGH] 修复 JWT get_user_id_from_token 安全问题 + 异常消息泄露

**Files:**
- Modify: `backend/src/shared/infrastructure/security/jwt.py`

**Step 1: 移除 get_user_id_from_token 方法**

该方法 "without full validation" 是安全隐患（跳过过期校验）。搜索所有调用点：

```bash
grep -rn "get_user_id_from_token" backend/src/
```

如果有调用方，改用 `verify_token()` 替代。确认无调用后删除该方法。

**Step 2: 修复 verify_token 中的异常消息泄露**

将：
```python
except JoseError as e:
    raise InvalidTokenError(f"Invalid token: {str(e)}")
except KeyError as e:
    raise InvalidTokenError(f"Missing required claim: {str(e)}")
```

改为：
```python
except JoseError:
    raise InvalidTokenError("Invalid token")
except KeyError:
    raise InvalidTokenError("Invalid token")
```

原始错误通过日志记录（在中间件层）。

**Step 3: 运行测试**

```bash
cd backend && pytest tests/unit/shared/ tests/integration/auth/ -v
```

**Step 4: Commit**

```bash
git add backend/src/shared/infrastructure/security/jwt.py
git commit -m "security(backend): 移除跳过验证的 JWT 方法，修复异常消息泄露"
```

---

## Task 5: [MEDIUM] 密码字段添加 max_length 防止 DoS

**Files:**
- Modify: `backend/src/modules/auth/api/schemas/requests.py`

**Step 1: 搜索所有密码相关的 Field 定义**

```bash
grep -n "password" backend/src/modules/auth/api/schemas/requests.py
```

**Step 2: 为所有密码字段添加 max_length=128**

将所有 `password` 相关字段（`password`、`new_password`、`current_password`）添加：
```python
password: str | None = Field(None, max_length=128, description="Password for local login")
new_password: str = Field(..., min_length=12, max_length=128)
current_password: str = Field(..., min_length=1, max_length=128)
```

**Step 3: 运行测试**

```bash
cd backend && pytest tests/unit/auth/ tests/integration/auth/ -v
```

**Step 4: Commit**

```bash
git add backend/src/modules/auth/api/schemas/requests.py
git commit -m "security(backend): 密码字段添加 max_length=128 防止 bcrypt DoS 攻击"
```

---

## Task 6: [P1] 统一异常体系 — 外部服务异常改用 @problem

**Files:**
- Modify: `backend/src/modules/training/application/services/hyperpod_service.py`
- Modify: `backend/src/modules/training/application/services/mlflow_service.py`
- Modify: `backend/src/modules/monitoring/infrastructure/external/prometheus_client.py`

**Problem:**
`HyperPodServiceError`、`MLflowServiceError`、`PrometheusQueryError` 直接继承 `Exception`，不进入 `problem_exception_handler`，到 API 层返回 500 而非结构化错误。

**Step 1: 修改 hyperpod_service.py**

将：
```python
class HyperPodServiceError(Exception):
    def __init__(self, message: str, retries: int = 0, original_error: Exception | None = None):
        super().__init__(message)
        self.retries = retries
        self.original_error = original_error
```

改为（保留 retries 信息，使用 @problem 装饰器，加 import）：
```python
from dataclasses import dataclass
from src.shared.domain.problem import problem, Problem

@problem(503, "HYPERPOD_SERVICE_ERROR", "HyperPod 服务操作失败: {message}")
@dataclass
class HyperPodServiceError(Problem):
    message: str
    retries: int = 0
```

注意：调用方需要从 `HyperPodServiceError(message)` 改为 `HyperPodServiceError(message=message, retries=retries)`。

**Step 2: 搜索 HyperPodServiceError 实例化位置**

```bash
grep -rn "HyperPodServiceError(" backend/src/
```

将所有 `HyperPodServiceError(msg, retries=n)` 改为 `HyperPodServiceError(message=msg, retries=n)`。

**Step 3: 修改 mlflow_service.py**

```python
from dataclasses import dataclass
from src.shared.domain.problem import problem, Problem

@problem(503, "MLFLOW_SERVICE_ERROR", "MLflow 服务操作失败: {message}")
@dataclass
class MLflowServiceError(Problem):
    message: str
```

搜索调用：
```bash
grep -rn "MLflowServiceError(" backend/src/
```

**Step 4: 修改 prometheus_client.py**

```python
from dataclasses import dataclass
from src.shared.domain.problem import problem, Problem

@problem(503, "PROMETHEUS_QUERY_ERROR", "Prometheus 查询失败: {query}")
@dataclass
class PrometheusQueryError(Problem):
    query: str
```

搜索调用：
```bash
grep -rn "PrometheusQueryError(" backend/src/
```

**Step 5: 运行架构合规测试**

```bash
cd backend && pytest tests/architecture/ -v
```

**Step 6: 运行相关单元测试**

```bash
cd backend && pytest tests/unit/training/ tests/unit/monitoring/ -v
```

**Step 7: Commit**

```bash
git add backend/src/modules/training/application/services/hyperpod_service.py \
        backend/src/modules/training/application/services/mlflow_service.py \
        backend/src/modules/monitoring/infrastructure/external/prometheus_client.py
git commit -m "refactor(backend): 外部服务异常统一继承 Problem，加入 @problem 装饰器体系"
```

---

## Task 7: [P1] 修复 datetime 时区不一致

**Files:**
- Modify: `backend/src/modules/monitoring/application/services/prometheus_service.py`
- Modify: `backend/src/modules/billing/application/services/pricing_model.py`
- Modify: `backend/src/modules/training/infrastructure/repositories/checkpoint_repository_impl.py`

**Step 1: 找到 prometheus_service.py 中的无时区 datetime**

```bash
grep -n "fromtimestamp\|datetime.now()\|utcnow" backend/src/modules/monitoring/application/services/prometheus_service.py
```

将 `datetime.fromtimestamp(float(value[0]))` 改为：
```python
from datetime import UTC
datetime.fromtimestamp(float(value[0]), tz=UTC)
```

**Step 2: 找到 pricing_model.py 中的无时区 datetime**

```bash
grep -n "datetime.now()" backend/src/modules/billing/application/services/pricing_model.py
```

将 `datetime.now()` 改为：
```python
from src.shared.utils import utc_now
utc_now()
```

**Step 3: 找到 checkpoint_repository_impl.py 中的 utcnow()**

```bash
grep -n "utcnow" backend/src/modules/training/infrastructure/repositories/checkpoint_repository_impl.py
```

将 `datetime.utcnow()` 改为 `utc_now()`（确认 import `from src.shared.utils import utc_now`）。

**Step 4: 运行测试**

```bash
cd backend && pytest tests/unit/training/ tests/unit/monitoring/ tests/unit/billing/ -v
```

**Step 5: Commit**

```bash
git add backend/src/modules/monitoring/application/services/prometheus_service.py \
        backend/src/modules/billing/application/services/pricing_model.py \
        backend/src/modules/training/infrastructure/repositories/checkpoint_repository_impl.py
git commit -m "fix(backend): 统一 datetime 时区，全部使用 UTC-aware datetime"
```

---

## Task 8: [P1] 修复监控 API 端点的静默吞错 + 封装违规

**Files:**
- Modify: `backend/src/modules/monitoring/api/endpoints.py`
- Modify: `backend/src/modules/monitoring/application/services/cluster_health_service.py`

**Problem:**
1. 5 个端点用 `except Exception:` 吞掉所有错误，无日志记录
2. `get_cluster_health` 端点直接访问 `health_service._cluster_repository` 私有属性

**Step 1: 修复 ClusterHealthService，添加 get_cluster_by_name 公开方法**

在 `cluster_health_service.py` 的 `ClusterHealthService` 类中添加：
```python
async def get_cluster_by_name(self, cluster_name: str):
    """通过名称获取集群实体."""
    return await self._cluster_repository.get_by_name(cluster_name)
```

**Step 2: 修复 assert 为真正的条件检查**

将：
```python
assert cluster.id is not None, "Cluster must have ID"
```
改为：
```python
if cluster.id is None:
    raise EntityNotFoundError(entity_type="HyperPodCluster", entity_id="unknown")
```

**Step 3: 修复 HealthCheckResult 的无类型 list**

```python
from .prometheus_service import StorageAlert, NetworkAlert

@dataclass
class HealthCheckResult:
    cluster_id: int
    cluster_name: str
    status: HealthStatus
    storage_alerts: list[StorageAlert]
    network_alerts: list[NetworkAlert]
    checked_at: datetime
```

**Step 4: 修复 endpoints.py — 移除裸 except，添加日志，使用公开方法**

每个端点的 `except Exception:` 改为：
```python
import structlog
logger = structlog.get_logger(__name__)

# 在每个 except 块中：
except Exception as e:
    logger.warning("prometheus_unavailable", error=str(e), endpoint="cluster_metrics")
    return ClusterMetricsResponse(cluster_name=cluster_name, metrics=[])
```

对于 `get_cluster_health` 端点，将：
```python
cluster_repo: IHyperPodClusterRepository = health_service._cluster_repository
cluster = await cluster_repo.get_by_name(cluster_name)
```
改为：
```python
cluster = await health_service.get_cluster_by_name(cluster_name)
```

**Step 5: 修复 IPrometheusClient 接口位置（架构违规）**

当前 `IPrometheusClient` 定义在 `infrastructure/external/prometheus_client.py`，而 `PrometheusService`（Application 层）直接导入它。

创建 `backend/src/modules/monitoring/application/interfaces/prometheus_client.py`：
```python
"""Prometheus 客户端接口 - Application 层定义，Infrastructure 层实现."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class IPrometheusClient(ABC):
    @abstractmethod
    async def query_instant(self, query: str, time: datetime | None = None) -> Any: ...

    @abstractmethod
    async def query_range(self, query: str, start: datetime, end: datetime, step: str = "60s") -> Any: ...
```

在 `prometheus_service.py` 中改为从 application/interfaces 导入：
```python
from ..interfaces.prometheus_client import IPrometheusClient
```

在 `infrastructure/external/prometheus_client.py` 中继承 application 层的接口：
```python
from ...application.interfaces.prometheus_client import IPrometheusClient

class PrometheusClient(IPrometheusClient):
    ...
```

**Step 6: 运行架构测试**

```bash
cd backend && pytest tests/architecture/ -v
```

**Step 7: 运行单元测试**

```bash
cd backend && pytest tests/unit/monitoring/ -v
```

**Step 8: Commit**

```bash
git add backend/src/modules/monitoring/
git commit -m "fix(backend): 修复监控模块架构违规和静默吞错问题"
```

---

## Task 9: [P2] 修复 MLflowService 弃用 asyncio API

**Files:**
- Modify: `backend/src/modules/training/application/services/mlflow_service.py`

**Step 1: 修改 _run_sync 方法**

将：
```python
return await asyncio.get_event_loop().run_in_executor(None, func)
```
改为：
```python
return await asyncio.get_running_loop().run_in_executor(None, func)
```

**Step 2: 运行测试**

```bash
cd backend && pytest tests/unit/training/ -k "mlflow" -v
```

**Step 3: Commit**

```bash
git add backend/src/modules/training/application/services/mlflow_service.py
git commit -m "fix(backend): 替换已弃用的 asyncio.get_event_loop() 为 get_running_loop()"
```

---

## Task 10: [P2] 修复 TrainingSyncService 多次查询优化

**Files:**
- Modify: `backend/src/modules/training/application/services/training_sync_service.py`
- Modify: `backend/src/modules/training/domain/repositories/training_job_repository.py`
- Modify: `backend/src/modules/training/infrastructure/repositories/training_job_repository_impl.py`

**Problem:** `_get_active_jobs` 对 4 个状态分别查询（4 次 SQL），应用 `WHERE status IN (...)` 合并为 1 次。

**Step 1: 在仓库接口添加 list_by_statuses 方法**

在 `ITrainingJobRepository` 中添加：
```python
@abstractmethod
async def list_by_statuses(self, statuses: list[JobStatus], page_size: int = 1000) -> list[TrainingJob]:
    """通过多个状态批量查询，等效于 WHERE status IN (...)."""
    ...
```

**Step 2: 实现 list_by_statuses**

在 `TrainingJobRepositoryImpl` 中实现：
```python
async def list_by_statuses(self, statuses: list[JobStatus], page_size: int = 1000) -> list[TrainingJob]:
    status_values = [s.value for s in statuses]
    stmt = (
        select(TrainingJobModel)
        .where(TrainingJobModel.status.in_(status_values))
        .limit(page_size)
    )
    result = await self._session.execute(stmt)
    return [self._to_entity(m) for m in result.scalars()]
```

**Step 3: 修改 training_sync_service.py**

将：
```python
async def _get_active_jobs(self) -> list[TrainingJob]:
    active_statuses = [JobStatus.SUBMITTED, JobStatus.RUNNING, JobStatus.PAUSED, JobStatus.PREEMPTED]
    all_jobs: list[TrainingJob] = []
    for status in active_statuses:
        jobs, _ = await self._repo.list_jobs(status=status, page_size=1000)
        all_jobs.extend(jobs)
    return all_jobs
```

改为：
```python
async def _get_active_jobs(self) -> list[TrainingJob]:
    active_statuses = [JobStatus.SUBMITTED, JobStatus.RUNNING, JobStatus.PAUSED, JobStatus.PREEMPTED]
    return await self._repo.list_by_statuses(active_statuses)
```

**Step 4: 为新方法写测试**

在 `tests/unit/training/` 中添加对 `_get_active_jobs` 使用单次查询的验证。

**Step 5: 运行测试**

```bash
cd backend && pytest tests/unit/training/ tests/integration/training/ -v
```

**Step 6: Commit**

```bash
git add backend/src/modules/training/
git commit -m "perf(backend): 优化 TrainingSyncService，4 次状态查询合并为 1 次 IN 查询"
```

---

## Task 11: [P2] 前端 — shared/utils 纳入 Git 追踪

**Files:**
- Stage: `frontend/src/shared/utils/` (untracked 目录)

**Step 1: 查看 utils 目录内容**

```bash
ls frontend/src/shared/utils/
```

Expected: `formatters.ts`, `dateRange.ts`, `index.ts`

**Step 2: 验证编译正常**

```bash
cd frontend && npm run build 2>&1 | head -30
```

**Step 3: Git add**

```bash
git add frontend/src/shared/utils/
git status
```

Expected: `utils/` 目录所有文件变为 "Changes to be committed"。

**Step 4: Commit**

```bash
git commit -m "feat(frontend): 新增 shared/utils 工具函数模块（formatters, dateRange）"
```

---

## Task 12: [P2] 前端 — 提取 DateRangePicker i18nStrings 为共享常量

**Files:**
- Modify: `frontend/src/shared/utils/index.ts`
- Create: `frontend/src/shared/utils/dateRangePickerConfig.ts`
- Modify: `frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx`
- Modify: `frontend/src/features/reports/pages/CostAnalysisPage.tsx`
- Modify: `frontend/src/features/reports/pages/ResourceUsageReportPage.tsx`
- Modify: `frontend/src/features/audit/pages/AuditLogsPage.tsx`

**Step 1: 读取任意一个文件中的 i18nStrings 定义**

```bash
grep -n "i18nStrings" frontend/src/features/audit/pages/AuditLogsPage.tsx | head -5
```

**Step 2: 创建共享常量文件**

`frontend/src/shared/utils/dateRangePickerConfig.ts`：
```typescript
import type { DateRangePickerProps } from "@cloudscape-design/components";

/**
 * DateRangePicker 的国际化字符串配置（中文）
 * 供各页面复用，避免重复定义
 */
export const DATE_RANGE_PICKER_I18N: DateRangePickerProps.I18nStrings = {
  todayAriaLabel: "今天",
  nextMonthAriaLabel: "下个月",
  previousMonthAriaLabel: "上个月",
  customRelativeRangeDurationLabel: "时长",
  customRelativeRangeDurationPlaceholder: "输入时长",
  customRelativeRangeOptionLabel: "自定义范围",
  customRelativeRangeOptionDescription: "设置自定义范围",
  customRelativeRangeUnitLabel: "时间单位",
  formatRelativeRange: (e) => {
    const isSingular = e.amount === 1;
    const unit =
      e.unit === "hour"
        ? isSingular ? "小时" : "小时"
        : e.unit === "day"
          ? isSingular ? "天" : "天"
          : isSingular ? "周" : "周";
    return `最近 ${e.amount} ${unit}`;
  },
  formatUnit: (unit, isSingular) =>
    unit === "hour" ? "小时" : unit === "day" ? "天" : "周",
  relativeModeTitle: "相对时间",
  absoluteModeTitle: "绝对时间",
  relativeRangeSelectionHeading: "选择时间范围",
  startDateLabel: "开始日期",
  endDateLabel: "结束日期",
  startTimeLabel: "开始时间",
  endTimeLabel: "结束时间",
  clearButtonLabel: "清除并关闭",
  cancelButtonLabel: "取消",
  applyButtonLabel: "应用",
};

/**
 * DateRangePicker 验证函数 - 确保开始时间不晚于结束时间
 */
export const validateDateRange = (
  value: DateRangePickerProps.Value | null
): DateRangePickerProps.ValidationResult => {
  if (value?.type === "absolute") {
    if (new Date(value.startDate) > new Date(value.endDate)) {
      return { valid: false, errorMessage: "开始日期不能晚于结束日期" };
    }
  }
  return { valid: true };
};
```

**Step 3: 在 shared/utils/index.ts 中导出**

在 `index.ts` 末尾添加：
```typescript
export * from "./dateRangePickerConfig";
```

**Step 4: 在 4 个文件中替换本地 i18nStrings**

在每个文件中：
1. 删除本地 `const i18nStrings = { ... }` 定义（约 25 行）
2. 导入：`import { DATE_RANGE_PICKER_I18N, validateDateRange } from "@shared/utils";`
3. 将 `DateRangePicker` 的 `i18nStrings={localI18n}` 改为 `i18nStrings={DATE_RANGE_PICKER_I18N}`
4. 将 `isValidRange={...}` 改为 `isValidRange={validateDateRange}`

**Step 5: 编译验证**

```bash
cd frontend && npm run build
```

Expected: 无错误。

**Step 6: 运行测试**

```bash
cd frontend && npm test -- --run
```

**Step 7: Commit**

```bash
git add frontend/src/shared/utils/ \
        frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx \
        frontend/src/features/reports/pages/CostAnalysisPage.tsx \
        frontend/src/features/reports/pages/ResourceUsageReportPage.tsx \
        frontend/src/features/audit/pages/AuditLogsPage.tsx
git commit -m "refactor(frontend): 提取 DateRangePicker i18nStrings 为 shared/utils 共享常量"
```

---

## Task 13: [P2] 前端 — 修复 AuditLogsPage 相对时间范围过滤无效

**Files:**
- Modify: `frontend/src/features/audit/pages/AuditLogsPage.tsx`

**Problem:** `dateRange?.type === "relative"` 分支未处理，用户选"最近 7 天"时 API 不会加时间过滤。

**Step 1: 读取 shared/utils/dateRange.ts 了解现有工具**

```bash
cat frontend/src/shared/utils/dateRange.ts
```

**Step 2: 修改 filters 构建 useMemo**

在 `AuditLogsPage.tsx` 中，将：
```typescript
if (dateRange?.type === "absolute") {
  params.start_date = dateRange.startDate;
  params.end_date = dateRange.endDate;
}
```

改为：
```typescript
if (dateRange?.type === "absolute") {
  params.start_date = dateRange.startDate;
  params.end_date = dateRange.endDate;
} else if (dateRange?.type === "relative") {
  // 将相对时间范围转换为绝对时间戳
  const now = new Date();
  const end = now.toISOString();
  const amount = dateRange.amount;
  const unit = dateRange.unit; // "hour" | "day" | "week" | "month" | "year"
  const msMap: Record<string, number> = {
    second: 1000,
    minute: 60 * 1000,
    hour: 60 * 60 * 1000,
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000,
    year: 365 * 24 * 60 * 60 * 1000,
  };
  const start = new Date(now.getTime() - amount * (msMap[unit] ?? msMap.day)).toISOString();
  params.start_date = start;
  params.end_date = end;
}
```

**Step 3: 运行测试**

```bash
cd frontend && npm test -- tests/unit/features/audit/ --run
```

**Step 4: Commit**

```bash
git add frontend/src/features/audit/pages/AuditLogsPage.tsx
git commit -m "fix(frontend): 修复 AuditLogsPage 相对时间范围过滤无效问题"
```

---

## Task 14: [P2] 前端 — 统一 API 导入路径

**Files:**
- Modify: 10 个 API 文件（见下）

**Problem:** 10 个文件用 `@shared/api/client`，只有 resource-quotas 正确用 `@shared/api`。

**Step 1: 确认 shared/api/index.ts 已导出 apiClient**

```bash
cat frontend/src/shared/api/index.ts | grep apiClient
```

**Step 2: 批量替换**

```bash
cd frontend
# 替换所有 @shared/api/client 为 @shared/api
find src/features -name "*.ts" -o -name "*.tsx" | xargs grep -l "@shared/api/client" | while read f; do
  sed -i '' 's|from "@shared/api/client"|from "@shared/api"|g' "$f"
  echo "Fixed: $f"
done
```

**Step 3: 验证编译**

```bash
npm run build
```

**Step 4: Commit**

```bash
git add src/features/
git commit -m "refactor(frontend): 统一 API 客户端导入路径为 @shared/api"
```

---

## Task 15: [P2] 前端 — 修复 resource-quotas hooks 结构冲突

**Files:**
- Modify: `frontend/src/features/resource-quotas/hooks.ts`
- Modify: `frontend/src/features/resource-quotas/hooks/index.ts`
- Modify: `frontend/src/features/resource-quotas/index.ts`

**Problem:** `hooks.ts`（根级，含 TanStack Query hooks）和 `hooks/index.ts`（目录，含业务逻辑）并存，导致 TypeScript 解析歧义。

**Step 1: 读取两个 hooks 文件内容**

```bash
cat frontend/src/features/resource-quotas/hooks.ts
cat frontend/src/features/resource-quotas/hooks/index.ts
```

**Step 2: 将 hooks.ts 中的 TanStack Query hooks 迁移到 api/queries.ts**

按照架构规范，TanStack Query hooks 应在 `api/queries.ts`。

检查是否已有该文件：
```bash
ls frontend/src/features/resource-quotas/api/
```

将 `hooks.ts` 中的 `useResourceLimitConfigs`、`useCreateResourceLimitConfig`、`useUpdateResourceLimitConfig` 移入 `api/queries.ts`（如不存在则创建）。

**Step 3: 删除 hooks.ts 根级文件**

```bash
rm frontend/src/features/resource-quotas/hooks.ts
```

**Step 4: 将类型定义从 hooks/index.ts 迁移到 types/index.ts**

将 `ResourceQuota` 和 `QuotaUsage` 接口移入 `types/index.ts`，hooks/index.ts 中改为从 types 导入。

**Step 5: 更新 index.ts 导出**

确保 `features/resource-quotas/index.ts` 导出顺序正确：
```typescript
export * from './types';
export * from './api';
export * from './hooks';
// ...
```

**Step 6: 验证编译**

```bash
cd frontend && npm run build
```

**Step 7: Commit**

```bash
git add frontend/src/features/resource-quotas/
git commit -m "refactor(frontend): 修复 resource-quotas hooks 结构冲突，TanStack Query hooks 迁移至 api/queries.ts"
```

---

## Task 16: [P3] 前端 — 修复 MonitoringDashboardPage iframe 安全问题

**Files:**
- Modify: `frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx`

**Step 1: 找到 iframe 代码**

```bash
grep -n "iframe" frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx
```

**Step 2: 添加 sandbox 属性，移除废弃 frameBorder，修复硬编码颜色**

将：
```tsx
<iframe
  src={grafanaUrl}
  width="100%"
  height="600"
  frameBorder="0"
  style={{ border: "none", borderRadius: "4px", backgroundColor: "#f8f8f8" }}
/>
```

改为：
```tsx
<iframe
  src={grafanaUrl}
  width="100%"
  height="600"
  title="Grafana 监控仪表盘"
  sandbox="allow-scripts allow-same-origin"
  style={{ border: "none", borderRadius: "4px" }}
  loading="lazy"
/>
```

注意：移除 `frameBorder`（废弃属性，已有 CSS `border: none` 覆盖）和硬编码背景色 `#f8f8f8`。

**Step 3: 修复导入路径（直接引用内部文件）**

将：
```typescript
import { MetricsCharts } from "../components/MetricsCharts";
```
改为：
```typescript
import { MetricsCharts } from "../components";
```

**Step 4: 验证编译**

```bash
cd frontend && npm run build
```

**Step 5: Commit**

```bash
git add frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx
git commit -m "fix(frontend): iframe 添加 sandbox 属性，修复组件导入路径"
```

---

## Task 17: [P3] 前端 — 修复 UserManagementPage 类型断言和导入路径

**Files:**
- Modify: `frontend/src/features/admin/pages/UserManagementPage.tsx`

**Step 1: 修复组件导入路径**

将：
```typescript
import { UserFormModal } from "../components/UserFormModal";
```
改为：
```typescript
import { UserFormModal } from "../components";
```

**Step 2: 修复 roleFilter 和 statusFilter 类型断言**

将 `roleFilter as UserRole` 改为使用类型守卫：
```typescript
// 替代 as 断言，使用 includes 验证
const isUserRole = (v: string): v is UserRole =>
  ["admin", "researcher", "viewer"].includes(v);

// 在过滤器构建中
if (roleFilter && isUserRole(roleFilter)) {
  params.role = roleFilter;
}
```

类似处理 `statusFilter as UserStatus`。

**Step 3: 验证编译**

```bash
cd frontend && npm run build
```

**Step 4: Commit**

```bash
git add frontend/src/features/admin/pages/UserManagementPage.tsx
git commit -m "fix(frontend): 修复 UserManagementPage 导入路径和类型断言"
```

---

## Task 18: [P3] 基础设施 — AMP Workspace 添加审计日志

**Files:**
- Modify: `infrastructure/cdk/stacks/observability/observability_stack.py`

**Step 1: 读取 _create_amp_workspace 方法**

```bash
grep -n -A 15 "_create_amp_workspace" infrastructure/cdk/stacks/observability/observability_stack.py
```

**Step 2: 添加 CloudWatch Logs 日志配置**

将：
```python
def _create_amp_workspace(self) -> aps.CfnWorkspace:
    return aps.CfnWorkspace(
        self,
        "AmpWorkspace",
        alias=f"{self.env_config.resource_prefix}-amp",
        tags=create_cfn_tags(...),
    )
```

改为（先创建 Log Group，再配置 AMP）：
```python
def _create_amp_workspace(self) -> aps.CfnWorkspace:
    # 创建 AMP 审计日志组
    log_group = logs.LogGroup(
        self,
        "AmpAuditLogs",
        log_group_name=f"/aws/amp/{self.env_config.resource_prefix}",
        retention=logs.RetentionDays.NINETY_DAYS,
        removal_policy=RemovalPolicy.DESTROY,
    )

    return aps.CfnWorkspace(
        self,
        "AmpWorkspace",
        alias=f"{self.env_config.resource_prefix}-amp",
        logging_configuration=aps.CfnWorkspace.LoggingConfigurationProperty(
            log_group_arn=log_group.log_group_arn,
        ),
        tags=create_cfn_tags(...),
    )
```

确认 `aws_cdk.aws_logs as logs` 和 `RemovalPolicy` 已导入。

**Step 3: 运行 CDK 测试**

```bash
cd infrastructure/cdk && pytest tests/unit/test_observability_stack.py -v
```

**Step 4: Commit**

```bash
git add infrastructure/cdk/stacks/observability/observability_stack.py
git commit -m "feat(cdk): AMP Workspace 添加 CloudWatch Logs 审计日志配置"
```

---

## 最终验证

**Step 1: 后端全量检查**

```bash
cd backend && black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
```

Expected: 全部通过。

**Step 2: 前端全量检查**

```bash
cd frontend && npm run lint && npm test -- --run && npm run build
```

Expected: 全部通过。

**Step 3: CDK 测试**

```bash
cd infrastructure/cdk && pytest tests/ -v
```

Expected: 全部通过。

---

## 执行顺序建议

| 优先级 | Tasks | 理由 |
|--------|-------|------|
| **必须先做** | Task 1, 2 | 安全 CRITICAL，可能暴露密钥 |
| **第二优先** | Task 3, 4, 5 | 安全 HIGH，影响生产安全性 |
| **第三优先** | Task 6, 7, 8 | 架构/功能正确性 |
| **第四优先** | Task 9, 10, 11 | 代码质量和性能 |
| **最后** | Task 12-18 | 前端和基础设施改善 |
