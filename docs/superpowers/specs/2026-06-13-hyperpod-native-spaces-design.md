# 设计文档：HyperPod 原生 Spaces 开发环境

> **状态**：已批准（待 spec 评审）
> **日期**：2026-06-13
> **范围**：在现有 `spaces` 模块内新增第二种在线开发环境创建方式——基于 SageMaker HyperPod 原生 Spaces add-on，与已实现的 SageMaker Studio Spaces（方式一）端到端对称。

---

## 1. 背景与目标

### 1.1 现状

平台已实现**方式一：SageMaker Studio Spaces**，端到端完整（后端能力 + API + 前端 UI + 真实 AWS E2E）：

- 后端 `SageMakerSpacesClient`（aioboto3）走 SageMaker Studio API：`create_space`（写配置 + EBS 存储）→ `create_app`（拉起真实计费的计算实例）→ `create_presigned_domain_url`（签发免登录 URL 直达 JupyterLab）。
- 计算实例**独立计费、不消耗 HyperPod 集群算力**。
- 前端 `spaces` 模块，状态机 `pending → running → stopped/failed/deleted`，以 SageMaker App 状态为事实源做 lazy sync。

### 1.2 目标

新增**方式二：HyperPod 原生 Spaces**，让算法工程师可选择在 HyperPod EKS 集群上创建在线开发环境（JupyterLab / Code Editor）。两种方式**互补共存，由用户按场景选择**。

### 1.3 三个已确认的核心决策

| 决策 | 选择 | 含义 |
|------|------|------|
| 两种方式关系 | **互补共存，按场景选** | 统一数据模型 + `backend` 判别字段；创建时用户选类型；两者长期并存 |
| 集群资源治理 | **完整纳入 Task Governance** | HyperPod Space 像训练任务一样走配额校验 + Kueue 调度 + 可被高优先级抢占（实为保护开发会话） |
| 交付范围 | **端到端完整功能** | 后端 client/service/API + 前端创建选型与列表区分 + 真实 AWS E2E，与方式一对称 |
| 访问方式 | **Web UI + 本地 VS Code 都支持** | 影响 add-on 安装时的依赖配置 |

---

## 2. 核实到的技术现实（带证据）

> 以下事实通过 AWS 官方文档与实际集群状态核实，是设计的依据，而非假设。

### 2.1 两种方式技术栈对比

| 维度 | 方式一（Studio Spaces） | 方式二（HyperPod 原生 Spaces） |
|------|------|------|
| 编程接口 | SageMaker Studio API（aioboto3） | **K8s CRD** `workspace.jupyter.org/v1alpha1` kind `Workspace` |
| 计算位置 | 独立计费实例，**不占集群** | **集群节点**，消耗 HyperPod GPU/CPU |
| 生命周期 | `create_space` → `create_app` → `delete` | `spec.desiredStatus: Running/Stopped` 切换 |
| 免登录访问 | `create_presigned_domain_url` | 创建 `WorkspaceConnection` CRD → 读 `status.workspaceConnectionUrl` |
| 配额治理 | 无（独立实例） | **Kueue 原生**：priority-class + ClusterQueue 配额 + 抢占 |

### 2.2 HyperPod Spaces CRD 操作（AWS 文档确认）

- **创建**：`POST /apis/workspace.jupyter.org/v1alpha1/namespaces/{ns}/workspaces`，`spec.desiredStatus: Running` + `spec.templateRef`（引用 admin 配置的 `WorkspaceTemplate`）。
- **启停**：`PATCH workspaces/{name}` merge `spec.desiredStatus: Running|Stopped`。
- **删除**：`DELETE workspaces/{name}`。
- **访问**：`POST .../workspaceconnections`（kind `WorkspaceConnection`，`workspaceConnectionType: web-ui|vscode-remote`），读 `status.workspaceConnectionUrl`。
- HyperPod CLI（`hyp create hyp-space`）与 kubectl 均为对 CRD 的封装。

### 2.3 Task Governance 是 add-on 原生能力（AWS 文档 `task-governance.md`）

- `WorkspaceTemplate` CRD 支持 `kueue.x-k8s.io/priority-class` label。
- 推荐优先级：**交互式空间 100 > 训练 75 > 评估 50 > 批处理 25**。
- 交互式空间可抢占低优先级任务，保护开发会话不被中断。
- 资源共享策略：Strict（不借不被借）vs Flexible（借出但不被借/不在可回收资源上运行）。

### 2.4 集群现状（关键缺口）

| 项 | 状态 |
|------|------|
| HyperPod 集群 `ai-platform-dev-hyperpod`（EKS `ai-platform-dev-eks`） | ✅ InService |
| Kueue（`kueue.x-k8s.io` CRD） | ✅ 已装 |
| `dev-spaces` namespace | ✅ 存在 |
| 训练用 Kueue 队列 | ✅ 在线 |
| **Spaces add-on（`workspace.jupyter.org` CRD）** | ❌ **未安装——任何方案的前置基础设施任务** |

### 2.5 可复用的现有样板

- `backend/src/modules/training/infrastructure/kueue/kueue_client.py`：httpx + Pod ServiceAccount token 异步调 K8s API，开发环境 graceful 降级——**方式二管理 CRD 的现成模式**。
- 方式一 `spaces` 模块的 lazy sync 状态同步架构、`@problem` 异常体系、前端 TanStack Query 模式、真实 AWS E2E 框架。

---

## 3. 架构与数据模型

### 3.1 模块归属

在现有 `backend/src/modules/spaces` 内扩展，**不新建模块**。两种 backend 共享同一 `Space` 实体、仓库、API 路由，差异收敛到「策略客户端」一层。

### 3.2 领域实体变更

**`domain/value_objects/space_enums.py`** 新增：

```python
class SpaceBackend(Enum):
    STUDIO = "studio"
    HYPERPOD = "hyperpod"
```

**`domain/entities/space.py`** 新增字段：

```python
backend: SpaceBackend = SpaceBackend.STUDIO   # 判别字段，默认 studio 向后兼容
namespace: str | None = None                  # 仅 hyperpod：CRD 所在 K8s namespace
queue_name: str | None = None                 # 仅 hyperpod：Kueue local queue
workspace_template: str | None = None         # 仅 hyperpod：WorkspaceTemplate 引用
# 现有 sagemaker_space_arn / lifecycle_config_arn 保持，仅 studio 使用
```

### 3.3 统一状态机

两种 backend 共用现有 `SpaceStatus`（`pending → running → stopped/failed/deleted`）。HyperPod `Workspace.status` 映射：

| Workspace CRD 状态 | 平台 SpaceStatus |
|------|------|
| Creating / Pending | pending |
| Running | running |
| Stopped | stopped |
| Failed / Degraded | failed |
| (CRD 不存在) | stopped |

与方式一「以真实资源状态为事实源做 lazy sync」同构——事实源从 SageMaker App 换成 `Workspace` CRD。

> **规划阶段需验证**：add-on 尚未安装（§2.4），上表的 CRD 状态字段名（`status.workspaceConnectionUrl`）与状态枚举值（`Creating/Running/Stopped/Failed/Degraded`）来自 AWS 文档，需在「基础设施就绪」阶段对照真实集群 CRD schema 核验后再固化映射表——§3.3 的状态映射依赖这些精确字符串。

### 3.4 数据库迁移

`development_spaces` 表增量加列（Alembic）：`backend`（默认 `'studio'`，存量行自动归类）、`namespace`、`queue_name`、`workspace_template`。对存量方式一空间零影响。

### 3.5 前端类型对齐

`SpaceSummary`/`SpaceDetail` 加 `backend` 字段；`SPACE_BACKEND_LABELS = { studio: 'SageMaker Studio', hyperpod: 'HyperPod 集群' }`；HyperPod 专属可空字段 `namespace`/`queue_name`/`workspace_template` 仅详情展示。

---

## 4. 后端组件与 K8s 集成

### 4.1 共同接口（策略模式）

新增 `application/interfaces/space_backend_client.py`：

```python
class ISpaceBackendClient(ABC):
    async def provision_space(self, space: Space) -> dict      # 创建底层资源，返回需持久化的标识
    async def delete_space(self, space: Space) -> None         # 幂等删除
    async def start_space(self, space: Space) -> None          # 拉起计算
    async def stop_space(self, space: Space) -> None           # 释放计算、保留存储
    async def describe_space(self, space: Space) -> dict | None # {status,...}，不存在返回 None
    async def create_access_url(self, space: Space, conn_type: str) -> str
```

> `provision_space` 返回 `dict` 沿用现有 `ISageMakerSpacesClient` 风格（`dict[str, Any]`）。规划阶段明确各 backend 返回的 key：studio 返回 `{"arn": ...}`（写入 `sagemaker_space_arn`），hyperpod 返回 `{"namespace": ..., "workspace_name": ...}`（写入对应字段），让 service 知道该持久化什么。

### 4.2 两个实现，service 对称分发

- **`StudioSpaceBackend`**（`infrastructure/external/`）：将现有 `SageMakerSpacesClient`（**底层 aioboto3 客户端一行不动**，已通过真实 AWS E2E 验证）适配到 `ISpaceBackendClient`。把目前散落在 `SpaceService.create_space` 的 Studio 独有编排（`create_space` + `create_app` + 失败时 orphan 清理）**上移到此适配器**，使 service 变为 backend 无关。
- **`HyperPodSpaceBackend`**（`infrastructure/external/`）：httpx → K8s API 实现方式二（见 §4.3）。
- **`SpaceService`** 持有 `dict[SpaceBackend, ISpaceBackendClient]`，按 `space.backend` 分发（`self._backends[space.backend]`），杜绝 service 内 if/else，新增第三种 backend 时 service 零改动（开闭原则）。
- **跨切面平台逻辑**（去重、SLA 计时、状态机、metrics 上报）留在 service，backend 无关；**实现细节**（orphan 清理）进各自适配器。

### 4.3 方式二客户端：httpx → K8s API（关键决策，非偏好）

选 httpx 直连而非 `sagemaker.hyperpod` SDK，依据：

| 维度 | httpx → K8s API（选用） | sagemaker.hyperpod SDK |
|------|------|------|
| 异步 | ✅ 原生 async（符合项目强制规范） | ❌ 同步，需 `run_in_executor`（规范禁止） |
| 集群上下文 | ✅ Pod ServiceAccount token，无需 kubeconfig | ❌ 需 `set_cluster_context` 配 kubeconfig，容器内不可靠 |
| CRD 覆盖 | ✅ 直接操作 Workspace/WorkspaceConnection/Template | ⚠️ `HpSpace` 对 access/template 覆盖待验证 |
| 现有样板 | ✅ `KueueClient` 同款 token+httpx 模式（已生产验证） | 训练 job 用，但 space 模块未引入 |

> 注：训练模块用同步 SDK 提交 job 是既有妥协（在 async 函数内调同步 SDK 阻塞事件循环），不复制到新模块。

**核心操作**（全部 httpx 调 K8s API Server，复用 `KueueClient` 的 token/CA 解析）：

- **provision**：`POST .../workspaces`，body 含 `spec.desiredStatus: Running`、`spec.templateRef`、资源 requests/limits、Kueue priority-class label。
- **start/stop**：`PATCH workspaces/{name}` merge `spec.desiredStatus`。
- **delete**：`DELETE workspaces/{name}`，404 幂等。
- **describe**：`GET workspaces/{name}`，读 `status` 映射；不存在返回 None。
- **create_access_url**：`POST .../workspaceconnections`，轮询读 `status.workspaceConnectionUrl`。

### 4.4 依赖注入

`api/dependencies.py` 新增 `get_hyperpod_spaces_client()`；`get_space_service` 注入两个 backend 组装成字典传给 service。

### 4.5 异常

复用 `SpaceError`/`InvalidSpaceStateError`/`SpaceQuotaExceededError`；新增 `HyperPodSpaceBackendError`（K8s API 失败，400）、`SpaceBackendUnavailableError`（add-on 未装/集群不可达，503）。

### 4.6 架构合规

`HyperPodSpaceBackend` 在 `infrastructure/external/`（httpx 属基础设施）；接口在 application 层。符合 Clean Architecture 与 SDK-First（K8s REST 无成熟异步 SDK 时 httpx 薄封装 < 100 行为规范允许）。

---

## 5. 配额治理与生命周期

### 5.1 创建时配额校验链（仅 hyperpod；studio 跳过——不占集群）

```
create_space(backend=hyperpod):
  1. 去重检查（backend 无关）
  2. 分流 → HyperPodSpaceBackend.provision:
     a. 通过 shared IQuotaChecker 校验配额（复用 quotas 模块，与训练任务同源）
     b. 配额不足 → SpaceQuotaExceededError(429)
     c. POST Workspace CRD，带:
        - kueue.x-k8s.io/queue-name label → 团队 local queue
        - kueue.x-k8s.io/priority-class label → interactive-space-priority(权重 100)
        - resources requests/limits
  3. 计 SLA、存库
```

> **规划阶段需解决的集成细节**：现有 `IQuotaChecker`（`shared/domain/interfaces/quota_checker.py`）是**按 `user_id` 设计**的（`check_quota(user_id, resource_type, amount) -> bool`），而 Kueue ClusterQueue 是**团队范围**的。规划时需决定二者映射方式：(a) 解析 user→team 后查团队配额，或 (b) 将 `IQuotaChecker` 校验作为前置软门，把 Kueue admission 作为真正的硬门（推荐——避免与 Kueue 重复造配额逻辑，前者给用户即时反馈，后者是事实裁决者）。实现者不应假设一个团队键的方法签名。

### 5.2 治理策略（AWS 文档推荐）

- **优先级**：交互式空间 100 > 训练 75 > 评估 50 > 批处理 25。开发会话可抢占低优先级训练任务，保护工程师不被中断。
- **资源共享**：**Flexible Resource Sharing**——空闲时允许其他团队借用开发配额，但开发空间自身禁止借用（不在可回收资源上运行），避免被意外驱逐。治理与体验的平衡点。

### 5.3 生命周期与配额影响

| 操作 | HyperPod 行为 | 配额影响 |
|------|------|------|
| create | POST Workspace `desiredStatus: Running` + Kueue admission | 占用配额 |
| stop | PATCH `desiredStatus: Stopped`，Pod 释放、PVC 保留 | 释放算力配额 |
| start | PATCH `desiredStatus: Running`，重新 Kueue admission | 重新占用 |
| delete | DELETE Workspace CRD + PVC | 完全释放 |
| 状态读取 | lazy sync：describe CRD `status` → 平台状态 | 反映 admission（`pending` = 排队/被抢占） |

### 5.4 治理可见性

HyperPod Space 详情暴露 Kueue admission 状态（复用 `KueueClient._parse_workload` 的 admitted/quota_reserved/pending 解析），让工程师看到「因配额不足排队中」而非空转——与训练任务调试页体验一致。

---

## 6. 前端与访问流

### 6.1 契约对齐（`types/index.ts`）

新增 `SpaceBackend = 'studio' | 'hyperpod'`；`SpaceSummary`/`SpaceDetail` 加 `backend`；`SPACE_BACKEND_LABELS`；HyperPod 专属可空字段。

### 6.2 创建页（`CreateSpacePage.tsx`）

表单顶部加「环境类型」`Select`（单页切换，非独立入口/向导分叉）：

- **Studio Spaces**（独立实例·按需计费·不占集群）——分支表单保持现状。
- **HyperPod 集群**（共享集群算力·纳入团队配额）——实例选项切换为集群节点规格，展示「团队队列」，加 Cloudscape `Alert` 说明「将占用团队 ClusterQueue 配额，空闲资源会被回收」。

### 6.3 列表 / 详情页

列表加「环境类型」列（`Badge`：Studio / HyperPod）；详情页 HyperPod 空间额外展示 Kueue admission 状态区块（排队中/已准入/被抢占）。

### 6.4 访问流安全（关键修正）

现有 `useOpenSpaceIDE` 硬编码白名单 `.sagemaker.aws`，但 HyperPod 访问 URL 是 admin 配的自定义 DNS 域（Route53 + External DNS），**会被现有检查拦截**。

**改为**：后端在 `access-url` 响应返回完整可信 URL，前端只校验 `https:` 协议 + 非空 host。理由：HyperPod 自定义 DNS 域部署期才确定，硬编码进前端会随环境漂移；开放重定向防护由后端保证（URL 来自可信 K8s API 响应，非用户输入）。

### 6.5 复用现状

- `useSpaces` 的 `pending → 10s 轮询` 对两种 backend 通用（Kueue admission 也表现为 pending），无需改动。
- `spaceApi.ts` 的 `createSpace` 请求体加可选 `backend`；start/stop/delete/access-url 端点路径不变（统一实体，后端按存储的 backend 自动分流）。

---

## 7. 基础设施前置任务

> 核实确认：`workspace.jupyter.org` CRD 未安装。这些是方式二实现的前置依赖。

| 任务 | 内容 | 依赖 |
|------|------|------|
| 装 Spaces add-on | `ai-platform-dev-eks` 安装 SageMaker Spaces add-on（Custom install，启用 web UI） | EKS Pod Identity Agent、Cert-manager、EBS CSI Driver（部分需核验） |
| Web UI 访问依赖 | AWS Load Balancer Controller + External DNS + Route53 域 + SSL 证书 | 上一项 |
| 本地 VS Code 依赖 | SSM Advanced On-Premises Instance 注册（按计算小时计费） | add-on remote access 配置 |
| Kueue 治理配置 | `dev-spaces` 的 ClusterQueue/LocalQueue + `interactive-space-priority`(100) priority-class + WorkspaceTemplate | Kueue（已装） |
| EKS 访问授权 | 后端 Pod ServiceAccount 增加 `workspace.jupyter.org` / `WorkspaceConnection` 的 RBAC 权限 | add-on |

纳入 `infrastructure/` 子项目（CDK + K8s manifests）。**实现计划显式区分「基础设施就绪」与「应用层编码」**：应用层 TDD 可先用 mock K8s API 推进，E2E 阶段才依赖真实 add-on。

---

## 8. 错误处理

| 场景 | 处理 | HTTP |
|------|------|------|
| add-on 未装 / 集群不可达 | `SpaceBackendUnavailableError`（明确报错，非静默失败） | 503 |
| 配额不足 | `SpaceQuotaExceededError`（复用） | 429 |
| Workspace CRD 创建失败 | `HyperPodSpaceBackendError`（附 K8s API 原因） | 400 |
| 非运行态请求 access-url | `InvalidSpaceStateError`（复用） | 409 |
| describe 时 CRD 不存在 | lazy sync 视为 stopped（同方式一 App 不存在语义） | — |
| WorkspaceConnection URL 轮询超时 | `SpaceBackendError`（提示稍后重试） | 400 |

K8s API 调用沿用 `KueueClient` 容错：开发环境（无集群 token）graceful 降级，不阻塞本地开发。

---

## 9. 测试策略

> 对齐方式一的 70+ 单测 + 真实 AWS E2E。

- **单元测试**（`tests/unit/spaces/`）：
  - `test_entity_space`：`SpaceBackend` 枚举与实体新字段、状态映射。
  - `test_svc_*`：`HyperPodSpaceBackend`（mock httpx 响应验证 CRD body 构造、状态映射、配额校验分流、错误转换）；service 按 backend 分发的策略字典（mock 两个 backend，验证调对）。
  - **TDD 红绿全程**，方式一现有测试保持绿。
- **集成测试**（`tests/integration/spaces/`）：`test_api_*` 验证 backend 字段路由、429/503/409 错误响应格式。
- **E2E**（`frontend/e2e` + 真实 AWS）：与方式一对称——创建 HyperPod Space → Kueue admission → 列表 running → 打开 web UI 验证落地集群 IDE 域（非登录页）→ stop → delete，断言真实 CRD 生命周期与配额占用/释放。**用 CPU 实例控制成本**（对齐近期 `ml.t3.medium` E2E 改造）。

- **契约文档**：`specs/.../contracts/` 更新 spaces OpenAPI，create 请求加 backend、响应加 backend + HyperPod 字段。

---

## 10. 范围边界（YAGNI）

- **不做**：方式一与方式二之间的空间迁移/转换；HyperPod Space 的自定义镜像构建（用 admin 配的 WorkspaceTemplate 默认镜像）；Studio 方式的任何重构（仅适配封装，底层不动）。
- **不做**：GPU MIG 分区（用整卡分配，文档支持的高级特性留待后续）。
- **聚焦**：与方式一对称的端到端 CRUD + 治理 + 访问。
