# AI 训练平台前端设计规范（精简版）

> 本文档是开发者快速参考指南。完整版请查阅：`specs/frontend-design-guide.md`

---

## 一、核心设计原则

| 原则 | 要点 | 实践 |
|------|------|------|
| **效率优先** | 关键操作 ≤3 秒可达 | 首页快速入口、智能默认值、批量操作 |
| **渐进复杂** | 三层用户路径 | 模板→配置→自定义/YAML |
| **一致可信** | 操作可预测、可撤销 | 统一反馈模式、危险操作二次确认 |
| **Cloudscape First** | 禁止自定义样式覆盖 | 仅使用 Cloudscape 组件和变量 |

---

## 二、色彩系统

### 主色调
```css
--primary: #0972d3;        /* 主操作按钮 */
--primary-hover: #065299;
--primary-active: #033160;
```

### 任务状态色彩

| 状态 | 颜色 | Badge | 含义 |
|------|------|-------|------|
| `submitted` | 灰色 | `grey` | 已提交，等待调度 |
| `pending` | 蓝色 | `blue` | 等待资源 |
| `running` | 绿色 | `green` | 正在运行 |
| `paused` | 黄色 | `yellow` | 用户暂停 |
| `preempted` | 橙色 | `orange` | 被抢占 |
| `completed` | 绿色 | `green` | 成功完成 |
| `failed` | 红色 | `red` | 执行失败 |
| `cancelled` | 灰色 | `grey` | 用户取消 |

### 间距系统（基于 8px 网格）
```typescript
xs: '4px'   // 紧凑元素
s:  '8px'   // 行内元素
m:  '16px'  // 段落/卡片内
l:  '24px'  // 区块间距
xl: '32px'  // 页面区域
```

---

## 三、组件选择指南

| 场景 | 推荐组件 | 备选 |
|------|---------|------|
| 主操作 | `<Button variant="primary">` | - |
| 次要操作 | `<Button>` | `<Button variant="link">` |
| 状态展示 | `<StatusIndicator>` | `<Badge>` |
| 数据表格 | `<Table>` | `<Cards>` |
| 详情展示 | `<KeyValuePairs>` | `<ColumnLayout>` |
| 表单容器 | `<Form>` + `<Container>` | - |
| 分步流程 | `<Wizard>` | - |
| 通知消息 | `<Flashbar>` | - |
| 确认弹窗 | `<Modal>` | - |
| 侧边详情 | `<SplitPanel>` | `<Drawer>` |

---

## 四、状态反馈规范

### 操作反馈时效

| 操作类型 | 时效要求 | 反馈方式 |
|---------|---------|---------|
| 按钮点击 | 即时 | Loading 状态 |
| 表单提交 | ≤100ms | Spinner + 禁用按钮 |
| API 请求 | ≤3s | 进度指示器 |
| 后台任务 | 完成通知 | Toast + 通知中心 |

### 反馈组件示例
```tsx
// 成功
<Flashbar items={[{ type: "success", content: "任务创建成功" }]} />

// 错误（带重试）
<Flashbar items={[{
  type: "error",
  content: "创建失败",
  action: <Button>重试</Button>
}]} />

// 加载状态
<StatusIndicator type="loading">正在提交...</StatusIndicator>
```

---

## 五、页面模板

### 5.1 列表页
```tsx
<Container>
  <Header variant="h1" actions={<Button variant="primary">创建</Button>}>
    训练任务
  </Header>
  <SpaceBetween size="l">
    {/* 筛选区 */}
    <PropertyFilter {...filterProps} />

    {/* 表格区 */}
    <Table
      columnDefinitions={columns}
      items={items}
      loading={isLoading}
      pagination={<Pagination {...paginationProps} />}
      preferences={<CollectionPreferences {...preferencesProps} />}
      selectionType="multi"
      empty={<EmptyState onCreate={handleCreate} />}
    />
  </SpaceBetween>
</Container>
```

### 5.2 详情页
```tsx
<SpaceBetween size="l">
  {/* 概览卡片 */}
  <Container header={<Header variant="h2" actions={<ActionButtons />}>概览</Header>}>
    <ColumnLayout columns={4} variant="text-grid">
      <KeyValuePairs items={overviewItems} />
    </ColumnLayout>
  </Container>

  {/* Tab 切换 */}
  <Tabs tabs={[
    { id: "metrics", label: "训练指标", content: <MetricsPanel /> },
    { id: "logs", label: "日志", content: <LogsPanel /> },
    { id: "config", label: "配置", content: <ConfigPanel /> },
  ]} />
</SpaceBetween>
```

### 5.3 表单页
```tsx
<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link">取消</Button>
      <Button variant="primary" loading={submitting}>提交</Button>
    </SpaceBetween>
  }
>
  <Container header={<Header variant="h2">基础配置</Header>}>
    <SpaceBetween size="m">
      <FormField
        label="任务名称"
        constraintText="3-64 个字符"
        errorText={errors.name}
      >
        <Input value={name} onChange={e => setName(e.detail.value)} />
      </FormField>
    </SpaceBetween>
  </Container>

  <ExpandableSection headerText="高级配置">
    {/* 高级选项 */}
  </ExpandableSection>
</Form>
```

### 5.4 表格配置
```tsx
const columnDefinitions = [
  {
    id: 'name',
    header: '任务名称',
    cell: (item) => <Link href={`/jobs/${item.id}`}>{item.name}</Link>,
    sortingField: 'name',
    minWidth: 150,
  },
  {
    id: 'status',
    header: '状态',
    cell: (item) => <StatusIndicator type={statusMap[item.status]}>{item.status}</StatusIndicator>,
    sortingField: 'status',
    minWidth: 100,
  },
  {
    id: 'actions',
    header: '操作',
    cell: (item) => (
      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="link">查看</Button>
        <Button variant="link">停止</Button>
      </SpaceBetween>
    ),
    minWidth: 120,
  },
];
```

---

## 六、禁止事项

```tsx
// ❌ 禁止：自定义样式覆盖
<Button style={{ backgroundColor: 'red' }}>危险</Button>

// ❌ 禁止：内联 CSS
<div style={{ marginTop: 20 }}>...</div>

// ❌ 禁止：原生 HTML 元素
<input type="text" />

// ❌ 禁止：第三方图表库
import { LineChart } from 'recharts';

// ❌ 禁止：硬编码颜色
<Container style={{ backgroundColor: '#ffffff' }}>
```

**正确做法：**
```tsx
// ✅ 使用 Cloudscape 组件
<Button variant="primary">确认</Button>
<SpaceBetween size="m">...</SpaceBetween>
<Input value={value} onChange={handleChange} />
<LineChart series={[...]} />  // from @cloudscape-design/components
<Container variant="default">  // 自动适配主题
```

---

## 七、危险操作确认

需要二次确认的操作：
- 删除训练任务
- 停止运行中的任务
- 删除数据集
- 清空检查点
- 重置配额

```tsx
<Modal
  header="确认删除"
  footer={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link">取消</Button>
      <Button variant="primary" disabled={confirmInput !== jobName}>
        确认删除
      </Button>
    </SpaceBetween>
  }
>
  <Alert type="warning">此操作不可撤销</Alert>
  <FormField label="请输入任务名称以确认">
    <Input value={confirmInput} onChange={e => setConfirmInput(e.detail.value)} />
  </FormField>
</Modal>
```

---

## 八、暗色模式

```tsx
import { applyMode, Mode } from '@cloudscape-design/global-styles';

// 主题切换
const setTheme = (theme: 'light' | 'dark' | 'system') => {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyMode(isDark ? Mode.Dark : Mode.Light);
  } else {
    applyMode(theme === 'dark' ? Mode.Dark : Mode.Light);
  }
};

// 默认使用 Cloudscape 组件，自动适配暗色模式
// 不要硬编码背景色或文字色
```

---

## 九、提交前检查清单

### 页面必备
- [ ] 页面标题（Header 组件）
- [ ] 面包屑导航
- [ ] 主操作按钮（右上角）
- [ ] 加载状态处理
- [ ] 空状态设计
- [ ] 错误状态处理

### 表单必备
- [ ] 字段标签和提示
- [ ] 必填标记
- [ ] 实时验证
- [ ] 错误消息
- [ ] 提交确认

### 表格必备
- [ ] 排序功能
- [ ] 分页功能
- [ ] 列偏好设置
- [ ] 空状态
- [ ] 加载状态
- [ ] 行操作

### 代码质量
- [ ] TypeScript 严格模式通过
- [ ] ESLint 无警告
- [ ] 无自定义 CSS
- [ ] 全部使用 Cloudscape 组件
- [ ] 暗色模式下无显示异常

---

## 十、常用 Import

```tsx
// 核心组件
import {
  AppLayout,
  BreadcrumbGroup,
  Button,
  Container,
  Header,
  SpaceBetween,
  Table,
  Tabs,
} from '@cloudscape-design/components';

// 表单组件
import {
  Form,
  FormField,
  Input,
  Select,
  Checkbox,
  RadioGroup,
  DatePicker,
} from '@cloudscape-design/components';

// 反馈组件
import {
  Alert,
  Flashbar,
  Modal,
  StatusIndicator,
  Spinner,
  ProgressBar,
} from '@cloudscape-design/components';

// 数据展示
import {
  Cards,
  KeyValuePairs,
  ColumnLayout,
  Grid,
  LineChart,
  PieChart,
} from '@cloudscape-design/components';

// 导航组件
import {
  SideNavigation,
  TopNavigation,
  Link,
  Pagination,
} from '@cloudscape-design/components';

// 主题
import { applyMode, Mode } from '@cloudscape-design/global-styles';
```

---

> **完整版文档**: `specs/frontend-design-guide.md`
>
> 包含：详细视觉规范、页面设计指南、性能优化、无障碍设计、国际化、差异化竞争力设计等。
