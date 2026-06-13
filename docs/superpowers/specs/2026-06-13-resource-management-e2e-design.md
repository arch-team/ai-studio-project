# 资源管理模块深度 E2E 测试与全栈修复设计

> 状态: 设计已批准，待落地实施
> 日期: 2026-06-13
> 目标环境: http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com
> 分支: feature/ui-audit-infrastructure

---

## 1. 背景与目标

对平台「资源管理」模块进行深度 E2E 测试，覆盖该模块下全部功能，发现的问题自行修复（全栈：前端 + 后端 + 必要基础设施），直到所有功能在真实 dev 环境正确运行。

「资源管理」= 侧边栏「资源管理」分组下的两个页面：

| 页面 | 路由 | 后端端点 | 真实状态（已验证） |
|------|------|---------|------|
| 配额管理 | `/resource-quotas` | `/api/v1/resource-limit-configs` | 基本健康，200 + 真实数据 |
| 资源监控 | `/monitoring` | `/api/v1/monitoring/*`、`/api/v1/clusters` | 整页崩坏，核心端点全部 404 |

**完成的硬标准**：两个页面在真实 dev 环境，所有功能交互正确、有真实数据源的部分展示真实数据、无数据源的部分优雅降级（显示"暂无数据"而非崩溃/白屏/报错）；Playwright 套件 100% 通过 + 关键交互浏览器实测截图佐证。

---

## 2. 现状诊断（基于真实环境验证）

### 2.1 配额管理页 — 基本健康

- 后端 `/api/v1/resource-limit-configs` 返回 200 且有真实数据（当前 9+ 条记录）。
- 前端为标准 Cloudscape 表格 + 新建/编辑 Modal + 表单校验。
- 已有较完整 Playwright E2E（`resource-quotas.spec.ts` + `resource-quotas-crud.spec.ts`），且支持 `E2E_BASE_URL` 跑真实环境。
- 缺口：分页未真实触发、校验边界覆盖不足、remote 写操作断言过于宽松、缺删除能力（待定性）。

### 2.2 资源监控页 — 前后端契约错位，整页崩坏

前端调用的端点与后端实际提供的端点**完全是两套契约**：

| 前端实际调用（`monitoringApi.ts`） | 真实响应 | 后端实际提供 | 真实响应 |
|------|------|------|------|
| `GET /clusters` | **404** | `GET /monitoring/clusters/{name}/metrics` | 200 |
| `GET /monitoring/utilization` | **404** | `GET /monitoring/grafana/dashboards` | 200 |
| `GET /monitoring/alerts` | **404** | `GET /monitoring/storage` | 200（数据全 0） |
| `GET /monitoring/metrics` | **404** | `GET /monitoring/network` | 200（数据全 0） |
| | | `GET /monitoring/clusters/{name}/health` | 200（cluster_id:0, unknown） |

**根因**：后端 monitoring 模块从未实现前端期望的「集群列表 + 利用率 + 指标序列 + 告警」四件套；且 `PrometheusService` 默认指向 `localhost:9090`（未接 AMP），`hyperpod_clusters` 表为空。

### 2.3 可观测性基建 — 已在线（关键修正）

最初判断"无监控基建"是错误的。经 AWS 只读核实，dev 环境的可观测性数据链路**早已打通且实时有效**：

- **AMP Workspace** `ai-platform-dev-amp`（`ws-577036b0-ac41-4e0b-81a5-4436385b0fdc`）：`ACTIVE`，endpoint `https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-577036b0-.../`
- **HyperPod Observability EKS Add-on** `amazon-sagemaker-hyperpod-observability` v1.0.4：`ACTIVE`，已绑定 AMP，无健康问题
- **指标数据**：18 个采集目标全部在线、约 10.5 万条活跃序列、最新样本约 10 秒延迟；含完整 GPU 指标族（`DCGM_FI_DEV_GPU_UTIL` 等）、node-exporter、cadvisor、apiserver 指标
- **HyperPod 集群** `ai-platform-dev-hyperpod`（id `ndownj7gq0f5`）：`InService`，3 实例组（controller-group ml.m5.xlarge、gpu-training-group ml.g5.2xlarge、system-group ml.m5.4xlarge），各 1 节点
- CDK `ObservabilityStack` 已部署（`ai-platform-dev-observability` 栈 CREATE/UPDATE_COMPLETE）

**结论**：基建不缺。监控页"跑不通"是**后端软件层未接通已有基建**，而非缺基础设施。这把"重量级基建项目"缩小为"全栈软件对齐 + 配置接通"。

---

## 3. 修复方案

### 3.1 监控页数据策略（核心架构决策）

监控页数据分两类，性质不同，处理方式不同：

**第一类 — 实时指标/利用率曲线（秒级、海量时序）**
- 唯一权威源：AMP（Prometheus）。
- 策略：**直接实时查 AMP，绝不入库**。把秒级时序灌入 MySQL 是反模式。

**第二类 — 集群拓扑/状态（慢变、权威源在 AWS 控制面）**
- 唯一权威源：SageMaker `describe-cluster`。
- 策略：**读穿透缓存（read-through cache）**。DB（`hyperpod_clusters` 表）为主；记录缺失或过期时，实时回源 SageMaker `describe-cluster` 写库再返回。
- 理由：
  1. 既有代码已为此铺路（表、`HyperPodCluster` 实体、`IHyperPodClusterRepository`、`ClusterHealthService.sync` 入口齐全）——表空是同步从未实现，非设计错误。
  2. 架构规范 `sdk-first.md` 明确「慢变控制面数据不应让前端每次刷新穿透 AWS 控制面 API」（`describe-cluster` 有限流风险，30 秒轮询会触发）。
  3. 支持集群与训练任务/配额跨实体 JOIN。
  4. AWS 控制面抖动时监控页仍可显示陈旧数据，不整页挂。
- 本轮形态：按需同步（read-through），不引入独立 K8s CronJob；接口设计与将来加 CronJob 后台同步完全兼容。

### 3.2 后端改造项

**A. 接通 AMP（配置 + SigV4）**
- backend settings 注入 AMP `prometheus_endpoint`（从 observability stack output 或环境变量读取）。
- `PrometheusClient` 增加 AWS SigV4 签名（AMP 查询 API 强制 SigV4），用 aioboto3 凭证签名 httpx 请求。复用平台现有 aioboto3 范式。

**B. 补齐 4 个端点（对齐前端既有契约）**

| 新增端点 | 数据来源 | 说明 |
|------|------|------|
| `GET /monitoring/clusters` | `hyperpod_clusters` 表（读穿透回源 SageMaker） | 集群列表，对齐 `ClusterListResponse` |
| `GET /monitoring/utilization` | AMP 即时查询聚合 | CPU/内存/GPU 利用率，对齐 `ResourceUtilization[]` |
| `GET /monitoring/metrics` | AMP range 查询 | 时间序列，对齐 `MetricSeries[]` |
| `GET /monitoring/alerts` | 本轮返回结构正确的空集 | 告警子系统是独立大功能，YAGNI，不在资源管理范围内强行造 |

> 端点路径需与前端 `monitoringApi.ts` 调用完全对齐（含 `/clusters` 是否带 `/monitoring` 前缀，以前端实际调用为准）。

**C. 回填集群数据**
- 实现读穿透同步逻辑：从 SageMaker `describe-cluster`（`ai-platform-dev-hyperpod`）映射写入 `hyperpod_clusters` 表。
- 字段映射：ClusterStatus → status、InstanceGroups → instance_groups/节点数、GPU 实例 → gpu_count 等。

### 3.3 前端改造项

- **Grafana iframe 死链**：当前指向 `/grafana`（未部署 AMG）。改为优雅处理：指向 AMP 关联的 Amazon Managed Grafana（若未配置则显示引导文案而非空白 iframe）。不强行部署 AMG。
- 监控页各 Tab（概览/指标趋势/Grafana/告警）在无数据时统一降级为"暂无数据"，不崩溃。

### 3.4 取舍记录（YAGNI）

| 项 | 决策 | 理由 |
|----|------|------|
| 告警（alerts）真实数据 | **不做**，返回空集 | 告警规则引擎是独立大功能，超出资源管理范围 |
| Prometheus/Grafana 自建 | **不做** | AWS 托管路线（AMP + Add-on）已在线，自建会与既有架构冲突 |
| 集群信息独立 CronJob | **不做**（本轮） | 用读穿透退化形态，留兼容接口给将来 |
| 配额删除功能 | **记录为发现项**，待用户定夺 | 当前页面仅"编辑"无"删除"，可能涉及后端级联，不擅自加 |

---

## 4. 测试范围

### 4.1 配额管理页（补深度与边界）

已覆盖（保留）：列表渲染、表单字段、创建/编辑 CRUD、基本校验、无障碍。

补充边界测试：
- **分页**：真实触发 `total_pages > 1` 翻页（现有数据已有 9+ 条）。
- **校验边界**：数值上下限、超长配置名、重复配置名（后端 409）、各角色枚举完整覆盖。
- **写操作数据自洽**：创建后列表计数 +1、编辑后值持久化（收紧现有宽松断言为真实成功断言）。
- **错误态**：后端 500/422 时 Alert 正确展示而非白屏。

### 4.2 资源监控页（新建套件）

新建 `monitoring.spec.ts`，覆盖：
- 页面加载不报错（核心回归——当前是 404 崩坏）。
- 概览 Tab：集群概览展示真实集群数据（名称/状态/节点数）、资源利用率展示真实 AMP 数据。
- 指标趋势 Tab：时间序列图表渲染、时间范围选择、自动刷新间隔切换。
- Grafana Tab：开关切换、降级文案/真实入口正确。
- 告警 Tab：空集时正确显示"暂无告警"。
- 时间范围选择器与自动刷新交互。

---

## 5. 执行闭环

```
阶段1 诊断：扩展 Playwright 套件（真实环境）跑两页全功能 → 归档所有失败项
阶段2 修复：按模块修
        配额：补边界测试 + 修发现项
        监控：后端接通 AMP + 补 4 端点 + 集群读穿透回填 + 前端降级（TDD 红绿）
阶段3 验证：① 重跑 Playwright 套件全绿
            ② 关键交互浏览器实测截图取证
阶段4 回归：ui-audit 截图流水线确认无视觉回归 → 循环直到全绿
```

---

## 6. 交付物

- 扩展后的 Playwright E2E 套件：`resource-quotas-*.spec.ts`（补边界）+ 新建 `monitoring.spec.ts`
- 后端新增端点与 AMP 接通的单元/集成测试
- 关键交互浏览器实测截图
- 测试与修复报告（含发现项清单：如配额删除能力缺口）

---

## 7. 已验证事实索引（供实施参考）

| 事实 | 值 |
|------|------|
| 真实环境登录 | `loginViaAPI`，默认 `admin/Admin123!`，sessionStorage 注入 refresh_token |
| AMP Workspace ID | `ws-577036b0-ac41-4e0b-81a5-4436385b0fdc` |
| AMP endpoint | `https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-577036b0-ac41-4e0b-81a5-4436385b0fdc/` |
| HyperPod 集群名 | `ai-platform-dev-hyperpod`（InService，3 实例组） |
| EKS 集群名 | `ai-platform-dev-eks` |
| Observability Add-on | `amazon-sagemaker-hyperpod-observability` v1.0.4（ACTIVE） |
| AWS 账号/区域 | 897473508751 / us-east-1 |
| 后端 SageMaker 复用范式 | `training/infrastructure/hyperpod/cluster_client.py`、`spaces/infrastructure/external/sagemaker_spaces_client.py` |
| 后端 monitoring 路由前缀 | `/api/v1/monitoring` |
