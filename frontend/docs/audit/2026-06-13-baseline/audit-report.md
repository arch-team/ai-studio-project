# UI/UX 基线审计报告（阶段 1）

> 审计日期：2026-06-13 | 场景：baseline
> 范围：13 模块 29 页面（billing 无页面除外），截图 160 张（状态 × 双主题）
> 方法：截图流水线（Playwright，MockApi 注入状态）→ 13 路 design-reviewer 独立四维度评分 → 聚合
> 配套文件：[score-matrix.md](score-matrix.md)（评分矩阵）、[findings.md](findings.md)（问题清单）

---

## 1. 执行摘要

| 指标 | 数值 |
|------|------|
| 全局均分 | **3.72** / 5.0（28 个有效评分页面） |
| 达标率（≥4.0） | **36%**（10/28） |
| P0 问题 | 14 条 |
| P1 问题 | 17 条（含 1 条全局装饰物，跨 7+ 模块） |
| P2 问题 | 11 条（节选） |
| 待回归 | 1 项（checkpoints 二级数据态未覆盖） |

**核心结论**：信息架构（IA 均分 4.05）是全平台最稳固的能力面——页面骨架、信息分区、主次操作普遍达标，default 态质量明显高于异常态。**交互完整度（IX 均分 3.43）是系统性短板**，集中表现为 error 态的缺失、退化与不一致——这是把多个本可达标（IA/VIS 已 4.0+）的页面拖到门槛线下的决定性因素。视觉层面暗色模式适配普遍合格，个别图表渲染（monitoring/cost-analysis 量纲混用）和一个全局装饰物（"沙滩 emoji"）是主要拖分项。

**与"商用产品水准"的差距可归纳为一句话**：核心设计能力已具备（有数据的正常态接近标杆），但异常态处理、跨页一致性、数据可视化严谨性这三项"商用产品的可信度细节"尚未成体系。这恰好验证了 spec 的判断——差距不在视觉风格本身，而在交互完整度与一致性。

---

## 2. 高频问题模式 Top 5（阶段 2 规范的内容优先级输入）

### 模式 1：error 态系统性失守（最高频，影响 9 个页面，含 8 条 P0）

错误态是本次审计最严重、最普遍的问题，且呈现多种失败形态：

- **静默降级为正常态**（最危险）：dashboard/home 把加载失败伪装成"指标 0 + 系统全绿"；model-versions、dataset-versions 把失败降级为"空数据"——用户据此误判平台状态。
- **整页骨架塌缩**：audit-logs、user-management、reports 两页、model-detail、dataset-detail、template-detail 的 error 态丢失 Header/面包屑/筛选区，退化为孤立的裸文本错误框，无导航出口。
- **与 empty 态语义叠加**：training-list、space-list、resource-quotas 的 error 态下方仍渲染"暂无数据/创建"空态引导，失败与"无数据可创建"矛盾并存。
- **缺恢复动作**：几乎所有 error 态都没有"重试"按钮。

→ **规范启示**：阶段 2 必须产出统一的「错误态模式」——保留页面骨架（Header+面包屑）+ Cloudscape Alert（图标+标题+描述）+ 重试/返回动作，且错误态必须抑制 empty 态内容、绝不静默降级。这是单一规范可同时拉升约 9 个页面的最高杠杆点。

### 模式 2：全局装饰物"沙滩 emoji"污染（影响 7+ 模块所有页面）

右下角悬浮的"沙滩/棕榈树"彩色圆形图标出现在几乎所有页面所有状态，部分页面遮挡内容。疑似遗留的占位/调试 widget，是整个应用最显著且最易修复的专业感杀手。

→ **规范启示**：这不是设计规范问题而是一处需立即清除的遗留组件（阶段 4 批次 1 优先移除）。但它的存在说明缺少"生产构建不得含占位/调试元素"的检查项。

### 模式 3：empty/loading 态范围与完整性不足（影响约 8 个页面）

- empty 态普遍缺引导 CTA（dataset-list、admin-home、resource-quotas、training-list）；
- 部分页面的 empty/loading 只覆盖主表格而放任其他区域满载（template-list 的"热门模板"卡片在空态/加载态仍满载，自相矛盾）；
- loading 态多为孤立 spinner，缺骨架屏（template-detail、model-detail、monitoring、user-management）。

→ **规范启示**：阶段 2 的「四态完整性规范」需明确——empty 带主操作 CTA、loading 用骨架屏并覆盖全部数据区、各态间页面骨架稳定不跳变。

### 模式 4：跨页一致性漂移（术语/配色/模式）

- **状态术语中英混用**：model-versions 用英文枚举，list/detail 用中文（违反项目规范要求的 `{ENTITY}_STATUS_LABELS` 单一映射）；
- **空文案不统一**：list 用"暂无模型"、versions 用"暂无版本历史"；
- **图表配色语义冲突**：cost-analysis 同页折线图与环形图，蓝色一处代表"总计"一处代表"计算"；
- **同页标题跳变**：space-detail 的 loading 态泛化标题 vs default 态实体名。

→ **规范启示**：阶段 2 的「UX 文案规范」需建立单一术语映射表 + 状态标签常量；设计 token 需定义数据可视化的类别配色序列（一类一色，全局复用）。

### 模式 5：数据可视化严谨性缺失（影响 monitoring、cost-analysis 两个图表密集页）

monitoring 两大图表和 cost-analysis 折线图都犯了**量纲混用**错误——把百分比与绝对字节数、把聚合值与分项画在同一量纲/同一坐标轴，导致图表传达的信息与真实数据相悖。这是专业 BI 产品不会犯的错误，直接破坏监控/成本页的立身之本（数据可信）。

→ **规范启示**：阶段 2 的「页面模板」中 Dashboard 模板需含图表规范——同图同量纲、聚合值与分项分离（独立 KPI 或独立图）、类别配色统一。

---

## 3. 各模块小结

| 模块 | 均分 | 一句话结论 |
|------|------|-----------|
| **datasets** | 4.0 | 四态覆盖最完整、detail 页信息架构达标杆水准，是全平台最佳实践；移除装饰物+统一 error 态后可上探 4.3-4.5。 |
| **reports** | 4.1 | reports-home/resource-usage 达标，被含图表的 cost-analysis（3.8，图表量纲混用+配色冲突）拉低；error 态两页一致塌缩。 |
| **training** | 3.9 | create（4.4）与 detail 信息架构出色，被 detail 的 error 态裸文本（3.4）拖累；checkpoints 四态待回归。 |
| **models** | 3.7 | list（4.4）标杆水准，detail/versions 因 error 态 P0（死胡同/降级为空）跌破门槛；状态术语中英混用。 |
| **spaces** | 3.7 | create/detail 达标，被 ide 页（2.8，IDE 功能缺失沦为列表复制品）严重拉低；列表 error 态语义矛盾。 |
| **auth** | 3.9 | login 品牌感全平台最强（渐变+logo+技术注脚），接近门槛；差登录辅助交互（密码显隐/忘记密码）。 |
| **admin** | 3.8 | 正常态达标，error 态整页塌缩（P0）+ dashboard 空态缺 CTA；"正常态达标、异常态生硬"的典型。 |
| **templates** | 3.6 | detail 信息架构优秀，但 list 的 empty/loading 范围错配（热门卡片满载）+ 两页 error/loading 不统一。 |
| **dashboard** | 3.6 | 首页门面，IA/VIS/CONS 均达 4.0，唯 error 态把故障伪装成健康（P0）——门面位置危害放大。 |
| **shared** | 3.1 | not-found/unauthorized 同源，布局未垂直居中失衡 + 缺品牌/插画；两页一致性是优点。 |
| **monitoring** | 3.0 | 骨架与三态框架达标，但两大核心图表量纲混用失真（P0×2）+ 装饰物，监控页可信度失守。 |
| **audit** | 2.9 | default/loading/empty 三态达对外演示水准，被单点 error 态整页塌缩（P0）拖到全平台最低区。 |

---

## 4. 修复批次建议

> 基于 spec §7 预设批次，结合实际评分微调。原则：先修一处可拉升多页的系统性问题（error 态规范、装饰物），再按业务关键度推进。

### 前置全局修复（批次 0，最高杠杆，建议最先做）

- **F-020 移除全局"沙滩 emoji"装饰物**：一处修复提升 7+ 模块观感，零风险。
- **建立统一 error 态组件/模式**（对应 F-001/004/005/006/007/008/011/014/021/023/025/027/028）：保留骨架 + Cloudscape Alert + 重试 + 抑制 empty 叠加 + 禁止静默降级。这是单一规范拉升约 9 个页面的最高杠杆点，应在阶段 2 规范中优先定义、阶段 4 最先落地。

### 批次 1：平台门面与核心流程（DoD 门槛 4.5）

training（list/create/detail）+ dashboard/home + 全局导航/MainLayout + spaces/ide（P0 功能缺失需产品决策：实现 IDE 工作区 or 移除重复导航）。
- 重点：dashboard error 态（F-001/030）、training-detail error 态（F-021）、ide 页定位（F-002/003）、training mock 数据修正（F-040）、checkpoints 回归（F-060）。

### 批次 2：高频业务模块（DoD 门槛 4.0）

datasets、models、spaces（list/detail/create）、monitoring。
- 重点：monitoring 图表量纲修复（F-009/010）、models error 态与术语统一（F-005/006/031）、spaces 列表 error 态（F-004/029）、各模块 empty CTA（F-041）。

### 批次 3：低频/管理类模块（DoD 门槛 4.0）

templates、audit、reports、admin、resource-quotas、shared、auth。
- 重点：audit/admin/reports error 态塌缩（F-007/011/014）、template-list 空态范围（F-026）、cost-analysis 图表配色与分层（F-012/013/034）、shared 页居中与品牌化（F-035/049）、resource-quotas error 态（F-028）。

---

## 5. 阶段衔接

本基线审计完成 spec 的**阶段 1**。下一步进入**阶段 2（靶向设计规范）**，四份产出的内容优先级直接由本报告 §2 的"高频问题模式 Top 5"驱动：

1. `interaction-states.md` ← 模式 1/3（error 态统一模式 + 四态完整性，最高优先级）
2. `design-tokens.md` ← 模式 5（数据可视化类别配色序列）
3. `ux-writing.md` ← 模式 4（术语映射表 + 状态标签常量）
4. `page-templates.md` ← 模式 5（Dashboard 图表规范）+ 模式 1（各模板的错误/空/加载态）

阶段 2 计划将在本报告评审通过后另行编写。
