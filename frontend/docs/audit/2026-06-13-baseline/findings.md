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
| F-004 | spaces/space-list | IX | error 态下 Alert"加载失败"与表格内 empty 态"暂无开发空间/创建开发空间"同屏并存，语义矛盾，失败时不应提供"创建"引导 | space-list--error--light/dark.png |
| F-005 | models/model-detail | IX | error 态（资源不存在）为死胡同：无面包屑/标题/图标/恢复操作（重试或返回列表），用户无法继续，远低于同模块 list 错误态水准 | model-detail--error--light/dark.png |
| F-006 | models/model-versions | IX | error 态与 empty 态渲染完全一致（均"暂无版本历史"空表格），加载失败被错误降级为"无数据"，无 Alert/重试，掩盖故障并误导用户 | model-versions--error--light/dark.png |
| F-007 | audit/audit-logs | IX | error 态整页塌缩为裸容器，丢失标题/面包屑/筛选区，仅一行红色裸文本，无图标/Alert/重试，破坏审计页可信度 | audit-logs--error--light/dark.png |
| F-008 | audit/audit-logs | CONS | error 态与本模块 loading/empty 态（均保留页面 chrome）实现完全不一致，亦与 resource-quotas 的 Alert 式 error 态不一致，缺乏统一错误呈现组件 | audit-logs--error--dark.png |
| F-009 | monitoring/monitoring | VIS | 「资源使用对比」堆叠柱状图量纲混用：百分比指标（CPU/内存/GPU，个位数）与存储绝对值（50 万级）共用 0–600000 单一 Y 轴，前三组柱被压成贴地不可见细线，整图退化为"单根存储柱"，无法对比 | monitoring--default--light/dark.png |
| F-010 | monitoring/monitoring | VIS | 「资源分布」环形图量纲混用：CPU 62%/内存 48%/GPU 87% 三个百分比与"存储"50 万级绝对值放入同一维度求占比，致三项退化为环顶极细色块、引导线交叠，"存储"独占整环 95%+ 面积，占比含义失真 | monitoring--default--light/dark.png |
| F-011 | reports/resource-usage、cost-analysis | CONS | error 态丢失整个页面骨架（顶栏/面包屑/Header/操作按钮消失），仅剩孤立错误容器，与 default/loading 态外壳不一致（两页一致地错，走了独立渲染分支未复用骨架） | resource-usage--error--light.png, cost-analysis--error--light.png |
| F-012 | reports/cost-analysis | VIS | 成本趋势折线图将"总计"聚合值与计算/存储/网络/其他分项画在同一量纲折线图：总计与计算两条蓝线高度重叠不可区分，存储/网络/其他被压缩贴底不可读 | cost-analysis--default--light.png |
| F-013 | reports/cost-analysis | CONS | 同页折线图与环形图颜色语义冲突：蓝色在折线图=总计、在环形图=计算（同色不同义）；"其他"折线图为灰、环形图为橙红（同义不同色），跨图阅读被误导 | cost-analysis--default--light/dark.png |
| F-014 | admin/user-management | IX | error 态整页框架塌缩：加载失败时 Header/面包屑/标题/筛选器全部消失，仅剩孤立红字错误框，无重试按钮、无导航出口，用户陷入死胡同 | user-management--error--light/dark.png |

## P1 — 明显不专业（跨模块高频）

### 全局装饰物残留（最高频，跨 7+ 模块）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-020 | 全局（datasets/spaces/templates/monitoring/reports/admin 等所有页面） | VIS | 右下角悬浮"沙滩/棕榈树"彩色 emoji 圆形图标出现在几乎所有页面所有状态，疑似遗留的占位/调试 widget，部分页面遮挡内容，是整个应用最显著的专业感杀手 | dataset-list--default--light.png 及全站多数截图 |

### error 态退化（除已列 P0 外）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-021 | training/training-detail | IX/CONS | error 态为裸红字"资源不存在"，缺错误图标/返回/重试按钮，与 list 页 error 态（Alert+重试）模式不统一 | training-detail--error--light/dark.png |
| F-022 | training/training-list | IX | error 态下方表格叠加渲染 empty 态文案"暂无训练任务/尚未创建任何训练任务"，错误与空状态逻辑冲突 | training-list--error--light/dark.png |
| F-023 | datasets/dataset-detail | IX/CONS | loading/error 态丢失页面 Header 与面包屑，整页塌缩为单个空 Container，error 时无上下文也无"返回列表"出口 | dataset-detail--error--light.png, dataset-detail--loading--light.png |
| F-024 | datasets/dataset-versions | IX/CONS | error 态与 empty 态视觉完全相同（均"暂无版本记录"+"创建第一个版本"），未区分"加载失败"与"无数据"语义 | dataset-versions--error--light.png |
| F-025 | templates/template-detail | IX/CONS | loading 态为孤立居中 spinner 无骨架/无面包屑；error 态用纯红字非 Cloudscape Alert，丢失页面头部；与 list 页错误态不一致 | template-detail--loading--light.png, template-detail--error--light.png |
| F-026 | templates/template-list | IX | empty 态自相矛盾：表格显示"暂无模板(0)"但"热门模板"区仍满载 5 张卡片；loading 态同样仅表格显示加载、卡片已满载，加载范围不一致；error 态缺重试按钮 | template-list--empty--light.png, template-list--loading--light.png, template-list--error--light.png |
| F-027 | monitoring/monitoring | IX | error 态仅"加载失败"纯红色文案，无重试/图标/引导，未用 Cloudscape Alert+action 模式，用户无恢复路径 | monitoring--error--light/dark.png |
| F-028 | resource-quotas/resource-quotas | IX | error 态 Alert 缺重试按钮，且 Alert 下方表格仍渲染"暂无配置"空态，错误与空态语义叠加 | resource-quotas--error--light/dark.png |
| F-029 | spaces/space-detail | CONS | loading 态标题为泛化"空间详情"，default 态为实体名"running-jupyter-space"，加载前后标题跳变 | space-detail--loading--light.png |
| F-030 | dashboard/home | IX | error 态"系统状态"面板在数据获取失败时仍显示全绿"运行正常/就绪/无"，与页头 pill 叠加放大"一切正常"的错误信号，应降级为"未知/无法获取" | home--error--dark.png |

### 术语/文案/CTA 一致性

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-031 | models/model-versions | CONS | 状态枚举中英不一致：versions 页用英文 deployed/registered/archived/failed，list/detail 页用中文已部署/已注册/已归档/已失效，同一术语跨页混用 | model-versions--default--light.png |
| F-032 | datasets/dataset-create、space-create | IX | 必填字段缺少显式视觉强标记（红色 `*`），仅靠"必填"文字提示，校验前用户难以快速识别必填项 | dataset-create--default--light.png, space-create--default--light.png |
| F-033 | admin/admin-home | IX | 管理后台 dashboard 空列表态缺少"新建用户"主操作 CTA，与 user-management 独立页（右上角有"+新建用户"）不一致，空态下引导断裂 | admin-home--default--light/dark.png |
| F-034 | reports/cost-analysis | CONS | 分类口径不一致：折线图无"数据传输"系列，但环形图与明细表含"数据传输"独立类别，维度对不上；KPI 数值用高饱和蓝色偏离 Cloudscape 中性色且与 reports-home 不一致 | cost-analysis--default--light.png |
| F-035 | shared/not-found、unauthorized | IA | 内容顶部对齐而非视口垂直居中，下方大片空白，页面重心失衡，呈"未完成布局"观感 | not-found--default--light/dark.png, unauthorized--default--light/dark.png |
| F-036 | monitoring/monitoring | CONS | 告警表"状态"列对严重/警告/信息三种级别一律显示相同"⚠️ 触发中"黄色图标，状态指示与级别列语义割裂 | monitoring--default--light.png |

## P2 — 打磨项（节选高价值项）

| 编号 | 模块/页面 | 维度 | 问题描述 | 截图 |
|------|----------|------|---------|------|
| F-040 | training/training-detail | VIS | "持续时间 21114h 27m"（约 2.4 年）为异常 mock 数据，"完成时间 -"裸破折号，对外演示前需修正 fixture 与空值展示 | training-detail--default--light.png |
| F-041 | datasets/dataset-list | IX | empty 态仅有文案缺引导主操作按钮（如"注册第一个数据集"），与 versions 页 empty 有 CTA 不一致 | dataset-list--empty--light.png |
| F-042 | models/model-versions | IA | 关键指标列为纯文本，未高亮最优值或迷你可视化，横向对比效率有提升空间 | model-versions--default--light.png |
| F-043 | datasets/dataset-versions | IA | 版本表未对最新/当前版本做视觉强调（无 latest/当前徽标），用户难一眼识别活跃版本 | dataset-versions--default--light.png |
| F-044 | training/training-list | VIS | "运行中"状态图标语义偏弱（灰色样式），与其他状态明确色彩图标不协调 | training-list--default--light.png |
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

（本次审计未发现需移交后端的 API 缺口；F-040 的异常 mock 数据属审计 fixture 范畴，在前端 audit/fixtures 修正。）
