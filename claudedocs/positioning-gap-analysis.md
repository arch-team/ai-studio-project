# 定位一致性诊断报告：规范 / 技术方案 / 选型 / 实现 vs 平台定位

> **日期**: 2026-06-13
> **范围**: 对照"企业级多租户 LLMOps 训练平台"定位，审查 spec / plan / constitution / product-architecture 四份规范与后端实际代码的差距与冲突
> **方法**: 文档原文比对 + 代码 grep 取证（非推测）
> **性质**: 诊断报告，不含任何文件修改

---

## 0. 执行摘要

差距的最大来源**不是"实现没跟上定位"**，而是**规范层对定位的措辞不统一，且上一轮新增的 `product-architecture.md` 将定位向 "LLMOps / 一等租户" 方向拔高，超出了 spec 和代码的实际范围**。

```
冲突来源分布（按性质）
─────────────────────────────────────────────
规范拔高定位（product-architecture）  ~50%   规范 > spec ≈ 实现
spec 与 constitution 措辞不统一        ~25%   历史遗留
实现欠账（billing 缺 Domain 等）       ~25%   实现 < spec（真实技术债）
```

**核心结论**：当前代码实现与 `spec.md` 的"AI 训练平台"定位**基本一致**；分歧主要出在规范文档之间，需要先统一定位措辞，再谈实现演进。

---

## 1. 三方定位措辞分歧（🔴 根因）

| 来源 | 自我定位原文 | 范围关键词 | 是否含"部署/推理" |
|------|------------|-----------|------------------|
| `spec.md`（标题 + Input） | "企业级 **AI 训练平台**" | 模型训练、算力调度、数据管理、多租户、成本核算 | ❌ 不含 |
| `constitution.md`（愿景声明 L64） | "统一的企业级 **AI 平台**…自助式模型**开发、训练和部署**" | 开发 + 训练 + **部署** | ✅ 含部署 |
| `product-architecture.md`（上一轮新增） | "企业级**多租户 LLMOps** 训练平台" | LLMOps、全生命周期闭环 | ✅ 含部署+推理监控 |

**取证**：
- `grep "LLMOps" spec.md` → **0 命中**。"LLMOps""全生命周期闭环"为上一轮基于用户口头描述 + 架构图演绎引入，非 spec 原生术语。
- `spec.md` 中"训练平台"出现在标题、Input、对外宣传定义（L228）。

**影响**：三者范围递增（训练 ⊂ 含部署 ⊂ LLMOps），直接决定"模型部署/推理服务是否属于平台范围"这一边界问题（见 §3）。

---

## 2. "LLMOps" 名称与实际能力不符（🟡）

`product-architecture.md` 使用 "LLMOps"（大模型运维），但 spec 与代码均无 LLM 特有能力。

**取证（grep 全部 0 命中）**：
| LLM 特性 | 关键词 | 代码命中 |
|---------|--------|---------|
| 微调 | LoRA / SFT / RLHF / fine-tune / 微调 | ❌ |
| 推理优化 | vLLM / 量化 / quantize | ❌ |
| Prompt / 检索 | prompt / embedding / 向量 / RAG | ❌ |
| token 计费 | token 计费 | ❌ |

**实际能力**：通用 PyTorch 分布式训练（DDP / FSDP / DeepSpeed ZeRO，见 spec L633-638）。训练对象是通用深度学习模型，非专门面向 LLM。

**建议措辞**：准确表述为 **"AI 训练平台"** 或 **"MLOps 训练平台"**；"LLMOps" 属夸大。

---

## 3. 模型部署/推理：规范声称闭环，实现仅有状态位（🔴 边界问题）

`product-architecture.md` §3 描述了"阶段 9：部署与推理监控"和"推理数据回流闭环"，但实现层并不存在真正的部署/推理能力。

**取证**（`models` 模块）：
- ✅ 有：`ModelStatus.DEPLOYED` 状态枚举、`inference_specification` 透传字段、`is_deployed()` 判断方法。
- ❌ 无：任何执行部署的 Service、推理 Endpoint 管理、Serving 适配器、推理监控采集。

**判定**：代码只**记录**"模型已部署"这一状态标记，**不具备**部署/推理服务能力。这印证实现是按"训练平台 → 模型注册到 Registry 即结束"做的，`product-architecture.md` 的"全生命周期闭环"超前于实现与 spec。

---

## 4. 多租户：概念被拔高为一等实体，实现是配额维度（🔴 最实质）

| 层 | 多租户的表达方式 | 取证 |
|----|-----------------|------|
| `spec.md` FR-008 | "按**部门/项目**分配资源配额" + ClusterQueue/LocalQueue 隔离 | L711 原文 |
| `data-model.md` | **无 `tenants` 表**；9 张表无独立 `tenant_id` 贯穿；靠 `resource_quotas` + `users.department/project` 表达 | 表清单 §1-9 |
| 后端代码 | `grep -i tenant` → **0 命中**；无 `Tenant` 实体、无 `tenant_id`、无 `TenantSpace` | 全 backend |
| `product-architecture.md` | "**租户空间 (Tenant Space) 作为第一类概念**""租户即隔离边界""租户层" | §0/§4 |

**判定**：spec 与实现中，多租户是**配额管理的一个维度**（department/project 标签 + Kueue 队列隔离），**不是独立领域对象**。`product-architecture.md` 将其拔高为"租户层 / 租户空间实体"，属**规范引入的冲突**，非实现欠账。

**两个可选方向**（取决于 §7 定位裁决）：
- (a) 降级规范措辞：把"租户空间一等实体"改为"多租户配额隔离（按部门/项目）"，对齐 spec/代码。
- (b) 接受演进决策：明确"将多租户提升为一等实体"是有意的架构演进，需补 `tenants` 表 + `tenant_id` 改造 + 迁移（成本高，需立项）。

---

## 5. 实现内部的真实技术债（与定位无关）

| 项 | 现状 | 违反 | 级别 |
|----|------|------|------|
| `billing` 模块缺 Domain 层 | 仅 `application/services`（cost_calculator/pricing_model 等 7 个）+ api，**无 entities/value_objects** | `backend/.claude/rules/architecture.md`（DDD 要求 Domain 层建模） | 🟡 |
| `monitoring` Domain 偏薄 | 仅 `hyperpod_cluster.py` 一个实体 | spec 要求训练指标监控 + 告警，领域建模不足 | 🟢 |
| 前后端模块映射 | 后端 9 业务模块 / 前端 13 features | `admin/dashboard/reports` 为前端聚合视图（合理）；`resource-quotas↔quotas`、`templates↔training` 对应 | ✅ 无缺口 |

---

## 6. 一致的部分（避免以偏概全）

为保持评估平衡，以下维度**规范与实现一致**：

- ✅ **HyperPod Native-First**（宪法 I）：代码确用 `sagemaker-hyperpod` SDK，未自建训练/调度引擎。
- ✅ **三级优先级调度**（宪法 II）：PriorityClass high/medium/low 与 spec 一致。
- ✅ **分层检查点**（宪法 IV）：NVMe→FSx→S3 在 spec L741 与 training 模块均有体现。
- ✅ **核心实体术语**：TrainingJob/Dataset/Checkpoint/Model/ResourceQuota/Space 代码命名与 spec 术语表一致。
- ✅ **DDD 分层**（除 billing 外）：training/datasets/models/auth 等模块 entities/services/repositories 结构完整。

---

## 7. 待裁决：项目真实定位

修正方向取决于定位裁决，三种可能：

| 选项 | 以谁为准 | 部署/推理 | 对 product-architecture.md 的处理 |
|------|---------|----------|----------------------------------|
| **A. AI/MLOps 训练平台** | spec.md | 不含（到 Registry 止） | 从 LLMOps 降级为"AI 训练平台"，多租户降级为配额维度 |
| **B. 含部署的全生命周期平台** | constitution.md | 含（标为 roadmap） | 保留闭环描述，但明确标注部署/推理"待实现" |
| **C. LLMOps 平台** | product-architecture.md | 含 + LLM 特性 | 规范引领，spec/代码补 LLM 能力 + 租户实体（成本最高） |

---

## 8. 建议的后续动作（按裁决展开）

1. **统一定位措辞**：spec / constitution / product-architecture 三处定位句改为一致表述（一次性 docs 提交）。
2. **修正 product-architecture.md**：按裁决降级或标注 roadmap，消除"规范 > 实现"的悬空承诺。
3. **补 billing Domain 层**：抽出 `CostRecord` / `BudgetAlert` 等实体，对齐 DDD 规范（独立技术债，可单独排期）。
4. **（如选 C）立项**：LLM 能力 + 租户一等实体改造需独立 spec + 数据迁移，不应隐含在"修规范"里。

---

---

## 9. 决策结论（2026-06-13 用户逐项裁决）

| Gap | 决策 | 落实动作 |
|-----|------|---------|
| **1. 定位** | **含部署的全生命周期平台（对齐 constitution）** | 范围 = 开发 + 训练 + 部署；修正 product-architecture.md 定位句 |
| **2. 名称** | **「企业级 AI 平台」**（去掉 "LLMOps"） | product-architecture.md 全文改名，对齐宪法愿景原词 |
| **3. 部署/推理** | **标为 roadmap 待实现** | 规范保留"部署+推理监控"阶段，明确标注 ⚠️ 未实现 |
| **4. 多租户** | **立项改造为一等实体**（演进目标） | 规范标注当前为配额维度实现 + 一等实体为演进方向；立项建议见 §9.1 |
| **5. billing 技术债** | **登记，不立即修** | 见 §9.2 技术债登记 |

### 9.1 立项建议：多租户一等实体改造（待立项，本次不写 spec）

> 用户裁决"立项改造为一等实体"，但本次仅登记建议，**不生成正式 spec**。后续可用 `/speckit-specify` 单独启动。

**目标**：将多租户从"配额维度（department/project 标签 + Kueue 队列隔离）"提升为独立领域实体 `TenantSpace`。

**改造点清单**（供未来立项参考）：
- **数据层**：新增 `tenant_spaces` 表；为 `users / datasets / training_jobs / models / resource_quotas / checkpoints` 等表增加 `tenant_id` 外键。
- **领域层**：新增 `auth` 或独立 `tenants` 模块的 `TenantSpace` 实体 + 仓库接口。
- **隔离改造**：数据查询全链路注入 `tenant_id` 过滤；S3 前缀按 tenant 划分；K8s Namespace 与 tenant 绑定。
- **迁移**：现存数据按 department/project 回填 tenant_id 的数据迁移脚本（Alembic + 数据回填）。
- **影响面**：跨 9 个模块的破坏性改造，需独立 feature spec + 数据迁移演练 + 回滚预案。
- **风险**：高（涉及全表外键与查询改造），建议作为独立里程碑，不与现有功能开发混排。

### 9.2 技术债登记：billing 模块缺 Domain 层

> 用户裁决"先记录，不立即修"。

- **现状**：`billing` 仅有 `application/services`（cost_calculator / pricing_model / cost_allocation / usage_aggregator / report_service 等 7 个）+ api 层，无 `domain/entities` 与 `domain/value_objects`。
- **违反**：`backend/.claude/rules/architecture.md` 的 DDD 分层要求（业务规则应在 Domain 层建模）。
- **建议修复方向**（未来排期）：抽出 `CostRecord`（成本记录）、`BudgetAlert`（预算预警，对应多级 80%/90%/100% 阈值）、`BillingPeriod`（计费周期）等值对象/实体，将散落在 service 的业务规则下沉至 Domain。
- **优先级**：🟡 中（不阻塞功能，但累积会侵蚀架构一致性）。

---

> **本报告为诊断 + 决策记录。** §9 决策已确认；规范层修正（Gap 1/2/3/4）将同步落实到 `.claude/rules/product-architecture.md`。Gap 4 立项与 Gap 5 重构本次不执行，仅登记。
