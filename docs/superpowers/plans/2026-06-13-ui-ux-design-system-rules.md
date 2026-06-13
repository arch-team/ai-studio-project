# 阶段 2：靶向设计规范层 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `frontend/.claude/rules/` 新增 4 份设计规范（interaction-states / ux-writing / page-templates / design-tokens），把已落地的视觉/交互实践文档化并补齐空白，让 Claude Code 开发新页面时有"图纸"可依。

**Architecture:** 产出是规范文档（Markdown），非代码——TDD 红绿不适用，但"可验证"原则仍在：每份规范的验证点是"代码骨架/token 值与实际代码一致"+"交叉引用链接可达"。4 份按 Top5 优先级排序产出，单向交叉引用，最后更新配套文档引用并整体校验。

**Tech Stack:** Markdown 规范文档（对齐现有 11 份 rules 的风格：速查卡 + 表格 + 可复制代码骨架）

**Spec:** `docs/superpowers/specs/2026-06-13-ui-ux-design-system-rules-design.md`（已批准）

---

## 背景知识（执行者必读）

**项目约定**：所有文档/注释/commit 用中文；commit 格式 `<类型>(<范围>): <描述>`，范围用 `frontend`。

**核心原则**：本计划**只写规范文档，不改任何主题代码**。`brandTheme.ts` / `InlineErrorState` 等已落地代码是"事实基准"——规范如实记录它们；发现理想与代码有差距时，规范里标 `> ⚠️ 待改项：...（关联 F-0XX）` 但**不在本计划修代码**。

**已勘察确认的事实基准**（执行时以实际文件为准，行号可能微移）：

| 事实 | 位置/值 |
|------|---------|
| 品牌主色（明/暗） | `#0D6557` / `#42E0CC`（`src/shared/theme/brandTheme.ts` 的 `BRAND_COLORS.primaryLight/primaryDark`） |
| 全部品牌色值 | `brandTheme.ts` 的 `BRAND_COLORS`（15 个键）+ 图表 `colorChartsPaletteCategorical1~5`（各明暗双值）+ `JOB_STATUS_CHART_COLORS`（4 个单值）。注：个数仅供参考，Task 3 Step 3 用脚本比对实际 hex 值，不依赖计数 |
| 中文字体栈 | `brandTheme.ts` 的 `FONT_FAMILY_BASE` |
| Hero 渐变 | `brandTheme.ts` 的 `heroHeaderBackground(mode)` |
| Logo | `brandAssets.ts` 的 `BRAND_LOGO_SRC` |
| error 态范式 | `src/shared/components/feedback/InlineErrorState.tsx`（props: message/title/onRetry）+ 阶段4改造的 9 页（如 `TrainingJobDetailPage` error 块在 PageLayout 内） |
| 配色预览页 | `frontend/docs/brand-palette-preview.html`（已生成，色值与 brandTheme.ts 核对一致，可作 design-tokens.md 的可视化参考链接） |
| STATUS_LABELS 模式 | 已在 6 模块落地（`JOB_STATUS_LABELS`、`MODEL_STATUS_LABELS` 等，`Record<Status, string>` 形式，值为中文）。ux-writing 是固化此既有命名约定，非从零设计 |
| F-031 待改项实质 | `MODEL_STATUS_LABELS` 本身是中文映射；审计"中英混用"指页面某处直接显示了英文枚举值而非走 LABELS 映射——待改项是"所有状态展示必须走 {ENTITY}_STATUS_LABELS" |
| component-design.md §4 | 163-215 行"状态反馈与交互"（4.1 时效 / 4.2 Flashbar / 4.3 Modal），改为指向 interaction-states 的链接 |
| CLAUDE.md 失效引用 | `frontend/CLAUDE.md` 第 98 行 `../specs/frontend-design-guide.md`（文件不存在），清理 |

**现有 rules 风格参考**：打开 `frontend/.claude/rules/component-design.md` 或 `state-management.md` 看格式——开头"## 0. 速查卡片"含决策表/陷阱清单，正文用表格 + 代码块，简洁。新 4 份必须对齐此风格。

**文件结构总览**：

```
新建（frontend/.claude/rules/）:
  interaction-states.md   # Top1 error + Top2 四态（篇幅最大）
  ux-writing.md           # Top3 一致性
  page-templates.md       # Top4 模板 + Top5 图表
  design-tokens.md        # 视觉基础（反向提炼 brandTheme.ts）

修改:
  frontend/.claude/rules/component-design.md   # §4 改为指向 interaction-states 的链接
  frontend/.claude/rules/checklist.md          # 补指向新规范的自检项
  frontend/CLAUDE.md                           # 导航表加 4 份；删第 98 行失效引用
```

**交叉引用方向**（每个概念唯一真实源，单向引用）：
- `page-templates` 的四态接入点 → 链到 `interaction-states`
- `page-templates` 的图表配色 → 链到 `design-tokens`
- `interaction-states` 的错误/空态文案 → 链到 `ux-writing`
- 颜色/字体真实源 = `design-tokens`；状态处理 = `interaction-states`；文案 = `ux-writing`；页面骨架 = `page-templates`

---

### Task 1: interaction-states.md（篇幅最大，Top1+Top2）

**Files:**
- Create: `frontend/.claude/rules/interaction-states.md`

- [ ] **Step 1: 提炼事实基准**

阅读以下文件，提炼已落地的 error 态范式（作为规范的事实依据，不改它们）：
- `src/shared/components/feedback/InlineErrorState.tsx`（组件 props 与铁律注释）
- `src/features/training/pages/TrainingJobDetailPage.tsx`（error 块在 PageLayout 内的写法——详情页范式）
- `src/features/training/pages/TrainingJobListPage.tsx`（列表页 error 在 PageLayout 内 + Alert + 重试）
- `src/features/models/pages/ModelVersionsPage.tsx`（多 query / 子资源 error 显式报错，非降级为空）
- `frontend/docs/audit/2026-06-13-baseline/findings.md`（F-001/004/005/006/007/008/011/014 是 error 态问题；F-041 空态缺 CTA）

- [ ] **Step 2: 写入 interaction-states.md**

按设计文档 §3.1 的章节结构写，对齐现有 rules 风格（速查卡优先）。必含内容：

1. §0 速查卡：四态决策表（页面类型 list/detail/form/dashboard × 该有哪些态）+ 陷阱清单（裸 Container 塌缩 / 静默降级为 0 或 [] / error 与 empty 同屏）
2. §1 错误态（最高优先级）：
   - 铁律 4 条：保留 PageLayout 骨架 / 绝不静默降级为空 / error 必抑制 empty / 必带重试
   - InlineErrorState 用法（从 `@shared/components` 导入；3 个场景代码骨架：列表页、详情页固定标题、多 query 子资源显式报错）
   - 反模式对照表（裸 Container / `data ?? []` 吞错 → InlineErrorState）
   - 错误文案 → 链到 ux-writing.md
3. §2 加载态：骨架屏 vs Spinner 决策表 / 禁止整页塌缩为孤立 spinner / 各页面类型 loading 范式
4. §3 空态：empty 必带引导 CTA（标注 F-041 待改项）/ empty ≠ error 的区分 / 空态文案 → 链到 ux-writing.md
5. §4 成功态：Flashbar + 跳转链路 / 乐观更新反馈（可引用 component-design 现有 Flashbar 示例）
6. §5 状态完整性矩阵：列表/详情/表单/Dashboard × 四态 → 各自该渲染什么（表格）
7. 末尾"已知差距清单"：汇总本规范涉及的待改项（如个别页面空态缺 CTA）

代码骨架必须与实际代码一致（InlineErrorState 的 props 名、import 路径）。

- [ ] **Step 3: 自检**

- 文件开头有"> **职责**: ..."一行（对齐现有 rules）
- 所有代码骨架的 import 路径、组件 props 名与实际代码核对一致
- 对 ux-writing 的链接用相对路径 `ux-writing.md`（同目录）

- [ ] **Step 4: Commit**

```bash
git add frontend/.claude/rules/interaction-states.md
git commit -m "docs(frontend): 新增交互状态规范（四态完整性 + error 态铁律）"
```

---

### Task 2: ux-writing.md（Top3 一致性）

**Files:**
- Create: `frontend/.claude/rules/ux-writing.md`

- [ ] **Step 1: 提炼事实基准**

- 根 `CLAUDE.md` 与 `specs/001-ai-training-platform/spec.md` 的术语标准（核心实体命名：训练任务/数据集/检查点/模型/资源配额/开发空间；训练任务状态机 submitted→running→...）
- 现有 `{ENTITY}_STATUS_LABELS` 写法（`src/features/training/types/index.ts` 的 `JOB_STATUS_LABELS`、`src/features/models/types/index.ts` 的 `MODEL_STATUS_LABELS`）——这是要固化的既有约定
- `findings.md` 的 F-031（状态展示须走 LABELS 映射，禁止直接显示英文枚举值）

- [ ] **Step 2: 写入 ux-writing.md**

按设计文档 §3.2 章节结构。必含：

1. §0 速查卡：术语映射表（实体中文名 + 对应类/表/路径，与根 CLAUDE.md 术语表对齐；扩展 UI 场景：按钮动词如"创建/提交/取消"、状态名词统一）
2. §1 状态标签常量：`{ENTITY}_STATUS_LABELS` 模式（明确这是固化既有约定：`Record<Status, string>` 中文映射，定义在模块 `types/index.ts`）；铁律"所有状态展示必须走 LABELS 映射，禁止页面直接渲染英文枚举值"（标 F-031 待改项）
3. §2 文案模式：空状态（说明 + 引导 CTA 文案）/ 错误信息（发生什么 + 怎么办）/ 确认对话框（后果说明）/ 表单帮助文本（constraintText vs description 分工）—— 各给好/坏对照
4. §3 中文规范：标点（全角）、中英混排空格、数字单位（GPU/节点/百分比）
5. §4 语气基准：专业 / 直接 / 无废话（给改写对照例）
6. 末尾"已知差距清单"：F-031 等

- [ ] **Step 3: 自检**

- "职责"一行齐全
- 术语映射表与根 CLAUDE.md 术语标准一致（训练任务=TrainingJob 等）
- STATUS_LABELS 写法与实际代码一致

- [ ] **Step 4: Commit**

```bash
git add frontend/.claude/rules/ux-writing.md
git commit -m "docs(frontend): 新增 UX 文案规范（术语映射 + 状态标签 + 文案模式）"
```

---

### Task 3: design-tokens.md（反向提炼 brandTheme.ts）

**Files:**
- Create: `frontend/.claude/rules/design-tokens.md`

> **此任务最易错**：所有色值必须与 `brandTheme.ts` 逐字核对，不能凭记忆抄。

- [ ] **Step 1: 逐字摘录事实基准**

打开 `src/shared/theme/brandTheme.ts` 和 `src/shared/theme/brandAssets.ts`，逐字摘录（不要凭记忆）：
- `BRAND_COLORS` 全部 15 个键值对（primaryLight `#0D6557`、primaryDark `#42E0CC`、各 hover/active、onPrimaryDark、link×4、focus×2、selectedBg×2）
- `colorChartsPaletteCategorical1~5` 的明暗双值
- `JOB_STATUS_CHART_COLORS`（running `#0AA08E` / completed `#67A353` / failed `#D63F38` / paused `#8C8C94`）
- `FONT_FAMILY_BASE` 完整字体栈字符串
- `heroHeaderBackground` 的明暗两个渐变字符串
- `BRAND_LOGO_SRC` / `BRAND_LOGO_ALT`（brandAssets.ts）

- [ ] **Step 2: 写入 design-tokens.md**

按设计文档 §3.4 章节结构。必含：

1. §0 速查卡：品牌色板表（主色/链接/焦点/选中，明暗双列）+ 字体栈 + "何时用 token"决策
2. §1 品牌主题：深空离子青理念（摆脱 AWS 蓝）/ `applyBrandTheme()` 接入点（main.tsx 渲染前调用）/ 零自定义 CSS 铁律（改色只改 token）
3. §2 色彩 token：主色/链接/焦点/选中（明暗双值 + WCAG AA 对比度标注，如 primaryLight 对白字 ≈5.9:1）
4. §3 图表色：5 组分类色序列（明暗双值）+ 4 个状态语义色（`JOB_STATUS_CHART_COLORS`）
5. §4 字体排版：中文字体栈 / Cloudscape 字号 token
6. §5 Hero 与 Logo：`heroHeaderBackground` 用法 / `BRAND_LOGO_SRC`
7. 链到配色预览页 `frontend/docs/brand-palette-preview.html`（可视化参考）

- [ ] **Step 3: 色值一致性核验（关键）**

逐一比对 design-tokens.md 写的每个色值 vs brandTheme.ts：

```bash
cd frontend
grep -oE "#[0-9A-Fa-f]{6}" src/shared/theme/brandTheme.ts src/shared/theme/brandAssets.ts | grep -oE "#[0-9A-Fa-f]{6}" | tr 'a-f' 'A-F' | sort -u > /tmp/theme_colors.txt
grep -oE "#[0-9A-Fa-f]{6}" .claude/rules/design-tokens.md | tr 'a-f' 'A-F' | sort -u > /tmp/doc_colors.txt
echo "=== 文档独有色值（须确认每个都有理由）===" && comm -13 /tmp/theme_colors.txt /tmp/doc_colors.txt
```

Expected: 文档独有色值为空（或每个都是有意的说明性示例）。任何 brandTheme 里没有的品牌色值都是错误，必须修正。

- [ ] **Step 4: Commit**

```bash
git add frontend/.claude/rules/design-tokens.md
git commit -m "docs(frontend): 新增设计 token 规范（深空离子青主题文档化）"
```

---

### Task 4: page-templates.md（Top4 模板 + Top5 图表）

**Files:**
- Create: `frontend/.claude/rules/page-templates.md`

- [ ] **Step 1: 提炼事实基准**

阅读现有页面提炼四大模式骨架（不改它们）：
- 列表页：`src/features/training/pages/TrainingJobListPage.tsx`
- 详情页：`src/features/training/pages/TrainingJobDetailPage.tsx`
- 表单页：`src/features/training/pages/CreateTrainingJobPage.tsx`
- Dashboard：`src/features/dashboard/pages/HomePage.tsx`、`src/features/monitoring/pages/MonitoringDashboardPage.tsx`
- 骨架组件：`src/shared/components/PageLayout.tsx`（props: title/description/actions/counter/breadcrumbs/hero/heroExtra/children）
- 图表问题：`findings.md` 的 F-009/010/012/013（量纲混用）

- [ ] **Step 2: 写入 page-templates.md**

按设计文档 §3.3 章节结构。必含：

1. §0 速查卡：四大页面模式 → 何时用哪个（决策表）
2. §1-4 四大模板（列表/详情/表单/Dashboard），每个含：
   - 区域结构 ASCII 图
   - 必备元素清单（如列表页：PageLayout + 筛选区 + Table 排序/分页/列偏好 + 四态）
   - Cloudscape 组件映射
   - 可复制骨架（基于 PageLayout）
   - 四态接入点 → 链到 interaction-states.md
3. §5 图表严谨性规范（Top5）：
   - 同图同量纲（百分比与绝对值不可同轴）
   - 聚合值与分项分离（"总计"不与分项画同一折线图）
   - 类别配色 → 链到 design-tokens.md 的分类色序列
   - 标 F-009/010/012/013 待改项（monitoring/cost-analysis 现状未遵循）
4. 末尾"已知差距清单"：图表量纲待改项

- [ ] **Step 3: 自检**

- "职责"一行齐全
- PageLayout props 与实际组件一致
- 对 interaction-states / design-tokens 的链接为同目录相对路径

- [ ] **Step 4: Commit**

```bash
git add frontend/.claude/rules/page-templates.md
git commit -m "docs(frontend): 新增页面模板规范（四大模式骨架 + 图表严谨性）"
```

---

### Task 5: 更新配套文档引用

**Files:**
- Modify: `frontend/.claude/rules/component-design.md`（§4）
- Modify: `frontend/.claude/rules/checklist.md`
- Modify: `frontend/CLAUDE.md`

- [ ] **Step 1: component-design.md §4 改为链接**

§4"状态反馈与交互"（约 163-215 行，含 4.1 时效 / 4.2 Flashbar / 4.3 Modal）：保留章节标题与一句话概述，正文改为指向 interaction-states.md 的链接（单一真实源）。不删除 4.2/4.3 的示例（可保留作快速参考），但加注"完整规范见 interaction-states.md"。

- [ ] **Step 2: checklist.md 补自检项**

在合适章节（如"Cloudscape 合规"后新增"设计规范"段）补充指向 4 份新规范的 PR 自检项：
```markdown
## 设计规范

- [ ] 错误/加载/空/成功四态完整（详见 interaction-states.md）
- [ ] 错误态保留 PageLayout 骨架 + 重试，不静默降级
- [ ] 状态展示走 {ENTITY}_STATUS_LABELS 映射（详见 ux-writing.md）
- [ ] 页面遵循四大模式之一（详见 page-templates.md）
- [ ] 颜色只用 design token，无硬编码色值（详见 design-tokens.md）
- [ ] 图表同量纲、类别配色用分类色序列
```

- [ ] **Step 3（可选）: accessibility.md 补对比度链接**

`accessibility.md` 的颜色对比度章节补一句"品牌色对比度值见 `design-tokens.md`"（spec §2.2 列的配套增强）。不删除已有内容，仅加指针。若该文件无颜色对比度章节则跳过并说明。

- [ ] **Step 4: frontend/CLAUDE.md 导航表更新**

- 删除第 98 行失效引用 `| ../specs/frontend-design-guide.md | 完整视觉规范... |`
- 在文档导航表加入 4 份新规范行：
```markdown
| `.claude/rules/design-tokens.md` | 品牌色板、字体、图表色、Hero（深空离子青 token） |
| `.claude/rules/page-templates.md` | 列表/详情/表单/Dashboard 四大页面模式骨架 + 图表规范 |
| `.claude/rules/interaction-states.md` | 错误/加载/空/成功四态完整性 + error 态铁律 |
| `.claude/rules/ux-writing.md` | 术语映射、状态标签、文案模式、中文规范 |
```

- [ ] **Step 5: 校验链接可达**

```bash
cd frontend
ls .claude/rules/design-tokens.md .claude/rules/page-templates.md .claude/rules/interaction-states.md .claude/rules/ux-writing.md
grep -c "frontend-design-guide" CLAUDE.md && echo "失效引用仍在" || echo "失效引用已清理"
```

Expected: 4 文件都在；失效引用已清理。

- [ ] **Step 6: Commit**

```bash
git add frontend/.claude/rules/component-design.md frontend/.claude/rules/checklist.md frontend/.claude/rules/accessibility.md frontend/CLAUDE.md
git commit -m "docs(frontend): 配套文档引用接入设计规范，清理失效引用"
```

---

### Task 6: 整体校验

- [ ] **Step 1: 交叉引用可达性校验**

```bash
cd frontend/.claude/rules
for f in interaction-states ux-writing page-templates design-tokens; do
  echo "=== $f.md 引用的 .md ===";
  grep -oE "[a-z-]+\.md" $f.md | sort -u;
done
```

逐一确认引用的 .md 文件都存在于同目录。无悬空链接、无循环详述（每个概念只在唯一真实源详述，其余处只放链接）。

- [ ] **Step 2: design-tokens 色值终校验**

重跑 Task 3 Step 3 的色值比对脚本，确认 design-tokens.md 的品牌色值与 brandTheme.ts 零差异。

- [ ] **Step 3: 风格一致性抽查**

抽查 4 份新规范，确认都有"## 0. 速查卡片"或等价速查结构、"> **职责**:"开头一行、表格 + 代码块为主——与现有 11 份 rules 风格一致。

- [ ] **Step 4: 向用户汇报**

汇总：4 份规范落盘、配套引用更新、色值核验结果、待改项清单（供后续修复）。

---

## 验收清单（计划级 DoD）

- [ ] 4 份规范落盘 `frontend/.claude/rules/`，风格对齐现有 rules（速查卡 + 表格 + 代码骨架 + "职责"开头）
- [ ] design-tokens 的所有品牌色值与 `brandTheme.ts` 逐字一致（脚本校验零差异）
- [ ] 四份交叉引用链接可达、单一真实源无重复详述
- [ ] `component-design.md` §4 改为指向 interaction-states 的链接（保留组件选择内容）
- [ ] `checklist.md` 补充设计规范自检项
- [ ] `frontend/CLAUDE.md` 导航表加 4 份新规范、删第 98 行失效引用
- [ ] 各规范末尾"已知差距清单"汇总待改项（F-009/010/012/013/031/041 等），作为后续修复指针

## 不在本计划内

- 不改任何主题代码（`brandTheme.ts` 等）——只文档化
- 不修 findings 里的待改项（规范只标指针；修复是后续阶段）
- 不做移动端/动效规范
- 不删除 component-design.md / accessibility.md 已有内容（只把重叠章节改链接）

> 注：列表页（如 `TrainingJobListPage`）的 error 态用内联 `Alert`+重试范式，详情/子资源类用 `InlineErrorState`——interaction-states.md 应如实记录两种范式（列表页 Alert、详情页 InlineErrorState），不要误以为全部统一到 InlineErrorState。
