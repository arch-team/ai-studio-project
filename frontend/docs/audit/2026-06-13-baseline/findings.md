# UI/UX 基线审计问题清单

> 审计日期：2026-06-13 | 场景：baseline
> 编号规则：F-### 稳定编号，供阶段 4 修复任务引用
> 严重度：P0（破坏可用性/可信度）> P1（明显不专业）> P2（打磨项）

## P0 — 破坏可用性/可信度（11 条）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-001 | dashboard/home | IX | error 态把加载失败静默降级为指标"0"+图表空态"暂无任务数据"+系统状态全绿"运行正常"，无 Flashbar/Alert/重试，将故障伪装成"平台健康且无数据"，严重误导用户判断 | home--error--light/dark.png |
| F-002 | spaces/ide | IA | "在线 IDE"页与 space-list 渲染几乎完全相同的空间列表，仅导航高亮不同；作为 special 类型未提供 IDE 工作区/会话启动器，两个导航项指向同一内容，用户点击认知落空 | ide--default--light.png vs space-list--default--light.png |
| F-003 | spaces/ide | IX | "在线 IDE"页无任何 IDE 特有交互（会话启动/终端/连接状态/未运行引导），核心交互闭环缺失，导航项缺乏独立功能价值 | ide--default--light.png |
| F-004 | spaces/space-list | IX | ✅ **已修复（2026-06-14 batch-2）**。原：error Alert 与表格 empty"暂无开发空间/创建开发空间"CTA 同屏。修复：error 时 Table empty 槽改为中性占位"无法显示开发空间列表"，抑制"创建"CTA（R3）。 | space-list--error--light/dark.png |
| F-005 | models/model-detail | IX | ✅ **已修复**（InlineErrorState）。error/!model 保留 PageLayout 骨架（标题+面包屑）+ InlineErrorState + 重试/返回，符合范式 A（R1/R4）。 | model-detail--error--light/dark.png |
| F-006 | models/model-versions | IX | ✅ **已修复**。主资源 !model 保留骨架报错；子资源 versionsError 显式 InlineErrorState 报错，不静默降级为空表（R2）。 | model-versions--error--light/dark.png |
| F-007 | audit/audit-logs | IX | ✅ **已修复**。error 保留 PageLayout 骨架（标题"审计日志"+面包屑）+ InlineErrorState + 重试（R1/R4）。 | audit-logs--error--light/dark.png |
| F-008 | audit/audit-logs | CONS | error 态与本模块 loading/empty 态（均保留页面 chrome）实现完全不一致，亦与 resource-quotas 的 Alert 式 error 态不一致，缺乏统一错误呈现组件 | audit-logs--error--dark.png |
| F-009 | monitoring/monitoring | VIS | ✅ **已修复（2026-06-14）**。原：「资源使用对比」堆叠柱状图量纲混用，百分比指标与存储绝对值（50 万级）共用单一 Y 轴，前三组柱贴地不可见。修复：柱状图改为各资源利用率对比（CPU/内存/GPU/存储 统一 0–100% 量纲，`formatUtilizationBarData`），四柱可读可比。回归确认 VIS 4.5。 | monitoring--default--light/dark.png |
| F-010 | monitoring/monitoring | VIS | ✅ **已修复（2026-06-14）**。原：「资源分布」环形图把三个百分比与存储绝对值放入同一维度求占比，存储独占整环 95%+。修复：异量纲不可求占比，移除该饼图（`formatUtilizationCompareData` 改为同量纲利用率对比柱状图），消除冗余与失真。回归确认。 | monitoring--default--light/dark.png |
| F-011 | reports/resource-usage、cost-analysis | CONS | ✅ **已修复**。两页 error 均保留 PageLayout 骨架（标题+面包屑）+ InlineErrorState + 重试（R1）。 | resource-usage--error--light.png, cost-analysis--error--light.png |
| F-012 | reports/cost-analysis | VIS | ✅ **已修复（2026-06-14）**。原：成本趋势折线图把"总计"聚合值与各分项同图，总计与计算重叠、小项贴底。修复：移除"总计"折线（`buildCostTrendSeries` 仅画分项），总成本由顶部 KPI 卡单独承载。回归确认。 | cost-analysis--default--light.png |
| F-013 | reports/cost-analysis | CONS | ✅ **已修复（2026-06-14）**。原：折线图与环形图同色不同义（蓝=总计/蓝=计算）、同义不同色。修复：两图均删除硬编码 hex，走 Cloudscape 分类色板 token（`colorChartsPaletteCategorical*`，品牌青打头），分项顺序一致，同类别跨图自动同色。回归确认 CONS 4.5。 | cost-analysis--default--light/dark.png |
| F-014 | admin/user-management | IX | ✅ **已修复**。error 保留 PageLayout 骨架（标题"用户管理"+面包屑）+ InlineErrorState + 重试（R1/R4）。 | user-management--error--light/dark.png |

## P1 — 明显不专业（跨模块高频）

### 全局装饰物残留（最高频，跨 7+ 模块）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| ~~F-020~~ | ~~全局~~ | VIS | ❌ **误报（2026-06-14 排查关闭）**。右下角悬浮彩色 emoji 圆形图标经全量排查（`src/` + `index.html` + `main.tsx` + 布局 + 审计脚本 `auditSetup.ts` + `playwright.config.ts`）**确认非应用代码**——源码中不存在任何沙滩 emoji、`position:fixed` 悬浮元素或第三方挂件脚本；`auditSetup` 仅注入 sessionStorage/localStorage，不操作 DOM。该图标系**截图机器的浏览器扩展**（如划词翻译/客服挂件）注入，且在 2026-06-14 修复后截图中位置纹丝不动（与代码改动无关）。结论：非平台缺陷，不修代码，建议截图环境用纯净 profile 复跑以消除。 | （误报，无需修复） |

### error 态退化（除已列 P0 外）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-021 | training/training-detail | IX/CONS | ✅ **已修复**。error/!job 保留 PageLayout 骨架 + InlineErrorState（title 区分"加载失败"/"任务不存在"）+ 条件重试，与 list 页范式统一。 | training-detail--error--light/dark.png |
| F-022 | training/training-list | IX | ✅ **已修复（2026-06-14 batch-2）**。TrainingJobTable 新增 `hasError` prop，error 时 empty 槽改为中性占位"无法显示训练任务列表"，不与"加载失败"同屏（R3）。 | training-list--error--light/dark.png |
| F-023 | datasets/dataset-detail | IX/CONS | ✅ **已修复（2026-06-14 batch-2）**。loading 改骨架内 Spinner；error/!dataset 改为 PageLayout 骨架 + InlineErrorState（title 区分"加载失败"/"数据集不存在"）+ 条件重试（R1/R4）。 | dataset-detail--error--light.png, dataset-detail--loading--light.png |
| F-024 | datasets/dataset-versions | IX/CONS | ✅ **已修复（2026-06-14 batch-2）**。!dataset 改 PageLayout 骨架 + InlineErrorState；版本子资源 error 显式报错 + error 时抑制"创建第一个版本"empty CTA（R1/R2/R3/R4）。 | dataset-versions--error--light.png |
| F-025 | templates/template-detail | IX/CONS | ✅ **已修复（2026-06-14 batch-2）**。loading 改骨架内 Spinner；error/!template 改为 PageLayout 骨架 + InlineErrorState + 条件重试，复用既有 breadcrumbs（R1/R4）。 | template-detail--loading--light.png, template-detail--error--light.png |
| F-026 | templates/template-list | IX | empty 态自相矛盾：表格显示"暂无模板(0)"但"热门模板"区仍满载 5 张卡片；loading 态同样仅表格显示加载、卡片已满载，加载范围不一致；error 态缺重试按钮 | template-list--empty--light.png, template-list--loading--light.png, template-list--error--light.png |
| F-027 | monitoring/monitoring | IX | ✅ **已修复**。error 保留 PageLayout 骨架（标题"资源监控"+面包屑）+ InlineErrorState + 重试（R1/R4）。 | monitoring--error--light/dark.png |
| F-028 | resource-quotas/resource-quotas | IX | ✅ **已修复（2026-06-14 batch-2）**。hook 解构 refetch，error Alert 补"重试"按钮；error 时 Table empty 槽改中性占位，抑制"暂无配置"空态（R2/R3/R4）。 | resource-quotas--error--light/dark.png |
| F-029 | spaces/space-detail | CONS | loading 态标题为泛化"空间详情"，default 态为实体名"running-jupyter-space"，加载前后标题跳变 | space-detail--loading--light.png |
| F-030 | dashboard/home | IX | ✅ **已修复（2026-06-14 batch-2 完整收口）**。原"平台服务"已早先降级；本次补齐"调度器"（→"未知"）、"失败任务"/"暂停任务"计数（→"无法获取"）在 error 时一并降级，系统状态面板不再有任何子项伪装全绿（R2）。 | home--error--dark.png |

### 术语/文案/CTA 一致性

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-031 | models/model-versions | CONS | ✅ **已修复（2026-06-14 P1）**。ModelVersionTable 状态列原裸渲染英文枚举 `{item.status}`，改为走 `MODEL_STATUS_LABELS` 中文映射（已注册/已部署/已归档/已失效），与 list/detail 页一致。 | model-versions--default--light.png |
| ~~F-032~~ | datasets/dataset-create、space-create | IX | ❌ **误判（2026-06-14 P1 关闭）**。"必填字段红色 `*`"与项目规范冲突：ux-writing.md §2.4 与 page-templates.md §3.3 约定必填字段以 Cloudscape `FormField constraintText="必填"` 标注，且 design-tokens/component-design 严禁内联样式（零自定义 CSS 铁律），红星实现需 `<span style>` 违规。当前 `constraintText="必填"` 写法**符合规范**，非缺陷。如需视觉红星须先升级设计规范。 | dataset-create--default--light.png, space-create--default--light.png |
| F-033 | admin/admin-home | IX | ✅ **已修复（2026-06-14 P1）**。UserManagementPage 空态（含 embedded 模式，admin dashboard Tab 内无页头按钮）Table empty 槽补"新建用户"主操作 CTA，空态引导不再断裂。 | admin-home--default--light/dark.png |
| F-034 | reports/cost-analysis | CONS | ⚠️ **部分修复（2026-06-14 P1）**。KPI 数值颜色已修：移除 `color="text-status-info"`（高饱和蓝）改用默认中性文字色，与 reports-home 一致，并清除 costCards 死代码硬编码 hex。**剩余**：折线图缺"数据传输"系列与环形图/明细表分类口径不一致，属后端字段缺口 F-070（移交后端），前端不伪造。 | cost-analysis--default--light.png |
| F-035 | shared/not-found、unauthorized | IA | 内容顶部对齐而非视口垂直居中，下方大片空白，页面重心失衡，呈"未完成布局"观感 | not-found--default--light/dark.png, unauthorized--default--light/dark.png |
| F-036 | monitoring/monitoring | CONS | ✅ **已修复（2026-06-14 P1）**。AlertsPanel 状态列原对所有未解决告警一律 `type="warning"`（黄图标），改为 resolved→success、其余按 `ALERT_SEVERITY_COLORS[severity]` 联动（critical 红/warning 黄/info 蓝），与"级别"列语义呼应。 | monitoring--default--light.png |

## P2 — 打磨项（节选高价值项）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-040 | training/training-detail | VIS | "持续时间 21114h 27m"（约 2.4 年）为异常 mock 数据，"完成时间 -"裸破折号，对外演示前需修正 fixture 与空值展示 | training-detail--default--light.png |
| F-041 | datasets/dataset-list | IX | empty 态仅有文案缺引导主操作按钮（如"注册第一个数据集"），与 versions 页 empty 有 CTA 不一致 | dataset-list--empty--light.png |
| F-042 | models/model-versions | IA | 关键指标列为纯文本，未高亮最优值或迷你可视化，横向对比效率有提升空间 | model-versions--default--light.png |
| F-043 | datasets/dataset-versions | IA | 版本表未对最新/当前版本做视觉强调（无 latest/当前徽标），用户难一眼识别活跃版本 | dataset-versions--default--light.png |
| F-044 | training/training-list | VIS | ✅ **已修复（2026-06-14 P1 核实确认）**。TrainingStatusBadge 中 `running` 已映射为 Cloudscape `in-progress` 类型（蓝色旋转动画），语义明确，与 pending/stopped 等弱语义灰图标区分清晰。 | training-list--default--light.png |
| F-045 | spaces/space-detail | VIS | SageMaker ARN 长字符串在 KeyValuePairs 第三列折行 3 行，与同行其他字段行底不对齐 | space-detail--default--dark.png |
| F-046 | admin/user-management | VIS | 截图视口不一致：admin-home 与空/加载/错误态约 1440px，user-management--default 约 720px（疑为截图流水线视口设置，建议核查，非 UI 缺陷） | user-management--default--light.png |
| F-047 | auth/login | IX | 密码字段无显隐切换图标、无"忘记密码/联系管理员"辅助入口（视产品定位） | login--default--light.png |
| F-048 | reports/cost-analysis | VIS | 环形图小占比类别（其他 1.8%、数据传输 2.8%）引线标签在左上拥挤堆叠 | cost-analysis--default--light.png |
| F-049 | shared/not-found、unauthorized | VIS/CONS | 缺品牌 logo、纯文字无插画/图标，视觉单薄，与 login 页品牌化水准落差 | not-found--default--light.png |
| F-050 | monitoring/monitoring | IX | loading 态整页仅单 Container+居中 spinner，缺指标卡/图表骨架占位，加载完成时布局跳变明显 | monitoring--loading--light.png |

## 待回归项

| 编号 | 模块/页面 | 说明 |
|------|----------|------|
| F-060 | training/checkpoints | 审计覆盖盲区：四态截图渲染相同（均"请选择训练任务"初始态），mock 未驱动二级检查点列表 API。需在 fixture 层补"预选任务"逻辑后回归，方能评估真实四态。 |

## 移交后端

| 编号 | 模块/页面 | 说明 |
|------|----------|------|
| F-070 | reports/cost-analysis | **数据契约不一致（2026-06-14 修 F-012/013 时发现）**：`DailyCost`（每日成本时间序列）缺 `data_transfer_cost_usd` 字段，而 `CostSummary` / `CostBreakdown` 均有"数据传输"分项。致成本趋势折线图只能画 4 类（计算/存储/网络/其他），饼图与明细表为 5 类（多"数据传输"），同页两图类别集合不一致（design-reviewer 标记 P2 CONS）。**前端不伪造日维度数据传输数据**；需后端在 daily_costs 时间序列补 `data_transfer_cost_usd` 字段后，前端 `DailyCost` 类型与 `buildCostTrendSeries` 同步加入该分项，使两图类别对齐。 |

> 注：F-040 的异常 mock 数据属审计 fixture 范畴，在前端 audit/fixtures 修正，非后端缺口。
