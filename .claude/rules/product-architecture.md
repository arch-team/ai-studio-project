# 产品架构规范 (Product Architecture Standards)

> **职责**: 产品架构的**单一真实源 (SSOT)**，从**业务视角**定义平台定位、五层业务架构、模型全生命周期与多租户模型。
>
> **定位区分**: 本文档是**产品/业务架构**（平台是什么、为谁服务、能力如何组织）；技术实现架构（DDD 分层、模块隔离、依赖方向）见 [`backend/.claude/rules/architecture.md`](../../backend/.claude/rules/architecture.md)。二者互补：产品架构定义 **WHAT/WHY**，技术架构定义 **HOW**。
>
> **术语权威**: 所有实体/调度术语以 [`specs/001-ai-training-platform/spec.md`](../../specs/001-ai-training-platform/spec.md) §Terminology Standards 为准，本文档不自创术语。
>
> **实现状态图例**: 本规范区分能力的落地状态——✅ **已实现**（代码已具备） / 🚧 **规划中 (roadmap)**（定位范围内但尚未实现）。Claude 据此判断某能力当前能否依赖。

---

## 0. 速查卡片

> Claude 描述平台、设计功能、规划模块归属时优先查阅此章节。

### 平台一句话定位

> **企业级 AI 平台**：为企业内不同业务线的算法团队提供标准化基础能力，使其完成 **数据管理 → 模型开发与训练 → 模型部署与运维** 的全生命周期工作，底层完全依赖 AWS SageMaker HyperPod 原生能力。
>
> **范围说明**（对齐项目宪法愿景"统一模型开发、训练、部署平台"）：平台覆盖**开发 + 训练 + 部署**全生命周期。其中 ✅ **数据管理、模型开发与训练、模型注册** 已实现；🚧 **模型部署与推理服务** 为 roadmap 规划中（当前 `models` 模块仅有部署状态位，无实际部署/推理执行能力）。

### 五层业务架构速查

| 层级 | 英文 | 职责 | 关键组件 |
|------|------|------|---------|
| **租户层** | Tenant Layer | 多租户配额隔离（当前按部门/项目；🚧 租户空间一等实体为演进方向，见 §4） | 业务线工作域、平台管理（跨租户运维） |
| **接入层** | Access Layer | 多入口统一接入与身份认证 | Web 控制台、RESTful API、CLI、Python SDK、在线开发环境 (Space)、SSO 网关、Webhook |
| **能力层** | Capability Layer | 模型全生命周期核心能力 + 平台治理横切 | ①数据管理 ②模型开发与训练 ③模型生命周期管理 ＋平台治理 |
| **核心服务层** | Core Service Layer | HyperPod 原生服务与可观测性 | HyperPod、监控可观测、日志告警、安全合规 |
| **基础设施层** | Infrastructure Layer | AWS 云资源底座 | 计算 (EKS/GPU)、存储 (S3/FSx)、网络 (VPC)、部署区域 (Multi-AZ) |

### 三大职责域速查

| 职责域 | 阶段 | 对应业务模块 |
|--------|------|-------------|
| **① 数据管理** | 数据接入 → 版本与质检 → 高速访问 | `datasets` |
| **② 模型开发与训练** | 实验/交互开发 → 分布式训练 → 检查点续训 | `training`、`spaces`、`monitoring` |
| **③ 模型生命周期管理** | 评估 → 注册审批 → 🚧 部署与推理监控 | `models` |
| **平台治理（横切）** | 隔离 · 配额 · 调度 · 计费 · 权限 · 审计 | `quotas`、`billing`、`auth`、`audit` |

### 核心架构约束

| 约束 | 说明 | 权威来源 |
|------|------|---------|
| **HyperPod Native-First** | 训练/调度/可观测优先用 HyperPod 原生能力，非自建 | 宪法 I |
| **多租户配额隔离** | 按部门/项目分配配额，逻辑隔离、配额独立 | 宪法 II · FR-008 |
| **共享底座** | 全租户复用同一套标准化能力与资源池，统一治理 | 宪法 II |
| **全生命周期可观测** | 训练指标监控反哺训练；🚧 推理监控闭环待部署能力落地 | 宪法 III |

---

## 1. 平台定位与目标

### 1.1 定位

平台为企业内**多条业务线的算法团队**构建**标准化基础能力**，目标是让各团队无需重复建设基础设施，即可在平台上完成模型的**开发、训练与部署**全生命周期工作（对齐项目宪法愿景）。

不同业务线在平台上以**逻辑隔离的工作域**形式共存：配额独立、数据互不可见、成员权限独立。

> **多租户实现状态**：当前以**配额维度**（部门/项目标签 + Kueue 队列）实现隔离（✅）；将其提升为独立的"租户空间 (TenantSpace)"一等实体是**已决策的演进方向**（🚧 待立项，见 §4.4）。

### 1.2 服务对象与价值

| 服务对象 | 核心诉求 | 平台提供的价值 |
|---------|---------|---------------|
| 算法工程师 | 专注建模，不关心底层运维 | 标准化训练/实验环境，开箱即用 |
| 数据工程师 | 数据资产高效管理 | 版本控制、质量保障、高速访问 |
| 平台管理员 | 跨租户资源治理 | 配额管理、全局监控、成本核算 |
| 业务线负责人 | 成本可见、资源公平 | 配额管理、按分钟计费、预算预警 |

### 1.3 核心目标 (北极星指标)

> 以下指标与 `spec.md` §Success Criteria 一致，KPI 变更须同步更新两处。

| 指标 | 目标 |
|------|------|
| GPU 资源利用率 | ≥ 70% |
| 训练成本降低 | ≥ 30% |
| 训练效率提升（周期缩短） | ≥ 50% |
| 系统可用性 | ≥ 99% |
| 故障恢复时间 | < 5 min |
| API P99 延迟 | < 3s |
| 并发用户支持 | ≥ 1000 |

---

## 2. 五层业务架构

> 自上而下，上层依赖下层；分层结构本身已表达调用方向，无需逐对连线。

### 2.1 租户层 (Tenant Layer)

每条业务线（推荐/NLP/CV/语音等）在平台上拥有一个**逻辑隔离的工作域**，外加跨租户的**平台管理**视角。

> 当前隔离机制与演进方向详见 §4 多租户架构。

### 2.2 接入层 (Access Layer)

| 入口 | 技术 | 主要用户 |
|------|------|---------|
| Web 控制台 | React + AWS Cloudscape | 全角色 |
| RESTful API | FastAPI | 系统集成 |
| CLI 工具 | hyperpod-cli | 算法工程师 |
| Python SDK | sagemaker-hyperpod | 算法工程师 |
| 在线开发环境 (Space) | SageMaker Spaces (JupyterLab) | 算法工程师 |
| SSO 网关 | SAML/OIDC | 企业身份集成 |
| Webhook | 事件通知 | 外部系统 (CI/CD、告警) |

> 术语注意：JupyterLab 环境统一称"在线开发环境 (Space)"或"开发空间"，**避免**使用"IDE/在线 IDE"（见 spec.md 命名规范）。

### 2.3 能力层 (Capability Layer)

平台核心。按 **模型全生命周期三大职责域 + 平台治理横切** 组织，详见 §3。

### 2.4 核心服务层 (Core Service Layer)

| 子域 | 关键组件 |
|------|---------|
| AWS SageMaker HyperPod | Cluster Mgmt、Training Operator、Task Governance (Kueue)、Spaces Add-on |
| 监控与可观测性 | Prometheus、Grafana、MLflow、HyperPod Observability Add-on |
| 日志与告警 | CloudWatch Logs、CloudWatch Alarms |
| 安全与合规 | IAM、KMS、CloudTrail、VPC |

### 2.5 基础设施层 (Infrastructure Layer)

| 子域 | 关键组件 |
|------|---------|
| 计算资源 | Amazon EKS、GPU 节点 (p4d/p5)、EFA 高速网络 |
| 存储资源 | Amazon S3、FSx for Lustre、NVMe SSD、Aurora MySQL |
| 网络资源 | VPC、ALB/NLB、PrivateLink |
| 部署区域 | Multi-AZ、AWS Region |

> 检查点采用分层存储：**NVMe → FSx for Lustre → S3**（宪法 IV）。

---

## 3. 模型全生命周期

> 平台的业务主线：数据 → 开发训练 → 部署运维。平台定位覆盖完整生命周期；部署段当前为 roadmap。

### 3.1 三大职责域与阶段

```
① 数据管理 ──数据就绪──▶ ② 模型开发与训练 ──产出模型──▶ ③ 模型生命周期管理
     ▲                                                          │
     └────────── 训练/推理指标反馈（🚧 完整推理闭环待部署落地）◀──┘
```

| 阶段 | 所属域 | 核心能力 | 业务模块 | 状态 |
|------|--------|---------|---------|------|
| 1. 数据接入与上传 | 数据管理 | 大文件分片、断点续传、多源接入 | `datasets` | ✅ |
| 2. 版本控制与质检 | 数据管理 | 数据集版本、差异比较、质量保障 | `datasets` | ✅ |
| 3. 高速访问 | 数据管理 | FSx Lustre、元数据管理、数据血缘 | `datasets` | ✅ |
| 4. 实验与交互式开发 | 开发与训练 | JupyterLab、实验追踪、超参管理 | `spaces`、`training` | ✅ |
| 5. 分布式训练 | 开发与训练 | DDP/FSDP/DeepSpeed、Gang Scheduling | `training` | ✅ |
| 6. 检查点与续训 | 开发与训练 | 分层存储、断点续训、指标监控 | `training`、`monitoring` | ✅ |
| 7. 模型评估 | 生命周期 | 指标评测、效果对比、质量门禁 | `models` | ✅ |
| 8. 注册与审批 | 生命周期 | Model Registry、审批流、血缘追踪 | `models` | ✅ |
| 9. 部署与推理监控 | 生命周期 | 模型部署、在线推理、性能监控 | `models`、`monitoring` | 🚧 roadmap |

> **阶段 9 状态说明**：`models` 模块当前仅有 `ModelStatus.DEPLOYED` 状态位与 `inference_specification` 透传字段，**无实际部署执行、推理 Endpoint 管理或推理监控采集能力**。该能力在平台定位范围内，但属规划中。

### 3.2 闭环要点

- **当前闭环**：阶段 6 的训练指标监控（`monitoring`）反哺训练调优，已实现。
- **🚧 完整闭环**：阶段 9 的推理监控数据回流至数据/训练，依赖部署能力落地后才能闭合（宪法 III 的完整形态）。
- **状态机一致性**：训练任务状态流转 `submitted → running → completed / failed / paused / preempted`，与 `spec.md` 一致。
- **抢占保护**：低优先级任务被抢占前自动创建检查点，保证数据不丢失（宪法 IV）。

---

## 4. 多租户架构

> 多租户是企业级平台的核心治理能力。**当前实现为配额维度隔离；提升为一等实体是已决策的演进方向。**

### 4.1 当前实现：配额维度隔离 (✅)

- 多租户通过 **`users` 的部门/项目标签 + `resource_quotas` 配额 + Kueue 队列** 表达，**非独立领域实体**。
- `spec.md` FR-008 原文：「按**部门/项目**分配资源配额，支持资源借用和限制」。
- 数据层：无独立 `tenant_id` 贯穿；隔离落在配额（ClusterQueue/LocalQueue）与权限（RBAC + 项目）维度。

### 4.2 五种隔离机制

| 隔离维度 | 实现机制 | 关联术语/模块 | 状态 |
|---------|---------|--------------|------|
| 命名空间隔离 | K8s Namespace | EKS | ✅ |
| 数据隔离 | S3 前缀 + IAM 策略 | `auth`、S3 | ✅ |
| 配额隔离 | ResourceQuota | `quotas` · FR-008 | ✅ |
| 权限隔离 | RBAC + 项目维度 | `auth` | ✅ |
| 调度隔离 | ClusterQueue / LocalQueue | Task Governance (Kueue) | ✅ |

> 调度隔离权威说明：资源配额与优先级**通过 HyperPod Task Governance API 配置**，仅状态监控/故障诊断时经 kubernetes-client 只读查询 Kueue CRD（需例外审批）。详见 spec.md §调度术语。

### 4.3 共享平台底座

| 底座能力 | 内容 |
|---------|------|
| 标准化能力 | 数据/训练/模型全流程标准化 |
| 弹性资源池 | HyperPod GPU 集群共享，按配额借用 |
| 统一可观测 | 监控/日志/告警/计费 |
| 安全合规 | IAM/KMS/审计/SSO |

### 4.4 演进方向：租户空间一等实体 (🚧 待立项)

> 已决策将多租户提升为独立领域实体，但**尚未立项实现**。本节为方向声明，正式设计须经独立 spec（`/speckit-specify`）。

- **目标**：引入 `TenantSpace` 实体，业务线 = 独立租户空间，封装专属数据集、模型仓库、实验空间、配额与成员。
- **改造面**（高风险，跨 9 模块）：新增 `tenant_spaces` 表 + 多表 `tenant_id` 外键 + 全链路查询过滤 + 数据迁移回填。
- **决策记录与改造点清单**：见 [`claudedocs/positioning-gap-analysis.md`](../../claudedocs/positioning-gap-analysis.md) §9.1。
- **约束**：在正式立项落地前，**不得**在代码中假设存在 `TenantSpace` 实体或 `tenant_id` 字段。

---

## 5. 架构原则对齐 (项目宪法)

> 产品架构必须与 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) 的核心原则一致（见 plan.md §Constitution Check）。

| 宪法原则 | 产品架构体现 |
|---------|-------------|
| **I. HyperPod Native-First** | 核心服务层完全基于 HyperPod 原生组件，不自建调度/训练引擎 |
| **I.B SDK-First** | 接入层提供 SDK/CLI，能力层封装 `sagemaker-hyperpod` SDK |
| **II. Multi-Tenant Governance** | 多租户配额隔离（部门/项目）+ 五种隔离机制 + Task Governance 三级优先级；🚧 租户一等实体演进中 |
| **III. Full Lifecycle Observability** | 训练指标监控 + 监控可观测子域已实现；🚧 推理监控闭环待部署能力落地 |
| **IV. Resilience & Auto-Recovery** | Auto-Resume + 分层检查点 (NVMe→FSx→S3) + 抢占前检查点 |

---

## 6. 术语标准对齐

> 完整术语见 [`spec.md`](../../specs/001-ai-training-platform/spec.md) §Terminology Standards。下表为产品架构高频术语速查。

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 集群 | `HyperPodCluster` | `hyperpod_clusters` | `/clusters` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |
| 审计日志 | `AuditLog` | `audit_logs` | `/audit-logs` |

**调度术语**：Task Governance（用户/API 层统一用语）、Kueue（底层引擎，仅监控/诊断提及）、ClusterQueue（集群级资源池）、LocalQueue（命名空间级队列）、PriorityClass（三级优先级 high/medium/low）。

> **保留术语**：`TenantSpace`（租户空间）为 §4.4 演进方向的预留实体名，当前代码中**不存在**，立项后以新 spec 为准。

---

## 7. 可视化参考

平台架构的三张可视化图表（飞书画板，可在线编辑）：

| 图 | 视角 | 内容 |
|----|------|------|
| 业务架构总览 | 五层分层 | 租户层 → 接入层 → 能力层 → 核心服务层 → 基础设施层 |
| 全生命周期闭环 | 流程闭环 | 三大职责域横向流转 + 指标反馈 |
| 多租户架构 | 隔离模型 | 业务线工作域 → 五种隔离 → 共享底座 → AWS 基础设施 |

> 飞书文档：https://www.feishu.cn/docx/MAa4d2ZB1obydZx23YPc8aGnnBb
>
> ⚠️ **图文差异说明**：飞书画板创建于本规范修订前，图中仍使用"LLMOps""租户层/租户空间"等旧措辞，且未标注 roadmap 状态。**图为辅助理解的可视化参考，术语与能力状态的权威源以本规范与 spec.md 为准**，二者不一致时以文字规范为准。

---

## 交叉引用

| 内容 | 文档 |
|------|------|
| 定位差距诊断与决策记录 | [claudedocs/positioning-gap-analysis.md](../../claudedocs/positioning-gap-analysis.md) |
| 技术实现架构（DDD 分层、模块隔离、依赖方向） | [backend/.claude/rules/architecture.md](../../backend/.claude/rules/architecture.md) |
| 完整功能需求与术语标准 | [specs/001-ai-training-platform/spec.md](../../specs/001-ai-training-platform/spec.md) |
| 技术选型、宪法检查、里程碑 | [specs/001-ai-training-platform/plan.md](../../specs/001-ai-training-platform/plan.md) |
| 项目宪法（不可违反的核心原则） | [.specify/memory/constitution.md](../../.specify/memory/constitution.md) |
| 数据模型设计 | [specs/001-ai-training-platform/data-model.md](../../specs/001-ai-training-platform/data-model.md) |
| Git 提交规范、文档命名等通用规则 | [.claude/rules/common.md](common.md) |
