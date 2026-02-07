# 从 MVP 到生产可用：AI Training Platform 开发路线图

## Context

AI Training Platform 当前整体完成度约 **75%**（后端 82%，前端 68%，CDK 78%，文档 88%）。
核心业务功能已基本实现（训练任务、数据集、检查点、配额、模型管理等），但在**部署自动化、可观测性、安全加固、外部集成**方面存在明显缺口。

**约束条件**：
- 个人开发者 + Claude Code，需要最大化开发效率
- 私有化部署到客户 AWS 账户，要求部署高度自动化和可重复
- 需要同时推进功能、部署、安全、稳定性四个维度

**目标**：将平台从当前 MVP+ 状态推进到生产可用，建立可持续的开发工作流。

---

## 第一部分：Claude Code 高效开发方法论

作为个人开发者，Claude Code 是你的核心生产力倍增器。以下是经过验证的最佳实践：

### 1.1 日常开发工作流

```
每日开发循环：
1. 启动会话 → 让 Claude 阅读相关 CLAUDE.md 和 ARCHITECTURE.md 建立上下文
2. 明确目标 → 用一句话描述今天要完成什么（如"实现 Rate Limiting 中间件"）
3. 计划模式 → 让 Claude 先进入 plan mode 探索现有代码、设计方案
4. 审批执行 → 审批计划后让 Claude 逐步实现
5. 验证提交 → 运行测试 → 审查 diff → 提交
```

### 1.2 最大化 Claude Code 效率的关键策略

**策略 1：保持高质量的 CLAUDE.md 文件**
- 你的 `backend/CLAUDE.md` 和 `docs/ARCHITECTURE.md` 已经非常优秀
- 每完成一个重大功能后，更新 CLAUDE.md 中的模式和约定
- 这是跨会话保持一致性的关键手段

**策略 2：利用 Plan Mode 做复杂任务**
- 任何涉及 3+ 文件的改动，先进 plan mode
- 让 Claude 先探索现有代码模式，避免重复造轮子
- 例：添加新中间件前，先让 Claude 分析现有中间件的注册方式

**策略 3：分解大任务为原子单元**
- 每次会话聚焦一个明确的原子目标（如一个中间件、一个 API 端点）
- 避免在单个会话中做跨模块的大规模重构
- 完成后立即提交，保持代码库干净

**策略 4：善用并行代理**
- 探索阶段用多个 Explore agent 并行搜索
- 测试/构建等独立操作并行执行
- 代码审查用专门的 review agent

**策略 5：利用 Spec-Kit 驱动开发**
- 你已有完善的 spec.md/plan.md/tasks.md 体系
- 每个新 Phase 先用 `/speckit.specify` 生成规范
- 用 `/speckit.tasks` 生成任务清单，逐个完成

### 1.3 推荐的开发节奏

```
周一-周四：功能开发（每天 1-2 个原子任务）
周五：审查整周代码 + 更新文档 + 运行全量测试
每两周：回顾进度，调整优先级
```

---

## 第二部分：生产就绪路线图（按优先级分 5 个 Phase）

### Phase A：部署基础设施（最高优先级）

> 私有化部署场景下，没有部署自动化就无法交付产品。

#### A1. Kubernetes 部署清单和 Helm Chart
- **目标**：创建可参数化的 Helm Chart，支持一键部署到客户 EKS
- **关键文件**：
  - `infrastructure/helm/backend/` — Chart.yaml, values.yaml, templates/
  - templates: deployment, service, ingress, configmap, secret, hpa, pdb
- **要点**：
  - 多环境 values 文件：values-dev.yaml, values-staging.yaml, values-prod.yaml
  - Readiness/Liveness probes 指向 `/health`
  - Resource limits 和 HPA 配置
  - PodDisruptionBudget 确保高可用
- **Claude Code 方式**：`让 Claude 参考现有 CDK Stack 的配置（如 EKS、ALB），生成匹配的 Helm Chart`

#### A2. CI/CD 流水线
- **目标**：GitHub Actions 实现构建 → 测试 → 推送镜像 → 部署
- **关键文件**：
  - `.github/workflows/ci.yml` — 测试 + lint
  - `.github/workflows/build.yml` — Docker build + ECR push
  - `.github/workflows/deploy.yml` — Helm upgrade
- **要点**：
  - 后端：pytest + ruff + mypy
  - 前端：vitest + eslint + tsc
  - CDK：pytest + cdk synth
  - 镜像推送到 ECR
- **Claude Code 方式**：`提供现有测试命令（在 CLAUDE.md 中已有），让 Claude 生成 workflow 文件`

#### A3. 密钥管理
- **目标**：消除硬编码密钥，集成 AWS Secrets Manager
- **关键文件**：
  - `backend/src/shared/infrastructure/config.py` — Settings 类（当前 SECRET_KEY 有默认值）
  - 新增：`backend/src/shared/infrastructure/secrets.py` — Secrets Manager 客户端
- **要点**：
  - DATABASE_URL、SECRET_KEY、AWS 凭证从 Secrets Manager 获取
  - 开发环境保持 .env 方式不变，生产环境切换到 Secrets Manager
  - Helm Chart 中通过 ExternalSecrets Operator 或 init container 注入

#### A4. 部署文档
- **目标**：编写客户可执行的部署指南
- **关键文件**：
  - `docs/deployment-guide.md` — 完整部署步骤
  - `docs/operations-runbook.md` — 运维手册
- **内容**：
  - 前置条件（AWS 账户、IAM 权限、域名）
  - CDK Bootstrap → Stack 部署顺序
  - Helm install 配置参数说明
  - 验证清单（health check、功能验证）

---

### Phase B：安全加固

> 企业级产品的安全底线。

#### B1. Rate Limiting 中间件
- **关键文件**：
  - `backend/src/shared/api/middleware/` — 新增 rate_limit.py
  - `backend/src/main.py` — 注册中间件（参考现有 CORS/AuditMiddleware 注册方式）
- **方案**：slowapi（基于 limits 库），支持 per-IP 和 per-user 限速
- **参考模式**：查看 `main.py:93-110` 现有中间件注册方式

#### B2. Security Headers 中间件
- **关键文件**：同上 middleware 目录
- **Headers**：X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Content-Security-Policy
- **实现**：简单的 Starlette middleware，约 30 行代码

#### B3. 输入验证加固
- **现状**：Pydantic schema 已做格式校验，但缺少内容安全检查
- **补充**：
  - 请求体大小限制（在 uvicorn/nginx 层配置）
  - 文件上传类型和大小白名单（datasets 模块）
  - SQL 参数化已由 SQLAlchemy 保证（无需额外处理）

#### B4. HTTPS 强制 + TLS 配置
- **现状**：CDK AlbStack 已配置 TLS，但应用层需配合
- **补充**：
  - Redirect HTTP → HTTPS（ALB 层 或 Ingress 层配置）
  - HSTS header（在 Security Headers 中间件中）

---

### Phase C：可观测性

> 没有监控的生产系统是盲飞。

#### C1. Prometheus Metrics 端点
- **关键文件**：
  - `backend/src/shared/infrastructure/metrics.py` — 指标定义
  - `backend/src/main.py` — 挂载 /metrics 端点
- **核心指标**：
  - `http_requests_total{method, status, endpoint}` — 请求计数
  - `http_request_duration_seconds{endpoint}` — 响应延迟 histogram
  - `db_query_duration_seconds` — 数据库查询耗时
  - `training_jobs_active{status}` — 训练任务状态分布
  - `storage_usage_bytes{type}` — 存储使用量
- **库**：prometheus-client 或 prometheus-fastapi-instrumentator（自动插桩）

#### C2. 结构化日志增强
- **现状**：structlog 已配置良好（`shared/infrastructure/logging_config.py`）
- **补充**：
  - 确保所有 Service 层方法有 entry/exit 日志
  - 外部调用（HyperPod、S3）记录延迟和状态
  - 标准化日志字段便于 CloudWatch Insights 查询

#### C3. Grafana Dashboard
- **现状**：`infrastructure/grafana/dashboards/` 目录已存在
- **补充**：
  - API 概览仪表板（QPS、P95 延迟、错误率）
  - 训练任务仪表板（提交量、成功率、平均训练时长）
  - 资源使用仪表板（GPU 利用率、配额消耗、存储容量）

#### C4. 告警规则
- **方案**：CloudWatch Alarms（配合 CDK 定义）
- **核心告警**：
  - API 错误率 > 5%
  - P95 延迟 > 2s
  - 数据库连接池使用率 > 80%
  - 磁盘使用率 > 85%
  - 训练任务失败率异常

---

### Phase D：功能补全

> 补齐核心业务缺口。

#### D1. Billing 模块 Domain 层
- **现状**：Application 层有 8 个服务但 Domain 层几乎为空
- **关键文件**：
  - `backend/src/modules/billing/domain/entities/` — 定义 CostRecord, UsageReport
  - `backend/src/modules/billing/domain/value_objects/` — Cost, ResourceUsage
  - `backend/src/modules/billing/domain/repositories/` — 仓库接口
- **参考**：遵循 training 模块的 Domain 层模式
- **Claude Code 方式**：`让 Claude 先读 training/domain 作为模板，再为 billing 生成同样结构`

#### D2. Billing API 端点补全
- **现状**：仅 2 个端点
- **需补充**：成本详情查询、用量明细、成本趋势、预算告警配置
- **参考**：`backend/src/modules/training/api/endpoints/` 的端点模式

#### D3. Domain Event 系统完善
- **现状**：EventBus 基类存在但各模块事件定义不足
- **需定义的事件**：
  - training: TrainingJobSubmitted, TrainingJobCompleted, TrainingJobFailed
  - datasets: DatasetUploaded, DatasetVersionCreated
  - quotas: QuotaExceeded, QuotaReleased
  - auth: UserCreated
- **关键文件**：各模块的 `domain/events.py`

#### D4. 外部集成加固
- **Kueue 客户端**：
  - 文件：`backend/src/modules/training/infrastructure/kueue/`
  - 功能：ClusterQueue 配额查询、Workload 提交/状态监控、优先级抢占
- **重试和熔断**：
  - 库：tenacity（重试） + pybreaker（熔断）
  - 位置：`backend/src/shared/infrastructure/resilience.py`
  - 应用到：所有 HyperPod/S3/Kueue 外部调用

#### D5. 前端完善
- **数据集 API 对接**：补全部分进行中的 API 集成
- **Spaces 集成验证**：确保与 SageMaker Spaces Add-on 正确交互
- **错误处理**：全局错误边界、网络错误重试提示

---

### Phase E：生产加固

> 提升系统整体健壮性。

#### E1. 数据库加固
- **RDS Multi-AZ**：CDK DatabaseStack 配置 `multi_az=True`
- **备份策略**：`backup_retention=Period.days(30)`
- **慢查询日志**：开启 MySQL slow_query_log 参数组
- **索引审查**：检查高频查询的索引覆盖（training_jobs, audit_logs, datasets）

#### E2. 灾难恢复
- **RDS 自动备份** + 跨区域复制（可选）
- **S3 版本控制**已开启（CDK StorageStack）
- **恢复演练文档**：数据库恢复步骤、S3 数据恢复、EKS 集群重建

#### E3. 性能基准测试
- **工具**：locust 或 k6
- **场景**：并发训练任务提交、大文件上传、批量查询
- **基线**：建立 P50/P95/P99 延迟基准

#### E4. OpenTelemetry 分布式追踪（可选增强）
- **库**：opentelemetry-instrumentation-fastapi
- **后端**：Jaeger 或 AWS X-Ray
- **价值**：跨服务请求追踪、性能瓶颈定位

---

## 第三部分：执行节奏建议

### 推荐执行顺序

```
Phase A（部署基础）→ Phase B（安全）→ Phase C（可观测性）→ Phase D（功能）→ Phase E（加固）
```

理由：私有化部署场景下，先有可交付的部署能力，再逐步加固。

### 每个 Phase 的 Claude Code 使用模式

| Phase | 推荐方式 | 说明 |
|-------|---------|------|
| A：部署 | Plan Mode + 一次性生成 | Helm/CI 文件相对独立，可整体生成 |
| B：安全 | 逐个中间件实现 | 每个中间件一个会话，参考现有中间件模式 |
| C：监控 | 参考库文档生成 | 用 context7 查 prometheus-client 文档 |
| D：功能 | Plan Mode + TDD | 先写测试，再实现，遵循项目 TDD 规范 |
| E：加固 | CDK 修改 + 文档 | 修改 CDK Stack 配置，编写运维文档 |

### 单个任务的 Claude Code 执行模板

```
1. "请先读 backend/CLAUDE.md 和 docs/ARCHITECTURE.md 了解项目规范"
2. "进入 plan mode，我要实现 [具体任务]"
3. [Claude 探索代码、设计方案]
4. [你审批计划]
5. [Claude 实现 + 测试]
6. "运行 pytest tests/ 验证"
7. "提交代码"
```

---

## 验证方案

每个 Phase 完成后的验证清单：

### Phase A 验证
```bash
# Helm Chart 语法
helm lint infrastructure/helm/backend/
helm template infrastructure/helm/backend/ -f values-dev.yaml

# CI 流水线
# 推送到分支，观察 GitHub Actions 是否正确触发

# 密钥管理
# 验证生产配置不含硬编码密钥
grep -r "change-me" backend/src/  # 应无结果

# 部署文档
# 按文档步骤在测试 AWS 账户执行一次完整部署
```

### Phase B 验证
```bash
# Rate Limiting
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  # 快速重复 10 次，应返回 429

# Security Headers
curl -I http://localhost:8000/health
# 应包含 X-Content-Type-Options, X-Frame-Options 等

# 后端测试
pytest tests/ -v
```

### Phase C 验证
```bash
# Metrics 端点
curl http://localhost:8000/metrics
# 应返回 Prometheus 格式指标

# 日志格式
uvicorn src.main:app --reload 2>&1 | head -20
# 应输出结构化 JSON

# 告警测试
# 手动触发一个错误场景，验证告警是否触发
```

### Phase D 验证
```bash
# Billing Domain
pytest tests/unit/billing/ -v

# Domain Events
pytest tests/unit/ -k "event" -v

# 架构合规
pytest tests/architecture -v

# 全量测试
pytest tests/ --cov=src --cov-report=term-missing
```

### Phase E 验证
```bash
# 性能基准
locust -f tests/performance/locustfile.py --headless -u 50 -r 5 --run-time 5m

# 数据库
# 检查 RDS Multi-AZ 状态
aws rds describe-db-instances --query 'DBInstances[].MultiAZ'

# 灾难恢复
# 执行一次数据库恢复演练
```
