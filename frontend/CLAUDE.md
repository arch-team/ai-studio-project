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

### Feature-Based Architecture (FSD)

项目采用 Feature-Sliced Design 架构，按功能模块组织代码：

```
src/
├── app/                    # 应用入口层
│   ├── providers/         # 全局 Provider (Query, Theme)
│   └── router/            # 路由配置和守卫
│       └── guards/        # AuthGuard, RoleGuard
├── features/              # 功能模块 (按业务领域划分)
│   └── auth/             # 认证模块
│       └── store/        # 模块级状态 (authStore)
├── layouts/               # 布局组件
│   ├── MainLayout/       # 主布局 (AppLayout + Navigation)
│   └── AuthLayout/       # 认证页布局
├── shared/                # 共享层
│   └── components/       # 通用组件
├── lib/                   # 基础设施层
│   ├── api/              # API 客户端
│   └── query/            # TanStack Query 配置和 queryKeys
├── store/                 # 全局状态 (Zustand slices)
│   └── slices/           # uiSlice, notificationSlice
├── types/                 # TypeScript 类型定义
└── tests/                 # 测试文件
    └── unit/             # 单元测试 (镜像 src 结构)
```

### 路径别名

`tsconfig.json` 和 `vite.config.ts` 配置了以下别名：

| 别名 | 路径 | 用途 |
|------|------|------|
| `@/` | `src/` | 通用引用 |
| `@app/` | `src/app/` | 应用入口 |
| `@features/` | `src/features/` | 功能模块 |
| `@shared/` | `src/shared/` | 共享组件 |
| `@layouts/` | `src/layouts/` | 布局组件 |
| `@lib/` | `src/lib/` | 基础设施 |
| `@store/` | `src/store/` | 全局状态 |
| `@types/` | `src/types/` | 类型定义 |

```typescript
// 推荐使用语义化别名
import { useAuthStore } from '@features/auth/store/authStore';
import { MainLayout } from '@layouts/MainLayout';
import { queryKeys } from '@lib/query';
import { useUIStore } from '@store/slices/uiSlice';
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

**API 客户端** (`src/lib/api/`):

Vite 开发服务器配置了 API 代理 (`/api` → `http://localhost:8000`)。

**环境变量** (`.env`):
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **注意**: Vite 环境变量必须以 `VITE_` 前缀开头才能在客户端代码中访问

### Query 键工厂

使用 `src/lib/query/queryKeys.ts` 中的 `queryKeys` 工厂函数管理缓存键：

```typescript
import { queryKeys } from '@lib/query';

// 使用示例
const { data } = useQuery({
  queryKey: queryKeys.trainingJobs.list({ status: 'running' }),
  queryFn: () => fetchTrainingJobs({ status: 'running' }),
});

// 键层级结构
queryKeys.trainingJobs.all          // ['trainingJobs']
queryKeys.trainingJobs.lists()      // ['trainingJobs', 'list']
queryKeys.trainingJobs.list(filters) // ['trainingJobs', 'list', filters]
queryKeys.trainingJobs.details()    // ['trainingJobs', 'detail']
queryKeys.trainingJobs.detail(id)   // ['trainingJobs', 'detail', id]
// 同样适用于: datasets, checkpoints, models, resourceQuotas, users
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

## Testing

### 测试配置

- **框架**: Vitest + Testing Library
- **测试文件位置**: `src/tests/unit/` (镜像源码目录结构)
- **配置文件**: `vitest.config.ts`

### Cloudscape 测试 Mock

`src/tests/setup.ts` 预配置了 Cloudscape 组件所需的浏览器 API mock：
- `window.matchMedia` (响应式布局)
- `ResizeObserver` (组件尺寸观察)
- `IntersectionObserver` (懒加载)

### 运行测试

```bash
npm test                                    # 运行所有测试
npm test -- src/tests/unit/store           # 运行特定目录
npm test -- --watch                         # 监听模式
npm run test:coverage                       # 覆盖率报告
```

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
