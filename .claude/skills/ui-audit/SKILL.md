---
name: ui-audit
description: 对前端页面执行 UI/UX 审计：运行截图流水线，委派 design-reviewer agent 四维度评分，聚合产出审计报告三件套。用法：/ui-audit [模块名|all]。适用于基线审计和批次修复后的回归审计。
---

# UI/UX 审计

对指定模块（或全部有页面的模块，12 业务模块 + dashboard，billing 无独立页面除外）执行"截图 → 独立评分 → 聚合报告"闭环。

## 参数

- `all`：全量审计（基线或全量回归）
- `<module>`：单模块审计（如 `training`），用于批次修复后的回归

## 流程

### 1. 运行截图流水线

```bash
cd frontend && npm run audit:screens            # all
cd frontend && npm run audit:screens -- --grep "<module>/"   # 单模块
```

确认输出目录 `frontend/e2e/audit/audit-output/<今日日期>/` 下 PNG 数量与测试数一致。失败的截图任务必须修复后重跑，不允许带着缺图评分。

### 2. 委派评分（每模块一次 Agent 调用）

对每个待审模块，用 Agent 工具派发 `design-reviewer` agent，prompt 提供：
- 截图目录绝对路径：`frontend/e2e/audit/audit-output/<日期>/<module>/`
- 该模块在 `frontend/e2e/audit/routes-manifest.ts` 中的页面清单（pageName、pageType、states）
- 指令：按其内置评分框架输出结构化报告

多模块时可并行派发（互相独立）。收集各模块返回的报告文本。

### 3. 聚合报告三件套

写入 `frontend/docs/audit/<日期>-<场景>/`（场景：`baseline` 或 `batch-N-regression`）：

**`score-matrix.md`** — 模块 × 4 维度评分矩阵（12 个有页面的模块 + dashboard；billing 无独立页面，矩阵末尾单独标注"billing: 无路由页面，不参与评分"）：
```markdown
| 模块 | 页面 | IA | IX | CONS | VIS | 综合 | 达标(≥4.0) |
|------|------|----|----|------|-----|------|-----------|
```
末尾给出：全局均分、达标率、最低分页面 Top 5。

**`findings.md`** — 问题清单，按严重度分组（P0 → P1 → P2），每条含：模块/页面、维度、描述、截图文件名。给每条分配稳定编号（如 `F-001`），供修复任务引用。

**`audit-report.md`** — 总报告：
- 执行摘要（全局均分、P0/P1/P2 计数、与上次审计对比——如有）
- 高频问题模式 Top 5（跨模块归纳,这是阶段 2 规范的内容优先级输入）
- 各模块一段式小结
- 修复批次建议（按 spec §7 的预设批次,结合实际评分微调）

### 4. 汇报

向用户输出：全局均分、达标率、P0 数量、报告文件路径。回归场景额外输出与基线的分数对比。

## 纪律

- 评分一律出自 design-reviewer agent,本上下文不打分、不改分
- 报告如实记录,包括 0 分页面和流水线缺陷
- 审计中发现的后端 API 缺口记入 findings（标注"移交后端"）,不在前端绕过
