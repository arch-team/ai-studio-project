# 阶段 2：靶向设计规范层设计

> 日期: 2026-06-13
> 状态: 已确认（用户逐节审批通过）
> 范围: 在 `frontend/.claude/rules/` 新增 4 份设计规范，把已落地实践文档化并补齐空白
> 上游依据: UI/UX 质量体系 spec（`docs/superpowers/specs/2026-06-12-ui-ux-quality-system-design.md`）的阶段 2；基线审计报告（`frontend/docs/audit/2026-06-13-baseline/audit-report.md`）的"高频问题 Top 5"

---

## 1. 背景与定位

### 1.1 这是什么

UI/UX 质量体系 spec 的阶段 2。前置阶段已完成：阶段 0+1（审计基础设施 + 基线审计，全局均分 3.72）、批次 0 + 阶段 4（error 态统一修复，9 个页面改造 + `InlineErrorState` 组件落地）。

阶段 2 的目标是把质量从"事后审计发现问题"转为"开发时即遵循规范、首次产出即达标"——产出 4 份设计规范，作为 Claude Code 开发新页面/改造旧页面时的"图纸"。

### 1.2 关键发现（影响本阶段性质）

勘察发现阶段 2 的真实性质不是"从零设计规范"，而是"文档化已落地实践 + 补齐空白"：

| 规范 | 已落地程度 | 本阶段动作 |
|------|-----------|-----------|
| design-tokens | **已完整落地**于 `src/shared/theme/brandTheme.ts`（深空离子青主题，明暗双模式，零自定义 CSS） | 反向提炼文档化 |
| interaction-states | error 态范式**已落地**（`InlineErrorState` + 阶段 4 的 9 页改造） | 提炼 error 范式 + 补齐 loading/empty/success 三态 |
| page-templates | 列表/详情/表单/Dashboard 页面**已存在**，`component-design.md` 有组件选择基础 | 提炼四大模式骨架 + 补图表规范 |
| ux-writing | **全新**，无现成代码可提炼 | 新写 |

### 1.3 已确认的关键决策

| 决策点 | 结论 |
|--------|------|
| 放置位置 | `frontend/.claude/rules/`（Claude Code 开发时自动加载，与现有 11 份 rules 交叉引用） |
| 文档形态 | 对齐现有 rules 风格：速查卡 + 表格 + 可复制代码骨架 |
| 与已落地代码的关系 | 只重写规范文档，**不动主题代码**；已落地的 `brandTheme.ts`/`InlineErrorState` 作"事实基准"，理想与代码有差距时规范标"⚠️ 待改项"但不在本阶段改 |
| 与现有规范的关系 | 新增独立 4 份 + 双向交叉引用；`component-design.md`/`accessibility.md` 重叠章节改为指向新规范的链接（单一真实源） |
| 交付范围 | 四份一次性全写，详略按 Top 5 优先级分配 |

---

## 2. 总体架构与文件清单

### 2.1 新增文件（4 份）

全部位于 `frontend/.claude/rules/`，风格对齐现有 rules（速查卡优先 + 表格 + 可复制代码骨架）：

| 新文件 | 性质 | 对应 Top 5 | 内容来源 |
|--------|------|-----------|---------|
| `interaction-states.md` | 提炼+补齐（篇幅最大） | Top1 error 态 + Top2 四态完整性 | 提炼 `InlineErrorState` + 阶段 4 范式；补 loading/empty/success |
| `ux-writing.md` | 全新 | Top3 跨页一致性 | 术语映射、文案模式、中文规范 |
| `page-templates.md` | 提炼+补齐 | Top4 + Top5 图表严谨性 | 提炼四大页面模式 + 图表规范 |
| `design-tokens.md` | 反向提炼 | （视觉基础） | 文档化 `brandTheme.ts` |

### 2.2 配套改动

| 文件 | 改动 |
|------|------|
| `frontend/CLAUDE.md` | 文档导航表加入 4 份新规范；**清理失效的 `../specs/frontend-design-guide.md` 引用**（该文件不存在） |
| `frontend/.claude/rules/component-design.md` | "状态反馈与交互"章节（§4）改为指向 `interaction-states.md` 的链接，保留组件选择内容 |
| `frontend/.claude/rules/accessibility.md` | 颜色对比度相关处补充指向 `design-tokens.md`（对比度已在 token 标注） |
| `frontend/.claude/rules/checklist.md` | PR Review 清单补充指向四份新规范的自检项 |

---

## 3. 四份规范的章节结构

### 3.1 `interaction-states.md`（篇幅最大）

```
0. 速查卡：四态决策表（页面类型 × 该有哪些态）+ 陷阱清单
1. 错误态（最高优先级）
   - 铁律：保留 PageLayout 骨架 / 绝不静默降级为空 / error 必抑制 empty / 必带重试
   - InlineErrorState 用法（列表 / 详情 / 多 query 三场景代码骨架）
   - 反模式对照表（裸 Container 塌缩 ❌ / 降级为 0 或空数组 ❌）
2. 加载态：骨架屏 vs Spinner 决策 / 各页面类型 loading 范式 / 禁止整页塌缩为孤立 spinner
3. 空态：empty 必带引导 CTA / empty ≠ error 的区分 / 列表与子资源空态
4. 成功态：Flashbar + 跳转链路 / 乐观更新反馈
5. 状态完整性矩阵（列表 / 详情 / 表单 / Dashboard × 四态 → 各自该渲染什么）
```

事实基准：`InlineErrorState`（`src/shared/components/feedback/InlineErrorState.tsx`）、阶段 4 改造的 9 个页面（如 `TrainingJobDetailPage` 的 error 块）。

### 3.2 `ux-writing.md`（全新）

```
0. 速查卡：术语映射表（与 spec 术语标准对齐，扩展 UI 场景：按钮动词 / 状态名词）
1. 状态标签常量：{ENTITY}_STATUS_LABELS 模式（解决 model-versions 中英混用 F-031）
2. 文案模式：空状态 / 错误信息（发生什么+怎么办）/ 确认对话框 / 表单帮助文本
3. 中文规范：标点、中英混排空格、数字单位
4. 语气基准：专业 / 直接 / 无废话
```

事实基准：根 `CLAUDE.md` 与 `specs/001-ai-training-platform/spec.md` 的术语标准表（训练任务/数据集/检查点等核心实体命名与状态机）。

### 3.3 `page-templates.md`（提炼+补齐）

```
0. 速查卡：四大页面模式 → 何时用哪个
1-4. 列表页 / 详情页 / 表单页 / Dashboard 模板
     （各含：区域结构 ASCII 图 + 必备元素清单 + Cloudscape 组件映射 + 可复制骨架 + 四态接入点）
5. 图表严谨性规范（Top5）：同图同量纲 / 聚合值与分项分离 / 类别配色用 design-tokens 序列
```

事实基准：现有列表页（`TrainingJobListPage`）、详情页（`TrainingJobDetailPage`）、表单页（`CreateTrainingJobPage`）、Dashboard（`HomePage`、`MonitoringDashboardPage`）、`PageLayout` 组件。

### 3.4 `design-tokens.md`（反向提炼）

```
0. 速查卡：品牌色板表（明/暗双值）+ 字体栈 + 何时用 token
1. 品牌主题：深空离子青理念 / applyBrandTheme 接入点 / 零自定义 CSS 铁律
2. 色彩 token：主色 / 链接 / 焦点 / 选中（明暗双值 + WCAG AA 对比度标注）
3. 图表色：分类色序列 + 状态语义色（JOB_STATUS_CHART_COLORS）
4. 字体与排版：中文字体栈 / Cloudscape 字号 token
5. Hero 页头：heroHeaderBackground 用法 / Logo（BRAND_LOGO_SRC）
```

事实基准（色值必须与代码逐一核对，不能写错）：`src/shared/theme/brandTheme.ts`（`BRAND_COLORS`、`JOB_STATUS_CHART_COLORS`、`heroHeaderBackground`）、`src/shared/theme/brandAssets.ts`（`BRAND_LOGO_SRC`）。

---

## 4. 交叉引用关系

四份规范按依赖方向单向引用，每个概念只在一处详述，避免"两处说法不一"：

```
design-tokens.md  ←──────┐ （颜色/字体的唯一真实源）
   ↑ 图表色序列          │
page-templates.md ───────┤ 图表规范引用 tokens 的分类色
   ↑ 各模板"四态接入点"    │
interaction-states.md ───┘ 状态矩阵被模板引用
   ↑ 文案
ux-writing.md  ←───────── 错误/空态文案被 interaction-states 引用
```

具体规则：
- `page-templates` 的四态接入点 → 链到 `interaction-states`
- `page-templates` 的图表配色 → 链到 `design-tokens`
- `interaction-states` 的错误/空状态文案 → 链到 `ux-writing`
- `component-design.md` 的"状态反馈与交互"章节 → 链到 `interaction-states.md`

每个概念的"唯一真实源"：颜色/字体在 design-tokens；状态处理在 interaction-states；文案在 ux-writing；页面骨架在 page-templates。

---

## 5. 与已落地代码的"事实基准/待改项"处理

规范如实记录已落地实现。发现理想与代码有差距时，规范里标 `> ⚠️ 待改项：...`，但本阶段不改代码。预期会标出的待改项（来自基线 findings）：

| 待改项 | 出现在 | 关联 finding |
|--------|--------|-------------|
| 图表量纲混用（百分比与绝对值同轴、聚合值与分项同图） | `page-templates.md` 图表规范 | F-009/010/012/013 |
| 状态标签中英混用（model-versions 用英文枚举） | `ux-writing.md` 状态标签常量 | F-031 |
| 空态缺引导 CTA（dataset-list 等） | `interaction-states.md` 空态 | F-041 |

每份规范末尾设"已知差距清单"小节，汇总该规范涉及的待改项，作为后续修复 backlog 的指针。

---

## 6. 验收方式

沿用既定标准（Claude 自审 + 用户抽查）：

- **代码一致性校验**：每份规范的代码骨架/token 值与实际代码核对。design-tokens 的色值**必须**与 `brandTheme.ts` 逐一核对（如 `primaryLight: '#0D6557'`），不能写错。
- **交叉引用校验**：四份间链接可达、无循环详述（每个概念只在唯一真实源详述）。
- **spec-document-reviewer 评审**通过。
- **用户抽查**：术语映射表是否符合预期、四态矩阵是否覆盖关心的场景。

---

## 7. 范围边界（明确不做）

- ❌ 不改 `brandTheme.ts` 等主题代码（只文档化）
- ❌ 不批量修 findings 里的待改项（规范只标指针，修复是后续阶段的事）
- ❌ 不做移动端/动效规范（沿用 spec 既定边界）
- ❌ 不删除 `component-design.md`/`accessibility.md` 的已有内容（只把重叠章节改为链接）

---

## 8. 成功标准

1. 4 份规范落盘 `frontend/.claude/rules/`，风格对齐现有 rules
2. design-tokens 的所有 token 值与 `brandTheme.ts` 逐一一致
3. 四份交叉引用链接可达、单一真实源无重复详述
4. `frontend/CLAUDE.md` 导航表更新、失效引用清理
5. 后续开发新页面时，Claude Code 能依据这 4 份规范产出首次即符合规范的页面（在下一次新页面开发或 `/ui-audit` 回归时验证）
