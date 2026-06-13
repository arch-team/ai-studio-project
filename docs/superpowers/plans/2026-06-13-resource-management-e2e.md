# 资源管理模块深度 E2E 测试与全栈修复 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让资源管理模块（配额管理页 `/resource-quotas` + 资源监控页 `/monitoring`）在真实 dev 环境全功能正确运行——配额页补深度边界测试、监控页接通已在线的 AMP 基建并补齐前后端契约。

**Architecture:** 监控页指标走实时查 AMP（不入库），集群信息走读穿透缓存（DB 为主，缺失/过期时回源 SageMaker `describe-cluster`）。接通 AMP 需三步：CDK 给后端 IRSA 角色加 `aps:` 权限 → 后端配置 AMP 端点 → PrometheusClient 加 SigV4 签名。后端补齐前端既有契约的端点（`/clusters*` 无前缀、`/monitoring/*` 带前缀），故障时返回 200+空数据保证前端降级。

**Tech Stack:** 后端 Python/FastAPI/SQLAlchemy（DDD）+ botocore SigV4 + aioboto3；前端 React/Cloudscape/TanStack Query + Playwright；基础设施 AWS CDK（Python）。

**设计依据:** `docs/superpowers/specs/2026-06-13-resource-management-e2e-design.md`（已通过两轮评审 + 用户确认）

---

## 关键事实速查（实施时参考）

| 项 | 值 |
|----|----|
| 真实环境 | `http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com` |
| 登录 | `admin / Admin123!`，`loginViaAPI` 注入 sessionStorage |
| AMP endpoint | `https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-577036b0-ac41-4e0b-81a5-4436385b0fdc/` |
| AMP service name（SigV4） | `aps` |
| HyperPod 集群 | `ai-platform-dev-hyperpod`（InService，3 实例组：controller-group/gpu-training-group/system-group） |
| 后端 IRSA role | `ai-platform-dev-backend-service-role`（已有 `sagemaker:DescribeCluster`，**无 `aps:*`**） |
| schema 真源 | `frontend/src/features/monitoring/types/index.ts` |
| 前端 baseURL | `/api/v1`；集群走 `/clusters*`（无 monitoring 前缀），指标/利用率/告警走 `/monitoring/*` |
| ORM | `backend/src/modules/monitoring/infrastructure/models/hyperpod_cluster_model.py` |
| ClusterStatus enum | `creating/active/updating/deleting/failed`（SageMaker `InService` → 映射为 `active`） |

**测试命令**：
- 后端单元：`cd backend && pytest tests/unit/monitoring -v`（注意：现有测试目录是 `tests/unit/monitoring/`，**无** `modules/` 中间层；`tests/unit/modules/monitoring/` 仅含 domain 子目录，新建测试一律放 `tests/unit/monitoring/`）
- 后端集成：`cd backend && pytest tests/integration/monitoring -v`
- 后端质量门：`cd backend && black --check src/ && ruff check src/ && mypy src/`
- 前端 E2E（真实环境）：`cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com npm run test:e2e -- e2e/tests/<spec>`
- CDK 校验：`cd infrastructure/cdk && ruff check . && mypy . && pytest -m unit`
- CDK diff：`cd infrastructure/cdk && cdk diff ai-platform-dev-iam --context env=dev`

---

## 阶段 0：决策确认与诊断

### Task 0.1: 确认配额删除能力决策

**这是人工决策点，非代码任务。**

- [ ] **Step 1: 向用户确认** 配额管理页当前仅"编辑"无"删除"。确认删除能力是否纳入本轮：
  - 若纳入 → 在 Task 5.x 增加后端 `DELETE /resource-limit-configs/{id}` + 前端删除按钮 + 删除 E2E 用例。
  - 若不纳入 → 记录为发现项，§4.1 测试不含删除。
- [ ] **Step 2: 记录决策** 在本计划末尾"决策记录"追加结论。

### Task 0.2: 诊断式 E2E 跑通现状基线

**Files:**
- 临时运行，不产出文件（仅归档失败项到记忆/报告）

- [ ] **Step 1: 跑配额页现有套件（真实环境）**

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npm run test:e2e -- e2e/tests/resource-quotas.spec.ts e2e/tests/resource-quotas-crud.spec.ts
```
Expected: 大部分通过（配额页基本健康），记录任何失败项。

- [ ] **Step 2: 手动探查监控页端点（确认 404 基线）**

用 §关键事实 的登录 token，curl/python 探查 `/api/v1/clusters`、`/api/v1/monitoring/utilization`、`/api/v1/monitoring/metrics`、`/api/v1/monitoring/alerts`，确认全部 404（修复前基线）。

- [ ] **Step 3: 归档基线** 记录两页失败项清单，作为修复完成的对照基准。不提交代码。

---

## 阶段 2A：CDK — 后端 IRSA 角色增加 AMP 查询权限

> 这是接通 AMP 的前置基建改动。必须先部署，否则后端查 AMP 会 403。

### Task 2A.1: 给 backend-service-role 增加 aps 权限

**Files:**
- Modify: `infrastructure/cdk/stacks/foundation/iam_stack.py`（`_create_backend_service_role`，在 `CloudWatchLogsAccess` policy 块——约 line 355-367——之后、`cdk.Tags.of(role)`（约 line 369）之前插入）
- Test: `infrastructure/cdk/tests/unit/test_iam_stack.py`（追加；先确认该文件的断言风格）

- [ ] **Step 1: 先看现有 IAM 测试结构** —— 确认是否有 `backend_iam_template` fixture，没有则用 `Template.from_stack(...)` 本地构造（参照同目录 `test_sagemaker_hyperpod_stack.py` 的 `Match.array_with(...)` 风格）。

Run: `cd infrastructure/cdk && grep -n "def test.*backend\|Template.from_stack\|backend_iam_template\|Match" tests/unit/test_iam_stack.py | head`

- [ ] **Step 2: 写失败测试** —— 断言 backend role 含 aps 权限（fixture/构造方式按 Step 1 实际情况）

```python
def test_backend_role_has_amp_query_permissions():
    """后端服务角色应具备 AMP 查询权限以接通监控页指标。"""
    # 用与现有 backend role 测试相同的 Template 构造方式
    template = Template.from_stack(_build_iam_stack())  # 复用文件内现有 helper
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Action": Match.array_with([
                            "aps:QueryMetrics",
                            "aps:GetSeries",
                            "aps:GetLabels",
                            "aps:GetMetricMetadata",
                        ]),
                        "Effect": "Allow",
                    })
                ])
            }
        },
    )
```

- [ ] **Step 3: 运行测试验证失败**

Run: `cd infrastructure/cdk && pytest tests/unit/test_iam_stack.py::test_backend_role_has_amp_query_permissions -v`
Expected: FAIL（当前角色无 aps 权限）

- [ ] **Step 4: 实现 —— 插入 aps policy statement**

在 `_create_backend_service_role` 的 `CloudWatchLogsAccess` policy 块之后插入：

```python
        role.add_to_policy(
            iam.PolicyStatement(
                sid="AmpQueryAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "aps:QueryMetrics",
                    "aps:GetSeries",
                    "aps:GetLabels",
                    "aps:GetMetricMetadata",
                ],
                resources=[
                    f"arn:aws:aps:{self.env_config.region}:{self.env_config.account}:workspace/*",
                ],
            )
        )
```

> 注：资源用 workspace 通配（dev 单 workspace）；如需收紧可注入具体 workspace ARN，但 observability stack 与 iam stack 无直接依赖，通配更简单且 dev 可接受。

- [ ] **Step 5: 运行测试验证通过**

Run: `cd infrastructure/cdk && pytest tests/unit/test_iam_stack.py::test_backend_role_has_amp_query_permissions -v`
Expected: PASS

- [ ] **Step 6: 质量门 + diff**

Run: `cd infrastructure/cdk && ruff check . && mypy . && cdk diff ai-platform-dev-iam --context env=dev`
Expected: lint/type 通过；diff 仅显示新增一条 IAM policy statement

- [ ] **Step 7: 提交**

```bash
git add infrastructure/cdk/stacks/foundation/iam_stack.py infrastructure/cdk/tests/
git commit -m "feat(cdk): 后端服务角色增加 AMP 查询权限（接通监控页指标）"
```

### Task 2A.2: 部署 iam stack 到 dev

- [ ] **Step 1: 部署**

Run: `cd infrastructure/cdk && cdk deploy ai-platform-dev-iam --context env=dev --require-approval never`
Expected: UPDATE_COMPLETE

- [ ] **Step 2: 验证权限生效**

```bash
aws iam list-role-policies --role-name ai-platform-dev-backend-service-role
aws iam get-role-policy --role-name ai-platform-dev-backend-service-role --policy-name <含 aps 的 policy>
```
Expected: 输出含 `aps:QueryMetrics` 等。无需提交（部署动作）。

---

## 阶段 2B：后端 — AMP 接入层（SigV4 + 配置）

### Task 2B.1: Settings 增加 AMP 端点配置

**Files:**
- Modify: `backend/src/shared/infrastructure/config.py`（HyperPod 配置块后，约 line 42-43）
- Test: `backend/tests/unit/shared/test_config.py`（若无则新建）

- [ ] **Step 1: 写失败测试**

```python
def test_settings_has_amp_endpoint_default_none():
    from src.shared.infrastructure.config import Settings
    s = Settings()
    assert hasattr(s, "amp_query_endpoint")
    assert hasattr(s, "amp_region")
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/unit/shared/test_config.py::test_settings_has_amp_endpoint_default_none -v`
Expected: FAIL（AttributeError）

- [ ] **Step 3: 实现 —— 在 Settings 增加字段**

在 `# HyperPod` 块后插入：

```python
    # Amazon Managed Prometheus (AMP) — 监控页指标数据源
    # 未配置时 PrometheusClient 回退 localhost:9090（本地开发），dev/prod 须显式设置
    amp_query_endpoint: str | None = None
    amp_region: str = "us-east-1"
```

- [ ] **Step 4: 运行验证通过**

Run: `cd backend && pytest tests/unit/shared/test_config.py::test_settings_has_amp_endpoint_default_none -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/shared/infrastructure/config.py backend/tests/unit/shared/
git commit -m "feat(backend): Settings 增加 AMP 查询端点配置"
```

### Task 2B.2: PrometheusClient 增加 SigV4 签名

**Files:**
- Modify: `backend/src/modules/monitoring/infrastructure/external/prometheus_client.py`
- Test: `backend/tests/unit/monitoring/test_prometheus_sigv4.py`（新建）

- [ ] **Step 1: 写失败测试** —— 验证请求被 SigV4 签名（含 Authorization 头）

```python
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC

@pytest.mark.asyncio
async def test_query_instant_signs_request_with_sigv4(monkeypatch):
    """启用 AMP 时，query_instant 应对请求做 SigV4 签名（带 Authorization 头）。"""
    from src.modules.monitoring.infrastructure.external.prometheus_client import PrometheusClient

    captured = {}

    class FakeResponse:
        def raise_for_status(self): ...
        def json(self): return {"status": "success", "data": {"result": []}}

    async def fake_get(self, url, params=None, headers=None):
        captured["headers"] = headers or {}
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    # CI/本地无 AWS 凭证时 get_credentials() 返回 None → SigV4Auth 抛错。
    # 必须 mock 假凭证，否则测试因环境无凭证而误红。
    from botocore.credentials import Credentials
    monkeypatch.setattr("boto3.Session.get_credentials", lambda self: Credentials("AKIATEST", "secret"))
    # 注入 AMP 端点触发签名分支
    client = PrometheusClient(endpoint="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-x", use_sigv4=True)
    await client.query_instant("up")
    assert "Authorization" in captured["headers"]
    assert "AWS4-HMAC-SHA256" in captured["headers"]["Authorization"]
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/unit/monitoring/test_prometheus_sigv4.py -v`
Expected: FAIL（PrometheusClient 无 use_sigv4 参数 / 无签名）

- [ ] **Step 3: 实现 SigV4 签名**

改造 `PrometheusClient`：构造函数读取 settings 的 `amp_query_endpoint`，新增 `use_sigv4` 标志；新增私有方法用 botocore 签名。核心代码：

```python
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import boto3

class PrometheusClient(IPrometheusClient):
    def __init__(self, endpoint: str | None = None, timeout: float = 30.0, use_sigv4: bool | None = None):
        settings = get_settings()
        # 回退优先级：显式传入 > AMP 端点 > 旧 prometheus_endpoint（向后兼容现有 5 端点）> 本地
        # 注意：现有 storage/network/cluster-metrics 端点共用此单例，必须保留 prometheus_endpoint 兼容
        self._endpoint = (
            endpoint
            or settings.amp_query_endpoint
            or getattr(settings, "prometheus_endpoint", None)
            or "http://localhost:9090"
        ).rstrip("/")
        self._region = settings.amp_region
        # 显式传入优先；否则按端点是否为 AMP 自动判定
        self._use_sigv4 = use_sigv4 if use_sigv4 is not None else "aps-workspaces" in self._endpoint
        self._timeout = timeout

    def _sign_headers(self, method: str, url: str) -> dict[str, str]:
        """对 AMP 请求做 SigV4 签名，返回 Authorization 等头。"""
        session = boto3.Session()
        credentials = session.get_credentials()
        aws_request = AWSRequest(method=method, url=url)
        SigV4Auth(credentials, "aps", self._region).add_auth(aws_request)
        return dict(aws_request.headers)

    async def query_instant(self, query: str) -> list[dict[str, Any]]:
        url = f"{self._endpoint}/api/v1/query?query={httpx.QueryParams({'query': query})['query']}"
        # AMP 要求签名作用于带 query string 的完整 URL；用 params 单独传会导致签名不匹配
        full_url = f"{self._endpoint}/api/v1/query"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            req = client.build_request("GET", full_url, params={"query": query})
            headers = self._sign_headers("GET", str(req.url)) if self._use_sigv4 else {}
            response = await client.get(full_url, params={"query": query}, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                raise PrometheusQueryError(message=data.get("error", "Unknown error"))
            return data.get("data", {}).get("result", [])
```

> 同样改造 `query_range`（对 `/api/v1/query_range` 带完整 query string 签名）。SigV4 须签名最终 URL（含 query params），故先 `build_request` 得到完整 URL 再签名。

- [ ] **Step 4: 运行验证通过**

Run: `cd backend && pytest tests/unit/monitoring/test_prometheus_sigv4.py -v`
Expected: PASS

- [ ] **Step 5: 回归现有 monitoring 测试（覆盖共用单例的 5 个旧端点）**

Run: `cd backend && pytest tests/unit/monitoring/ -v && pytest tests/integration/monitoring/ -v`
Expected: PASS（本地/旧端点分支不签名，行为不变；确认 storage/network/cluster-metrics 等共用 `get_prometheus_client()` 单例的端点未受回退链改动影响）

- [ ] **Step 6: 提交**

```bash
git add backend/src/modules/monitoring/infrastructure/external/prometheus_client.py backend/tests/unit/monitoring/test_prometheus_sigv4.py
git commit -m "feat(backend): PrometheusClient 增加 AMP SigV4 签名支持"
```

---

## 阶段 2C：后端 — 补齐监控页端点

### Task 2C.1: 新增响应 schema（对齐前端类型）

**Files:**
- Modify: `backend/src/modules/monitoring/api/schemas/responses.py`
- Test: `backend/tests/unit/monitoring/test_schema_monitoring.py`（新建）

- [ ] **Step 1: 写失败测试** —— 验证新 schema 字段与前端对齐

```python
def test_cluster_summary_response_fields():
    from src.modules.monitoring.api.schemas.responses import ClusterSummaryResponse
    fields = ClusterSummaryResponse.model_fields
    for f in ["id", "cluster_name", "cluster_arn", "region", "status",
              "health_status", "total_nodes", "available_nodes",
              "total_gpu_count", "last_sync_at", "created_at"]:
        assert f in fields

def test_resource_utilization_response_fields():
    from src.modules.monitoring.api.schemas.responses import ResourceUtilizationResponse
    for f in ["resource_type", "total", "used", "available", "utilization_percentage", "unit"]:
        assert f in ResourceUtilizationResponse.model_fields

def test_metric_series_response_fields():
    from src.modules.monitoring.api.schemas.responses import MetricSeriesResponse
    for f in ["metric_name", "labels", "data_points"]:
        assert f in MetricSeriesResponse.model_fields

def test_alert_list_response_is_paginated():
    from src.modules.monitoring.api.schemas.responses import AlertListResponse
    for f in ["items", "total", "page", "page_size", "total_pages"]:
        assert f in AlertListResponse.model_fields

def test_cluster_summary_nullable_fields_accept_none():
    """前端 ClusterSummary 中 health_status/total_gpu_count/last_sync_at 可空，
    后端 schema 必须允许 None，否则真实 describe-cluster 缺字段时 500。"""
    from src.modules.monitoring.api.schemas.responses import ClusterSummaryResponse
    # 用最小必填集 + nullable 字段省略 实例化，不应抛错
    obj = ClusterSummaryResponse(
        id=1, cluster_name="c", cluster_arn="arn", region="us-east-1",
        status="active", total_nodes=3, available_nodes=3,
        created_at="2026-06-13T00:00:00Z",
    )
    assert obj.health_status is None
    assert obj.total_gpu_count is None
    assert obj.last_sync_at is None
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/unit/monitoring/test_schema_monitoring.py -v`
Expected: FAIL（ImportError）

- [ ] **Step 3: 实现 schema** —— 追加到 `responses.py`（字段名严格对齐 `frontend/.../monitoring/types/index.ts` 的 `ClusterSummary`/`ResourceUtilization`/`MetricSeries`/`AlertListResponse`）

```python
class ClusterSummaryResponse(BaseModel):
    id: int
    cluster_name: str
    cluster_arn: str
    region: str
    status: str
    health_status: str | None = None
    total_nodes: int
    available_nodes: int
    total_gpu_count: int | None = None
    available_gpu_count: int | None = None
    total_cpu_cores: int | None = None
    available_cpu_cores: int | None = None
    last_sync_at: datetime | None = None
    created_at: datetime

class ClusterListResponse(BaseModel):
    items: list[ClusterSummaryResponse] = Field(default_factory=list)
    total: int = 0

class ResourceUtilizationResponse(BaseModel):
    resource_type: str  # cpu | memory | gpu | storage
    total: float
    used: float
    available: float
    utilization_percentage: float
    unit: str

class MetricSeriesResponse(BaseModel):
    metric_name: str
    labels: dict[str, str] = Field(default_factory=dict)
    data_points: list[MetricDataPointResponse] = Field(default_factory=list)

class AlertResponse(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    source: str
    resource_type: str
    resource_id: str
    fired_at: datetime
    resolved_at: datetime | None = None
    status: str

class AlertListResponse(BaseModel):
    items: list[AlertResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
```

- [ ] **Step 4: 运行验证通过 + mypy**

Run: `cd backend && pytest tests/unit/monitoring/test_schema_monitoring.py -v && mypy src/modules/monitoring/api/schemas/`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/monitoring/api/schemas/responses.py backend/tests/unit/monitoring/test_schema_monitoring.py
git commit -m "feat(backend): 监控页响应 schema（集群列表/利用率/指标序列/告警）"
```

### Task 2C.2a: 补齐 HyperPodCluster 仓库缺失方法（前置依赖）

> 评审核实：`IHyperPodClusterRepository` 接口声明了 `get_by_id/create/update`，但 `HyperPodClusterRepositoryImpl` **只实现了** `get_by_name/get_by_arn/list_clusters/count_clusters`。读穿透服务依赖 `create`/`update`，必须先补齐实现。**不新增 `list_all`/`upsert`**——直接用现有 `list_clusters()`（读全部）+ `get_by_arn()`（查重）+ `create()`/`update()`（写）组合，避免改接口契约（YAGNI）。

**Files:**
- Modify: `backend/src/modules/monitoring/infrastructure/repositories/hyperpod_cluster_repository_impl.py`（补 `get_by_id`/`create`/`update`）
- Test: `backend/tests/integration/monitoring/test_repo_hyperpod_cluster.py`（新建）

- [ ] **Step 1: 写失败集成测试**（真实 DB）—— `create` 后能 `get_by_arn` 查到、`update` 改 status 生效

```python
@pytest.mark.asyncio
async def test_create_and_get_by_arn(db_session):
    repo = HyperPodClusterRepositoryImpl(db_session)
    entity = _make_cluster_entity(cluster_arn="arn:aws:sagemaker:...:cluster/abc")
    await repo.create(entity)
    found = await repo.get_by_arn("arn:aws:sagemaker:...:cluster/abc")
    assert found is not None and found.cluster_name == entity.cluster_name

@pytest.mark.asyncio
async def test_update_changes_status(db_session):
    repo = HyperPodClusterRepositoryImpl(db_session)
    entity = await repo.create(_make_cluster_entity())
    entity.status = ClusterStatus.ACTIVE
    await repo.update(entity)
    refetched = await repo.get_by_id(entity.id)
    assert refetched.status == ClusterStatus.ACTIVE
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/integration/monitoring/test_repo_hyperpod_cluster.py -v`
Expected: FAIL（`create`/`update`/`get_by_id` 未实现，NotImplementedError 或 AttributeError）

- [ ] **Step 3: 实现 `get_by_id`/`create`/`update`**（参照同模块 `get_by_name` 的 ORM↔Entity 映射风格）

- [ ] **Step 4: 运行验证通过**

Run: `cd backend && pytest tests/integration/monitoring/test_repo_hyperpod_cluster.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/monitoring/infrastructure/repositories/hyperpod_cluster_repository_impl.py \
        backend/tests/integration/monitoring/test_repo_hyperpod_cluster.py
git commit -m "feat(backend): 补齐 HyperPodCluster 仓库 get_by_id/create/update 实现"
```

### Task 2C.2b: 集群读穿透服务（DB 缓存 + 回源 SageMaker）

**Files:**
- Create: `backend/src/modules/monitoring/application/services/cluster_sync_service.py`
- Create: `backend/src/modules/monitoring/infrastructure/external/sagemaker_cluster_client.py`（复用 `training/.../hyperpod/cluster_client.py` 的 aioboto3 范式）
- Test: `backend/tests/unit/monitoring/test_svc_cluster_sync.py`（新建）

- [ ] **Step 1: 写失败测试** —— 缺失/过期时回源、命中时不回源（用现有 repo 方法名 `list_clusters`/`get_by_arn`/`create`/`update`）

```python
@pytest.mark.asyncio
async def test_get_clusters_refetches_when_db_empty():
    """DB 为空时应回源 SageMaker 并写库。"""
    mock_repo = AsyncMock()
    mock_repo.list_clusters.return_value = []   # DB 空
    mock_repo.get_by_arn.return_value = None    # 不存在 → create
    mock_sagemaker = AsyncMock()
    mock_sagemaker.describe_cluster.return_value = _fake_describe_cluster()
    svc = ClusterSyncService(mock_repo, mock_sagemaker, ttl_seconds=300, cluster_name="ai-platform-dev-hyperpod")
    result = await svc.get_clusters()
    mock_sagemaker.describe_cluster.assert_awaited()  # 回源
    mock_repo.create.assert_awaited()                 # 写库（新建）
    assert len(result) >= 1

@pytest.mark.asyncio
async def test_get_clusters_uses_db_when_fresh():
    """DB 有新鲜记录时不回源。"""
    mock_repo = AsyncMock()
    mock_repo.list_clusters.return_value = [_fresh_cluster()]  # last_sync_at 在 TTL 内
    mock_sagemaker = AsyncMock()
    svc = ClusterSyncService(mock_repo, mock_sagemaker, ttl_seconds=300)
    await svc.get_clusters()
    mock_sagemaker.describe_cluster.assert_not_awaited()  # 不回源

@pytest.mark.asyncio
async def test_get_clusters_updates_existing_when_stale():
    """DB 有但过期 → 回源后走 update（按 cluster_arn 查重命中）。"""
    mock_repo = AsyncMock()
    mock_repo.list_clusters.return_value = [_stale_cluster()]  # last_sync_at 超 TTL
    mock_repo.get_by_arn.return_value = _stale_cluster()       # arn 已存在 → update
    mock_sagemaker = AsyncMock()
    mock_sagemaker.describe_cluster.return_value = _fake_describe_cluster()
    svc = ClusterSyncService(mock_repo, mock_sagemaker, ttl_seconds=300, cluster_name="ai-platform-dev-hyperpod")
    await svc.get_clusters()
    mock_repo.update.assert_awaited()  # 已存在走 update 而非 create
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/unit/monitoring/test_svc_cluster_sync.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 SageMaker 集群客户端**（薄封装，复用 aioboto3 Session 范式）

```python
# sagemaker_cluster_client.py
import aioboto3
from src.shared.infrastructure import get_settings

# SageMaker ClusterStatus → 领域 ClusterStatus 值映射
_STATUS_MAP = {
    "InService": "active", "Creating": "creating", "Updating": "updating",
    "Deleting": "deleting", "Failed": "failed", "RollingBack": "updating",
    "SystemUpdating": "updating",
}

class SageMakerClusterClient:
    def __init__(self, session: aioboto3.Session | None = None, region: str | None = None):
        settings = get_settings()
        self._session = session or aioboto3.Session()
        self._region = region or settings.aws_region

    async def describe_cluster(self, cluster_name: str) -> dict:
        async with self._session.client("sagemaker", region_name=self._region) as sm:
            return await sm.describe_cluster(ClusterName=cluster_name)

    async def list_cluster_nodes(self, cluster_name: str) -> list[dict]:
        async with self._session.client("sagemaker", region_name=self._region) as sm:
            resp = await sm.list_cluster_nodes(ClusterName=cluster_name)
            return resp.get("ClusterNodeSummaries", [])
```

- [ ] **Step 4: 实现读穿透服务**（TTL 判断 + asyncio.Lock 单飞 + 按 arn 查重决定 create/update）

```python
# cluster_sync_service.py — 核心逻辑（用现有 repo 方法，不新增接口）
import asyncio
from datetime import timedelta
from src.shared.utils import utc_now

class ClusterSyncService:
    def __init__(self, cluster_repo, sagemaker_client, ttl_seconds: int = 300,
                 cluster_name: str | None = None):
        self._repo = cluster_repo
        self._sagemaker = sagemaker_client
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cluster_name = cluster_name  # 默认从 settings.hyperpod_cluster_name
        self._lock = asyncio.Lock()

    async def get_clusters(self) -> list[HyperPodCluster]:
        existing, _ = await self._repo.list_clusters()  # 现有方法返回 (items, total) 或 list，按实际签名取
        if existing and self._is_fresh(existing):
            return existing
        # 回源（单飞保护，避免并发首请求击穿）
        async with self._lock:
            existing, _ = await self._repo.list_clusters()
            if existing and self._is_fresh(existing):
                return existing
            await self._sync_from_sagemaker()
            result, _ = await self._repo.list_clusters()
            return result

    def _is_fresh(self, clusters) -> bool:
        return all(
            c.last_sync_at is not None and (utc_now() - c.last_sync_at) < self._ttl
            for c in clusters
        )

    async def _sync_from_sagemaker(self) -> None:
        raw = await self._sagemaker.describe_cluster(self._cluster_name)
        entity = self._map_to_entity(raw)
        # 按 cluster_arn 查重：存在则 update，否则 create（替代 upsert）
        existing = await self._repo.get_by_arn(entity.cluster_arn)
        if existing is not None:
            entity.id = existing.id
            await self._repo.update(entity)
        else:
            await self._repo.create(entity)
```

> 注：`list_clusters()` 实际签名见 impl（可能返回 list 或 (items, total)），实现时按真实签名调整解包。

字段映射 `_map_to_entity`：`ClusterName`→cluster_name、`ClusterArn`→cluster_arn、`ClusterStatus` 经 `_STATUS_MAP`→status、`InstanceGroups`（list）→instance_groups(JSON) 且 `sum(CurrentCount)`→total_nodes、GPU 实例组累计→total_gpu_count、`utc_now()`→last_sync_at。

- [ ] **Step 5: 运行验证通过**

Run: `cd backend && pytest tests/unit/monitoring/test_svc_cluster_sync.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/modules/monitoring/application/services/cluster_sync_service.py \
        backend/src/modules/monitoring/infrastructure/external/sagemaker_cluster_client.py \
        backend/tests/unit/monitoring/test_svc_cluster_sync.py
git commit -m "feat(backend): 集群读穿透同步服务（DB 缓存 + 回源 SageMaker）"
```

### Task 2C.3: 利用率聚合服务（AMP 即时查询）

**Files:**
- Modify: `backend/src/modules/monitoring/application/services/prometheus_service.py`（增加 `get_resource_utilization`）
- Test: `backend/tests/unit/monitoring/test_svc_prometheus.py`（追加）

- [ ] **Step 1: 写失败测试**

```python
@pytest.mark.asyncio
async def test_get_resource_utilization_returns_cpu_mem_gpu():
    mock_client = AsyncMock()
    # 模拟三次 instant 查询返回值
    mock_client.query_instant.side_effect = [
        [{"value": [0, "45.0"]}],  # cpu
        [{"value": [0, "60.0"]}],  # memory
        [{"value": [0, "30.0"]}],  # gpu
    ]
    svc = PrometheusService(mock_client)
    result = await svc.get_resource_utilization()
    types = {r.resource_type for r in result}
    assert {"cpu", "memory", "gpu"}.issubset(types)
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/unit/monitoring/test_svc_prometheus.py::test_get_resource_utilization_returns_cpu_mem_gpu -v`
Expected: FAIL

- [ ] **Step 3: 实现 `get_resource_utilization`**（PromQL 见 spec §3.2-B）

```python
@dataclass
class ResourceUtilizationPoint:
    resource_type: str
    total: float
    used: float
    available: float
    utilization_percentage: float
    unit: str

# PromQL（实施时用 awscurl 对 AMP 校准）
_UTIL_QUERIES = {
    "cpu": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "memory": '(1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes)) * 100',
    "gpu": 'avg(DCGM_FI_DEV_GPU_UTIL)',
}

async def get_resource_utilization(self) -> list[ResourceUtilizationPoint]:
    points = []
    for rtype, query in _UTIL_QUERIES.items():
        pct = await self._query_instant_value(query)
        points.append(ResourceUtilizationPoint(
            resource_type=rtype, total=100.0, used=pct,
            available=100.0 - pct, utilization_percentage=round(pct, 1), unit="%",
        ))
    return points
```

- [ ] **Step 4: 运行验证通过**

Run: `cd backend && pytest tests/unit/monitoring/test_svc_prometheus.py::test_get_resource_utilization_returns_cpu_mem_gpu -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/monitoring/application/services/prometheus_service.py backend/tests/unit/monitoring/test_svc_prometheus.py
git commit -m "feat(backend): 资源利用率聚合服务（AMP CPU/内存/GPU 即时查询）"
```

### Task 2C.4: 新增端点 + 路由挂载 + 错误降级

**Files:**
- Create: `backend/src/modules/monitoring/api/cluster_endpoints.py`（`/clusters*` 无前缀路由）
- Modify: `backend/src/modules/monitoring/api/endpoints.py`（增加 `/utilization`、`/metrics`、`/alerts`）
- Modify: `backend/src/modules/monitoring/api/dependencies.py`（注入 ClusterSyncService）
- Modify: `backend/src/router.py`（挂载 clusters_router，无 `/monitoring` 前缀）
- Test: `backend/tests/integration/monitoring/test_api_monitoring_endpoints.py`（新建）

- [ ] **Step 1: 写失败集成测试** —— 验证鉴权、端点存在、返回正确 schema、故障降级 200

> fixture 名以现有 conftest 为准（已核实）：HTTP 客户端是 `client`（`tests/conftest.py`），鉴权头是 `engineer_auth_headers`/`admin_auth_headers`（`tests/integration/conftest.py`）。**无** `async_client`/`auth_headers`。降级测试用 FastAPI 的 `app.dependency_overrides` 替换 service（参照现有集成测试做法；如 `test_api_metrics.py` 的 DI 用法）。

```python
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_clusters_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/clusters")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_get_clusters_returns_list(client: AsyncClient, engineer_auth_headers: dict[str, str]):
    resp = await client.get("/api/v1/clusters", headers=engineer_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total" in body

@pytest.mark.asyncio
async def test_get_utilization_returns_list(client: AsyncClient, engineer_auth_headers: dict[str, str]):
    resp = await client.get("/api/v1/monitoring/utilization", headers=engineer_auth_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_get_alerts_returns_empty_paginated(client: AsyncClient, engineer_auth_headers: dict[str, str]):
    resp = await client.get("/api/v1/monitoring/alerts", headers=engineer_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == [] and body["total"] == 0

@pytest.mark.asyncio
async def test_utilization_degrades_to_200_on_amp_failure(
    client: AsyncClient, engineer_auth_headers: dict[str, str]
):
    """AMP 故障时端点返回 200 + 空数据，不返回 5xx。"""
    from src.main import app
    from src.modules.monitoring.api.dependencies import get_prometheus_service

    failing = AsyncMock()
    failing.get_resource_utilization.side_effect = Exception("AMP unreachable")
    app.dependency_overrides[get_prometheus_service] = lambda: failing
    try:
        resp = await client.get("/api/v1/monitoring/utilization", headers=engineer_auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.pop(get_prometheus_service, None)
```

- [ ] **Step 2: 运行验证失败**

Run: `cd backend && pytest tests/integration/monitoring/test_api_monitoring_endpoints.py -v`
Expected: FAIL（404 / 端点不存在）

- [ ] **Step 3: 实现 cluster_endpoints.py**（`/clusters`、`/clusters/{id}`、`/clusters/{id}/nodes`、`/clusters/{id}/metrics`）+ 错误降级

```python
# cluster_endpoints.py
router = APIRouter()

@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(
    _: None = Depends(get_current_active_user),
    sync_service: ClusterSyncService = Depends(get_cluster_sync_service),
) -> ClusterListResponse:
    try:
        clusters = await sync_service.get_clusters()
        items = [_to_summary_response(c) for c in clusters]
        return ClusterListResponse(items=items, total=len(items))
    except Exception as e:
        logger.warning("cluster_list_degraded", error=str(e))
        return ClusterListResponse(items=[], total=0)  # 降级，不 5xx
```

- [ ] **Step 4: 实现 endpoints.py 新增三端点**（`/utilization`、`/metrics`、`/alerts`，均 try/except 降级）

```python
@router.get("/utilization", response_model=list[ResourceUtilizationResponse])
async def get_utilization(
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> list[ResourceUtilizationResponse]:
    try:
        points = await prometheus_service.get_resource_utilization()
        return [ResourceUtilizationResponse(**asdict(p)) for p in points]
    except Exception as e:
        logger.warning("utilization_degraded", error=str(e))
        return []

@router.get("/metrics", response_model=list[MetricSeriesResponse])
async def get_metrics(
    metric_names: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    step: int = Query(60),
    _: None = Depends(get_current_active_user),
    prometheus_service: PrometheusService = Depends(get_prometheus_service),
) -> list[MetricSeriesResponse]:
    try:
        # 复用 query_metrics，转为 MetricSeriesResponse
        ...
    except Exception as e:
        logger.warning("metrics_degraded", error=str(e))
        return []

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1), page_size: int = Query(20),
    _: None = Depends(get_current_active_user),
) -> AlertListResponse:
    # 本轮告警子系统未实现，返回结构正确的空集（YAGNI）
    return AlertListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
```

- [ ] **Step 5: dependencies.py 注入 ClusterSyncService**

```python
def get_sagemaker_cluster_client() -> SageMakerClusterClient:
    return SageMakerClusterClient()

async def get_cluster_sync_service(
    cluster_repo: IHyperPodClusterRepository = Depends(get_cluster_repository),
    sagemaker_client: SageMakerClusterClient = Depends(get_sagemaker_cluster_client),
) -> ClusterSyncService:
    settings = get_settings()
    return ClusterSyncService(cluster_repo, sagemaker_client, cluster_name=settings.hyperpod_cluster_name)
```

- [ ] **Step 6: router.py 挂载 clusters_router（无 monitoring 前缀）**

在 `router.py` 增加 import 和挂载：
```python
from src.modules.monitoring.api.cluster_endpoints import router as clusters_router
# ...
api_router.include_router(clusters_router, tags=["集群监控"])  # 路径自带 /clusters，无 prefix
```

- [ ] **Step 7: 运行验证通过 + 质量门**

Run: `cd backend && pytest tests/integration/monitoring/test_api_monitoring_endpoints.py -v && black --check src/ && ruff check src/ && mypy src/`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/src/modules/monitoring/ backend/src/router.py backend/tests/integration/monitoring/
git commit -m "feat(backend): 补齐监控页端点（集群/利用率/指标/告警）+ 故障降级"
```

### Task 2C.5: 修正 monitoring 模块 __init__ 导出

**Files:**
- Modify: `backend/src/modules/monitoring/__init__.py`（当前为 `__all__ = []` 占位，与实际实现矛盾）

- [ ] **Step 1: 更新导出** —— 导出 router、Service、Entity（参考其他模块 `__init__.py` 风格）。

- [ ] **Step 2: 架构合规测试**

Run: `cd backend && pytest tests/architecture -v -k monitoring`
Expected: PASS（不导出 ORM/RepoImpl）

- [ ] **Step 3: 提交**

```bash
git add backend/src/modules/monitoring/__init__.py
git commit -m "fix(backend): monitoring 模块 __init__ 导出公开 API（移除占位）"
```

---

## 阶段 2D：后端部署与 AMP 联调

### Task 2D.1: 部署后端到 dev 并配置 AMP 环境变量

**Files:**
- Modify: `infrastructure/k8s/base/application/backend-deployment.yaml`（注入 `AMP_QUERY_ENDPOINT`、`HYPERPOD_CLUSTER_NAME` 环境变量）

- [ ] **Step 1: 注入环境变量**

```yaml
        - name: AMP_QUERY_ENDPOINT
          value: "https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-577036b0-ac41-4e0b-81a5-4436385b0fdc"
        - name: HYPERPOD_CLUSTER_NAME
          value: "ai-platform-dev-hyperpod"
```

- [ ] **Step 2: 构建并部署后端镜像**（按平台现有部署流程，参考既有 backend 部署 commit）

- [ ] **Step 3: 真实环境联调 —— 验证 4 端点不再 404**

```bash
# 用登录 token 探查
GET /api/v1/clusters                → 200，items 含 ai-platform-dev-hyperpod（status=active）
GET /api/v1/monitoring/utilization  → 200，cpu/memory/gpu 有真实值
GET /api/v1/monitoring/metrics?metric_names=DCGM_FI_DEV_GPU_UTIL → 200，有 data_points
GET /api/v1/monitoring/alerts       → 200，空集
```
Expected: 全部 200，集群与利用率有真实数据。

- [ ] **Step 4: PromQL 数值交叉验证**

用 awscurl 对 AMP 直接跑 §3.2-B 的 PromQL，与 `/monitoring/utilization` 返回值交叉核对，确认数值正确（非 0、合理范围）。

```bash
awscurl --service aps --region us-east-1 \
  "https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-577036b0-ac41-4e0b-81a5-4436385b0fdc/api/v1/query?query=avg(DCGM_FI_DEV_GPU_UTIL)"
```

- [ ] **Step 5: 记录联调结果**（截图/输出存档，无代码提交）

---

## 阶段 3A：前端 — 监控页降级与 Grafana 死链修复

### Task 3A.1: Grafana iframe 死链优雅降级

**Files:**
- Modify: `frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx`（`GrafanaDashboard` 组件，约 line 282-343）
- Test: `frontend/tests/unit/features/monitoring/MonitoringDashboardPage.test.tsx`（追加或新建）

- [ ] **Step 1: 写失败测试** —— Grafana 未配置时显示引导文案而非空白 iframe

```typescript
it('Grafana 未配置时显示引导文案而非死链 iframe', () => {
  // VITE_GRAFANA_URL 未设置
  render(<MonitoringDashboardPage />, { /* providers */ });
  // 切到 Grafana tab
  // 断言显示引导文案，不渲染 src="/grafana/..." 的 iframe
});
```

- [ ] **Step 2: 运行验证失败**

Run: `cd frontend && npm test -- tests/unit/features/monitoring/MonitoringDashboardPage.test.tsx`
Expected: FAIL

- [ ] **Step 3: 实现降级** —— `GrafanaDashboard` 检查 `VITE_GRAFANA_URL` 是否配置；未配置时显示 Cloudscape 引导文案（"Grafana 仪表盘尚未配置，请联系管理员"），不渲染死链 iframe。

- [ ] **Step 4: 运行验证通过**

Run: `cd frontend && npm test -- tests/unit/features/monitoring/MonitoringDashboardPage.test.tsx`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx frontend/tests/unit/features/monitoring/
git commit -m "fix(frontend): 监控页 Grafana 未配置时优雅降级（消除死链 iframe）"
```

> 注：前端 hooks/api 已按正确契约调用，后端补齐端点后即自动接通，前端无需改 api 层。若联调发现字段不匹配，在此追加修正任务。

---

## 阶段 3B：E2E 测试套件

### Task 3B.1: 配额页补边界测试

**Files:**
- Modify: `frontend/e2e/tests/resource-quotas-crud.spec.ts`（真实环境组追加用例）

- [ ] **Step 1: 追加分页测试** —— 数据 ≥ 1 页时翻页（现数据 9+ 条，若 page_size=20 不触发分页，则测试构造或验证分页器存在性逻辑）。
- [ ] **Step 2: 追加校验边界** —— 超长配置名、重复名（后端 409）、各角色枚举。
- [ ] **Step 3: 收紧创建断言** —— 真实环境创建成功后断言列表计数 +1（替换现有"记录不报错"宽松断言）。
- [ ] **Step 4: 追加错误态** —— mock 后端 500/422，断言 Alert 显示而非白屏。

- [ ] **Step 5: 跑真实环境验证**

Run: `cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com npm run test:e2e -- e2e/tests/resource-quotas-crud.spec.ts`
Expected: 全绿

- [ ] **Step 6: 提交**

```bash
git add frontend/e2e/tests/resource-quotas-crud.spec.ts
git commit -m "test(frontend): 配额页补边界测试（分页/校验/计数自洽/错误态）"
```

### Task 3B.2: 新建监控页 E2E 套件

**Files:**
- Create: `frontend/e2e/pages/MonitoringPage.ts`（Page Object，参考 `ResourceQuotasPage.ts` 风格 + 继承 `BasePage`）
- Create: `frontend/e2e/tests/monitoring.spec.ts`

- [ ] **Step 1: 写 Page Object** —— 封装四 Tab 切换、集群概览卡、利用率卡、时间范围选择器、自动刷新切换、告警空态。

- [ ] **Step 2: 写测试套件**（Tab→端点映射见 spec §4.2）

```typescript
test.describe("资源监控页 - 真实 Dev 环境", () => {
  test.skip(!isRemote, "仅真实环境运行");

  test("页面加载不报错（404 崩坏回归）", async ({ page }) => {
    await navigateWithAuth(page, "/monitoring");
    // 断言页面标题可见、无整页错误
  });

  test("概览 Tab 显示真实集群数据", async ({ page }) => {
    // 集群名 ai-platform-dev-hyperpod、状态、节点数可见
  });

  test("概览 Tab 显示真实资源利用率", async ({ page }) => {
    // CPU/内存/GPU 利用率卡有数值
  });

  test("指标趋势 Tab 渲染时间序列图表", async ({ page }) => { /* ... */ });
  test("时间范围选择 + 自动刷新切换", async ({ page }) => { /* ... */ });
  test("Grafana Tab 降级文案/入口正确", async ({ page }) => { /* ... */ });
  test("告警 Tab 显示暂无告警", async ({ page }) => { /* ... */ });
});
```

- [ ] **Step 3: 跑真实环境验证**

Run: `cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com npm run test:e2e -- e2e/tests/monitoring.spec.ts`
Expected: 全绿（修复后）

- [ ] **Step 4: 提交**

```bash
git add frontend/e2e/pages/MonitoringPage.ts frontend/e2e/tests/monitoring.spec.ts
git commit -m "test(frontend): 新建资源监控页 E2E 套件（真实环境全功能）"
```

---

## 阶段 3C：浏览器实测取证

### Task 3C.1: 关键交互浏览器实测截图

**Files:**
- 产出截图到 `frontend/e2e/artifacts/`（不入库或按现有约定）

- [ ] **Step 1: 配额页** —— 浏览器打开 `/resource-quotas`，实测创建/编辑流程，截图列表、Modal、成功 Flashbar。
- [ ] **Step 2: 监控页** —— 浏览器打开 `/monitoring`，逐 Tab 截图：概览（真实集群+利用率）、指标趋势（曲线）、Grafana（降级/入口）、告警（空态）。
- [ ] **Step 3: 归档截图** 作为完成证据，写入测试报告。

---

## 阶段 4：回归与交付

### Task 4.1: ui-audit 视觉回归

- [ ] **Step 1: 跑 ui-audit 截图流水线**（covering resource-quotas + monitoring 两页）确认无视觉回归。

Run: `/ui-audit resource-quotas` 及 `/ui-audit monitoring`（按 ui-audit skill 用法）

- [ ] **Step 2: 处理回归项**（若有）→ 修复 → 重跑，循环至无回归。

### Task 4.2: 全量验证与报告

- [ ] **Step 1: 后端全测试 + 覆盖率门**

Run: `cd backend && pytest --cov=src --cov-fail-under=85`
Expected: PASS

- [ ] **Step 2: 前端 E2E 全套（真实环境）两页全绿**

Run: `cd frontend && E2E_BASE_URL=... npm run test:e2e -- e2e/tests/resource-quotas.spec.ts e2e/tests/resource-quotas-crud.spec.ts e2e/tests/monitoring.spec.ts`
Expected: 全绿

- [ ] **Step 3: 对照阶段 0 基线** 确认所有归档失败项已解决。

- [ ] **Step 4: 撰写测试与修复报告** → `claudedocs/resource-management-e2e-report.md`（含发现项清单：如配额删除决策结论、PromQL 交叉验证数据、截图索引）。

- [ ] **Step 5: 提交报告**

```bash
git add claudedocs/resource-management-e2e-report.md
git commit -m "docs(*): 资源管理模块 E2E 测试与修复报告"
```

---

## 完成标准（硬门）

- [ ] 配额页：真实环境 Playwright 套件全绿，含分页/校验边界/计数自洽/错误态
- [ ] 监控页：4 端点真实环境全部 200，集群概览+利用率展示真实数据，指标趋势有曲线，告警/Grafana 优雅降级
- [ ] PromQL 数值经 AMP 交叉验证正确
- [ ] 后端覆盖率 ≥ 85%，质量门（black/ruff/mypy）通过
- [ ] CDK 质量门通过，iam stack 已部署
- [ ] ui-audit 无视觉回归
- [ ] 关键交互浏览器截图齐备
- [ ] 测试与修复报告完成

---

## 决策记录

| 决策 | 结论 | 时间 |
|------|------|------|
| 配额删除能力是否纳入 | 待 Task 0.1 确认 | - |
| 告警数据 | 返回空集（YAGNI） | spec 已定 |
| 集群数据策略 | 读穿透缓存 | spec 已定 |
| Prometheus/Grafana | 复用已在线 AMP，不自建 | spec 已定 |

---

## 风险与注意事项

- **SigV4 签名 URL 必须含 query string**：AMP 对完整 URL（含 `?query=...`）签名，用 httpx params 单独传会导致签名不匹配 → 403。务必先 `build_request` 得到最终 URL 再签名。
- **读穿透首次回源延迟**：`hyperpod_clusters` 表当前空，首请求秒级延迟；已加 asyncio.Lock 单飞，前端请求超时需 ≥ 该延迟。
- **ClusterStatus 映射**：SageMaker `InService` ≠ 领域 enum，必须经 `_STATUS_MAP` 映射为 `active`，否则 enum 校验失败。
- **iam stack 必须先部署**（阶段 2A）再做后端 AMP 联调（阶段 2D），否则 403。
- **monitoring 模块 `__init__.py` 占位与实现矛盾**：Task 2C.5 修正，避免导入混乱。
