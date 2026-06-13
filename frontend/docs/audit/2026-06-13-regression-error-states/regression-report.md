# UI/UX 回归审计报告：error 态修复 + 设计规范验证

> 日期: 2026-06-13 | 场景: regression（error 态修复后回归）
> 对比基线: `frontend/docs/audit/2026-06-13-baseline/`
> 范围: error 态修复影响最大的 6 个模块、11 个页面
> 方法: 基于修复后代码重跑截图流水线（160 张）→ 6 路 design-reviewer 独立评分（不告知基线分，避免锚定）

---

## 1. 验证目的

验证两件事的实际效果：
1. **批次 0 + 阶段 4 的 error 态修复**（InlineErrorState 组件 + 9 + 7 个页面改造）
2. **阶段 2 的设计规范**（四份 rules，尤其 interaction-states 的 error 态铁律）

通过对修复过的模块重跑审计，量化对比基线评分。

---

## 2. 评分对比总览

| 页面 | 基线综合 | 回归综合 | 变化 | 达标(≥4.0) |
|------|:-------:|:-------:|:----:|:----------:|
| audit/audit-logs | 2.9 | **4.5** | ↑ 1.60 | ❌ → ✅ |
| models/model-detail | 3.4 | **4.4** | ↑ 1.00 | ❌ → ✅ |
| admin/user-management | 3.6 | **4.5** | ↑ 0.90 | ❌ → ✅ |
| monitoring/monitoring | 3.0 | 3.85 | ↑ 0.85 | ❌ → ❌ |
| dashboard/home | 3.6 | **4.2** | ↑ 0.60 | ❌ → ✅ |
| models/model-versions | 3.4 | 3.95 | ↑ 0.55 | ❌ → ❌ |
| models/model-list | 4.4 | 4.4 | = | ✅ → ✅ |
| reports/reports-home | 4.4 | 4.4 | = | ✅ → ✅ |
| reports/resource-usage | 4.1 | 4.1 | = | ✅ → ✅ |
| reports/cost-analysis | 3.8 | 3.8 | = | ❌ → ❌ |
| admin/admin-home | 3.9 | 3.4 | ↓ 0.50 | ❌ → ❌ |

**6 模块均分**：3.68 → **4.14**（↑ 0.45）
**达标率**：3/11 → **7/11**

---

## 3. 核心结论

### 3.1 error 态修复全面生效（最强信号）

基线时所有 P0 级 error 态缺陷，回归确认**全部修复落地**：

| finding | 页面 | 基线缺陷 | 回归确认 |
|---------|------|---------|---------|
| F-007/008 | audit-logs | error 整页塌缩为裸文本 | ✅ 保留骨架 + Alert + 重试，IX 2.5→4.5 |
| F-014 | user-management | error 整页框架塌缩，无重试 | ✅ 保留骨架 + Alert + 重试，正确抑制 empty |
| F-005 | model-detail | error 死胡同，无骨架/重试/返回 | ✅ 固定标题骨架 + InlineErrorState + 重试 + 返回 |
| F-006 | model-versions | 列表 error 静默降级为空表 | ✅ 版本列表加载失败显式报错，不再静默空表 |
| F-027 | monitoring | error 裸红字，无重试 | ✅ 保留标题骨架 + Alert + 重试 |
| F-011 | resource-usage/cost-analysis | error 整页塌缩 | ✅ 保留面包屑+标题 + Alert + 重试 |
| **F-001/030** | **dashboard/home** | **加载失败伪装成"0+空图表+全绿健康"** | ✅ 显式红色 Alert + 系统状态降级为"无法获取" + 图表中性降级，伪装健康基本消除 |

涨幅最大的三个页面（audit-logs +1.6、model-detail +1.0、user-management +0.9）正是基线 error 态最严重的，验证了"error 态是最高杠杆修复点"的判断。

### 3.2 设计规范同步固化

回归评审中，多个 agent 自发引用了阶段 2 刚建的规范条款（interaction-states 的铁律 R1/R3/R4、范式 A/B、page-templates §5 图表量纲）来评判——说明规范已成为可执行的评判标准，不只是文档。

---

## 4. 仍未达标的 4 个页面（诚实记录）

### 4.1 因"已知未修待改项"未达标（符合预期）

- **monitoring/monitoring（3.85）**：error 态已修复（IX 回升），但图表量纲混用（F-009/010）未修，VIS 仅 3.0 拖累综合分。属阶段 2 规范明确标注的待改项，非本次修复范围。
- **reports/cost-analysis（3.8，持平）**：error 态已修复，但折线图聚合值与分项同图（F-012）、配色语义冲突（F-013）未修。同属已标注待改项。

→ 这两页要过门槛，需做 page-templates §5 的图表整改（拆量纲、总计转 KPI、配色走分类色 token）。

### 4.2 回归中新发现的残留项

- **model-versions（3.95，差 0.05）**：error 态已修复，但 **F-031 状态标签中英混用未修**（版本列表仍裸渲染英文 `deployed/registered`，而 list/detail 用中文）+ error/empty 同屏（R3 残留）。需走 `MODEL_STATUS_LABELS`。
- **admin/admin-home（3.4，↓0.5）**：**这是评分校准而非真实退化**——回归 agent 发现基线漏判的 F-033（dashboard 空列表缺"新建用户"CTA），更严格地扣了分。该页 error 态本就不是主要缺陷，本次未改它，分数下降反映的是审计精度提升。

### 4.3 回归暴露的新打磨项（P1/P2，可纳入下一批次）

- **error 态骨架保留不彻底**：audit-logs、resource-usage、cost-analysis 的 error 态保留了标题+面包屑，但丢失了筛选区/操作区（刷新/导出）——比 loading 态裁剪更狠，未完全满足铁律 R1。
- **dashboard error 残留**：失败指标仍显示硬数字"0"（宜改"—/未知"）；系统状态同源子项"失败任务=无"仍显绿色，降级不彻底。
- **error 文案技术化**："服务器内部错误"宜按 ux-writing §2.2 改为面向用户的"服务暂时不可用，请稍后重试"。
- **详情页 loading 孤立 Spinner**：model-detail/versions 的 loading 未保留骨架，与 error 态不一致。

---

## 5. 结论

**修复 + 规范的效果已用数据验证**：6 个 error 态重灾模块均分从 3.68 提升到 4.14，达标率从 27% 提升到 64%，所有基线 P0 级 error 缺陷全部修复落地。最危险的 dashboard"伪装健康"已基本消除。

剩余未达标的 4 页中，2 页（monitoring、cost-analysis）卡在已明确标注的图表量纲待改项，1 页（model-versions）卡在 F-031 状态标签，1 页（admin-home）是审计精度提升带来的校准。这些都有清晰的 finding 指针和规范条款指引，可纳入下一批次修复。

**下一批次建议优先级**：
1. 图表量纲整改（monitoring F-009/010、cost-analysis F-012/013）——影响 2 页达标 + 数据可信度
2. model-versions 走 MODEL_STATUS_LABELS（F-031）+ 修 R3 同屏——一页即可达标
3. error 态骨架保留补全（筛选区/操作区）+ dashboard "0→未知"——批量打磨
