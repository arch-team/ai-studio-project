# UI/UX 基线审计评分矩阵

> 审计日期：2026-06-13 | 场景：baseline（阶段 1 全量基线）
> 评分框架：IA 30% / IX 30% / CONS 25% / VIS 15%，1-5 分，商用门槛 4.0
> 评分由 13 路 design-reviewer 独立评审（截图：13 模块 × 状态 × 双主题，共 160 张）

## 评分矩阵

| 模块 | 页面 | IA | IX | CONS | VIS | 综合 | 达标(≥4.0) |
|------|------|----|----|------|-----|------|:----------:|
| dashboard | home | 4.0 | 2.5 | 4.0 | 4.0 | 3.6 | ❌ |
| auth | login | 4.0 | 3.5 | 4.0 | 4.0 | 3.9 | ❌ |
| training | training-list | 4.5 | 3.5 | 4.0 | 4.0 | 4.0 | ✅ |
| training | training-create | 4.5 | 4.0 | 4.5 | 4.5 | 4.4 | ✅ |
| training | training-detail | 4.5 | 3.0 | 3.0 | 3.5 | 3.4 | ❌ |
| training | checkpoints | 4.0 | N/A | 4.0 | 4.0 | 无效* | ⚠️ |
| templates | template-list | 4.0 | 3.0 | 3.5 | 4.0 | 3.6 | ❌ |
| templates | template-detail | 4.5 | 3.0 | 3.0 | 4.0 | 3.6 | ❌ |
| models | model-list | 4.5 | 4.0 | 4.5 | 4.5 | 4.4 | ✅ |
| models | model-detail | 4.5 | 2.5 | 3.0 | 4.0 | 3.4 | ❌ |
| models | model-versions | 4.0 | 2.5 | 3.5 | 4.0 | 3.4 | ❌ |
| datasets | dataset-list | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | ✅ |
| datasets | dataset-create | 4.0 | 3.5 | 4.0 | 4.0 | 3.9 | ❌ |
| datasets | dataset-detail | 4.5 | 4.0 | 4.0 | 4.0 | 4.1 | ✅ |
| datasets | dataset-versions | 4.0 | 4.5 | 4.0 | 4.0 | 4.1 | ✅ |
| resource-quotas | resource-quotas | 4.0 | 3.5 | 3.5 | 4.0 | 3.7 | ❌ |
| spaces | space-list | 4.0 | 3.5 | 4.0 | 4.0 | 3.9 | ❌ |
| spaces | space-create | 4.0 | 3.5 | 4.5 | 4.5 | 4.1 | ✅ |
| spaces | space-detail | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | ✅ |
| spaces | ide | 2.5 | 2.5 | 3.0 | 3.5 | 2.8 | ❌ |
| monitoring | monitoring | 3.5 | 3.0 | 3.5 | 2.0 | 3.0 | ❌ |
| audit | audit-logs | 4.0 | 2.5 | 2.5 | 3.5 | 2.9 | ❌ |
| admin | admin-home | 4.0 | 3.5 | 4.0 | 4.0 | 3.9 | ❌ |
| admin | user-management | 4.0 | 3.0 | 4.0 | 4.0 | 3.6 | ❌ |
| reports | reports-home | 4.5 | 4.0 | 4.5 | 4.5 | 4.4 | ✅ |
| reports | resource-usage | 4.5 | 4.5 | 3.5 | 4.0 | 4.1 | ✅ |
| reports | cost-analysis | 4.0 | 4.5 | 3.0 | 3.5 | 3.8 | ❌ |
| shared | not-found | 3.0 | 3.0 | 3.5 | 3.0 | 3.1 | ❌ |
| shared | unauthorized | 3.0 | 3.0 | 4.0 | 3.0 | 3.1 | ❌ |

> billing：无路由页面，不参与评分。
> *checkpoints：master-detail 模式，列表数据依赖先选中训练任务（二级 API），本次 mock 状态切换引擎仅控制顶层列表 API，四态截图渲染相同（均为"请选择训练任务"初始引导态），IX 维度无法评估。综合分不作为商用结论，需在 fixture 层补"预选任务"逻辑后回归。其余三维度（IA 4.0 / CONS 4.0 / VIS 4.0）仅供参考。

## 汇总指标

- **全局均分**：3.72（28 个有效评分页面，checkpoints 因四态无效不计入）
- **达标率**：10/28 = 36%
- **达标页面（10 个）**：training-list、training-create、model-list、dataset-list、dataset-detail、dataset-versions、space-create、space-detail、reports-home、resource-usage

## 最低分 Top 5

| 排名 | 页面 | 综合分 | 核心问题 |
|------|------|--------|---------|
| 1 | spaces/ide | 2.8 | "在线 IDE"页是 space-list 的导航复制品，无真正 IDE 工作区/会话入口（P0） |
| 2 | audit/audit-logs | 2.9 | error 态整页塌缩为裸文本，丢失标题/面包屑/筛选区（P0） |
| 3 | monitoring/monitoring | 3.0 | 两大核心图表量纲混用（百分比与字节数同轴），数据可视化失真（P0×2） |
| 4 | shared/not-found | 3.1 | 内容顶部对齐未垂直居中，布局失衡 + 缺品牌/插画 |
| 4 | shared/unauthorized | 3.1 | 同 not-found（同源布局缺陷） |

## 维度均分（28 页）

| 维度 | 均分 | 观察 |
|------|------|------|
| IA 信息架构 | 4.05 | 最强项——页面骨架/信息分区普遍达标 |
| IX 交互完整度 | 3.43 | 最弱项——error 态缺失/退化是系统性短板 |
| CONS 一致性 | 3.79 | error 态处理跨页不统一拖累 |
| VIS 视觉品质 | 3.88 | 暗色模式适配普遍合格；个别图表渲染与装饰物拖分 |
