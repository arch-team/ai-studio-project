# 前端 UI/UX 商用化质量体系设计

> 日期: 2026-06-12
> 状态: 已确认（用户逐节审批通过）
> 范围: `frontend/` 子项目（React + Cloudscape，13 个 feature 模块 = 12 个业务模块 + dashboard）

---

## 1. 背景与目标

### 1.1 问题陈述

当前前端项目由 Claude Code 开发，功能层面可用，但距离"商用产品"的 UI/UX 水准存在四类系统性差距（用户确认）：

1. **页面信息架构与布局** — 页面组织像"功能堆砌"，信息层级不清，缺少 Dashboard 级的全局体验设计
2. **交互完整度与细节** — 加载/空/错误状态缺失或敷衍、操作反馈不到位、表单体验生硬、缺少引导文案
3. **一致性与整体感** — 各模块各自为政：列表页、详情页、表单页模式不统一，术语和文案漂移
4. **视觉风格本身** — Cloudscape 默认样式过于"AWS 控制台"，缺乏自有产品感

### 1.2 目标

构建一套**审计驱动**的系统化方案，使 Claude Code 后续开发和改造的前端页面稳定达到商用产品 UI/UX 水准。"商用水准"的判定方式为 **Claude 自审评分 + 用户抽查**。

### 1.3 关键决策（澄清阶段确认）

| 决策点 | 结论 |
|--------|------|
| 视觉定制深度 | Design Token 级定制（Cloudscape Theming API，不破坏组件体系） |
| 视觉基准来源 | 参照标杆 ML 平台（Databricks、W&B、Vertex AI）提炼 |
| 方案组成 | 设计规范层 + Claude Code 工作流层 + 验证闭环层 + 存量改造计划（四层全选） |
| 构建路径 | 方案 C：审计驱动（先全量审计 → 靶向定规范 → 按严重度修复） |
| 验收方式 | Claude 自审评分报告 + 用户抽查关键页面 |

---

## 2. 总体架构：审计驱动五阶段

```
阶段 0: 审计基础设施              阶段 1: 全量审计           阶段 2: 靶向规范
┌──────────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ 截图流水线 (Playwright)│      │ 13 模块全页面      │      │ Design Tokens    │
│ 评分框架定义           │ ───► │ 四维度评分         │ ───► │ 页面模板          │
│ /ui-audit skill      │      │ 问题清单+审计报告   │      │ UX 文案规范       │
│ design-reviewer agent│      │ (= /ui-audit 首跑) │      │ 交互状态矩阵       │
└──────────────────────┘      └──────────────────┘      └──────────────────┘
                                                                 │
阶段 4: 批量修复+回归          阶段 3: 工作流固化                  ▼
┌──────────────────┐      ┌──────────────────┐
│ 三批次修复         │ ◄─── │ rules 增强        │
│ 每批审计回归       │      │ /ui-fix skill    │
│ DoD: 见 §7        │      │ (引用阶段2规范)    │
└──────────────────┘      └──────────────────┘
```

**核心逻辑**：先用真实截图建立"现状基线"，让规范针对实际问题而非凭空制定；规范固化为 Claude Code 可执行机制后，修复过程本身就是对闭环的持续验证。

**阶段职责澄清**（评分独立性与刻度可比性的保障）：

- **`/ui-audit` skill 和 `design-reviewer` agent 在阶段 0 创建**——基线评分（阶段 1）与后续回归评分（阶段 4）必须出自同一把尺子（同一 agent + 同一评分 prompt），否则前后分数不可比。
- 阶段 1 的全量审计即 `/ui-audit` 的首次运行，评分全程由 design-reviewer agent 在独立上下文完成，主上下文不评分。
- 阶段 0 创建的 agent 评分依据为 §3.2 评分框架 + 锚点（此时阶段 2 规范尚未存在，属预期行为：基线衡量"现状离商用直觉有多远"）；阶段 2 规范产出后更新 agent 的评审输入清单，阶段 4 回归评分增加"是否符合四份规范"的判定依据。
- `/ui-fix` skill 依赖阶段 2 的规范与模板，故在阶段 3 创建。

---

## 3. 阶段 0：审计基础设施

### 3.1 截图流水线

复用现有 Playwright 配置（`frontend/playwright.config.ts`、`e2e/` 的认证前置和 MockApi 设施），新增独立的截图脚本目录：

```
frontend/e2e/audit/
├── screenshot-pipeline.spec.ts   # 遍历所有路由 × 关键状态截图
├── routes-manifest.ts            # 路由清单（13 模块全页面 + 状态变体）
└── audit-output/                 # 截图产出（gitignore，按日期归档）
    └── 2026-06-12/
        ├── training-list-default.png
        ├── training-list-empty.png
        ├── training-list-error.png
        └── ...
```

**截图覆盖矩阵**：每个页面 × 4 种状态（默认有数据 / 空状态 / 加载中 / 错误）× 2 主题（Light/Dark）。状态通过 MockApi 注入（复用 e2e 现有 route interception 设施）。对页面类型不适用的状态按 §5.4 状态矩阵中的 "-" 豁免（如表单页无列表空状态），不机械凑数。

### 3.2 四维度评分框架

每个页面按四个维度评分（1-5 分），对应用户确认的四类差距：

| 维度 | 权重 | 评分要点 |
|------|------|---------|
| **信息架构 (IA)** | 30% | 信息层级清晰度、扫描效率、主次操作区分、关键信息可达性（与同类商用 ML 平台对照） |
| **交互完整度 (IX)** | 30% | 四态完备（loading/empty/error/success）、操作反馈、表单验证体验、引导与帮助文案 |
| **一致性 (CONS)** | 25% | 同类页面模式统一（列表/详情/表单/Dashboard 四大模式）、术语与文案一致、组件用法一致 |
| **视觉品质 (VIS)** | 15% | Token 应用正确性、间距节奏、暗色模式无瑕疵、整体专业感 |

**评分锚点**（统一刻度，避免主观漂移）：

- **5** = 可直接对外演示给客户，与 Databricks/W&B 同屏不违和
- **4** = 商用可接受，有可挑剔的小瑕疵
- **3** = 内部工具水准，功能完整但体验生硬
- **2** = 有明显缺陷（状态缺失、布局混乱）
- **1** = 不可用或严重破损

**页面综合分** = 加权平均。**商用门槛 = 4.0**。

### 3.3 审计报告产出

```
frontend/docs/audit/
├── 2026-06-12-baseline/
│   ├── audit-report.md          # 总报告：每页评分表 + Top 问题归类
│   ├── findings.md              # 问题清单（每条含截图引用、严重度、所属维度）
│   └── score-matrix.md          # 13 模块 × 4 维度评分矩阵
```

问题按严重度分级：**P0**（破坏可用性/可信度，如错误状态白屏）、**P1**（明显不专业，如空状态只有一行字）、**P2**（打磨项，如间距不齐）。

---

## 4. 阶段 1：全量审计执行

- 运行 `/ui-audit all`：截图流水线对 13 个模块（training, datasets, models, spaces, audit, billing, monitoring, templates, reports, admin, auth, resource-quotas, dashboard）的全部页面生成基线截图
- design-reviewer agent 逐页按评分框架打分（独立上下文），输出审计报告三件套
- 审计结论直接驱动阶段 2 的规范内容优先级：**问题出现频率最高的模式优先写入规范**

---

## 5. 阶段 2：靶向设计规范层（四份产出）

> 位置：`specs/design-system/`（与现有 `specs/001-ai-training-platform/` 平级，作为跨 feature 的设计规范）

### 5.1 `design-tokens.md` + 实现

**视觉方向**（从 Databricks/W&B/Vertex AI 提炼的共性）：

- 深色侧边导航 + 浅色中性主体内容区
- 单一品牌强调色（蓝紫色系），状态色语义化且克制
- 数据密集型排版：紧凑行高、等宽数字字体（指标/ID 场景）

**实现方式**：Cloudscape 官方 Theming API（`applyTheme` + design tokens 覆盖），新增：

```
frontend/src/app/theme/
├── theme.ts          # applyTheme 配置：品牌色、圆角、字体 token 覆盖
└── index.ts
```

**约束更新**：`tech-stack.md` 的"禁止自定义 CSS"修订为——
- ✅ 允许：`app/theme/` 内的 Cloudscape Theming API 配置
- ❌ 仍禁止：组件级自定义 CSS、内联样式、绕过 Cloudscape 的样式 hack

### 5.2 `page-templates.md`（四大页面模式模板）

每个模板定义：区域结构图（ASCII）、必备元素清单、Cloudscape 组件映射、可复制的代码骨架。

1. **列表页模板**：Header（标题+计数+主操作）→ 筛选区（属性过滤+搜索）→ Table（排序/分页/列偏好/批量操作）→ 四态处理（含空状态引导：图标+说明+CTA 按钮）
2. **详情页模板**：BreadcrumbGroup → Header（状态+生命周期操作组）→ 概览 KeyValuePairs 容器 → Tabs（子资源/日志/监控）→ 轮询刷新模式
3. **表单/向导页模板**：单页表单（Form + Container 分组 + FormField 校验）与多步 Wizard 的选择标准、字段帮助文案规范、提交反馈链路（禁用按钮 → Spinner → Flashbar → 跳转）
4. **Dashboard 模板**：指标卡行（关键数字+趋势）→ 主图表区 → 最近活动/快捷入口，信息密度与留白平衡基准

### 5.3 `ux-writing.md`（UX 文案规范）

- 术语表：与 `specs/001-ai-training-platform/spec.md` 术语标准对齐，扩展 UI 场景用语（按钮动词、状态名词统一）
- 文案模式：空状态（说明+引导 CTA）、错误信息（发生了什么+怎么办）、确认对话框（后果说明）、表单帮助文本（constraintText/description 分工）
- 语气基准：专业、直接、无废话；中文文案标点与空格规范

### 5.4 `interaction-states.md`（交互状态矩阵）

每类异步交互的完整状态机及对应 Cloudscape 实现：

| 场景 | loading | empty | error | success | 部分失败 |
|------|---------|-------|-------|---------|---------|
| 列表查询 | Table loading | 引导式空状态 | 重试式错误 | - | - |
| 详情查询 | Container loading | 404 页 | 错误 Alert + 返回 | - | - |
| 创建/编辑提交 | 按钮 loading + 禁用 | - | 字段级 + Flashbar | Flashbar + 跳转 | - |
| 危险操作 | Modal 内 loading | - | Modal 内 Alert | Flashbar + 列表刷新 | 批量操作逐项反馈 |
| 长任务（训练） | 状态轮询 + 进度 | - | 失败原因展示 | 完成通知 | - |

---

## 6. Claude Code 工作流组件（阶段 0 与阶段 3 分批交付）

### 6.1 rules 增强（阶段 3）

- `frontend/.claude/rules/component-design.md` → 引用四大页面模板，新增"新页面必须声明所属模式"规则
- `frontend/.claude/rules/checklist.md` → 注入四维度评分自检条目
- `frontend/CLAUDE.md` → 文档导航表加入 `specs/design-system/` 四份规范；同时清理表中失效的 `../specs/frontend-design-guide.md` 引用（该文件不存在，职责由 `specs/design-system/` 取代）

### 6.2 两个自定义 skill

```
.claude/skills/
├── ui-audit/SKILL.md    # /ui-audit [模块名|all]   （阶段 0 创建）
└── ui-fix/SKILL.md      # /ui-fix [页面路径]        （阶段 3 创建）
```

- **`/ui-audit`**（阶段 0 创建）：对指定模块（或全量）运行截图流水线 → 委派 design-reviewer agent 逐页打分 → 产出/更新审计报告。阶段 1 的全量审计是其首次运行，阶段 4 每批修复的回归审计复用。
- **`/ui-fix`**（阶段 3 创建，依赖阶段 2 规范）：对指定页面执行"读审计 findings → 对照页面模板与状态矩阵改造 → 截图自检 → 委派 design-reviewer 重新评分 → 输出 before/after 对比"的完整闭环。

### 6.3 一个 design-reviewer agent（阶段 0 创建）

`.claude/agents/design-reviewer.md`：独立上下文的设计评审 agent，输入为页面截图（多状态×双主题）+ 评分框架（§3.2），输出结构化评分报告（四维度分项分 + 问题清单 + 修复建议）。`/ui-audit` 和 `/ui-fix` 的评分环节均委派给此 agent，保证评分独立性（写代码的上下文不给自己打分）。

**评审输入随阶段演进**：阶段 0-1 仅依据评分框架与锚点；阶段 2 规范产出后，将四份规范加入 agent 的评审输入清单（agent 定义中以引用方式声明，避免内容复制漂移）。

---

## 7. 阶段 4：三批次修复计划

> 批次划分在阶段 1 审计报告产出后按实际评分微调；以下为基于业务关键度的预设。

| 批次 | 范围 | 理由 |
|------|------|------|
| **批次 1** | training（列表/详情/创建）+ dashboard + 全局导航/MainLayout | 平台核心流程 + 全局印象面 |
| **批次 2** | datasets、models、spaces、monitoring | 高频业务模块 |
| **批次 3** | billing、audit、reports、templates、admin、resource-quotas、auth | 低频/管理类模块 |

**每批次 DoD（完成定义）**：

1. 批内全部页面综合评分达标（design-reviewer agent 评定）：**批次 1 ≥ 4.5，批次 2/3 ≥ 4.0**（批次 1 是平台门面与核心流程，门槛对齐 §10 成功标准）
2. 四态覆盖完整（截图流水线可证，按 §5.4 矩阵豁免不适用状态）
3. Light/Dark 双主题截图无瑕疵
4. 既有单元/集成/E2E 测试全绿，`npm run lint` 与 `tsc --noEmit` 通过
5. before/after 截图对比报告产出，**用户抽查关键页面通过**

**修复顺序**：每批内先 P0 → P1 → P2；P2 在评分已达该批次门槛时可降级为 backlog。

---

## 8. 范围边界（明确不做）

- ❌ 移动端适配（桌面优先，Cloudscape 自带的响应式行为保留即可）
- ❌ 自定义动效/微交互（保持 Cloudscape 内置过渡）
- ❌ 组件级自定义 CSS / 自研组件库（Token 级定制为上限）
- ❌ 多语言 i18n 架构（文案规范只覆盖中文）
- ❌ 后端 API 改造（前端用现有 API；审计中发现的 API 缺口记录到 findings 移交后端）

---

## 9. 错误处理与风险

| 风险 | 应对 |
|------|------|
| 评分主观漂移（同一页面两次评分差异大） | 评分锚点定义 + design-reviewer agent 固定 prompt + 评分时强制对照锚点描述逐维度给出理由 |
| Theming 定制引发暗色模式回归 | 截图矩阵强制双主题覆盖；theme.ts 改动必须全量跑截图流水线 |
| 修复破坏既有功能 | DoD 包含全量测试绿 + lint/类型检查；遵循现有 TDD 工作流 |
| 截图流水线对远程环境依赖不稳定 | 截图走 MockApi 注入状态（复用 e2e 设施），不依赖真实后端数据 |
| 规范文档与实际代码漂移 | 阶段 2 基于审计发现给出初版代码骨架；阶段 4 各批次完成后用实际改造代码反向校准回填模板，保持规范与代码同步 |

---

## 10. 成功标准

1. 13 个模块全部页面综合评分 ≥ 4.0，批次 1 页面（training/dashboard/全局导航）≥ 4.5（与 §7 DoD 一致）
2. 任意新页面开发时，Claude Code 能通过规范 + 模板 + `/ui-fix` 闭环产出首次即 ≥ 4.0 的页面
3. 用户抽查通过率：批次验收时抽查页面无 P0/P1 级新发现
