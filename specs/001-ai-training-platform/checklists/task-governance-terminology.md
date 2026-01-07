# Checklist: HyperPod Task Governance 与 Kueue 术语清晰性

**目的**: 验证项目文档中关于 HyperPod Task Governance 和 Kueue 的表述是否清晰、一致且无歧义,确保开发团队准确理解技术边界和使用场景。

**创建时间**: 2026-01-05
**适用范围**: spec.md、plan.md、tasks.md 全文档
**检查深度**: 标准 (terminology clarity + consistency)

---

## Requirement Completeness (术语定义完整性)

### 核心术语定义

- [x] CHK001 - HyperPod Task Governance 是否在首次出现时明确定义为"AWS 原生资源调度组件,基于 Kueue 实现"? [Completeness, Spec §L38-42] ✅ 已在 Terminology Standards 增加调度和资源管理术语子章节
- [x] CHK002 - Kueue 是否明确定义为"底层开源调度引擎,被 HyperPod Task Governance 集成"? [Completeness, Spec §L43] ✅ 术语表已定义
- [x] CHK003 - 是否明确说明 HyperPod Task Governance 与 Kueue 的层级关系(封装/抽象关系)? [Clarity, Spec §L42-43] ✅ 术语表已说明"基于 Kueue 开源引擎封装"
- [x] CHK004 - 是否定义了术语"Kueue Workload"并说明其与训练任务(TrainingJob)的映射关系? [Completeness, Spec §L44] ✅ 术语表已定义映射关系

### 职责边界定义

- [x] CHK005 - 是否明确说明 HyperPod Task Governance 负责的功能范围(资源配额、优先级调度、抢占策略)? [Completeness, Spec §FR-004/FR-008] ✅ 已在术语表添加功能范围总结表(Spec §L55-63)
- [x] CHK006 - 是否明确说明 Kueue 负责的底层能力(Workload 调度、Queue 管理、Gang Scheduling)? [Completeness, Gap] ✅ 已在术语表添加"Kueue 底层能力说明"小节(Spec §L65-74)
- [x] CHK007 - 是否明确说明用户/开发者应该使用哪个抽象层(Task Governance API vs Kueue API)? [Clarity, Gap] ✅ 已在术语表添加"抽象层使用决策指南"表格(Spec §L76-91)

---

## Requirement Clarity (术语使用清晰性)

### 一致性用词

- [x] CHK008 - 在描述资源配额管理时,是否统一使用"HyperPod Task Governance"而非"Kueue"? [Consistency, Spec §FR-008] ✅ 已为 FR-008 增加实施约束(Spec §L913-915) & 修改 ResourceQuota 定义强调管理抽象层(Spec §L1017)
- [ ] CHK009 - 在描述底层调度状态(Workload.status.admission)时,是否明确说明这是"Kueue CRD 状态"? [Clarity, Spec §Training Job State Model L373-389]
- [ ] CHK010 - 在描述抢占策略时,是否统一表述为"HyperPod Task Governance 原生抢占机制(基于 Kueue Preemption)"? [Consistency, Spec §FR-004 L766-775]
- [ ] CHK011 - 在描述优先级配置时,是否统一表述为"Kueue PriorityClass: high/medium/low,由 HyperPod Task Governance 管理"? [Consistency, Spec §FR-004 L771]

### 歧义消除

- [ ] CHK012 - 当同时提及"Kueue"和"Task Governance"时,是否清楚说明上下文关系(避免读者误解为两个独立组件)? [Ambiguity, Spec §FR-004]
- [ ] CHK013 - 在状态转换描述中,是否明确区分"用户层状态(TrainingJob.status)"和"Kueue 层状态(Workload.conditions)"? [Clarity, Spec §Training Job State Model L312-343]
- [ ] CHK014 - 在 tasks.md 任务描述中,是否清晰说明哪些任务需要直接操作 Kueue CRD(如有),并标注例外审批需求? [Clarity, Tasks §T008d-1]

---

## Requirement Consistency (跨文档一致性)

### spec.md vs plan.md 一致性

- [ ] CHK015 - spec.md FR-004 抢占策略描述与 plan.md Technical Context 中 HyperPod Task Governance 描述是否一致? [Consistency, Spec §FR-004 vs Plan §L13]
- [ ] CHK016 - spec.md Terminology Standards 中"资源配额"定义是否与 plan.md 中 Kueue PriorityClass 描述一致? [Consistency, Spec §L959 vs Plan §L119]
- [ ] CHK017 - spec.md Training Job State Model 中 Kueue 状态映射逻辑与 plan.md Phase 1 基础设施描述是否一致? [Consistency, Spec §L373-389 vs Plan §L223]

### spec.md vs tasks.md 一致性

- [ ] CHK018 - tasks.md T008d-1 任务描述的"Task Governance (Kueue)"表述是否与 spec.md FR-004 定义一致? [Consistency, Tasks §L220-224 vs Spec §FR-004]
- [ ] CHK019 - tasks.md T036 HyperPod SDK 集成任务中,是否清晰说明不直接操作 Kueue API(遵循 SDK-First 原则)? [Consistency, Tasks §L399 vs Spec Constitution]
- [ ] CHK020 - tasks.md T037 状态同步服务描述是否明确区分"HyperPod SDK 状态查询"和"Kueue Workload 细粒度监控"的使用场景? [Clarity, Tasks §L407 vs Spec §Training Job State Model]

---

## Scenario Coverage (使用场景覆盖)

### 标准使用场景

- [ ] CHK021 - 是否明确说明开发者通过 HyperPod SDK 提交训练任务,底层自动调用 Task Governance,无需手动操作 Kueue? [Coverage, Spec §FR-001]
- [ ] CHK022 - 是否明确说明资源配额配置通过 HyperPod Task Governance API,而非直接修改 Kueue ClusterQueue? [Coverage, Spec §FR-008]
- [ ] CHK023 - 是否明确说明优先级调度由 Task Governance 管理,开发者仅需指定 high/medium/low 优先级? [Coverage, Spec §FR-004]

### 例外场景

- [ ] CHK024 - 是否明确定义在哪些场景下可能需要直接查询 Kueue Workload CRD(如细粒度状态监控)? [Gap, Exception Flow]
- [ ] CHK025 - 是否明确说明直接操作 Kueue CRD 的例外场景需要治理委员会审批(遵循宪章 Principle I.B)? [Coverage, Exception Flow]
- [ ] CHK026 - 是否明确说明当 HyperPod SDK 不支持某些 Kueue 高级特性时,备选方案是 kubernetes-client 而非绕过 Task Governance? [Coverage, Exception Flow]

---

## Acceptance Criteria Quality (验收标准可测量性)

### FR-004 抢占策略验收

- [ ] CHK027 - FR-004 抢占策略的验收标准是否可客观验证(如"高优先级任务成功抢占低优先级任务资源")? [Measurability, Spec §FR-004]
- [ ] CHK028 - FR-004 验收标准是否明确基于 HyperPod Task Governance 行为测试,而非直接测试 Kueue 内部逻辑? [Clarity, Spec §FR-004]

### FR-008 资源配额验收

- [ ] CHK029 - FR-008 资源配额的验收标准是否明确测试"通过 Task Governance API 配置配额"而非"直接修改 Kueue ClusterQueue YAML"? [Measurability, Spec §FR-008]
- [ ] CHK030 - FR-008 验收标准是否包含"配额限制正确应用到训练任务调度"这一端到端场景? [Coverage, Spec §FR-008]

### 状态转换验收

- [ ] CHK031 - Training Job State Model 的验收标准是否明确区分"用户可见状态转换"和"底层 Kueue Workload 状态变化"? [Clarity, Spec §Training Job State Model L471-485]
- [ ] CHK032 - 状态转换测试是否可以仅通过 HyperPod SDK API 验证,无需直接查询 Kueue CRD? [Measurability, Spec §Training Job State Model]

---

## Dependencies & Assumptions (依赖和假设)

### 技术依赖假设

- [ ] CHK033 - 是否明确假设 HyperPod Task Governance 完全封装 Kueue 功能,开发者无需理解 Kueue 内部实现? [Assumption, Spec Constitution]
- [ ] CHK034 - 是否明确假设 Kueue 版本兼容性由 HyperPod 平台维护,项目不需要单独管理 Kueue 升级? [Assumption, Gap]
- [ ] CHK035 - 是否明确假设 HyperPod SDK 提供的状态信息足够支持所有用户场景,无需绕过 SDK 查询 Kueue? [Assumption, Spec §FR-002]

### 组件边界假设

- [ ] CHK036 - 是否明确假设 Task Governance 是唯一的资源调度接口,不允许直接创建/修改 Kueue Workload CRD? [Assumption, Spec Constitution]
- [ ] CHK037 - 是否明确假设 Gang Scheduling 配置由 Task Governance 托管,开发者无需理解 Kueue Gang Scheduling 参数? [Assumption, Spec §FR-003]
- [ ] CHK038 - 是否明确假设抢占冷却期、借用策略等高级参数由 Task Governance 默认配置,无需定制化? [Assumption, Spec §FR-004 L771-775]

---

## Ambiguities & Conflicts (模糊性和冲突)

### 术语模糊性

- [ ] CHK039 - 在描述"Kueue 接纳成功"时,是否可能被误解为需要直接调用 Kueue API? [Ambiguity, Spec §Training Job State Model L349]
- [ ] CHK040 - 在描述"配置 Kueue ClusterQueue"时,是否可能被误解为手动修改 YAML 文件? [Ambiguity, Tasks §T008d-1 L223]
- [ ] CHK041 - 在描述"查询 Kueue Workload 状态"时,是否明确说明这是通过 HyperPod SDK 还是 kubernetes-client? [Ambiguity, Tasks §T037 L407]

### 实施冲突

- [ ] CHK042 - spec.md 强调"使用 HyperPod Task Governance 原生机制"与 tasks.md 中"MAY 使用 kubernetes-client 配置 Kueue"是否存在冲突? [Conflict, Spec §FR-004 vs Tasks §T008d-1]
- [ ] CHK043 - spec.md Constitution "SDK-First 原则"与 tasks.md 中多处"kubernetes-client 备选方案"是否存在冲突? [Conflict, Spec Constitution vs Tasks §T037/T036]
- [ ] CHK044 - spec.md FR-004 "完全采用 HyperPod 原生抢占规则"与 tasks.md T008d-1 "不做自定义扩展"描述是否一致? [Consistency, Spec §FR-004 L771 vs Tasks §T008d-1 L224]

---

## Traceability (可追溯性)

### 术语定义溯源

- [ ] CHK045 - 是否提供 HyperPod Task Governance 官方文档链接作为术语定义权威来源? [Traceability, Gap]
- [ ] CHK046 - 是否提供 Kueue 官方文档链接并说明其与 Task Governance 的关系? [Traceability, Gap]
- [ ] CHK047 - spec.md 中引用的 Kueue Preemption Documentation 是否与 HyperPod 官方文档一致? [Traceability, Spec §FR-004 L224]

### 需求溯源

- [ ] CHK048 - FR-004 抢占策略需求是否可追溯到 HyperPod Task Governance 功能文档? [Traceability, Spec §FR-004]
- [ ] CHK049 - FR-008 资源配额需求是否可追溯到 Kueue ClusterQueue/LocalQueue 设计文档? [Traceability, Spec §FR-008]
- [ ] CHK050 - Training Job State Model 中的 Kueue 状态映射逻辑是否可追溯到 Kueue API 规范? [Traceability, Spec §Training Job State Model L373-389]

---

## 检查清单元数据

- **总检查项**: 50 项
- **高优先级项** (阻塞性模糊): CHK001-CHK007, CHK012-CHK014, CHK039-CHK044 (17 项)
- **覆盖率目标**: ≥90% 检查项标注具体文档位置引用 (已达成)
- **预期使用场景**:
  - 技术写作审查 (technical writer review)
  - 开发团队理解验证 (developer onboarding)
  - 架构决策记录更新 (ADR refinement)
- **建议修复优先级**:
  1. 消除术语模糊性 (CHK039-CHK041)
  2. 解决实施冲突 (CHK042-CHK044)
  3. 补充核心术语定义 (CHK001-CHK004)
  4. 增强可追溯性 (CHK045-CHK050)
