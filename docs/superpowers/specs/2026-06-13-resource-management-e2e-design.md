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

前端调用的端点与后端实际提供的端点**是两套互不重合的契约**（下表左右两列**无对应关系**：左列为前端调用且全部 404，右列为后端现存但前端从未消费）。

前端 `monitoringApi.ts` 实际调用（apiClient baseURL = `/api/v1`，故下列均自动带 `/api/v1` 前缀）：

| 前端实际调用 | 真实响应 |
|------|------|
| `GET /clusters`（**无** monitoring 前缀） | **404** |
| `GET /clusters/{id}`、`/clusters/{id}/nodes`、`/clusters/{id}/metrics` | **404** |
| `GET /monitoring/utilization` | **404** |
| `GET /monitoring/metrics` | **404** |
| `GET /monitoring/alerts`、`POST /monitoring/alerts/{id}/acknowledge` | **404** |

后端 monitoring 模块现存（前端未使用）：

| 后端实际提供 | 真实响应 |
|------|------|
| `GET /monitoring/clusters/{name}/metrics` | 200 |
| `GET /monitoring/grafana/dashboards` | 200 |
| `GET /monitoring/storage`、`/monitoring/network` | 200（数据全 0，因未接 AMP） |
| `GET /monitoring/clusters/{name}/health` | 200（cluster_id:0, unknown，因表空） |

**根因**：后端 monitoring 模块从未实现前端期望的「集群列表 + 利用率 + 指标序列 + 告警」四件套；且 `PrometheusService` 默认指向 `localhost:9090`（未接 AMP），`hyperpod_clusters` 表为空。

**路径契约（已实地核实，写死，不再"以前端为准"）**：前端集群相关请求走**无 monitoring 前缀**的 `/api/v1/clusters*`，指标/利用率/告警走**带前缀**的 `/api/v1/monitoring/*`。后端据此新增端点必须严格匹配这两种前缀（见 §3.2-B）。

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

**A. 接通 AMP（IAM 权限 + 配置 + SigV4）**

接通 AMP 是**三件事**，缺一不可：

1. **IAM 权限（必需的基础设施改动，非纯软件配置）**：后端 IRSA 角色 `ai-platform-dev-backend-service-role`（ServiceAccount `ai-platform:backend-service-sa`）当前**无任何 `aps:` 权限**（已核实）。需在 CDK `iam_stack.py` 的 `_create_backend_service_role` 增加一条 policy：`aps:QueryMetrics`、`aps:GetSeries`、`aps:GetLabels`、`aps:GetMetricMetadata`，资源限定到 AMP workspace ARN。改完需 `cdk deploy` iam stack。
   - 注：`sagemaker:DescribeCluster`、`sagemaker:ListClusterNodes` **该角色已有**（读穿透回填集群无需改 IAM）。
2. **配置**：backend settings（`src/shared/infrastructure/config.py`）注入 AMP `prometheus_endpoint`（值见 §7，从环境变量/observability stack output 读取）。K8s `backend-deployment.yaml` 注入对应环境变量。
3. **SigV4 签名（新增能力，无现成范式）**：AMP 查询 API 强制 SigV4。这**不是** boto3 SDK 调用，而是对发往 AMP `/api/v1/query`、`/api/v1/query_range` 的原始 HTTP 请求做 SigV4 签名。实现方式：用 `botocore.auth.SigV4Auth` + `botocore.awsrequest.AWSRequest` 对 httpx 请求签名（service name = `aps`）。凭证来源 = IRSA（Pod 内 `botocore` 自动从 web identity token 取）。
   - 区分：§7 索引的 `cluster_client.py`/`sagemaker_spaces_client.py` 是 **SageMaker SDK 调用范式**（用于 C 的 `describe-cluster`），**不适用**于 AMP HTTP 查询。AMP SigV4-HTTP 为本项目新增能力。

**B. 补齐端点（严格匹配前端两种前缀，对齐前端既有 TS 类型）**

响应 schema 的**唯一真源**是前端 `frontend/src/features/monitoring/types/index.ts`，后端 Pydantic 响应模型须逐字段对齐（字段名/类型/可空性）：

| 新增端点 | 数据来源 | 对齐的前端类型 |
|------|------|------|
| `GET /clusters`（无前缀，独立 router 或挂载点） | `hyperpod_clusters` 表（读穿透回源 SageMaker） | `ClusterListResponse` = `{ items: ClusterSummary[]; total }` |
| `GET /clusters/{id}` | 同上 | `ClusterDetail` |
| `GET /clusters/{id}/nodes` | SageMaker `ListClusterNodes` | `NodeListResponse` |
| `GET /clusters/{id}/metrics` | AMP range 查询 | `ClusterMetrics[]` |
| `GET /monitoring/utilization` | AMP 即时查询聚合 | `ResourceUtilization[]`（单值快照：`resource_type/total/used/available/utilization_percentage/unit`） |
| `GET /monitoring/metrics` | AMP range 查询 | `MetricSeries[]`（`metric_name/labels/data_points[]`） |
| `GET /monitoring/alerts` | 本轮返回结构正确的空集 | `AlertListResponse`（`items:[]/total:0/page/page_size/total_pages`） |

> `ResourceUtilization` 是单值快照（非序列），故 utilization 用 AMP **即时查询**（instant）；`MetricSeries.data_points` 是时间序列，故 metrics 用 **range 查询**。
>
> 前端 `/clusters` 无 monitoring 前缀，后端需为其单独挂载 router（不挂在 `/api/v1/monitoring` 下），或在 monitoring router 外新增 clusters router。实施时确认挂载点与 §1 路径一致。

**PromQL 草案**（基于 §2.3 已确认的真实指标族，实施时以 AMP 实测校准）：

| 指标 | PromQL 草案 | 聚合维度 |
|------|------|------|
| CPU 利用率 | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | 集群整体均值 |
| 内存利用率 | `(1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes)) * 100` | 集群整体 |
| GPU 利用率 | `avg(DCGM_FI_DEV_GPU_UTIL)` | 集群整体均值（或按 node 分组取 max） |

> PromQL 写错会静默返回错数据。实施时**必须**用 awscurl / AMP 控制台手动跑同一 PromQL，与端点返回值交叉核对（见 §4.2）。

**后端错误处理契约（保证前端可降级）**：监控页所有新端点在数据源故障时（AMP 超时/SigV4 失败/403、SageMaker 限流/抛错）**返回 200 + 空或陈旧数据**，**不返回 5xx**。集群读穿透回源失败时返回 DB 中陈旧数据（若有）或空列表，附最后同步时间戳。这样前端统一走"暂无数据"降级，不会整页崩。

**C. 回填集群数据（读穿透）**
- 读穿透逻辑：`GET /clusters` 命中时，若 DB 记录缺失或过期（超过 TTL，建议 5 分钟），触发 SageMaker `describe-cluster`（`ai-platform-dev-hyperpod`）映射写入 `hyperpod_clusters` 表再返回；否则直接返回 DB。
- **首次回源延迟预警**：表当前为空，首请求必然回源（秒级延迟）。需加并发保护（单飞/锁）避免并发首请求击穿同时多次 `describe-cluster`；首屏可接受一次秒级延迟，但前端请求超时需 ≥ 该延迟。
- 字段映射（`describe-cluster` → `hyperpod_clusters` 表，表结构见 ORM `hyperpod_cluster_model.py`）：`ClusterStatus`→status、`InstanceGroups[].CurrentCount` 求和→total_nodes、GPU 实例组→gpu_count、`ClusterArn`→cluster_arn 等。完整映射实施时对照 ORM 模型补齐。

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

前端 Tab → 消费端点映射（指导测试断言）：

| Tab | 消费端点 | 真实数据预期 |
|------|------|------|
| 概览 | `/clusters` + `/monitoring/utilization` | 集群名/状态/节点数 + CPU/内存/GPU 利用率均有真实值 |
| 指标趋势 | `/monitoring/metrics` | 时间序列曲线有真实数据点 |
| Grafana | （前端 iframe，不调后端数据 API） | 降级文案或真实 AMG 入口 |
| 告警 | `/monitoring/alerts` | 空集，显示"暂无告警" |

新建 `monitoring.spec.ts`，覆盖：
- 页面加载不报错（核心回归——当前是 404 崩坏）。
- 概览 Tab：集群概览展示真实集群数据（名称/状态/节点数）、资源利用率展示真实 AMP 数据。
- 指标趋势 Tab：时间序列图表渲染、时间范围选择、自动刷新间隔切换。
- Grafana Tab：开关切换、降级文案/真实入口正确。
- 告警 Tab：空集时正确显示"暂无告警"。
- 时间范围选择器与自动刷新交互。
- **错误态降级**：模拟 AMP/SageMaker 故障（或 mock 后端 200+空），验证页面降级为"暂无数据"而非崩溃。
- **PromQL 数值正确性交叉验证**（非纯 E2E，作为修复验证步骤）：用 awscurl/AMP 控制台手动跑 §3.2-B 的 PromQL，与 `/monitoring/utilization`、`/monitoring/metrics` 端点返回值交叉核对，确认数值真实正确。

---

## 5. 执行闭环

```
阶段0 决策确认：配额删除能力是否纳入（与用户确认）→ 决定 §4.1 是否含删除用例
阶段1 诊断：扩展 Playwright 套件（真实环境）跑两页全功能 → 归档所有失败项
阶段2 修复：按模块修
        配额：补边界测试 + 修发现项
        监控：后端 IAM 加 aps 权限(cdk deploy) → 接通 AMP(SigV4) → 补端点
              → 集群读穿透回填 → 前端降级（TDD 红绿）
阶段3 验证：① 重跑 Playwright 套件全绿
            ② PromQL 数值交叉核对
            ③ 关键交互浏览器实测截图取证
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
| 后端 monitoring 路由前缀 | `/api/v1/monitoring`；但 `/clusters` 系列**无** monitoring 前缀 |
| 后端服务身份 | IRSA：SA `ai-platform:backend-service-sa` → role `ai-platform-dev-backend-service-role` |
| 该角色已有权限 | `sagemaker:DescribeCluster`、`ListClusterNodes`（读穿透足够）；**无 `aps:*`（需新增）** |
| AMP IAM 改动位置 | `infrastructure/cdk/stacks/foundation/iam_stack.py` 的 `_create_backend_service_role` |
| schema 唯一真源 | `frontend/src/features/monitoring/types/index.ts` |
| 前端 apiClient baseURL | `/api/v1`（`src/shared/api/client.ts`） |
| hyperpod_clusters 表 ORM | `backend/src/modules/monitoring/infrastructure/models/hyperpod_cluster_model.py` |
