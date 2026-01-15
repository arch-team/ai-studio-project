# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**

## Project Overview
AI Training Platform 前端应用 - 基于 React + AWS Cloudscape Design System 的企业级 UI。

## Tech Stack
- **Language**: TypeScript 5.3.3
- **Framework**: React 18.2.0
- **Build**: Vite 5.0.12
- **Routing**: React Router 6.21.2
- **State**: Zustand 4.4.7 (客户端) + TanStack Query 5.17.0 (服务器)
- **UI**: AWS Cloudscape Design System 3.0.0
- **Testing**: Vitest 1.2.1, Testing Library
- **Code Quality**: ESLint, TypeScript ESLint

## Common Commands

```bash
npm install                     # 安装依赖
npm run dev                     # 开发服务器 (http://localhost:5173)
npm run build                   # 生产构建
npm test                        # 运行测试
npm run test:coverage           # 覆盖率报告
npm test -- src/hooks/useApi    # 运行单个测试文件
npm test -- --watch             # 监听模式
npm run lint                    # ESLint (--max-warnings 0)
```

## Architecture

### 路径别名

项目配置了 `@/` 路径别名指向 `src/` 目录：

```typescript
// 使用路径别名 (tsconfig.json 配置)
import { apiClient } from '@/lib/api';
import { useTrainingJobs } from '@/hooks/useApi';
import { TrainingJob } from '@/types';
```

### 目录结构

```
src/
├── main.tsx              # 应用入口
├── App.tsx               # 根组件
├── pages/                # 页面组件
│   └── HomePage.tsx
├── layouts/              # 布局组件
│   └── MainLayout.tsx
├── hooks/                # 自定义 Hooks
│   └── useApi.ts        # API 调用 Hook
├── store/                # Zustand 状态存储
│   └── index.ts
├── lib/                  # 工具库
│   ├── api.ts           # API 客户端 (fetch 封装)
│   └── queryClient.ts   # TanStack Query 配置
└── types/                # TypeScript 类型定义
    └── index.ts
```

## State Management Strategy

**分层管理原则**:
- **服务器状态 (TanStack Query)**: API 数据、缓存、同步、乐观更新
- **客户端状态 (Zustand)**: UI 状态、用户偏好、主题设置

```typescript
// TanStack Query - 服务器状态
const { data, isLoading } = useQuery({
  queryKey: ['training-jobs'],
  queryFn: () => apiClient.get('/training-jobs'),
});

// Zustand - 客户端状态
const useAppStore = create((set) => ({
  theme: 'system',
  setTheme: (theme) => set({ theme }),
}));
```

## API Integration

**API 客户端** (`src/lib/api.ts`):
```typescript
export const apiClient = new ApiClient(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
);
```

**环境变量** (`.env`):
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **注意**: Vite 环境变量必须以 `VITE_` 前缀开头才能在客户端代码中访问

### Query 键工厂

使用 `src/lib/queryClient.ts` 中的 `queryKeys` 工厂函数管理缓存键：

```typescript
import { queryKeys } from '@/lib/queryClient';

// 使用示例
const { data } = useQuery({
  queryKey: queryKeys.trainingJobs.list({ status: 'running' }),
  queryFn: () => apiClient.get('/training-jobs', { status: 'running' }),
});

// 可用的键工厂
queryKeys.trainingJobs.all          // ['training-jobs']
queryKeys.trainingJobs.list(filters) // ['training-jobs', 'list', filters]
queryKeys.trainingJobs.detail(id)    // ['training-jobs', 'detail', id]
// 同样适用于: datasets, models, checkpoints, spaces, users, quotas, auditLogs, system
```

## Design Principles

### Cloudscape-First 原则

**MUST** 遵循 `DESIGN.md` 中的规范:

1. **仅使用 Cloudscape 组件** - 禁止自定义样式覆盖
2. **禁止内联 CSS** - 使用 SpaceBetween 等布局组件
3. **禁止原生 HTML 元素** - 使用 Input, Select 等 Cloudscape 组件
4. **禁止第三方图表库** - 使用 Cloudscape LineChart, PieChart

```tsx
// ❌ 禁止
<Button style={{ backgroundColor: 'red' }}>危险</Button>
<div style={{ marginTop: 20 }}>...</div>
<input type="text" />

// ✅ 正确
<Button variant="primary">确认</Button>
<SpaceBetween size="m">...</SpaceBetween>
<Input value={value} onChange={handleChange} />
```

### 任务状态色彩

| 状态 | Badge | 说明 |
|------|-------|------|
| `submitted` | `grey` | 已提交，等待调度 |
| `pending` | `blue` | 等待资源 |
| `running` | `green` | 正在运行 |
| `paused` | `yellow` | 用户暂停 |
| `preempted` | `orange` | 被抢占 |
| `completed` | `green` | 成功完成 |
| `failed` | `red` | 执行失败 |
| `cancelled` | `grey` | 用户取消 |

### 间距系统 (8px 网格)

```typescript
xs: '4px'   // 紧凑元素
s:  '8px'   // 行内元素
m:  '16px'  // 段落/卡片内
l:  '24px'  // 区块间距
xl: '32px'  // 页面区域
```

## Page Templates

### 列表页

```tsx
<Container>
  <Header variant="h1" actions={<Button variant="primary">创建</Button>}>
    训练任务
  </Header>
  <SpaceBetween size="l">
    <PropertyFilter {...filterProps} />
    <Table
      columnDefinitions={columns}
      items={items}
      loading={isLoading}
      pagination={<Pagination {...} />}
      empty={<EmptyState />}
    />
  </SpaceBetween>
</Container>
```

### 详情页

```tsx
<SpaceBetween size="l">
  <Container header={<Header variant="h2">概览</Header>}>
    <KeyValuePairs items={overviewItems} />
  </Container>
  <Tabs tabs={[
    { id: "metrics", label: "训练指标", content: <MetricsPanel /> },
    { id: "logs", label: "日志", content: <LogsPanel /> },
  ]} />
</SpaceBetween>
```

### 表单页

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
    <FormField label="任务名称" errorText={errors.name}>
      <Input value={name} onChange={e => setName(e.detail.value)} />
    </FormField>
  </Container>
</Form>
```

## Theme Support

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

## Pre-commit Checklist

### 页面必备
- [ ] 页面标题 (Header 组件)
- [ ] 面包屑导航
- [ ] 主操作按钮 (右上角)
- [ ] 加载状态处理
- [ ] 空状态设计
- [ ] 错误状态处理

### 表格必备
- [ ] 排序功能
- [ ] 分页功能
- [ ] 空状态
- [ ] 加载状态
- [ ] 行操作

### 代码质量
- [ ] TypeScript 严格模式通过
- [ ] ESLint 无警告 (`--max-warnings 0`)
- [ ] 无自定义 CSS
- [ ] 全部使用 Cloudscape 组件
- [ ] 暗色模式下无显示异常

## Key Documentation

| 文档 | 位置 | 用途 |
|------|------|------|
| **设计规范** | `DESIGN.md` | Cloudscape 组件使用、页面模板 |
| **详细设计指南** | `../specs/frontend-design-guide.md` | 完整视觉规范、无障碍设计 |

## Common Imports

```tsx
// 核心组件
import {
  AppLayout, BreadcrumbGroup, Button, Container,
  Header, SpaceBetween, Table, Tabs,
} from '@cloudscape-design/components';

// 表单组件
import {
  Form, FormField, Input, Select, Checkbox,
} from '@cloudscape-design/components';

// 反馈组件
import {
  Alert, Flashbar, Modal, StatusIndicator,
} from '@cloudscape-design/components';

// 主题
import { applyMode, Mode } from '@cloudscape-design/global-styles';
```
