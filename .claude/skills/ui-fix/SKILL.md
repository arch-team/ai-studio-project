---
name: ui-fix
description: 对单个前端页面执行 UI/UX 修复闭环：读审计 findings → 对照设计规范改造 → 截图自检 → 委派 design-reviewer 重新评分 → 输出 before/after 对比。用法：/ui-fix <模块>/<页面> 或 /ui-fix F-0XX。适用于按 findings 逐页改造、把页面拉到商用门槛（≥4.0）。
---

# UI/UX 单页修复闭环

对指定页面执行"读问题 → 依规范改 → 截图自检 → 独立评分 → 对比"的完整闭环，确保修复后达标且不回退。

## 参数

- `<模块>/<页面>`：指定页面（如 `monitoring/monitoring`、`reports/cost-analysis`）
- `F-0XX`：指定 finding 编号，自动定位其所属页面（如 `/ui-fix F-009`）
- 可带多个：`/ui-fix F-009 F-010`（同页面的多条一起修）

## 前置依赖（都已就位）

| 依赖 | 位置 | 用途 |
|------|------|------|
| 审计 findings | `frontend/docs/audit/<日期>-baseline/findings.md` | 问题来源 + 稳定编号 |
| 四份设计规范 | `frontend/.claude/rules/{interaction-states,ux-writing,page-templates,design-tokens}.md` | 改造依据（如何改对） |
| 截图流水线 | `frontend/e2e/audit/`（`npm run audit:screens`） | 改造前后自检 |
| design-reviewer | `.claude/agents/design-reviewer.md` | 独立评分（写代码的上下文不给自己打分） |

## 流程

### 1. 定位问题与基线分

- 若传入 `F-0XX`，在 `findings.md` 中查到该条的所属页面、维度、描述、关联规范
- 在最新 `score-matrix.md` / 回归报告中查该页面的**当前分数**（作为 before 基线）
- 列出该页面所有待修 findings（不只传入的那条——同页面问题一并处理更高效）

### 2. 截图取证 before（可选但推荐）

```bash
cd frontend && npm run audit:screens -- --grep "<模块>/<页面>"
```
把当前截图归档为 before 参照（如 `audit-output/<日期>/<module>/` 下相关 png）。

### 3. 对照规范改造（TDD）

按 finding 维度查对应规范，遵循其铁律改造源码：

| finding 维度 | 查哪份规范 | 典型改法 |
|-------------|-----------|---------|
| error/loading/empty/success 态 | `interaction-states.md` | 保留 PageLayout 骨架 + InlineErrorState/Alert + 重试，不静默降级 |
| 术语/状态标签/文案 | `ux-writing.md` | 走 `{ENTITY}_STATUS_LABELS`，文案"发生什么+怎么办" |
| 页面结构/图表量纲 | `page-templates.md` | 套四大模式骨架；图表同量纲、聚合值与分项分离 |
| 颜色/硬编码 hex | `design-tokens.md` | 改用 design token，零自定义 CSS |

**强制 TDD**（改源码即走测试驱动）：
- 先在 `frontend/tests/unit/features/<module>/` 写/改失败测试，断言修复后的行为（如 error 态出现"加载失败"+重试按钮）
- 跑测试见失败 → 改源码 → 跑测试通过
- 改完跑 `npx tsc --noEmit` + `npm run lint`

### 4. 截图自检 after

```bash
cd frontend && AUDIT_DATE=$(date +%F) npm run audit:screens -- --grep "<模块>/<页面>"
```
用 Read 亲自看 after 截图，确认修复点视觉生效（error 态有骨架+重试、图表量纲正常、暗色无瑕疵等），不带病提交。

### 5. 委派 design-reviewer 重新评分

用 Agent 工具派发 `design-reviewer`（**评分一律出自它，本上下文不打分**），prompt 提供：
- after 截图目录绝对路径：`frontend/e2e/audit/audit-output/<日期>/<module>/`
- 该页在 `routes-manifest.ts` 的 pageName/pageType/states
- 指令：按内置四维度框架输出结构化评分

> 评分时**不告知 before 分数**，避免锚定偏差。

### 6. 输出 before/after 对比

向用户汇报：
- 该页 before → after 综合分变化、是否跨过 4.0 门槛
- 修复的 finding 编号清单
- after 评分中暴露的残留/新问题（如有）
- 截图佐证（before/after 关键状态）

若 after 仍未达标，列出剩余差距与下一步，**不谎报达标**。

## 纪律

- **评分独立**：评分必出自 design-reviewer agent，写代码的上下文不给自己打分、不改分
- **TDD 不跳过**：改源码必先写失败测试，禁止改完补测试或不写测试
- **如实对比**：after 分数如实记录，未达标就说未达标 + 剩余差距
- **不静默降级**：遵循 interaction-states 铁律，error 态绝不伪装成空/正常
- **只改本页**：聚焦目标页面，发现的他页问题记入 findings（不顺手改无关页面）
- **后端缺口**：发现后端 API 问题记入 findings 标注"移交后端"，不在前端绕过

## 与 /ui-audit 的关系

- `/ui-audit`：批量评分、产出报告三件套（发现问题）
- `/ui-fix`：单页改造闭环（解决问题）
- 典型工作流：`/ui-audit all` 出基线 → 按 findings 逐页 `/ui-fix` → `/ui-audit <module>` 回归验证涨分
