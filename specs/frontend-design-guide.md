# AI 训练平台前端设计规范

> 本文档是项目的前端 UI/UX 设计标准，所有前端开发 MUST 遵循此规范。
> 关联宪章: `constitution.md` Principle XI. UI/UX Consistency

## 版本信息

| 属性 | 值 |
|------|-----|
| Version | 1.0.0 |
| Created | 2026-01-15 |
| Last Updated | 2026-01-15 |
| Status | Active |

---

## 目标定位

打造一个**让用户评价远超同类平台**的企业级 AI 训练平台，通过以下核心策略：

- **效率至上**：减少用户操作步骤，提供智能默认值
- **专业可信**：企业级视觉语言，传递技术实力
- **认知友好**：降低学习曲线，渐进式复杂度展示
- **差异化体验**：在关键场景超越 SageMaker/Vertex AI/Azure ML

---

## 一、核心设计原则

### 1.1 效率优先原则

| 原则 | 描述 | 实践示例 |
|------|------|---------|
| **3 秒规则** | 关键任务入口 ≤3 秒可达 | 首页快速操作区 |
| **智能默认** | 90% 场景无需修改默认值 | 基于历史推荐配置 |
| **批量优先** | 支持多选批量操作 | 批量停止/删除训练任务 |
| **上下文保持** | 操作后保持用户位置 | Modal 操作后不跳转 |

### 1.2 渐进式复杂度原则

```
初级用户路径：模板 → 一键启动 → 监控结果
中级用户路径：配置 → 参数调整 → 详细监控
高级用户路径：自定义 → YAML 编辑 → API 集成
```

### 1.3 信任建立原则

- **透明性**：所有操作有明确反馈和状态
- **可预测**：相同操作产生一致结果
- **可撤销**：关键操作支持撤销或确认
- **可追溯**：完整的操作历史和审计日志

---

## 二、视觉设计规范

### 2.1 色彩系统

#### 品牌色（基于 Cloudscape）

```css
/* 主色调 - 传递专业、可信 */
--primary: #0972d3;        /* Cloudscape Blue - 主操作 */
--primary-hover: #065299;  /* 悬停状态 */
--primary-active: #033160; /* 激活状态 */

/* 语义色 - 状态传递 */
--success: #037f0c;        /* 成功/运行中 */
--warning: #8d6605;        /* 警告/等待中 */
--error: #d91515;          /* 错误/失败 */
--info: #0972d3;           /* 信息提示 */
```

#### 任务状态色彩映射

| 状态 | 颜色 | Badge 样式 | 含义 |
|------|------|-----------|------|
| `submitted` | 灰色 | `grey` | 已提交，等待调度 |
| `pending` | 蓝色 | `blue` | 等待资源 |
| `running` | 绿色 | `green` | 正在运行 |
| `paused` | 黄色 | `yellow` | 用户暂停 |
| `preempted` | 橙色 | `orange` | 被抢占 |
| `completed` | 绿色 | `green` | 成功完成 |
| `failed` | 红色 | `red` | 执行失败 |
| `cancelled` | 灰色 | `grey` | 用户取消 |

### 2.2 排版规范

```typescript
// 字体层级 - 使用 Cloudscape 内置
const typography = {
  h1: { size: '24px', weight: 700, lineHeight: 1.25 },  // 页面标题
  h2: { size: '20px', weight: 700, lineHeight: 1.3 },   // 区块标题
  h3: { size: '18px', weight: 600, lineHeight: 1.35 },  // 卡片标题
  body: { size: '14px', weight: 400, lineHeight: 1.5 }, // 正文
  small: { size: '12px', weight: 400, lineHeight: 1.4 },// 辅助文本
  mono: { family: 'Monaco, monospace', size: '13px' },  // 代码/数值
};
```

### 2.3 间距系统

```typescript
// 基于 8px 网格系统
const spacing = {
  xs: '4px',   // 紧凑元素间距
  s: '8px',    // 行内元素间距
  m: '16px',   // 段落/卡片内间距
  l: '24px',   // 区块间距
  xl: '32px',  // 页面区域间距
  xxl: '48px', // 主要分区间距
};
```

### 2.4 阴影与层级

```css
/* 卡片/容器 */
--shadow-card: 0 1px 2px rgba(0,28,36,0.15);

/* 悬停状态 */
--shadow-hover: 0 2px 8px rgba(0,28,36,0.15);

/* 模态框/弹出层 */
--shadow-modal: 0 4px 20px rgba(0,28,36,0.25);

/* 层级规范 */
z-index-dropdown: 100;
z-index-modal: 200;
z-index-notification: 300;
z-index-tooltip: 400;
```

---

## 三、导航与布局规范

### 3.1 全局导航结构

```
┌─────────────────────────────────────────────────────────────┐
│ TopNavigation                                                │
│ ┌──────────┬──────────────────────────────┬────────────────┐│
│ │ AI 训练平台 │ [面包屑路径]                 │ 🌙 🔔 👤 用户名││
│ └──────────┴──────────────────────────────┴────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌───────────────────────────────────────────────┤
│ │SideNav  │ │ 内容区域                                      │
│ │         │ │                                               │
│ │ 📊 首页  │ │  ┌─────────────────────────────────────────┐ │
│ │         │ │  │ Header + 操作按钮                        │ │
│ │ 🎯 训练  │ │  ├─────────────────────────────────────────┤ │
│ │  └任务   │ │  │                                         │ │
│ │  └模型   │ │  │ 主内容区                                │ │
│ │         │ │  │                                         │ │
│ │ 📁 数据  │ │  └─────────────────────────────────────────┘ │
│ │  └数据集 │ │                                               │
│ │         │ │                                               │
│ │ 💻 资源  │ │                                               │
│ │  └配额   │ │                                               │
│ │  └监控   │ │                                               │
│ │         │ │                                               │
│ │ 🔧 开发  │ │                                               │
│ │  └Spaces│ │                                               │
│ └─────────┘ └───────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

### 3.2 导航设计规范

#### 侧边栏规范

```typescript
interface NavItem {
  type: 'link' | 'section' | 'divider';
  text: string;
  href?: string;
  icon?: IconName;  // 一级菜单必须有图标
  badge?: { text: string; color: 'blue' | 'red' | 'grey'; };
  items?: NavItem[];
}

// 规范要求
// - 一级菜单数量: ≤7 个
// - 二级菜单数量: 每组 ≤5 个
// - 菜单文本: ≤8 个汉字
// - 图标风格: 使用 Cloudscape Icon 组件
```

#### 面包屑规范

```
层级结构: 首页 > 一级菜单 > 二级菜单 > 当前页面
示例: 首页 > 训练管理 > 训练任务 > 任务详情

规范:
- 最大层级: 4 层
- 当前页面不可点击
- 超过 4 层使用省略
```

### 3.3 页面布局模板

#### 列表页布局

```tsx
<Container>
  <Header
    variant="h1"
    actions={<ButtonGroup />}
    description="页面描述"
  >
    页面标题
  </Header>

  <SpaceBetween size="l">
    {/* 筛选区 */}
    <Grid gridDefinition={[{colspan: 3}, {colspan: 3}, {colspan: 3}, {colspan: 3}]}>
      <FormField label="状态"><Select /></FormField>
    </Grid>

    {/* 表格区 */}
    <Table
      columnDefinitions={columns}
      items={items}
      pagination={<Pagination />}
      preferences={<CollectionPreferences />}
    />
  </SpaceBetween>
</Container>
```

#### 详情页布局

```tsx
<SpaceBetween size="l">
  {/* 概览卡片 */}
  <Container header={<Header variant="h2" actions={<ActionButtons />}>任务概览</Header>}>
    <ColumnLayout columns={4} variant="text-grid">
      <KeyValuePairs items={overviewItems} />
    </ColumnLayout>
  </Container>

  {/* Tab 切换区 */}
  <Tabs tabs={[
    { id: "metrics", label: "训练指标", content: <MetricsPanel /> },
    { id: "logs", label: "日志", content: <LogsPanel /> },
    { id: "config", label: "配置详情", content: <ConfigPanel /> },
  ]} />
</SpaceBetween>
```

#### 表单页布局

```tsx
<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link">取消</Button>
      <Button variant="primary">提交</Button>
    </SpaceBetween>
  }
>
  <SpaceBetween size="l">
    <Container header={<Header variant="h2">基础配置</Header>}>
      <SpaceBetween size="m">
        <FormField label="任务名称" constraintText="必填，3-64 个字符">
          <Input />
        </FormField>
      </SpaceBetween>
    </Container>

    <ExpandableSection headerText="高级配置">
      {/* 高级选项 */}
    </ExpandableSection>
  </SpaceBetween>
</Form>
```

---

## 四、交互设计规范

### 4.1 反馈机制

#### 操作反馈时效

| 操作类型 | 反馈时效 | 反馈方式 |
|---------|---------|---------|
| 点击按钮 | 即时 | Loading 状态 |
| 表单提交 | ≤100ms | Spinner + 禁用按钮 |
| API 请求 | ≤3s | 进度指示器 |
| 长时操作 | 实时更新 | 进度条 + 预估时间 |
| 后台任务 | 完成通知 | Toast + 通知中心 |

#### 反馈组件选择

```tsx
// 成功反馈
<Flashbar items={[{ type: "success", content: "训练任务创建成功" }]} />

// 错误反馈
<Flashbar items={[{
  type: "error",
  content: "任务创建失败",
  action: <Button>重试</Button>
}]} />

// 加载状态
<Spinner size="large" />
<StatusIndicator type="loading">正在提交...</StatusIndicator>

// 进度反馈
<ProgressBar value={progress} label="上传进度" description={`${progress}%`} />
```

### 4.2 确认与撤销

#### 危险操作确认规范

```tsx
// 需要二次确认的操作
const dangerousActions = [
  '删除训练任务',
  '停止运行中的任务',
  '删除数据集',
  '清空检查点',
  '重置配额',
];

// 确认弹窗设计
<Modal
  header="确认删除"
  footer={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link">取消</Button>
      <Button variant="primary" loading={loading}>确认删除</Button>
    </SpaceBetween>
  }
>
  <Alert type="warning">
    此操作不可撤销。删除后，相关检查点和日志也将被清除。
  </Alert>
  <SpaceBetween size="s">
    <Box>将要删除: <strong>{jobName}</strong></Box>
    <FormField label="请输入任务名称以确认">
      <Input value={confirmInput} onChange={setConfirmInput} />
    </FormField>
  </SpaceBetween>
</Modal>
```

### 4.3 表单交互规范

#### 实时验证

```tsx
// 验证时机
// - blur: 失去焦点时验证
// - change: 已出错字段实时验证
// - submit: 提交前全量验证

<FormField
  label="任务名称"
  errorText={errors.name}
  constraintText="3-64 个字符，支持字母、数字、中划线"
>
  <Input invalid={!!errors.name} />
</FormField>
```

#### 智能表单设计

```tsx
// 条件字段显示
{framework === 'pytorch' && (
  <FormField label="分布式策略">
    <Select
      options={[
        { value: 'ddp', label: 'DDP (推荐)' },
        { value: 'fsdp', label: 'FSDP (大模型)' },
        { value: 'deepspeed', label: 'DeepSpeed ZeRO' },
      ]}
      placeholder="选择分布式策略"
    />
  </FormField>
)}

// 配置预估
<Alert type="info">
  预估资源消耗: 8 x A100 GPU, 约 ¥2,400/小时
  基于历史数据，预计训练时长: 4-6 小时
</Alert>
```

### 4.4 列表与表格交互

#### 表格功能规范

```tsx
<Table
  // 排序
  sortingColumn={sortColumn}
  sortingDescending={sortDesc}
  onSortingChange={handleSort}

  // 分页
  pagination={
    <Pagination
      currentPageIndex={page}
      pagesCount={totalPages}
      onChange={({ detail }) => setPage(detail.currentPageIndex)}
    />
  }

  // 列偏好设置
  preferences={
    <CollectionPreferences
      visibleContentPreference={{ options: columnOptions }}
      pageSizePreference={{ options: [10, 20, 50, 100] }}
    />
  }

  // 批量选择
  selectionType="multi"
  selectedItems={selectedItems}
  onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}

  // 空状态
  empty={
    <Box textAlign="center" color="inherit">
      <b>暂无训练任务</b>
      <Box padding={{ bottom: 's' }} variant="p">
        创建您的第一个训练任务开始使用平台
      </Box>
      <Button>创建任务</Button>
    </Box>
  }
/>
```

#### 筛选与搜索

```tsx
// 搜索框
<TextFilter
  filteringPlaceholder="搜索任务名称..."
  filteringText={filterText}
  onChange={({ detail }) => setFilterText(detail.filteringText)}
/>

// 属性筛选（高级）
<PropertyFilter
  query={query}
  onChange={({ detail }) => setQuery(detail)}
  filteringProperties={[
    { key: 'status', propertyLabel: '状态', operators: ['='] },
    { key: 'framework', propertyLabel: '框架', operators: ['='] },
    { key: 'createdAt', propertyLabel: '创建时间', operators: ['>', '<', '='] },
  ]}
/>
```

---

## 五、组件使用规范

### 5.1 Cloudscape 组件选择指南

| 场景 | 推荐组件 | 备选组件 |
|------|---------|---------|
| 主操作按钮 | `<Button variant="primary">` | - |
| 次要操作 | `<Button>` | `<Button variant="link">` |
| 危险操作 | `<Button variant="primary">` + 确认弹窗 | - |
| 状态展示 | `<StatusIndicator>` | `<Badge>` |
| 数据表格 | `<Table>` | `<Cards>` |
| 详情展示 | `<KeyValuePairs>` | `<ColumnLayout>` |
| 表单容器 | `<Form>` + `<Container>` | - |
| 分步流程 | `<Wizard>` | `<Steps>` |
| 选项卡 | `<Tabs>` | - |
| 通知消息 | `<Flashbar>` | - |
| 确认弹窗 | `<Modal>` | - |
| 侧边抽屉 | `<Drawer>` | `<SplitPanel>` |

### 5.2 禁止使用的模式

```tsx
// ❌ 禁止：自定义样式覆盖 Cloudscape
<Button style={{ backgroundColor: 'red' }}>危险</Button>

// ✅ 正确：使用语义化变体
<Button variant="primary">确认删除</Button>

// ❌ 禁止：内联 CSS
<div style={{ marginTop: 20 }}>...</div>

// ✅ 正确：使用 SpaceBetween
<SpaceBetween size="m">...</SpaceBetween>

// ❌ 禁止：原生 HTML 表单元素
<input type="text" />

// ✅ 正确：Cloudscape 表单组件
<Input value={value} onChange={handleChange} />

// ❌ 禁止：第三方图表库
import { LineChart } from 'recharts';

// ✅ 正确：使用 Cloudscape Charts
import { LineChart } from '@cloudscape-design/components';
```

### 5.3 图标使用规范

```tsx
import { Icon } from '@cloudscape-design/components';

// 导航图标
<Icon name="menu" />           // 菜单
<Icon name="search" />         // 搜索
<Icon name="notification" />   // 通知
<Icon name="settings" />       // 设置

// 操作图标
<Icon name="add-plus" />       // 创建
<Icon name="edit" />           // 编辑
<Icon name="remove" />         // 删除
<Icon name="refresh" />        // 刷新
<Icon name="download" />       // 下载
<Icon name="upload" />         // 上传

// 状态图标
<Icon name="status-positive" />    // 成功
<Icon name="status-warning" />     // 警告
<Icon name="status-negative" />    // 错误
<Icon name="status-pending" />     // 等待
<Icon name="status-in-progress" /> // 进行中
```

---

## 六、特定页面设计指南

### 6.1 首页（仪表板）

**设计目标**：一眼掌握平台状态，快速进入常用功能

```
┌─────────────────────────────────────────────────────────────┐
│ 欢迎回来，{用户名}                             [快速创建 ▼]  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 运行中任务    │ │ 等待中任务    │ │ GPU 利用率   │         │
│  │     12      │ │      5       │ │    78%      │         │
│  │   ↑3 vs 昨日 │ │   ↓2 vs 昨日 │ │   ↑5%       │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 最近任务                               [查看全部 →]   │   │
│  │  任务名称          状态      进度    操作            │   │
│  │  llama-finetune   🟢运行中   45%    [查看] [停止]   │   │
│  │  gpt-pretrain    🟡等待中    -     [查看] [取消]   │   │
│  │  bert-training   🟢已完成   100%   [查看] [下载]   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────┐ ┌────────────────────────┐      │
│  │ 资源配额               │ │ 本月成本               │      │
│  │ GPU: ████████░░ 80%   │ │ ¥45,230 / ¥60,000     │      │
│  │ 内存: █████░░░░░ 50%   │ │ ████████░░ 75%        │      │
│  │ 存储: ██████░░░░ 60%   │ │ 预计月底: ¥58,000     │      │
│  └────────────────────────┘ └────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 训练任务列表页

**设计目标**：高效管理大量任务，快速定位目标任务

**关键功能点**：

1. **状态快速筛选**（Tab 形式）
   - 全部 | 运行中(12) | 等待中(5) | 已完成(234) | 失败(3)

2. **批量操作工具栏**
   - 选中 3 个任务 | [批量停止] [批量删除] [导出配置]

3. **任务卡片/行信息**
   - 任务名称（可点击进入详情）
   - 状态徽章（带颜色编码）
   - 进度条（运行中任务）
   - 资源消耗（GPU数 × 节点数）
   - 运行时长/预计完成时间
   - 快捷操作（查看/停止/克隆）

4. **实时更新指示器**
   - 30 秒自动刷新
   - 手动刷新按钮
   - 最后更新时间显示

### 6.3 训练任务详情页

**设计目标**：全方位监控任务状态，快速定位问题

```
┌─────────────────────────────────────────────────────────────┐
│ ← 返回列表   llama-7b-finetune                              │
│                                           [停止] [克隆] ⋮  │
├─────────────────────────────────────────────────────────────┤
│  状态: 🟢 运行中    已运行: 2h 34m    预计剩余: 1h 20m      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 训练进度                                             │    │
│  │ ████████████████████░░░░░░░░░░ 65% (Epoch 13/20)   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  [ 指标 ] [ 日志 ] [ 检查点 ] [ 配置 ] [ 事件 ]             │
│  ═══════════════════════════════════════════════════════    │
│                                                              │
│  ┌────────────────────────────┐ ┌────────────────────────┐  │
│  │ Loss                       │ │ Learning Rate          │  │
│  │        ╲                   │ │ ─────╲                 │  │
│  │         ╲__                │ │       ╲____           │  │
│  │            ╲___            │ │            ╲___       │  │
│  │ 当前: 0.234    趋势: ↓     │ │ 当前: 1e-5            │  │
│  └────────────────────────────┘ └────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────┐ ┌────────────────────────┐  │
│  │ GPU 利用率                 │ │ 显存使用               │  │
│  │ ████████████████░░░░ 78%  │ │ ██████████████░░ 85%   │  │
│  │ 节点 1: 82%  节点 2: 74%  │ │ 68GB / 80GB            │  │
│  └────────────────────────────┘ └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 创建训练任务（向导）

**设计目标**：引导式配置，降低出错概率

```tsx
// 使用 Cloudscape Wizard 组件
const steps = [
  { title: '基础配置', description: '设置任务名称和框架', content: <BasicConfigStep /> },
  { title: '资源配置', description: '配置 GPU 和节点数量', content: <ResourceConfigStep /> },
  { title: '数据配置', description: '选择训练数据集', content: <DataConfigStep /> },
  { title: '训练参数', description: '设置超参数', content: <HyperparamsStep /> },
  { title: '确认提交', description: '检查配置并提交', content: <ReviewStep /> },
];

// 每一步都有：
// - 明确的必填/可选标记
// - 智能默认值（基于历史或最佳实践）
// - 配置预估（成本、时长）
// - 验证反馈
```

### 6.5 监控仪表板

**设计目标**：实时掌握集群健康状态

```
关键指标 KPI 区域（顶部）
├─ 集群利用率: 78%
├─ 活跃任务: 23
├─ 排队任务: 8
└─ 故障节点: 0

实时图表区域（中部）
├─ GPU 使用率趋势（折线图）
├─ 任务队列深度（面积图）
├─ 节点健康状态（热力图）
└─ 成本消耗趋势（柱状图）

节点详情区域（下部）
├─ 节点列表表格
├─ 状态筛选
└─ 快速操作（重启/维护模式）
```

---

## 七、响应式设计规范

### 7.1 断点定义

```typescript
const breakpoints = {
  xs: 0,      // 手机 (不主要支持)
  s: 576,     // 平板竖屏
  m: 768,     // 平板横屏
  l: 992,     // 小型桌面
  xl: 1200,   // 标准桌面
  xxl: 1400,  // 大型显示器
};

// 主要支持：l (992px) 及以上
// 最佳体验：xl (1200px) 及以上
```

### 7.2 布局适配规则

```tsx
// 表格列适配
<Table columnDefinitions={[
  { id: 'name', header: '名称', minWidth: 150 },
  { id: 'status', header: '状态', minWidth: 100 },
  { id: 'progress', header: '进度', minWidth: 120 },
  { id: 'createdAt', header: '创建时间', minWidth: 150 },  // 小屏可隐藏
  { id: 'actions', header: '操作', minWidth: 100 },
]} />

// 栅格适配
<Grid gridDefinition={[
  { colspan: { default: 12, l: 6, xl: 3 } },  // 4列 → 2列 → 1列
  { colspan: { default: 12, l: 6, xl: 3 } },
  { colspan: { default: 12, l: 6, xl: 3 } },
  { colspan: { default: 12, l: 6, xl: 3 } },
]}>
```

---

## 八、无障碍设计规范（WCAG 2.1 AA）

### 8.1 基本要求

```
颜色对比度:
- 正文文字: ≥ 4.5:1
- 大文字(≥18px): ≥ 3:1
- 图形/图标: ≥ 3:1

焦点指示:
- 所有可交互元素有可见焦点状态
- Tab 顺序符合逻辑流
```

```tsx
// ARIA 标签
<Button aria-label="创建新的训练任务">
  <Icon name="add-plus" />
</Button>

<Table aria-label="训练任务列表" />

// 表单关联
<FormField
  label="任务名称"
  description="用于标识训练任务的唯一名称"
  errorText={errors.name}
>
  <Input id="job-name" />
</FormField>
```

### 8.2 键盘导航

```
快捷键支持:
Ctrl/Cmd + K: 全局搜索
Ctrl/Cmd + N: 创建新任务
Esc: 关闭弹窗/取消操作
Enter: 确认操作
Tab: 下一个元素
Shift + Tab: 上一个元素
```

---

## 九、性能优化规范

### 9.1 加载性能

```tsx
// 骨架屏加载
<Table loading={isLoading} loadingText="正在加载训练任务..." />

// 分页加载
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['trainingJobs'],
  queryFn: fetchJobs,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
});

// 虚拟滚动（大数据量）
// 当列表项 > 100 时启用
```

### 9.2 实时更新策略

```tsx
// 任务状态轮询
const { data } = useQuery({
  queryKey: ['trainingJob', jobId],
  queryFn: () => fetchJob(jobId),
  refetchInterval: (data) => {
    if (data?.status === 'running') return 10000;   // 运行中: 10秒刷新
    if (data?.status === 'pending') return 30000;   // 等待中: 30秒刷新
    return false;                                    // 已完成: 不自动刷新
  },
});

// WebSocket 实时日志
useEffect(() => {
  const ws = new WebSocket(`/ws/jobs/${jobId}/logs`);
  ws.onmessage = (event) => appendLog(JSON.parse(event.data));
  return () => ws.close();
}, [jobId]);
```

### 9.3 缓存策略

```tsx
// React Query 缓存配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,       // 30秒内数据视为新鲜
      cacheTime: 5 * 60 * 1000,   // 5分钟缓存
      refetchOnWindowFocus: true,
      retry: 3,
    },
  },
});

// 乐观更新
const mutation = useMutation({
  mutationFn: updateJob,
  onMutate: async (newData) => {
    await queryClient.cancelQueries(['trainingJob', jobId]);
    const previous = queryClient.getQueryData(['trainingJob', jobId]);
    queryClient.setQueryData(['trainingJob', jobId], newData);
    return { previous };
  },
  onError: (err, newData, context) => {
    queryClient.setQueryData(['trainingJob', jobId], context.previous);
  },
});
```

---

## 十、差异化竞争力设计

### 10.1 智能化体验（超越竞品）

#### 智能配置推荐

```tsx
<Alert type="info">
  <Icon name="suggestions" /> 基于您团队的历史任务，推荐以下配置：
  - GPU: 8 × A100 (成功率 95%)
  - 批量大小: 32 (最优效率)
  - 学习率: 1e-4 (收敛最快)
  <Button variant="link">应用推荐配置</Button>
</Alert>

// 智能预警
<Alert type="warning">
  <Icon name="status-warning" /> 检测到潜在问题：
  - 当前配置可能导致 OOM，建议减小批量大小或增加节点
  - 预计训练时长 12 小时，超出您的配额剩余时间
</Alert>
```

#### 智能搜索

```tsx
// 自然语言搜索
<TextFilter filteringPlaceholder="搜索：精度大于95%的已完成任务" />

// 支持查询示例:
// - "昨天创建的失败任务"
// - "GPU利用率低于50%的运行中任务"
// - "llama 相关的所有任务"
```

### 10.2 协作体验

```tsx
// 实时协作指示
<Box>
  <Avatar name="张三" /> 张三正在查看此任务
  <Avatar name="李四" /> 李四 2 分钟前查看
</Box>

// 任务评论
<Container header="团队讨论">
  <SpaceBetween size="m">
    {comments.map(comment => (
      <Box key={comment.id}>
        <Avatar name={comment.author} />
        <Box>{comment.content}</Box>
        <Box color="text-status-inactive">{comment.time}</Box>
      </Box>
    ))}
    <Input placeholder="添加评论..." />
  </SpaceBetween>
</Container>

// 任务分享
<Button iconName="share">分享任务链接</Button>
```

### 10.3 个性化体验

```tsx
interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  defaultView: 'table' | 'cards';
  refreshInterval: 10 | 30 | 60;
  notifications: {
    taskComplete: boolean;
    taskFailed: boolean;
    quotaWarning: boolean;
  };
  pinnedJobs: string[];
  recentFilters: FilterConfig[];
}

// 快捷操作自定义
<Popover content={<QuickActionsConfig />}>
  <Button iconName="settings">自定义快捷操作</Button>
</Popover>
```

---

## 十一、国际化（i18n）规范

### 11.1 文本外化

```tsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();

<Header>{t('training.jobs.title')}</Header>
<Button>{t('common.create')}</Button>

// 命名空间:
// - common: 通用文本（按钮、标签）
// - training: 训练相关
// - data: 数据管理
// - resource: 资源管理
// - error: 错误消息
```

### 11.2 日期和数字格式化

```tsx
import { format, formatDistance } from 'date-fns';
import { zhCN } from 'date-fns/locale';

format(date, 'yyyy-MM-dd HH:mm', { locale: zhCN });
formatDistance(date, new Date(), { locale: zhCN, addSuffix: true });
// 输出: "2小时前"

// 数字格式化
new Intl.NumberFormat('zh-CN').format(12345);  // "12,345"
new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(1234.56);  // "¥1,234.56"

// 文件大小
function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let index = 0;
  while (bytes >= 1024 && index < units.length - 1) {
    bytes /= 1024;
    index++;
  }
  return `${bytes.toFixed(1)} ${units[index]}`;
}
```

---

## 十二、错误处理规范

### 12.1 错误分类与展示

```tsx
type ErrorType = 'validation' | 'network' | 'permission' | 'resource' | 'server' | 'unknown';

const errorDisplay: Record<ErrorType, DisplayStrategy> = {
  validation: 'inline',    // 表单字段内联显示
  network: 'flashbar',     // 顶部通知条
  permission: 'modal',     // 弹窗提示
  resource: 'flashbar',    // 顶部通知条
  server: 'page',          // 错误页面
  unknown: 'flashbar',     // 顶部通知条
};

const errorMessages = {
  'QUOTA_EXCEEDED': '资源配额不足，请联系管理员扩容或等待其他任务完成',
  'INVALID_CONFIG': '配置参数无效，请检查输入',
  'NETWORK_ERROR': '网络连接失败，请检查网络后重试',
  'PERMISSION_DENIED': '您没有权限执行此操作',
};
```

### 12.2 空状态设计

```tsx
// 列表空状态
<Table
  empty={
    <Box textAlign="center" color="inherit" padding="l">
      <Icon name="search" size="large" variant="disabled" />
      <Box variant="h3" padding={{ top: 's' }}>暂无训练任务</Box>
      <Box variant="p" color="text-body-secondary">
        创建您的第一个训练任务，开始 AI 模型训练之旅
      </Box>
      <Button variant="primary" iconName="add-plus">创建训练任务</Button>
    </Box>
  }
/>

// 搜索无结果
<Box textAlign="center" padding="l">
  <Icon name="search" size="large" variant="disabled" />
  <Box variant="h3">未找到匹配结果</Box>
  <Box variant="p">尝试调整搜索条件或 <Link>清除筛选</Link></Box>
</Box>
```

---

## 十三、暗色模式规范

### 13.1 主题切换机制

```tsx
import { applyMode, Mode } from '@cloudscape-design/global-styles';

interface ThemeStore {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  effectiveTheme: 'light' | 'dark';
}

// 主题切换
useEffect(() => {
  const mode = theme === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? Mode.Dark : Mode.Light)
    : (theme === 'dark' ? Mode.Dark : Mode.Light);
  applyMode(mode);
}, [theme]);

// 监听系统主题变化
useEffect(() => {
  if (theme !== 'system') return;
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handler = (e: MediaQueryListEvent) => applyMode(e.matches ? Mode.Dark : Mode.Light);
  mediaQuery.addEventListener('change', handler);
  return () => mediaQuery.removeEventListener('change', handler);
}, [theme]);
```

### 13.2 暗色模式色彩系统

#### 基础色彩映射

| 色彩变量 | 亮色模式 | 暗色模式 | 用途 |
|---------|---------|---------|------|
| `--background-primary` | `#ffffff` | `#0f1b2a` | 主背景 |
| `--background-secondary` | `#fafafa` | `#1a2638` | 次级背景/卡片 |
| `--background-tertiary` | `#f2f3f3` | `#243447` | 输入框/表格行 |
| `--text-primary` | `#000716` | `#d1d5db` | 主文本 |
| `--text-secondary` | `#5f6b7a` | `#8d9bae` | 次级文本 |
| `--border-default` | `#e9ebed` | `#354354` | 边框 |

#### 状态色彩适配

| 状态 | 亮色模式 | 暗色模式 | 场景 |
|------|---------|---------|------|
| **主色** | `#0972d3` | `#539fe5` | 主操作、链接 |
| **成功** | `#037f0c` | `#5aae68` | 成功状态 |
| **警告** | `#8d6605` | `#d4a932` | 警告状态 |
| **错误** | `#d91515` | `#ff7a7a` | 错误状态 |

### 13.3 组件暗色适配

```tsx
// ❌ 避免：硬编码背景色
<Container style={{ backgroundColor: '#ffffff' }}>

// ✅ 正确：使用 Cloudscape 自动处理
<Container variant="default">  // 自动适配主题
```

### 13.4 主题切换 UI 设计

```tsx
// 顶部导航快速切换
<TopNavigation
  utilities={[
    {
      type: 'button',
      iconName: theme === 'dark' ? 'status-positive' : 'status-negative',
      ariaLabel: '切换主题',
      onClick: () => toggleTheme(),
    },
  ]}
/>

// 设置页面完整选项
<FormField label="外观主题">
  <Tiles
    value={theme}
    onChange={({ detail }) => setTheme(detail.value)}
    items={[
      { value: 'light', label: '亮色模式', description: '经典亮色界面' },
      { value: 'dark', label: '暗色模式', description: '护眼深色界面' },
      { value: 'system', label: '跟随系统', description: '自动匹配系统主题设置' },
    ]}
  />
</FormField>
```

### 13.5 暗色模式设计原则

```
文本对比度（WCAG AA）:
- 正文文本: ≥ 4.5:1
- 大标题(≥18px): ≥ 3:1
- 图标: ≥ 3:1

暗色模式特别注意:
- 避免纯黑背景(#000000)，使用深灰蓝(#0f1b2a)
- 避免纯白文字(#ffffff)，使用浅灰(#d1d5db)
- 减少高饱和度色彩，避免视觉疲劳
```

---

## 附录：实施检查清单

### A. 每个页面必须包含

- [ ] 页面标题（Header 组件）
- [ ] 面包屑导航
- [ ] 主操作按钮（右上角）
- [ ] 加载状态处理
- [ ] 空状态设计
- [ ] 错误状态处理
- [ ] 响应式适配测试

### B. 每个表单必须包含

- [ ] 字段标签和提示
- [ ] 必填标记
- [ ] 实时验证
- [ ] 错误消息
- [ ] 提交确认
- [ ] 取消操作

### C. 每个表格必须包含

- [ ] 排序功能
- [ ] 分页功能
- [ ] 列偏好设置
- [ ] 空状态
- [ ] 加载状态
- [ ] 行操作

### D. 代码质量检查

- [ ] TypeScript 严格模式通过
- [ ] ESLint 无警告
- [ ] 无自定义 CSS
- [ ] 使用 Cloudscape 组件
- [ ] 国际化文本外化
- [ ] 无障碍标签完整

### E. 暗色模式检查

- [ ] 所有页面在暗色模式下无显示异常
- [ ] 状态色彩清晰可辨
- [ ] 图表和数据可视化易于阅读
- [ ] 主题切换过渡平滑无闪烁
