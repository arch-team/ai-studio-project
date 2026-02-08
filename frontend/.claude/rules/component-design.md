> **职责**: 组件设计规范 - Cloudscape 组件使用、组件类型、Props 设计、交互模式

# 组件设计规范 (Component Design Standards)

---

## 0. 速查卡片

### 组件类型速查

| 类型 | 职责 | 示例 | 位置 |
|------|------|------|------|
| **展示型** | 纯 UI 渲染，无状态 | Cloudscape `Table`, `StatusIndicator` | `shared/components/` |
| **容器型** | 业务逻辑，数据获取 | `TrainingJobList`, `DatasetForm` | `features/*/components/` |
| **页面型** | 组装容器+展示组件 | `TrainingListPage` | `features/*/pages/` |

### 组件决策流程

```
需要创建组件?
    ↓
包含业务逻辑? ──是──► features/{module}/components/
    │
   否
    ↓
是复用基础组件? ──是──► shared/components/
    │
   否
    ↓
是布局组件? ──是──► layouts/
```

### Props 设计速查

> Props 类型定义 (interface vs type) 和事件命名规则 (on/handle 前缀) 详见 [code-style.md](code-style.md) §0 和 §1

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| children 类型 | `children: React.ReactNode` | `children: any` |
| 可选属性 | `disabled?: boolean` | `disabled: boolean \| undefined` |
| 默认值 | 解构默认值 | Props 中定义默认 |

### 陷阱 ⚠️

- ❌ 自定义 CSS / 内联样式 → ✅ 使用 Cloudscape 组件
- ❌ 原生 HTML 表单控件 → ✅ Cloudscape `<Input>`, `<Select>` 等
- ❌ 第三方图表库 → ✅ Cloudscape 内置图表组件

---

## 1. 组件类型

### 1.1 展示型组件 (Presentational)

**关键模式**: Cloudscape 组件优先 + `Record<Status, Config>` 映射

```tsx
// 状态映射模式: Record<JobStatus, { type, label }> → <StatusIndicator type={type}>{label}</StatusIndicator>
const statusMap: Record<JobStatus, { type: string; label: string }> = {
  submitted: { type: 'pending', label: '已提交' },
  // ...其他状态
};
```

### 1.2 容器型组件 (Container)

**关键模式**: React Query 数据获取 + Cloudscape Table 三态处理

```tsx
// 必须处理 loading / items / empty 三个状态
<Table
  loading={isLoading}
  items={data?.items ?? []}
  header={<Header counter={`(${data?.total ?? 0})`}>标题</Header>}
  empty={<Box textAlign="center">暂无数据</Box>}
  columnDefinitions={[...]}
/>
```

### 1.3 复合组件 (Compound)

**关键模式**: Context 共享状态 + `Object.assign` 组合导出

```
1. createContext<ContextValue | null>(null)
2. Root 组件提供 Context.Provider
3. 子组件通过 useContext 消费状态
4. Object.assign(Root, { SubA, SubB }) 组合导出
```

---

## 2. Cloudscape 组件选择

### 2.1 场景映射表

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

### 2.2 禁止事项

| ❌ 禁止 | ✅ 正确做法 |
|--------|-----------|
| `style={{ backgroundColor: 'red' }}` | `<Button variant="primary">` |
| `<div style={{ marginTop: 20 }}>` | `<SpaceBetween size="m">` |
| `<input type="text" />` | `<Input value={v} onChange={h} />` |
| `import { LineChart } from 'recharts'` | `<LineChart />` (Cloudscape) |
| `style={{ backgroundColor: '#fff' }}` | `<Container variant="default">` |

---

## 3. Props 高级模式

### 3.1 继承原生属性

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div>
      {label && <label>{label}</label>}
      <input {...props} />
      {error && <span>{error}</span>}
    </div>
  );
}
```

> 注意: 使用 Cloudscape 组件时，优先使用 Cloudscape 的 Props 接口而非原生 HTML 属性

### 3.2 泛型组件

```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

export function List<T>({ items, renderItem, keyExtractor, emptyMessage = '暂无数据' }: ListProps<T>) {
  if (!items.length) return <Box textAlign="center">{emptyMessage}</Box>;
  return <ul>{items.map((item, i) => <li key={keyExtractor(item)}>{renderItem(item, i)}</li>)}</ul>;
}
```

---

## 4. 状态反馈与交互

### 4.1 操作反馈时效

| 操作类型 | 时效要求 | 反馈方式 |
|---------|---------|---------|
| 按钮点击 | 即时 | Loading 状态 |
| 表单提交 | ≤100ms | Spinner + 禁用按钮 |
| API 请求 | ≤3s | 进度指示器 |
| 后台任务 | 完成通知 | Flashbar + 通知中心 |

### 4.2 Flashbar 反馈示例

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

### 4.3 危险操作确认 (Modal)

需要二次确认的操作：删除任务、停止运行任务、删除数据集、清空检查点、重置配额

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

## 5. 组件文件结构

### 单组件

```
features/{module}/components/
├── TrainingJobTable.tsx
├── TrainingJobForm.tsx
├── TrainingJobStatusBadge.tsx
└── index.ts           # 统一导出
```

### 复合组件

```
shared/components/Tabs/
├── index.ts              # 导出 Tabs 和子组件
├── Tabs.tsx              # 主组件 + Context
├── TabList.tsx           # 子组件
├── Tab.tsx               # 子组件
├── TabPanel.tsx          # 子组件
├── Tabs.context.ts       # Context (可选分离)
└── Tabs.types.ts         # 类型定义
```

---

## 6. 暗色模式

```tsx
import { applyMode, Mode } from '@cloudscape-design/global-styles';

const setTheme = (theme: 'light' | 'dark' | 'system') => {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyMode(isDark ? Mode.Dark : Mode.Light);
  } else {
    applyMode(theme === 'dark' ? Mode.Dark : Mode.Light);
  }
};
```

> 默认使用 Cloudscape 组件，自动适配暗色模式。禁止硬编码背景色或文字色。
