# 资源管理模块深度 E2E 测试与全栈修复报告

> 日期: 2026-06-13
> 范围: 资源管理模块 = 配额管理页 `/resource-quotas` + 资源监控页 `/monitoring`
> 环境: dev `http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com`
> 分支: feature/ui-audit-infrastructure（隔离 worktree 执行）

---

## 1. 执行摘要

对资源管理模块两个页面做了深度 E2E 测试与全栈修复。核心成果：

- **资源监控页从"整页 404 崩坏"修复为"四端点全部返回真实数据、E2E 全绿"** —— 这是本轮最大的修复。
- **配额管理页补齐删除能力 + 深度边界测试**，CRUD 闭环完整。
- 修复过程中发现并解决了 **3 个真实 Bug**（2 个被降级机制掩盖），另发现 1 个系统性技术债和 1 个预存配置问题。

最终状态：本轮范围内后端 200 测试全绿、前端 54 单元测试全绿、监控页真实环境 E2E 6 项通过、配额删除/计数真实环境 E2E passed、质量门（lint/type/black/ruff/mypy 改动文件）全过、ui-audit 视觉无回归、浏览器实测 7 张截图取证。

---

## 2. 诊断结论（修复前基线）

| 页面 | 修复前真实状态 | 根因 |
|------|------|------|
| 配额管理 | 基本健康（端点 200 有数据），缺删除能力、边界测试不足 | — |
| 资源监控 | **四端点全部 404，整页崩坏** | 后端从未实现前端期望的「集群列表+利用率+指标序列+告警」端点；PrometheusService 未接 AMP；hyperpod_clusters 表为空 |

关键认知修正：可观测性基建（AMP Workspace + HyperPod Observability Add-on）**早已在线且实时有效**（10.5 万条活跃指标），监控页"跑不通"是后端软件层未接通已有基建，而非缺基建。

---

## 3. 完成的工作（按交付物）

### 3.1 基础设施（CDK）
- 后端 IRSA 角色 `ai-platform-dev-backend-service-role` 增加 `aps:QueryMetrics/GetSeries/GetLabels/GetMetricMetadata` 权限（接通 AMP 查询的前置）。已部署 dev 并验证生效。

### 3.2 后端（监控页全栈接通）
- **AMP 接入层**：Settings 加 `amp_query_endpoint`；PrometheusClient 加 AWS SigV4 签名（service=aps），保留 prometheus_endpoint 向后兼容。
- **响应 schema**：新增 ClusterListResponse/ClusterDetailResponse/NodeListResponse/ResourceUtilizationResponse/MetricSeriesResponse/AlertListResponse，逐字段对齐前端 TS 类型。
- **集群读穿透服务**：ClusterSyncService（DB 缓存 + 缺失/过期回源 SageMaker describe-cluster + asyncio.Lock 单飞）；SageMakerClusterClient（aioboto3 薄封装，实现 ISageMakerClusterClient 抽象）；InService→active 状态映射。
- **利用率聚合**：PrometheusService.get_resource_utilization（AMP 即时查询 CPU/内存/GPU）。
- **端点**：`/clusters*`（无 monitoring 前缀，对齐前端契约）+ `/monitoring/{utilization,metrics,alerts}`（带前缀），全部 try/except 故障降级返回 200+空数据。
- **modulemonitoring `__init__` 导出修正**（移除占位 `__all__=[]`）。

### 3.3 前端
- **配额删除能力**：api `deleteResourceLimitConfig` + hook `useDeleteResourceLimitConfig`（invalidate 列表）+ 页面删除按钮 + 二次确认 Modal（warning 提示 + 显示配置名 + loading 态）。
- **Grafana 死链降级**：未配置 VITE_GRAFANA_URL 时显示引导文案而非死链 iframe，文案对终端用户友好且不暴露 env 变量名。

### 3.4 测试
- 配额页边界 E2E：删除流程、二次确认拦截、删除取消、超长配置名、数值边界、计数自洽、错误态。
- 新建监控页 E2E 套件（MonitoringPage Page Object + monitoring.spec.ts）：四 Tab 全功能 + 真实数据断言。
- 浏览器实测取证脚本（capture-evidence.mjs）。

### 3.5 部署
- 后端 v1.2.28（含 AMP 接入 + SigV4 修复 + 时区修复）部署 dev。
- 前端 v1.0.19（配额删除 + Grafana 降级）部署 dev。

---

## 4. 发现并修复的 Bug

### 4.1 本轮引入修复的真实 Bug（3 个）

| # | Bug | 根因 | 修复 | 发现方式 |
|---|-----|------|------|---------|
| B1 | HyperPodCluster Enum 持久化崩溃 | ORM `Enum()` 默认按成员名（大写）读写，迁移列是小写值，DB 读回 LookupError | model 加 `values_callable` 按 .value 映射 | Task 2C.2a 真实 DB 集成测试 |
| B2 | AMP instant query 403 Forbidden | httpx 默认把空格编码为 `+`，AWS SigV4 要求 `%20`，含特殊字符的 PromQL 签名不匹配（而纯字母的 range query 恰好通过） | `urlencode(quote_via=quote)` 统一编码，签名与发送共用同一 URL | Task 2D.1 真实环境联调（utilization 返空，日志见 403） |
| B3 | 集群列表读穿透降级返空 | `_is_fresh()` 比较 aware `utc_now()` 与 MySQL 读回的 naive `last_sync_at`，TypeError 被降级掩盖 | 用项目既有 `ensure_aware()` helper 统一时区 | Task 2D.1 真实环境联调（集群列表返空，日志见 TypeError） |

**关键观察**：B2、B3 都被"故障降级返 200"机制掩盖——端点不崩但返回空数据。这印证了真实环境联调的价值：单测全绿 ≠ 真实可用，必须真打端点看真实数据。

### 4.2 发现但未在本轮修复的问题（记录待办）

| # | 问题 | 性质 | 建议 |
|---|------|------|------|
| F1 | Enum 持久化 Bug 系统性存在 | users（实测 UserRepositoryImpl.create 抛 LookupError）、quotas、audit 等模块的 ORM 用裸 `Enum()` + 小写 value，与 monitoring 修复前同病。因现有"集成测试"多用 mock session 从未触达真实 DB，CI 盲区长期掩盖 | **独立立项**：在 shared 收敛 Enum 映射策略 + 补真实 DB 的 test_repo_* 堵 CI 盲区 |
| F2 | CSP 字体报错（24 条） | Cloudscape 内联 data: 字体被 `font-src 'self'` CSP 拦截，回退系统字体。预存配置问题，不影响功能 | 非紧急：index.html CSP font-src 加 `data:` 或自托管字体 |

---

## 5. 验证证据

### 5.1 真实环境端点（监控页四端点，v1.2.28 后）
```
[200] /api/v1/clusters            → ai-platform-dev-hyperpod, status=active, 3 节点, gpu=1
[200] /api/v1/monitoring/utilization → cpu 5.1% / memory 6.7% / gpu 0%
[200] /api/v1/monitoring/metrics  → DCGM_FI_DEV_GPU_UTIL 真实时间序列
[200] /api/v1/monitoring/alerts   → 空集（告警子系统未实现，YAGNI）
```
PromQL 数值交叉验证（直查 AMP vs 端点）：memory 6.76% vs 6.7%、gpu 0 vs 0、cpu 同量级 → PromQL 语义正确。

### 5.2 自动化测试
| 范围 | 结果 |
|------|------|
| 后端 monitoring + quotas（单元+集成） | **200 passed** |
| 后端全量（单元+集成+架构） | 1909 passed, 10 failed（见 5.4）, 6 skipped |
| 前端 resource-quotas + monitoring 单元 | **54 passed** |
| 配额 E2E（真实环境 remote 组） | 删除流程、计数严格+1 等 **passed**（不再 skip） |
| 监控页 E2E（真实环境 remote 组） | **6 passed**（集群真实数据/利用率/指标/告警/Tab切换/404回归） |
| 质量门 | 前端 lint+type-check ✓；后端 black+ruff+mypy（改动文件）✓；CDK ruff+mypy ✓ |

### 5.3 浏览器实测取证（7 张截图，frontend/e2e/artifacts/resource-mgmt-evidence/）
配额列表、新建 Modal、删除二次确认（截图后取消未删数据）、监控概览（真实集群数据）、指标趋势、Grafana 降级、告警空态。ui-audit 视觉回归：14 张截图双主题无布局异常。

### 5.4 后端全量 10 个失败的诚实说明
10 个失败全部在 billing/training 模块集成测试，**无一涉及本轮改动的文件/函数**（堆栈无 monitoring/cluster_sync/prometheus_client/ensure_aware/values_callable/sigv4）。两类预存环境问题：
- training 测试 429 配额超限（共享 MySQL 配额数据=0 污染）。
- billing 报表 500 `Future attached to a different loop`（pytest-asyncio 事件循环作用域基础设施问题）。

结论：**本轮工作未引入任何回归。** 这些失败是其他模块的预存环境/数据问题，不在本轮范围。

---

## 6. 决策记录

| 决策 | 结论 |
|------|------|
| 配额删除能力 | 纳入本轮（后端已有 DELETE，补前端 UI + E2E） |
| 告警数据 | 返回结构正确的空集（告警子系统是独立大功能，YAGNI） |
| 集群数据策略 | 读穿透缓存（DB 为主，缺失/过期回源 SageMaker），指标实时查 AMP 不入库 |
| Prometheus/Grafana | 复用已在线的 AMP + Observability Add-on，不自建 |
| 监控页错误处理 | 数据源故障返回 200+空数据（不 5xx），保证前端优雅降级 |

---

## 7. 遗留与建议

1. **F1（Enum 系统性 Bug）建议尽快独立立项** —— users 模块实测已坏，可能影响生产，且 CI 盲区使其长期潜伏。
2. monitoring `/clusters/{id}/nodes` 端点本轮返回结构正确的空响应（SageMaker 只读客户端无 list_cluster_nodes 能力），已标 TODO，待后续接节点级数据。
3. 集群读穿透目前是按需回源（read-through），未来可加 K8s CronJob 后台同步（接口已兼容）。
4. F2（CSP 字体）非紧急，可在前端配置迭代时一并处理。
5. dev ALB 偶发 401（多实例负载均衡环境抖动），remote E2E 若偶发失败可留意此环境特性。
