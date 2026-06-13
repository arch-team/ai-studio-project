# HyperPod 原生 Spaces 开发环境 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有 AI 训练平台的 `spaces` 模块新增第二种在线开发环境创建方式（HyperPod 原生 Spaces add-on，基于 K8s CRD），与已实现的 SageMaker Studio Spaces 端到端对称。

**Architecture:** 统一 `Space` 实体加 `backend` 判别字段（studio/hyperpod）。抽取 `ISpaceBackendClient` 共同接口，方式一（aioboto3）与方式二（httpx→K8s CRD）各自实现，`SpaceService` 用 `dict[SpaceBackend, ISpaceBackendClient]` 策略分发。方式二通过 K8s API 操作 `workspace.jupyter.org/v1alpha1` Workspace/WorkspaceConnection CRD，复用训练模块 `KueueClient` 的 httpx + ServiceAccount token 异步模式，完整纳入 Kueue Task Governance。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy 2.0 async / Pydantic v2 / httpx / aioboto3 / Alembic（后端）；React + TypeScript + Cloudscape + TanStack Query（前端）；Playwright（E2E）。

**设计文档：** `docs/superpowers/specs/2026-06-13-hyperpod-native-spaces-design.md`

---

## 阶段划分

设计文档显式区分两个阶段。本计划据此组织：

- **Phase A：应用层编码（可立即开始）** — 用 mock K8s API 走 TDD，不依赖真实 add-on。Task 1–13。
- **Phase B：基础设施就绪** — 装 Spaces add-on、配 Kueue 治理、核验真实 CRD schema。Task 14–16。
- **Phase C：真实 AWS E2E** — 依赖 Phase B 完成。Task 17。

> Phase A 与 Phase B 可并行（不同人/不同 worktree）。Phase A 的状态映射表（Task 3）在 Phase B 核验真实 CRD 后可能需微调字段名——已在 Task 15 设回填检查点。

---

## 文件结构

**后端新建：**
- `backend/src/modules/spaces/application/interfaces/space_backend_client.py` — `ISpaceBackendClient` 共同接口
- `backend/src/modules/spaces/infrastructure/external/studio_space_backend.py` — 方式一适配器（包装现有 `SageMakerSpacesClient`）
- `backend/src/modules/spaces/infrastructure/external/hyperpod_space_backend.py` — 方式二实现（httpx→K8s CRD）
- `backend/src/modules/spaces/infrastructure/external/k8s_workspace_client.py` — K8s CRD 低层 httpx 客户端（薄封装，复用 KueueClient 模式）
- `backend/alembic/versions/20260613_xxxxxx_add_space_backend_fields.py` — 加 4 列迁移

**后端修改：**
- `domain/value_objects/space_enums.py` — 加 `SpaceBackend` 枚举
- `domain/entities/space.py` — 加 `backend`/`namespace`/`queue_name`/`workspace_template` 字段
- `domain/exceptions.py` — 加 `HyperPodSpaceBackendError`/`SpaceBackendUnavailableError`
- `infrastructure/models/space_model.py` — 加 4 列
- `infrastructure/repositories/space_repository_impl.py` — `_updatable_fields` 加新字段
- `application/services/space_service.py` — 改造为 backend 无关 + 策略分发 + 配额校验
- `api/schemas/requests.py` / `responses.py` — 加 backend 字段
- `api/dependencies.py` — 组装两个 backend + quota_checker
- 各 `__init__.py` — 导出新符号

**前端修改：**
- `src/features/spaces/types/index.ts` — 加 `SpaceBackend` 类型、label、字段
- `src/features/spaces/api/spaceApi.ts` / `queries.ts` — create 加 backend、access-url 安全校验放宽
- `src/features/spaces/pages/CreateSpacePage.tsx` — 加环境类型 Select
- `src/features/spaces/pages/SpaceListPage.tsx` — 加 backend 列

**基础设施（Phase B）：**
- `infrastructure/` — Spaces add-on 安装、Kueue 治理配置、RBAC（具体路径在 Task 14 确定）

**E2E（Phase C）：**
- `frontend/e2e/tests/spaces-hyperpod-remote.spec.ts` — 真实 AWS 生命周期测试

---

# Phase A：应用层编码

## Task 1: 新增 SpaceBackend 枚举

**Files:**
- Modify: `backend/src/modules/spaces/domain/value_objects/space_enums.py`
- Modify: `backend/src/modules/spaces/domain/value_objects/__init__.py`
- Test: `backend/tests/unit/spaces/test_vo_space_backend.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/spaces/test_vo_space_backend.py`：

```python
"""SpaceBackend 值对象测试。"""

from src.modules.spaces.domain.value_objects import SpaceBackend


class TestSpaceBackend:
    def test_studio_value(self) -> None:
        assert SpaceBackend.STUDIO.value == "studio"

    def test_hyperpod_value(self) -> None:
        assert SpaceBackend.HYPERPOD.value == "hyperpod"

    def test_from_value(self) -> None:
        assert SpaceBackend("hyperpod") is SpaceBackend.HYPERPOD
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_vo_space_backend.py -v`
Expected: FAIL — `ImportError: cannot import name 'SpaceBackend'`

- [ ] **Step 3: 实现**

在 `space_enums.py` 顶部 `SpaceInstanceType` 之前加入：

```python
class SpaceBackend(Enum):
    """开发环境后端类型。

    studio: SageMaker Studio Spaces（独立计费实例，不占集群）
    hyperpod: HyperPod 原生 Spaces（集群节点，纳入 Kueue 治理）
    """

    STUDIO = "studio"
    HYPERPOD = "hyperpod"
```

在 `domain/value_objects/__init__.py` 加入 `SpaceBackend` 到 import 和 `__all__`。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_vo_space_backend.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/domain/value_objects/ backend/tests/unit/spaces/test_vo_space_backend.py
git commit -m "feat(spaces): 新增 SpaceBackend 枚举区分 studio/hyperpod 后端"
```

---

## Task 2: Space 实体新增 backend 及 HyperPod 字段

**Files:**
- Modify: `backend/src/modules/spaces/domain/entities/space.py:20-40`
- Test: `backend/tests/unit/spaces/test_entity_space.py`

- [ ] **Step 1: 写失败测试**

在 `backend/tests/unit/spaces/test_entity_space.py` 末尾追加：

```python
class TestSpaceBackendField:
    def test_default_backend_is_studio(self) -> None:
        from src.modules.spaces.domain.value_objects import SpaceBackend

        space = Space(space_name="s1", owner_id=1)
        assert space.backend is SpaceBackend.STUDIO
        assert space.namespace is None
        assert space.queue_name is None
        assert space.workspace_template is None

    def test_hyperpod_backend_with_fields(self) -> None:
        from src.modules.spaces.domain.value_objects import SpaceBackend

        space = Space(
            space_name="s2",
            owner_id=1,
            backend=SpaceBackend.HYPERPOD,
            namespace="dev-spaces",
            queue_name="team-alpha-localqueue",
            workspace_template="sagemaker-jupyter-template",
        )
        assert space.backend is SpaceBackend.HYPERPOD
        assert space.namespace == "dev-spaces"
```

> 若 `Space` 必填字段更多导致构造失败，参照同文件已有 `Space(...)` 构造样例补齐参数。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_entity_space.py::TestSpaceBackendField -v`
Expected: FAIL — `backend` 字段不存在

- [ ] **Step 3: 实现**

`space.py` 的 import 加 `SpaceBackend`（从 `..value_objects`）。在实体字段区 `space_type` 之后加入：

```python
    backend: SpaceBackend = SpaceBackend.STUDIO

    # HyperPod backend 专属字段（仅 backend=HYPERPOD 使用）
    namespace: str | None = None
    queue_name: str | None = None
    workspace_template: str | None = None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_entity_space.py -v`
Expected: PASS（含原有测试）

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/domain/entities/space.py backend/tests/unit/spaces/test_entity_space.py
git commit -m "feat(spaces): Space 实体新增 backend 及 HyperPod 专属字段"
```

---

## Task 3: HyperPod Workspace 状态映射

**Files:**
- Create: `backend/src/modules/spaces/domain/value_objects/workspace_status.py`
- Modify: `backend/src/modules/spaces/domain/value_objects/__init__.py`
- Test: `backend/tests/unit/spaces/test_vo_workspace_status.py`

> 状态字符串来自 AWS 文档；Phase B Task 15 会对照真实集群核验后回填。

- [ ] **Step 1: 写失败测试**

```python
"""Workspace CRD 状态 → 平台 SpaceStatus 映射测试。"""

from src.modules.spaces.domain.value_objects import SpaceStatus, map_workspace_status


class TestMapWorkspaceStatus:
    def test_creating_maps_pending(self) -> None:
        assert map_workspace_status("Creating") is SpaceStatus.PENDING

    def test_running_maps_running(self) -> None:
        assert map_workspace_status("Running") is SpaceStatus.RUNNING

    def test_stopped_maps_stopped(self) -> None:
        assert map_workspace_status("Stopped") is SpaceStatus.STOPPED

    def test_failed_maps_failed(self) -> None:
        assert map_workspace_status("Failed") is SpaceStatus.FAILED

    def test_degraded_maps_failed(self) -> None:
        assert map_workspace_status("Degraded") is SpaceStatus.FAILED

    def test_none_maps_stopped(self) -> None:
        # CRD 不存在 = 无运行实例 = 已停止（同方式一语义）
        assert map_workspace_status(None) is SpaceStatus.STOPPED

    def test_unknown_maps_none(self) -> None:
        assert map_workspace_status("WeirdStatus") is None
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_vo_workspace_status.py -v`
Expected: FAIL — `ImportError: map_workspace_status`

- [ ] **Step 3: 实现**

创建 `workspace_status.py`：

```python
"""HyperPod Workspace CRD 状态映射。

状态字符串源自 AWS 文档（task-governance/create-manage-spaces），
Phase B 安装 add-on 后需对照真实集群 CRD schema 核验。
"""

from .space_enums import SpaceStatus

# Workspace.status.phase → 平台 SpaceStatus
_WORKSPACE_STATUS_MAP = {
    "Creating": SpaceStatus.PENDING,
    "Pending": SpaceStatus.PENDING,
    "Running": SpaceStatus.RUNNING,
    "Stopped": SpaceStatus.STOPPED,
    "Failed": SpaceStatus.FAILED,
    "Degraded": SpaceStatus.FAILED,
}


def map_workspace_status(phase: str | None) -> SpaceStatus | None:
    """映射 Workspace CRD phase 到平台状态。

    None（CRD 不存在）映射为 STOPPED；无法识别的状态返回 None（调用方不变更状态）。
    """
    if phase is None:
        return SpaceStatus.STOPPED
    return _WORKSPACE_STATUS_MAP.get(phase)
```

`__init__.py` 导出 `map_workspace_status`。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_vo_workspace_status.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/domain/value_objects/
git commit -m "feat(spaces): 新增 HyperPod Workspace CRD 状态映射"
```

---

## Task 4: 新增后端异常类型

**Files:**
- Modify: `backend/src/modules/spaces/domain/exceptions.py`
- Modify: `backend/src/modules/spaces/domain/__init__.py`（若导出异常）
- Test: `backend/tests/unit/spaces/test_exceptions_space.py`

- [ ] **Step 1: 写失败测试**

```python
"""Spaces 模块异常测试。"""

from src.modules.spaces.domain.exceptions import (
    HyperPodSpaceBackendError,
    SpaceBackendUnavailableError,
)


class TestHyperPodSpaceBackendError:
    def test_http_status_400(self) -> None:
        err = HyperPodSpaceBackendError(message="CRD apply failed")
        assert err.http_status == 400
        assert err.error_code == "HYPERPOD_SPACE_BACKEND_ERROR"


class TestSpaceBackendUnavailableError:
    def test_http_status_503(self) -> None:
        err = SpaceBackendUnavailableError(message="add-on not installed")
        assert err.http_status == 503
        assert err.error_code == "SPACE_BACKEND_UNAVAILABLE"
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_exceptions_space.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 实现**

在 `exceptions.py` 末尾加入（沿用现有 `@problem` + `@dataclass` 模式）：

```python
@problem(400, "HYPERPOD_SPACE_BACKEND_ERROR")
@dataclass
class HyperPodSpaceBackendError(Problem):
    """HyperPod Space K8s API 操作失败。"""

    message: str


@problem(503, "SPACE_BACKEND_UNAVAILABLE")
@dataclass
class SpaceBackendUnavailableError(Problem):
    """Space 后端不可达（add-on 未装 / 集群不可达）。"""

    message: str
```

若 `domain/__init__.py` 集中导出异常，补充这两个。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_exceptions_space.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/domain/
git commit -m "feat(spaces): 新增 HyperPod backend 异常类型"
```

---

## Task 5: 定义 ISpaceBackendClient 共同接口

**Files:**
- Create: `backend/src/modules/spaces/application/interfaces/space_backend_client.py`
- Modify: `backend/src/modules/spaces/application/interfaces/__init__.py`
- Test: `backend/tests/unit/spaces/test_interface_space_backend.py`

- [ ] **Step 1: 写失败测试**

```python
"""ISpaceBackendClient 接口契约测试。"""

import inspect

from src.modules.spaces.application.interfaces import ISpaceBackendClient


class TestISpaceBackendClient:
    def test_has_required_methods(self) -> None:
        for name in (
            "provision_space",
            "delete_space",
            "start_space",
            "stop_space",
            "describe_space",
            "create_access_url",
        ):
            assert hasattr(ISpaceBackendClient, name)

    def test_methods_are_async(self) -> None:
        assert inspect.iscoroutinefunction(ISpaceBackendClient.provision_space)
        assert inspect.iscoroutinefunction(ISpaceBackendClient.create_access_url)
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_interface_space_backend.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 实现**

创建 `space_backend_client.py`：

```python
"""Space 后端策略接口。

两种开发环境后端（Studio / HyperPod）实现此接口，SpaceService 按 backend 分发。
"""

from abc import ABC, abstractmethod
from typing import Any

from src.modules.spaces.domain.entities import Space


class ISpaceBackendClient(ABC):
    """开发环境后端统一接口。"""

    @abstractmethod
    async def provision_space(self, space: Space) -> dict[str, Any]:
        """创建底层资源并拉起计算。

        Returns:
            需持久化的标识。studio: {"arn": ...}；hyperpod: {"namespace": ..., "workspace_name": ...}
        """

    @abstractmethod
    async def delete_space(self, space: Space) -> None:
        """删除底层资源（幂等）。"""

    @abstractmethod
    async def start_space(self, space: Space) -> None:
        """拉起计算实例。"""

    @abstractmethod
    async def stop_space(self, space: Space) -> None:
        """释放计算实例，保留存储。"""

    @abstractmethod
    async def describe_space(self, space: Space) -> dict[str, Any] | None:
        """查询底层状态，返回 {"status": <平台 SpaceStatus 值>, ...}；不存在返回 None。"""

    @abstractmethod
    async def create_access_url(self, space: Space, conn_type: str) -> str:
        """签发免登录访问 URL。conn_type: web-ui | vscode-remote。"""
```

`__init__.py` 导出 `ISpaceBackendClient`。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_interface_space_backend.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/application/interfaces/ backend/tests/unit/spaces/test_interface_space_backend.py
git commit -m "feat(spaces): 定义 ISpaceBackendClient 共同接口"
```

---

## Task 6: StudioSpaceBackend 适配器（包装现有客户端，迁移编排）

**Files:**
- Create: `backend/src/modules/spaces/infrastructure/external/studio_space_backend.py`
- Modify: `backend/src/modules/spaces/infrastructure/external/__init__.py`
- Test: `backend/tests/unit/spaces/test_svc_studio_backend.py`

> 关键：把现有 `SpaceService.create_space` 里的 Studio 编排（create_space + create_app + orphan 清理）和 stop/start/delete/access 的 SageMaker 调用迁移进此适配器。底层 `SageMakerSpacesClient` 一行不动。

- [ ] **Step 1: 写失败测试**

```python
"""StudioSpaceBackend 适配器测试 —— 验证 Studio 编排被正确封装。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.modules.spaces.infrastructure.external.studio_space_backend import (
    StudioSpaceBackend,
)


def _studio_space() -> Space:
    return Space(
        id="s-1",
        space_name="dev-1",
        owner_id=1,
        backend=SpaceBackend.STUDIO,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        status=SpaceStatus.PENDING,
    )


@pytest.fixture
def mock_sagemaker() -> AsyncMock:
    client = AsyncMock()
    client.create_space.return_value = {"arn": "arn:aws:sagemaker:::space/x"}
    client.create_app.return_value = {"arn": "arn:aws:sagemaker:::app/x"}
    client.describe_app.return_value = {"status": "InService"}
    client.create_presigned_url.return_value = "https://x.studio.us-east-1.sagemaker.aws/..."
    return client


class TestProvision:
    async def test_provision_calls_create_space_then_app(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.provision_space(_studio_space())
        mock_sagemaker.create_space.assert_awaited_once()
        mock_sagemaker.create_app.assert_awaited_once()
        assert "arn" in result

    async def test_provision_orphan_cleanup_on_app_failure(self, mock_sagemaker: AsyncMock) -> None:
        mock_sagemaker.create_app.side_effect = RuntimeError("boom")
        backend = StudioSpaceBackend(mock_sagemaker)
        with pytest.raises(RuntimeError):
            await backend.provision_space(_studio_space())
        mock_sagemaker.delete_space.assert_awaited_once()


class TestDescribe:
    async def test_describe_maps_inservice_to_running(self, mock_sagemaker: AsyncMock) -> None:
        backend = StudioSpaceBackend(mock_sagemaker)
        result = await backend.describe_space(_studio_space())
        assert result["status"] == SpaceStatus.RUNNING.value
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_svc_studio_backend.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 实现**

创建 `studio_space_backend.py`，把 `space_service.py` 中 Studio 编排逻辑搬入。参考现有 `SpaceService` 的 `_IDE_TYPE_MAP`、`_APP_STATUS_MAP`、create/stop/start/delete/get_space_access_url 实现：

```python
"""Studio Spaces 后端适配器 —— 将 SageMakerSpacesClient 适配为 ISpaceBackendClient。"""

from typing import Any

import structlog

from src.modules.spaces.application.interfaces import (
    ISageMakerSpacesClient,
    ISpaceBackendClient,
)
from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import SpaceStatus, SpaceType

logger = structlog.get_logger(__name__)

_IDE_TYPE_MAP = {
    SpaceType.JUPYTER: "jupyterlab",
    SpaceType.VSCODE: "vscode",
    SpaceType.RSTUDIO: "jupyterlab",
}

# SageMaker App 状态 → 平台状态
_APP_STATUS_MAP = {
    "Pending": SpaceStatus.PENDING,
    "InService": SpaceStatus.RUNNING,
    "Deleting": SpaceStatus.STOPPED,
    "Deleted": SpaceStatus.STOPPED,
    "Failed": SpaceStatus.FAILED,
}


class StudioSpaceBackend(ISpaceBackendClient):
    def __init__(self, sagemaker_client: ISageMakerSpacesClient) -> None:
        self._sm = sagemaker_client

    def _ide_type(self, space: Space) -> str:
        return _IDE_TYPE_MAP.get(space.space_type, "jupyterlab")

    async def provision_space(self, space: Space) -> dict[str, Any]:
        ide_type = self._ide_type(space)
        result = await self._sm.create_space(
            name=space.space_name,
            instance_type=space.instance_type.value,
            ide_type=ide_type,
            lifecycle_config_arn=space.lifecycle_config_arn,
            storage_size_gb=space.storage_size_gb,
        )
        try:
            await self._sm.create_app(
                space_name=space.space_name,
                ide_type=ide_type,
                instance_type=space.instance_type.value,
                lifecycle_config_arn=space.lifecycle_config_arn,
            )
        except Exception:
            try:
                await self._sm.delete_space(space.space_name)
            except Exception:
                logger.warning("space_orphan_cleanup_failed", space_name=space.space_name)
            raise
        return {"arn": result.get("arn")}

    async def delete_space(self, space: Space) -> None:
        await self._sm.delete_app(space_name=space.space_name, ide_type=self._ide_type(space))
        await self._sm.delete_space(space.space_name)

    async def start_space(self, space: Space) -> None:
        await self._sm.create_app(
            space_name=space.space_name,
            ide_type=self._ide_type(space),
            instance_type=space.instance_type.value,
            lifecycle_config_arn=space.lifecycle_config_arn,
        )

    async def stop_space(self, space: Space) -> None:
        await self._sm.delete_app(space_name=space.space_name, ide_type=self._ide_type(space))

    async def describe_space(self, space: Space) -> dict[str, Any] | None:
        info = await self._sm.describe_app(space_name=space.space_name, ide_type=self._ide_type(space))
        if not isinstance(info, dict):
            return {"status": SpaceStatus.STOPPED.value}
        mapped = _APP_STATUS_MAP.get(info.get("status", ""))
        return {"status": mapped.value if mapped else None}

    async def create_access_url(self, space: Space, conn_type: str) -> str:
        return await self._sm.create_presigned_url(
            space_name=space.space_name, ide_type=self._ide_type(space)
        )
```

`__init__.py` 导出 `StudioSpaceBackend`。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_svc_studio_backend.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/infrastructure/external/ backend/tests/unit/spaces/test_svc_studio_backend.py
git commit -m "feat(spaces): StudioSpaceBackend 适配器封装 Studio 编排"
```

---

## Task 7: K8s Workspace CRD 低层客户端

**Files:**
- Create: `backend/src/modules/spaces/infrastructure/external/k8s_workspace_client.py`
- Test: `backend/tests/unit/spaces/test_svc_k8s_workspace_client.py`

> 复用 `backend/src/modules/training/infrastructure/kueue/kueue_client.py` 的 ServiceAccount token/CA 解析与 graceful 降级模式。先读那个文件作为模板。

- [ ] **Step 1: 写失败测试**（mock httpx）

```python
"""K8sWorkspaceClient 测试 —— mock httpx 验证 CRD 请求构造。"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.spaces.infrastructure.external.k8s_workspace_client import (
    K8sWorkspaceClient,
)


@pytest.fixture
def client() -> K8sWorkspaceClient:
    return K8sWorkspaceClient(k8s_api_url="https://k8s.test", token="tok")


class TestCreateWorkspace:
    async def test_posts_to_workspaces_endpoint(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.post = AsyncMock(return_value=MagicMock(status_code=201, json=lambda: {"metadata": {"name": "w1"}}))
            inst.post.return_value.raise_for_status = MagicMock()
            await client.create_workspace(
                namespace="dev-spaces",
                name="w1",
                body={"spec": {"desiredStatus": "Running"}},
            )
            url = inst.post.call_args[0][0]
            assert "/apis/workspace.jupyter.org/v1alpha1/namespaces/dev-spaces/workspaces" in url


class TestGetWorkspace:
    async def test_404_returns_none(self, client: K8sWorkspaceClient) -> None:
        with patch("httpx.AsyncClient") as mock_cls:
            inst = mock_cls.return_value.__aenter__.return_value
            inst.get = AsyncMock(return_value=MagicMock(status_code=404))
            result = await client.get_workspace("dev-spaces", "missing")
            assert result is None


class TestUnavailable:
    async def test_no_api_url_returns_none(self) -> None:
        c = K8sWorkspaceClient(k8s_api_url=None, token=None)
        # 无集群配置时降级（开发环境），describe 返回 None
        result = await c.get_workspace("dev-spaces", "w1")
        assert result is None
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_svc_k8s_workspace_client.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 实现**

创建 `k8s_workspace_client.py`，镜像 `KueueClient` 的结构（`_resolve_api_url`/`_resolve_token`/CA 解析），方法覆盖 CRD 操作：`create_workspace`/`get_workspace`/`patch_workspace_desired_status`/`delete_workspace`/`create_workspace_connection`/`get_workspace_connection`。基 path `/apis/workspace.jupyter.org/v1alpha1/namespaces/{ns}/workspaces`；connection path `/apis/connection.workspace.jupyter.org/v1alpha1/namespaces/{ns}/workspaceconnections`。404 返回 None，连接失败返回 None（graceful 降级），其余异常抛 `HyperPodSpaceBackendError`。

> 完整代码以 `KueueClient` 为模板编写（约 120 行）。PATCH 使用 `Content-Type: application/merge-patch+json`。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_svc_k8s_workspace_client.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/infrastructure/external/k8s_workspace_client.py backend/tests/unit/spaces/test_svc_k8s_workspace_client.py
git commit -m "feat(spaces): K8s Workspace CRD 低层 httpx 客户端"
```

---

## Task 8: HyperPodSpaceBackend 实现

**Files:**
- Create: `backend/src/modules/spaces/infrastructure/external/hyperpod_space_backend.py`
- Modify: `backend/src/modules/spaces/infrastructure/external/__init__.py`
- Test: `backend/tests/unit/spaces/test_svc_hyperpod_backend.py`

- [ ] **Step 1: 写失败测试**

```python
"""HyperPodSpaceBackend 测试 —— mock K8sWorkspaceClient 验证 CRD body 与状态映射。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.spaces.domain.entities import Space
from src.modules.spaces.domain.value_objects import (
    SpaceBackend,
    SpaceInstanceType,
    SpaceStatus,
    SpaceType,
)
from src.modules.spaces.infrastructure.external.hyperpod_space_backend import (
    HyperPodSpaceBackend,
    INTERACTIVE_SPACE_PRIORITY_CLASS,
)


def _hp_space() -> Space:
    return Space(
        id="h-1",
        space_name="dev-hp",
        owner_id=1,
        backend=SpaceBackend.HYPERPOD,
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        namespace="dev-spaces",
        queue_name="team-alpha-localqueue",
        workspace_template="sagemaker-jupyter-template",
        status=SpaceStatus.PENDING,
    )


@pytest.fixture
def mock_k8s() -> AsyncMock:
    k8s = AsyncMock()
    k8s.create_workspace.return_value = {"metadata": {"name": "dev-hp"}}
    k8s.get_workspace.return_value = {"status": {"phase": "Running"}}
    k8s.create_workspace_connection.return_value = None
    k8s.get_workspace_connection.return_value = {
        "status": {"workspaceConnectionUrl": "https://ide.dev.example.com/lab"}
    }
    return k8s


class TestProvision:
    async def test_provision_sets_kueue_labels_and_desired_running(self, mock_k8s: AsyncMock) -> None:
        backend = HyperPodSpaceBackend(mock_k8s)
        result = await backend.provision_space(_hp_space())
        body = mock_k8s.create_workspace.call_args.kwargs["body"]
        labels = body["metadata"]["labels"]
        assert labels["kueue.x-k8s.io/queue-name"] == "team-alpha-localqueue"
        assert labels["kueue.x-k8s.io/priority-class"] == INTERACTIVE_SPACE_PRIORITY_CLASS
        assert body["spec"]["desiredStatus"] == "Running"
        assert result["namespace"] == "dev-spaces"
        assert result["workspace_name"] == "dev-hp"


class TestLifecycle:
    async def test_stop_patches_desired_stopped(self, mock_k8s: AsyncMock) -> None:
        backend = HyperPodSpaceBackend(mock_k8s)
        await backend.stop_space(_hp_space())
        mock_k8s.patch_workspace_desired_status.assert_awaited_once()
        assert mock_k8s.patch_workspace_desired_status.call_args.kwargs["desired_status"] == "Stopped"

    async def test_describe_maps_running(self, mock_k8s: AsyncMock) -> None:
        backend = HyperPodSpaceBackend(mock_k8s)
        result = await backend.describe_space(_hp_space())
        assert result["status"] == SpaceStatus.RUNNING.value


class TestAccessUrl:
    async def test_create_access_url_reads_connection_status(self, mock_k8s: AsyncMock) -> None:
        backend = HyperPodSpaceBackend(mock_k8s)
        url = await backend.create_access_url(_hp_space(), conn_type="web-ui")
        assert url == "https://ide.dev.example.com/lab"
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_svc_hyperpod_backend.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 实现**

创建 `hyperpod_space_backend.py`，用 `map_workspace_status` 做状态映射，组装 Workspace CRD body（labels 含 queue-name + priority-class，spec 含 desiredStatus/templateRef/resources）。`create_access_url` 创建 WorkspaceConnection 后轮询 `get_workspace_connection` 读 `status.workspaceConnectionUrl`（带超时上限，超时抛 `SpaceError`）。

```python
INTERACTIVE_SPACE_PRIORITY_CLASS = "interactive-space-priority"
```

> 轮询用固定间隔 + 最大次数（参照 KueueClient 无内置 sleep，可用 `asyncio.sleep` + 上限计数）。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_svc_hyperpod_backend.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/infrastructure/external/ backend/tests/unit/spaces/test_svc_hyperpod_backend.py
git commit -m "feat(spaces): HyperPodSpaceBackend 实现 CRD 生命周期与访问"
```

---

## Task 9: SpaceService 改造为 backend 无关 + 策略分发 + 配额校验

**Files:**
- Modify: `backend/src/modules/spaces/application/services/space_service.py`
- Test: `backend/tests/unit/spaces/test_svc_space.py`（改造现有）

> 这是改动既有工作代码的核心任务。原有 spaces 单测全部保持绿（`tests/unit/spaces/`；注意另有一个 `tests/unit/modules/spaces/` 性能测试树，本计划新测试统一放 `tests/unit/spaces/`）。策略字典 `dict[SpaceBackend, ISpaceBackendClient]` 注入；配额校验仅 hyperpod。

- [ ] **Step 1: 写失败测试**

在 `test_svc_space.py` 新增（保留现有测试）：

```python
class TestBackendDispatch:
    async def test_create_hyperpod_calls_quota_then_hyperpod_backend(self) -> None:
        from src.modules.spaces.domain.value_objects import SpaceBackend

        mock_repo = AsyncMock(spec=ISpaceRepository)
        mock_repo.get_by_name_and_owner.return_value = None
        mock_repo.create.side_effect = lambda s: s
        studio = AsyncMock(spec=ISpaceBackendClient)
        hyperpod = AsyncMock(spec=ISpaceBackendClient)
        hyperpod.provision_space.return_value = {"namespace": "dev-spaces", "workspace_name": "w1"}
        quota = AsyncMock()
        quota.check_quota.return_value = True

        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.STUDIO: studio, SpaceBackend.HYPERPOD: hyperpod},
            quota_checker=quota,
        )
        await service.create_space(
            owner_id=1,
            data={"space_name": "dev-hp", "backend": "hyperpod", "instance_type": "ml.g5.xlarge"},
        )
        quota.check_quota.assert_awaited_once()
        hyperpod.provision_space.assert_awaited_once()
        studio.provision_space.assert_not_awaited()

    async def test_create_hyperpod_quota_exceeded_raises_429(self) -> None:
        from src.modules.spaces.domain.exceptions import SpaceQuotaExceededError
        from src.modules.spaces.domain.value_objects import SpaceBackend

        mock_repo = AsyncMock(spec=ISpaceRepository)
        mock_repo.get_by_name_and_owner.return_value = None
        hyperpod = AsyncMock(spec=ISpaceBackendClient)
        quota = AsyncMock()
        quota.check_quota.return_value = False
        quota.get_available_quota.return_value = 0

        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.HYPERPOD: hyperpod},
            quota_checker=quota,
        )
        with pytest.raises(SpaceQuotaExceededError):
            await service.create_space(
                owner_id=1,
                data={"space_name": "dev-hp", "backend": "hyperpod", "instance_type": "ml.g5.xlarge"},
            )
        hyperpod.provision_space.assert_not_awaited()

    async def test_create_studio_skips_quota(self) -> None:
        from src.modules.spaces.domain.value_objects import SpaceBackend

        mock_repo = AsyncMock(spec=ISpaceRepository)
        mock_repo.get_by_name_and_owner.return_value = None
        mock_repo.create.side_effect = lambda s: s
        studio = AsyncMock(spec=ISpaceBackendClient)
        studio.provision_space.return_value = {"arn": "arn:x"}
        quota = AsyncMock()

        service = SpaceService(
            space_repository=mock_repo,
            backends={SpaceBackend.STUDIO: studio},
            quota_checker=quota,
        )
        await service.create_space(
            owner_id=1,
            data={"space_name": "dev-1", "backend": "studio", "instance_type": "ml.g5.xlarge"},
        )
        quota.check_quota.assert_not_awaited()
```

> 现有测试用旧构造签名 `SpaceService(space_repository=..., sagemaker_client=...)`。改造时需更新现有 fixture `service`/`mock_sagemaker` 为策略字典形式，或保留向后兼容构造。**推荐**：构造改为 `backends: dict` + 可选 `quota_checker`，把现有测试的 `mock_sagemaker` 包进 `StudioSpaceBackend` 或直接 mock 为 `ISpaceBackendClient`。同步更新现有测试 fixture。

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/unit/spaces/test_svc_space.py::TestBackendDispatch -v`
Expected: FAIL

- [ ] **Step 3: 实现**

改造 `space_service.py`：
- 构造签名改为 `__init__(self, space_repository, backends: dict[SpaceBackend, ISpaceBackendClient], quota_checker: IQuotaChecker | None = None, metrics_service=None)`。
- `create_space`：去重 → 建实体（含 `backend`，从 `data.get("backend", "studio")`）→ 若 hyperpod 且 quota_checker 非空则 `check_quota`（资源量用实体 `get_resource_requirements`）→ `backend = self._backends[space.backend]` → `provision_space` → 用返回 dict 回填 arn/namespace/workspace_name → 计 SLA → 存库。
- `start_space`/`stop_space`/`delete_space`/`get_space_access_url`：lazy sync 改为调 `backend.describe_space`，操作改为调 `backend.start_space`/`stop_space`/`delete_space`/`create_access_url`。状态映射用返回的 `status` 字段（已是平台值）。
- 删去 service 内 `_IDE_TYPE_MAP`/`_APP_STATUS_MAP`/`_ensure_app_not_deleting`（已移入 StudioSpaceBackend；若 ensure_app_not_deleting 是 Studio 专属逻辑也下移）。

> 保留 metrics 上报、SLA 计时、状态机调用（backend 无关）。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/unit/spaces/test_svc_space.py -v`
Expected: PASS（全部，含改造后的原有测试）

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/application/services/space_service.py backend/tests/unit/spaces/test_svc_space.py
git commit -m "refactor(spaces): SpaceService 改为 backend 策略分发 + HyperPod 配额校验"
```

---

## Task 10: ORM 模型 + 数据库迁移

**Files:**
- Modify: `backend/src/modules/spaces/infrastructure/models/space_model.py`
- Modify: `backend/src/modules/spaces/infrastructure/repositories/space_repository_impl.py:24-32`
- Create: `backend/alembic/versions/20260613_HHMMSS_add_space_backend_fields.py`
- Test: `backend/tests/integration/spaces/test_repo_space.py`（若存在则扩展；否则在迁移后用现有集成测试验证）

- [ ] **Step 1: 写失败测试**（集成，验证持久化新字段）

在 spaces 集成测试中加入（`tests/integration/spaces/` 不存在则创建 `test_repo_space.py`）。`owner_id` 需用真实用户——复用 `tests/integration/conftest.py` 或就近模块集成测试的用户 fixture（FK 到 `users.id` 强制存在）：

```python
async def test_create_and_read_hyperpod_space_persists_backend(space_repository) -> None:
    from src.modules.spaces.domain.entities import Space
    from src.modules.spaces.domain.value_objects import SpaceBackend, SpaceInstanceType, SpaceType, SpaceStatus

    space = Space(
        space_name="hp-persist",
        owner_id=<existing_user_id>,
        backend=SpaceBackend.HYPERPOD,
        namespace="dev-spaces",
        queue_name="q1",
        workspace_template="tpl1",
        instance_type=SpaceInstanceType.ML_G5_XLARGE,
        space_type=SpaceType.JUPYTER,
        status=SpaceStatus.PENDING,
    )
    created = await space_repository.create(space)
    fetched = await space_repository.get_by_id(created.id)
    assert fetched.backend is SpaceBackend.HYPERPOD
    assert fetched.namespace == "dev-spaces"
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/integration/spaces/test_repo_space.py -v`
Expected: FAIL — 列不存在 / 实体无字段持久化

- [ ] **Step 3: 实现**

`space_model.py` 加列（`backend` 用 `Enum(SpaceBackend)` 默认 STUDIO；其余 `String` nullable）：

```python
from src.modules.spaces.domain.value_objects import SpaceBackend  # 加 import

    backend: Mapped[SpaceBackend] = mapped_column(
        Enum(SpaceBackend), nullable=False, default=SpaceBackend.STUDIO,
        index=True, comment="开发环境后端类型",
    )
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="HyperPod CRD namespace")
    queue_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Kueue local queue")
    workspace_template: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="WorkspaceTemplate 引用")
```

`space_repository_impl.py` 的 `_updatable_fields` 加 `"backend"`, `"namespace"`, `"queue_name"`, `"workspace_template"`。

生成迁移：`cd backend && alembic revision --autogenerate -m "add space backend fields"`，重命名为 `20260613_HHMMSS_add_space_backend_fields.py`，检查 `upgrade()` 含 4 个 `add_column`，`backend` 列 server_default 设为 `'STUDIO'`（与 Enum 按 name 持久化一致——参照现有迁移 `20260222_100300_revert_enum_to_uppercase.py` 的枚举大小写约定，**务必核对**存量枚举列是按 name 还是 value 存储）。

- [ ] **Step 4: 运行迁移 + 测试确认通过**

Run: `cd backend && alembic upgrade head && pytest tests/integration/spaces/test_repo_space.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/infrastructure/ backend/alembic/versions/ backend/tests/integration/spaces/
git commit -m "feat(spaces): development_spaces 表新增 backend 等字段及迁移"
```

---

## Task 11: API schema + 端点 + 依赖注入

**Files:**
- Modify: `backend/src/modules/spaces/api/schemas/requests.py`
- Modify: `backend/src/modules/spaces/api/schemas/responses.py`
- Modify: `backend/src/modules/spaces/api/dependencies.py`
- Test: `backend/tests/integration/spaces/test_api_space.py`（**新建** —— `tests/integration/spaces/` 目录尚不存在，需创建；override 模式参照已有的 `tests/integration/datasets/` 中 `app.dependency_overrides[...]` 用法）

- [ ] **Step 1: 写失败测试**

```python
async def test_create_hyperpod_space_routes_to_hyperpod_backend(client, auth_headers) -> None:
    resp = await client.post(
        "/api/v1/spaces",
        headers=auth_headers,
        json={"space_name": "hp-api", "backend": "hyperpod", "instance_type": "ml.g5.xlarge"},
    )
    assert resp.status_code == 201
    assert resp.json()["backend"] == "hyperpod"
```

> 集成测试需 mock 掉真实 K8s 调用——在 dependency override 注入 mock backend。`tests/integration/spaces/` 目录尚不存在，本任务创建；`app.dependency_overrides[get_space_service]` 的写法参照 `tests/integration/datasets/` 下已有的集成测试。

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && pytest tests/integration/spaces/test_api_space.py -k hyperpod -v`
Expected: FAIL

- [ ] **Step 3: 实现**

- `requests.py`：`CreateSpaceRequest` 加 `backend: SpaceBackendEnum = SpaceBackendEnum.STUDIO`（新增 `SpaceBackendEnum(str, Enum)`）。
- `responses.py`：`SpaceSummary` 加 `backend: SpaceBackendEnum`；`SpaceDetail` 加 `namespace`/`queue_name`/`workspace_template`（`str | None`）。
- `dependencies.py`：`get_space_service` 组装两个 backend + quota_checker：

```python
def get_studio_backend(sm=Depends(get_sagemaker_client)) -> ISpaceBackendClient:
    return StudioSpaceBackend(sm)

def get_hyperpod_backend() -> ISpaceBackendClient:
    return HyperPodSpaceBackend(K8sWorkspaceClient())

async def get_space_service(session=Depends(get_db), ...) -> SpaceService:
    quota_checker = QuotaCheckerImpl(ResourceQuotaRepository(session))  # 跨模块组装
    return SpaceService(
        space_repository=SpaceRepository(session),
        backends={SpaceBackend.STUDIO: studio_backend, SpaceBackend.HYPERPOD: hyperpod_backend},
        quota_checker=quota_checker,
        metrics_service=...,
    )
```

> 跨模块导入 `QuotaCheckerImpl`/`ResourceQuotaRepository` 仅在 API 层 dependencies（composition root），符合架构例外。

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && pytest tests/integration/spaces/test_api_space.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/modules/spaces/api/
git commit -m "feat(spaces): API 支持 backend 字段与双后端依赖组装"
```

---

## Task 12: 后端全量校验 + OpenAPI 契约更新

**Files:**
- Create: `specs/001-ai-training-platform/contracts/spaces-api.yaml`（**新建** —— 该目录当前只有 datasets/monitoring/resource-quotas/training-jobs/users，无 spaces 契约；参照 `training-jobs-api.yaml` 的结构新建）

- [ ] **Step 1: 全量校验**

Run: `cd backend && black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85`
Expected: 全绿。修复任何回归（特别是 Task 9 改造引入的）。

- [ ] **Step 2: 新建 OpenAPI 契约**

新建 `spaces-api.yaml`，覆盖 spaces 全部端点（list/create/get/start/stop/access-url/delete）；create 请求含 `backend`，响应 schema 含 `backend` + HyperPod 字段（`namespace`/`queue_name`/`workspace_template`）。结构参照同目录 `training-jobs-api.yaml`。

- [ ] **Step 3: 提交**

```bash
git add backend/ specs/
git commit -m "test(spaces): 后端全量校验通过 + 更新 spaces OpenAPI 契约"
```

---

## Task 13: 前端 —— 类型、创建选型、列表区分、访问校验

**Files:**
- Modify: `frontend/src/features/spaces/types/index.ts`
- Modify: `frontend/src/features/spaces/api/spaceApi.ts`
- Modify: `frontend/src/features/spaces/api/queries.ts:123-149`
- Modify: `frontend/src/features/spaces/pages/CreateSpacePage.tsx`
- Modify: `frontend/src/features/spaces/pages/SpaceListPage.tsx:160-200`
- Test: `frontend/tests/unit/features/spaces/CreateSpacePage.test.tsx`、`SpaceListPage.test.tsx`

- [ ] **Step 1: 写失败测试**

`CreateSpacePage.test.tsx` 加：选择「HyperPod 集群」环境类型后，提交请求体含 `backend: 'hyperpod'`，且显示配额 Alert。
`SpaceListPage.test.tsx` 加：列表渲染含「环境类型」列，HyperPod 行显示对应 Badge。

```typescript
it('选择 HyperPod 环境类型后提交 backend=hyperpod', async () => {
  const user = userEvent.setup();
  render(<CreateSpacePage />);
  // 打开环境类型 Select，选 HyperPod 集群
  await user.click(screen.getByLabelText('环境类型'));
  await user.click(screen.getByText(/HyperPod 集群/));
  await user.type(screen.getByLabelText('空间名称'), 'hp-space');
  await user.click(screen.getByRole('button', { name: '创建空间' }));
  // 断言 mutation 收到 backend: 'hyperpod'（mock createSpace 验证）
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/unit/features/spaces --run`
Expected: FAIL

- [ ] **Step 3: 实现**

- `types/index.ts`：加 `export type SpaceBackend = 'studio' | 'hyperpod';`，`SpaceSummary`/`SpaceDetail` 加 `backend`、HyperPod 可空字段，`SPACE_BACKEND_LABELS`，`CreateSpaceRequest` 加 `backend?`。
- `spaceApi.ts`：`createSpace` 已透传 data，无需改（确认 backend 在 body）。
- `queries.ts`：`useOpenSpaceIDE` 安全校验改为「仅校验 `https:` 协议 + 非空 host」（去掉硬编码 `.sagemaker.aws`）；保留同步开窗 + 写 URL 模式。
- `CreateSpacePage.tsx`：表单顶部加「环境类型」`Select`（studio/hyperpod）；选 hyperpod 时显示 Cloudscape `Alert`（占用团队配额提示）；提交时带 `backend`。
- `SpaceListPage.tsx`：`columnDefinitions` 加「环境类型」列，用 `Badge` 显示 `SPACE_BACKEND_LABELS[item.backend]`。

- [ ] **Step 4: 运行确认通过 + lint**

Run: `cd frontend && npm test -- tests/unit/features/spaces --run && npm run lint`
Expected: PASS + 无警告

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/spaces/ frontend/tests/unit/features/spaces/
git commit -m "feat(spaces): 前端支持 backend 选型、列表区分与访问 URL 校验放宽"
```

---

# Phase B：基础设施就绪

> 依赖真实 AWS 集群 `ai-platform-dev-eks`。可与 Phase A 并行。

## Task 14: 安装 SageMaker Spaces add-on

**Files:**
- Modify/Create: `infrastructure/` 下 add-on 安装清单（具体位置先探查 `infrastructure/cdk` 与 K8s manifests 现状）

- [ ] **Step 1: 探查与文档核实**

Run: `aws sagemaker list-clusters --region us-east-1` 确认集群；查阅 `https://docs.aws.amazon.com/sagemaker/latest/dg/operator-install.html` 核实依赖（EKS Pod Identity Agent、Cert-manager、EBS CSI Driver；web UI 需 ALB Controller + External DNS + Route53 + SSL）。
检查集群已装组件：`kubectl get pods -A | grep -iE "cert-manager|ebs-csi|load-balancer|external-dns"`。

- [ ] **Step 2: 安装 add-on（Custom install，启用 web UI）**

按官方文档安装。验证：`kubectl get crd | grep workspace.jupyter.org` 应出现 `workspaces.workspace.jupyter.org`。

- [ ] **Step 3: 验证 add-on 运行**

Run: `kubectl get pods -n sagemaker-spaces-system`（或文档指定的 operator namespace `jupyter-k8s-system`）
Expected: operator pod Running

- [ ] **Step 4: 记录到基础设施文档并提交**

```bash
git add infrastructure/
git commit -m "feat(infra): 安装 SageMaker Spaces add-on 与 web UI 依赖"
```

---

## Task 15: 核验真实 CRD schema 并回填状态映射

**Files:**
- Modify（按需）: `backend/src/modules/spaces/domain/value_objects/workspace_status.py`
- Modify（按需）: `hyperpod_space_backend.py` 的 CRD body / connection status 字段名

- [ ] **Step 1: 创建一个测试 Workspace 并 dump 真实 schema**

```bash
kubectl explain workspace.spec --recursive
kubectl get crd workspaces.workspace.jupyter.org -o yaml | grep -A5 "phase\|status"
```

- [ ] **Step 2: 核对状态枚举值与 connection URL 字段名**

对照 Task 3 的 `_WORKSPACE_STATUS_MAP` 与 Task 8 的 `status.workspaceConnectionUrl`、`spec.desiredStatus`。若真实字段名不同则修正。

- [ ] **Step 3: 修正后重跑相关单测**

Run: `cd backend && pytest tests/unit/spaces/test_vo_workspace_status.py tests/unit/spaces/test_svc_hyperpod_backend.py -v`
Expected: PASS

- [ ] **Step 4: 提交（如有修正）**

```bash
git add backend/src/modules/spaces/
git commit -m "fix(spaces): 按真实集群 CRD schema 校准 Workspace 状态映射"
```

---

## Task 16: 配置 Kueue 治理 + RBAC

**Files:**
- Create/Modify: `infrastructure/` 下 K8s manifests（ClusterQueue/LocalQueue/PriorityClass/WorkspaceTemplate/RBAC）

- [ ] **Step 1: 创建 interactive-space priority-class（权重 100）**

参照设计 §5.2 与 AWS `task-governance.md`。`dev-spaces` namespace 配 LocalQueue 关联团队 ClusterQueue；priority-class 权重 100（高于训练 75）。

- [ ] **Step 2: 创建 WorkspaceTemplate（admin 蓝图）**

JupyterLab + Code Editor 模板，含 defaultImage/allowedImages/defaultResources/priority-class label（参照设计 §2.3 的 YAML）。

- [ ] **Step 3: 配置后端 Pod ServiceAccount RBAC**

授予 `workspace.jupyter.org` workspaces 与 `connection.workspace.jupyter.org` workspaceconnections 的 get/list/create/patch/delete 权限。

- [ ] **Step 4: 验证**

Run: `kubectl get clusterqueue,localqueue -n dev-spaces && kubectl get workspacetemplate -A`
Expected: 队列与模板就绪。`kubectl auth can-i create workspaces --as=system:serviceaccount:<backend-ns>:<sa>` → yes

- [ ] **Step 5: 提交**

```bash
git add infrastructure/
git commit -m "feat(infra): 配置 HyperPod Spaces Kueue 治理与后端 RBAC"
```

---

# Phase C：真实 AWS E2E

## Task 17: HyperPod Space 真实生命周期 E2E

**Files:**
- Create: `frontend/e2e/tests/spaces-hyperpod-remote.spec.ts`
- 参照: `frontend/e2e/tests/spaces-remote.spec.ts`（方式一 E2E 样板）

> 依赖 Phase B 完成。用 CPU 实例控制成本（对齐近期 `ml.t3.medium` E2E 改造）。

- [ ] **Step 1: 写 E2E（对称方式一）**

创建 HyperPod Space → 列表显示（环境类型=HyperPod）→ 等待 Kueue admission 至 running → 打开 web UI 验证落地集群 IDE 域（非登录页）→ stop → delete。断言真实 CRD 生命周期。

- [ ] **Step 2: 运行 E2E**

Run: `cd frontend && npm run test:e2e -- spaces-hyperpod-remote`
Expected: PASS（真实 AWS）

- [ ] **Step 3: 验证残留清理**

确认测试后 `kubectl get workspaces -n dev-spaces` 无残留；Kueue 配额已释放。

- [ ] **Step 4: 提交**

```bash
git add frontend/e2e/
git commit -m "test(spaces): HyperPod Space 真实 AWS 生命周期 E2E"
```

---

## 完成标准

- [ ] Phase A：后端 `black/ruff/mypy/pytest --cov-fail-under=85` 全绿；前端 `npm test` + `npm run lint` 全绿
- [ ] 方式一现有功能零回归（原有 spaces 单测 + E2E 仍绿）
- [ ] Phase B：`workspace.jupyter.org` CRD 已装，Kueue 治理与 RBAC 就绪
- [ ] Phase C：HyperPod Space 真实 AWS E2E 通过，与方式一对称
- [ ] 新建 `spaces-api.yaml` OpenAPI 契约，含 backend 字段

## 范围边界（YAGNI，重申自设计 §10）

- 不做方式一↔方式二迁移、自定义镜像构建、GPU MIG 分区、方式一重构（仅适配封装）。
