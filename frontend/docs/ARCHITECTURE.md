# AI 训练平台前端架构规范

> **版本**: 1.0
> **最后更新**: 2026-01-23
> **架构模式**: Feature-Sliced Design + Modular Architecture

本文档是前端项目的**核心架构规范单一真实源 (Single Source of Truth)**。所有架构相关决策应以本文档为准。

---

## 目录

1. [架构概述](#1-架构概述)
2. [分层规则](#2-分层规则)
3. [模块间依赖规范](#3-模块间依赖规范)
4. [模块间通信方式](#4-模块间通信方式)
5. [模块结构规范](#5-模块结构规范)
6. [共享内核规范](#6-共享内核规范)
7. [状态管理规范](#7-状态管理规范)
8. [错误处理规范](#8-错误处理规范)
9. [架构合规检查](#9-架构合规检查)
10. [附录](#10-附录)

---

## 1. 架构概述

### 1.1 技术栈

| 类别 | 技术选型 |
|------|---------|
| **语言** | TypeScript 5.3+ |
| **框架** | React 18.2+ |
| **构建工具** | Vite 5.0+ |
| **路由** | React Router 6.x |
| **服务器状态** | TanStack Query 5.x |
| **客户端状态** | Zustand 4.x |
| **UI 组件库** | AWS Cloudscape Design System 3.x |
| **测试** | Vitest + Testing Library |

### 1.2 架构模式

本项目采用 **Feature-Sliced Design (FSD)** 架构，与后端 **Modular Monolith** 保持一致：

```
┌─────────────────────────────────────────────────────────────┐
│               Feature-Sliced Design (模块化)                 │
│   按业务领域垂直切分，模块间松耦合，共享基础设施                  │
├─────────────────────────────────────────────────────────────┤
│               Clean Architecture (分层)                      │
│   types → api → hooks → components → pages                  │
├─────────────────────────────────────────────────────────────┤
│                  State Management                            │
│   服务器状态 (TanStack Query) + 客户端状态 (Zustand)          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **模块自治** | 每个模块拥有独立的类型、API、hooks、组件 | 模块内 CRUD 完全独立 |
| **显式依赖** | 模块间依赖必须通过公共 API (index.ts) | 禁止导入内部文件 |
| **最小知识** | 模块只暴露必要的接口 | 内部实现对外不可见 |
| **单向依赖** | 禁止循环依赖 | 使用事件或共享接口解耦 |
| **后端对齐** | 前端模块划分与后端 Modular Monolith 一致 | 同名模块、同类型定义 |

### 1.4 模块划分

| 模块 | 职责 | 后端对应 |
|------|------|---------|
| `auth` | 用户认证与授权 | `modules/auth` |
| `training` | 训练任务管理 | `modules/training` |
| `datasets` | 数据集管理 | `modules/datasets` |
| `models` | 模型管理 | `modules/models` |
| `resource-quotas` | 资源配额管理 | `modules/quotas` |
| `spaces` | 开发空间管理 | `modules/spaces` |
| `audit` | 审计日志（只读） | `modules/audit` |
| `billing` | 成本统计（只读） | `modules/billing` |
| `monitoring` | 集群监控 | `modules/monitoring` |
| `shared` | 共享内核 | `shared/` |

---

## 2. 分层规则

### 2.1 项目目录结构

```
src/
├── app/                    # 应用入口层
│   ├── providers/         # 全局 Provider (Query, Theme)
│   └── router/            # 路由配置和守卫
├── features/              # 功能模块 (按业务领域划分)
│   ├── auth/
│   ├── training/
│   ├── datasets/
│   ├── models/
│   ├── resource-quotas/
│   ├── spaces/
│   ├── audit/
│   ├── billing/
│   └── monitoring/
├── layouts/               # 布局组件
│   ├── MainLayout/
│   └── AuthLayout/
├── shared/                # 共享内核 (对应后端 shared/)
│   ├── types/            # 共享类型 (错误、通用接口)
│   ├── api/              # API 客户端抽象
│   ├── hooks/            # 通用 hooks
│   └── events/           # 事件总线
├── lib/                   # 基础设施层
│   ├── api/              # (已迁移至 shared/api)
│   └── query/            # TanStack Query 配置
├── store/                 # 全局状态 (Zustand)
│   └── slices/
└── types/                 # 全局类型定义
```

### 2.2 模块内部分层

每个 feature 模块遵循以下分层结构：

```
┌─────────────────────────────────────────┐
│              Pages Layer                 │  ← 页面组件
│           (pages/*.tsx)                  │
├─────────────────────────────────────────┤
│           Components Layer               │  ← UI 组件
│         (components/*.tsx)               │
├─────────────────────────────────────────┤
│             Hooks Layer                  │  ← 业务逻辑 (对应后端 Application)
│          (hooks/index.ts)                │
├─────────────────────────────────────────┤
│              API Layer                   │  ← 数据访问
│    (api/queries.ts, api/*Api.ts)         │
├─────────────────────────────────────────┤
│             Types Layer                  │  ← 类型定义 (对应后端 Domain)
│          (types/index.ts)                │
└─────────────────────────────────────────┘
```

```
features/{module}/
├── types/
│   └── index.ts           # 类型定义 (对应后端 domain/entities)
├── api/
│   ├── {module}Api.ts     # 原始 API 调用
│   ├── queries.ts         # TanStack Query hooks
│   └── index.ts
├── hooks/
│   └── index.ts           # 业务逻辑 hooks (对应后端 application/services)
├── components/
│   └── index.ts           # UI 组件
├── pages/
│   └── index.ts           # 页面组件
└── index.ts               # 模块公共 API 导出
```

### 2.3 依赖方向

```
┌─────────────────────────────────────────────────────────┐
│                    模块内部分层                          │
│                                                         │
│   pages ──► components ──► hooks ──► api ──► types     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                    跨模块依赖                            │
│                                                         │
│   features/A  ───X───►  features/B   (禁止横向依赖)     │
│       │                    │                            │
│       └────────┬───────────┘                            │
│                ▼                                        │
│           shared/  (唯一允许的共享依赖)                  │
└─────────────────────────────────────────────────────────┘
```

**关键规则**:
- 依赖只能从上层指向下层
- Types 层是最底层，不依赖任何外部
- Pages/Components 可以导入 hooks、api、types
- Hooks 可以导入 api、types
- API 只能导入 types

---

## 3. 模块间依赖规范

### 3.1 黄金法则

| 规则 | 说明 | 强制性 |
|------|------|--------|
| **R1** | 模块的 Types 层**绝对不能**导入任何其他模块代码 | 🔴 强制 |
| **R2** | 模块间不能直接导入内部实现，只能通过 `index.ts` 导入 | 🔴 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享内核** | 🔴 强制 |
| **R4** | `auth` 模块的 `useAuthStore` 是**唯一例外**，可被其他模块导入 | 🟡 例外 |

### 3.2 允许的依赖

#### 3.2.1 共享内核依赖

所有模块可以导入 `shared/` 下的内容：

```typescript
// ✅ 类型共享
import { AppError, ErrorCode, getErrorMessage } from '@shared/types/errors';

// ✅ API 客户端共享
import { apiClient } from '@shared/api/client';

// ✅ 通用 Hooks 共享
import { usePagination, useDebounce, useLocalStorage } from '@shared/hooks';

// ✅ 事件总线共享
import { eventBus, useEventSubscription, useNotification } from '@shared/events';
```

#### 3.2.2 Query Keys 共享

所有模块可以导入 `lib/query` 下的 Query Keys：

```typescript
// ✅ Query Keys 共享
import { queryKeys } from '@lib/query';
```

#### 3.2.3 Auth 模块特殊依赖（唯一例外）

其他模块可以导入 auth 的认证状态：

```typescript
// ✅ 仅允许导入公开 API
import { useAuthStore } from '@features/auth';
```

### 3.3 禁止的依赖

```typescript
// ❌ 禁止：直接导入其他模块的内部文件
import { fetchTrainingJobs } from '@features/training/api/trainingJobApi';

// ❌ 禁止：直接导入其他模块的类型定义内部文件
import { TrainingJobSummary } from '@features/training/types/index';

// ❌ 禁止：模块 types 层导入任何外部模块
// features/training/types/index.ts
import { DatasetStatus } from '@features/datasets/types';  // 绝对禁止！
```

### 3.4 正确的跨模块依赖方式

```typescript
// ✅ 正确：通过模块公开 API 导入
import { TrainingJobSummary, useTrainingJobs } from '@features/training';

// ✅ 正确：通过事件总线通信
import { eventBus } from '@shared/events';
eventBus.publish('training-job:completed', { jobId: 123 });

// ✅ 正确：通过共享类型
import { AppError, ErrorCode } from '@shared/types/errors';
```

---

## 4. 模块间通信方式

### 4.1 通信模式决策矩阵

| 场景 | 推荐模式 | 实现方式 |
|------|---------|---------|
| 异步通知 (任务完成) | **Event Bus** | `shared/events/eventBus.ts` |
| 共享状态 (用户认证) | **Shared Store** | `features/auth/store` |
| 缓存失效联动 | **Query Invalidation** | TanStack Query |
| 共享类型/工具 | **Shared Kernel** | `shared/` |

### 4.2 事件驱动通信（推荐）

#### 定义事件类型

```typescript
// shared/events/eventBus.ts
export interface EventMap {
  'training-job:created': { jobId: number; jobName: string };
  'training-job:completed': { jobId: number; duration: number };
  'dataset:deleted': { datasetId: number };
  'notification:show': { type: 'success' | 'error'; message: string };
}
```

#### 发布事件

```typescript
// features/training/hooks/useCreateJob.ts
import { useEventPublisher } from '@shared/events';

export function useCreateTrainingJob() {
  const publish = useEventPublisher();
  const mutation = useMutation({
    mutationFn: createTrainingJob,
    onSuccess: (job) => {
      publish('training-job:created', { jobId: job.id, jobName: job.name });
    },
  });
  return mutation;
}
```

#### 订阅事件

```typescript
// features/audit/hooks/useAuditSubscription.ts
import { useEventSubscription } from '@shared/events';

export function useAuditSubscription() {
  useEventSubscription('training-job:created', (event) => {
    console.log('Training job created:', event.payload);
    // 触发审计日志刷新
  });
}
```

### 4.3 Query Invalidation 联动

```typescript
// features/training/api/queries.ts
export function useDeleteTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTrainingJob,
    onSuccess: () => {
      // 失效训练任务列表
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
      // 联动失效模型列表（训练任务删除可能影响关联模型）
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
    },
  });
}
```

### 4.4 核心事件清单

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| **training** | `training-job:created` | 任务创建 | audit, monitoring |
| **training** | `training-job:completed` | 任务完成 | audit, models |
| **training** | `training-job:failed` | 任务失败 | audit, monitoring |
| **datasets** | `dataset:deleted` | 数据集删除 | training |
| **auth** | `auth:logged-in` | 用户登录 | audit |
| **auth** | `auth:logged-out` | 用户登出 | 全局状态清理 |
| **notification** | `notification:show` | 显示通知 | 全局通知组件 |

---

## 5. 模块结构规范

### 5.1 目录结构模板

```
features/{module}/
├── types/
│   └── index.ts           # 类型定义 + UI Helper Constants
├── api/
│   ├── {module}Api.ts     # 原始 fetch 调用
│   ├── queries.ts         # TanStack Query hooks
│   └── index.ts           # API 导出
├── hooks/
│   └── index.ts           # 业务逻辑 hooks
├── components/
│   ├── {Entity}Table.tsx
│   ├── {Entity}Form.tsx
│   ├── {Entity}StatusBadge.tsx
│   └── index.ts           # 组件导出
├── pages/
│   ├── {Entity}ListPage.tsx
│   ├── {Entity}DetailPage.tsx
│   ├── Create{Entity}Page.tsx
│   └── index.ts           # 页面导出
└── index.ts               # 模块公共 API
```

### 5.2 文件命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 类型定义 | `types/index.ts` | `types/index.ts` |
| API 客户端 | `{module}Api.ts` | `trainingJobApi.ts` |
| Query Hooks | `queries.ts` | `queries.ts` |
| 业务 Hooks | `hooks/index.ts` 或 `use{Feature}.ts` | `useTrainingJobStats.ts` |
| UI 组件 | `{Entity}{Component}.tsx` | `TrainingJobTable.tsx` |
| 页面组件 | `{Entity}{Page}Page.tsx` | `TrainingJobListPage.tsx` |

### 5.3 `index.ts` 导出规则

每个模块必须在 `index.ts` 明确定义公开 API：

```typescript
// features/training/index.ts
/**
 * Training module - Public API exports.
 */

// Types
export * from './types';

// API (Query Hooks)
export * from './api';

// Hooks (业务逻辑)
export * from './hooks';

// Components
export * from './components';

// Pages
export * from './pages';
```

**禁止导出**:

```typescript
// ❌ 禁止直接导出内部实现细节
export { fetchTrainingJobs } from './api/trainingJobApi';  // 内部 API 调用
```

### 5.4 类型定义规范

```typescript
// features/{module}/types/index.ts

// === Enums ===
export type JobStatus = 'submitted' | 'running' | 'completed' | 'failed';

// === Entity Types (对应后端 Domain Entity) ===
export interface TrainingJobSummary {
  id: number;
  job_name: string;
  status: JobStatus;
  // ...
}

export interface TrainingJobDetail extends TrainingJobSummary {
  // 详情特有字段
}

// === Request Types (对应后端 API Schema) ===
export interface CreateTrainingJobRequest {
  job_name: string;
  // ...
}

// === Response Types ===
export interface TrainingJobListResponse {
  items: TrainingJobSummary[];
  total: number;
  page: number;
  page_size: number;
}

// === Filter Types ===
export interface TrainingJobFilters {
  status?: JobStatus;
  page?: number;
  page_size?: number;
}

// === UI Helper Constants ===
export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  submitted: '已提交',
  running: '运行中',
  completed: '已完成',
  failed: '已失败',
};

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  submitted: 'grey',
  running: 'green',
  completed: 'green',
  failed: 'red',
};
```

---

## 6. 共享内核规范

### 6.1 共享内核结构

```
shared/
├── types/
│   ├── errors.ts          # 统一错误类型 (对应后端 DomainError)
│   └── index.ts
├── api/
│   ├── client.ts          # API 客户端抽象
│   └── index.ts
├── hooks/
│   ├── useEntity.ts       # 通用 CRUD hooks
│   ├── usePagination.ts   # 分页 hooks
│   ├── useDebounce.ts     # 防抖 hooks
│   ├── useLocalStorage.ts # 本地存储 hooks
│   └── index.ts
├── events/
│   ├── eventBus.ts        # 事件总线实现
│   ├── useEvent.ts        # 事件 React hooks
│   └── index.ts
└── index.ts               # 统一导出
```

### 6.2 共享内核约束

- `shared/` 只包含**技术基础设施**和**跨模块抽象**
- **禁止**包含任何业务逻辑
- 类型定义 (AppError, ErrorCode) 是纯技术抽象
- 所有模块可以自由导入 `shared/` 内容

### 6.3 错误类型体系

```typescript
// shared/types/errors.ts

// 对应后端 DomainError 体系
export enum ErrorCode {
  // 通用错误
  UNKNOWN = 'UNKNOWN',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  // ...

  // 训练任务错误
  JOB_NOT_FOUND = 'JOB_NOT_FOUND',
  JOB_QUOTA_EXCEEDED = 'JOB_QUOTA_EXCEEDED',
  // ...
}

export class AppError extends Error {
  readonly code: ErrorCode;
  readonly details?: Record<string, unknown>;

  static fromApiResponse(response: ApiErrorResponse): AppError;
}
```

---

## 7. 状态管理规范

### 7.1 状态分类

| 类型 | 管理方案 | 示例 |
|------|---------|------|
| **服务器状态** | TanStack Query | API 数据、缓存 |
| **客户端状态** | Zustand | UI 状态、用户偏好 |
| **表单状态** | React Hook Form / useState | 表单输入 |
| **URL 状态** | React Router | 路由参数、查询参数 |

### 7.2 TanStack Query 规范

#### Query Key 工厂

```typescript
// lib/query/queryKeys.ts
export const queryKeys = {
  trainingJobs: {
    all: ['trainingJobs'] as const,
    lists: () => [...queryKeys.trainingJobs.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.trainingJobs.lists(), filters] as const,
    details: () => [...queryKeys.trainingJobs.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.trainingJobs.details(), id] as const,
  },
  // 其他实体...
};
```

#### Query Hook 模板

```typescript
// features/{module}/api/queries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';

export function use{Entity}s(filters: {Entity}Filters = {}) {
  return useQuery({
    queryKey: queryKeys.{entity}s.list(filters),
    queryFn: () => fetch{Entity}s(filters),
  });
}

export function use{Entity}(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.{entity}s.detail(String(id!)),
    queryFn: () => fetch{Entity}(id!),
    enabled: id !== undefined,
  });
}

export function useCreate{Entity}() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: create{Entity},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.{entity}s.lists() });
    },
  });
}
```

### 7.3 Zustand 规范

#### Store 结构

```typescript
// store/slices/uiSlice.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  setTheme: (theme: UIState['theme']) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'system',
      sidebarCollapsed: false,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    { name: 'ui-storage' }
  )
);
```

---

## 8. 错误处理规范

### 8.1 错误处理层级

```
┌─────────────────────────────────────────┐
│           Global Error Boundary          │  ← 捕获未处理异常
├─────────────────────────────────────────┤
│          Query Error Handler             │  ← API 错误处理
├─────────────────────────────────────────┤
│         Component Error Handling         │  ← 局部错误显示
└─────────────────────────────────────────┘
```

### 8.2 API 错误处理

```typescript
// shared/api/client.ts
export class ApiClient {
  async request<T>(path: string, config?: RequestConfig): Promise<T> {
    const response = await fetch(url, options);

    if (!response.ok) {
      throw await AppError.fromResponse(response);
    }

    return response.json();
  }
}
```

### 8.3 Query 错误处理

```typescript
// app/providers/QueryProvider.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof AppError && error.isNotFound()) {
          return false; // 404 不重试
        }
        return failureCount < 3;
      },
    },
    mutations: {
      onError: (error) => {
        if (error instanceof AppError) {
          eventBus.publish('notification:show', {
            type: 'error',
            message: getErrorMessage(error),
          });
        }
      },
    },
  },
});
```

### 8.4 错误码到 HTTP 状态码映射

| 错误码 | HTTP 状态码 | 场景 |
|--------|-------------|------|
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `VALIDATION_ERROR` | 422 | 参数验证失败 |
| `QUOTA_EXCEEDED` | 429 | 配额不足 |
| `UNAUTHORIZED` | 401 | 未认证 |
| `FORBIDDEN` | 403 | 无权限 |

---

## 9. 架构合规检查

### 9.1 ESLint 规则

`.eslintrc.cjs` 配置了模块边界检查：

```javascript
rules: {
  'no-restricted-imports': [
    'error',
    {
      patterns: [
        // 禁止导入其他 feature 模块的内部实现
        {
          group: ['@features/*/api/*', '!@features/*/api/index'],
          message: '请通过 @features/{module}/api 导入',
        },
        {
          group: ['@features/*/types/*', '!@features/*/types/index'],
          message: '请通过 @features/{module}/types 导入',
        },
        // ...
      ],
    },
  ],
}
```

### 9.2 运行合规检查

```bash
# 运行 ESLint 检查
npm run lint

# TypeScript 类型检查
npx tsc --noEmit
```

### 9.3 CI 集成

```yaml
# .github/workflows/ci.yml
- name: Lint
  run: npm run lint -- --max-warnings 0

- name: Type Check
  run: npx tsc --noEmit
```

---

## 10. 附录

### 10.1 快速参考卡片

```
┌────────────────────────────────────────────────────────┐
│          Feature Module 依赖速查                       │
├────────────────────────────────────────────────────────┤
│ ✅ 允许                                                │
│   • 导入 @shared/* 任意内容                            │
│   • 导入 @lib/query (queryKeys)                       │
│   • 导入 @features/auth (useAuthStore)                │
│   • 通过 index.ts 导入其他模块公开 API                  │
│   • 通过 EventBus 发布/订阅事件                        │
├────────────────────────────────────────────────────────┤
│ ❌ 禁止                                                │
│   • Types 层导入任何外部模块                           │
│   • 直接导入其他模块的内部文件                          │
│   • 模块间直接依赖实现细节                              │
├────────────────────────────────────────────────────────┤
│ 🔄 模块间通信                                          │
│   • 优先: EventBus (异步解耦)                          │
│   • 备选: Query Invalidation (缓存联动)                │
│   • 禁止: 直接导入其他模块实现                          │
└────────────────────────────────────────────────────────┘
```

### 10.2 路径别名速查

| 别名 | 路径 | 用途 |
|------|------|------|
| `@/` | `src/` | 通用引用 |
| `@app/` | `src/app/` | 应用入口 |
| `@features/` | `src/features/` | 功能模块 |
| `@shared/` | `src/shared/` | 共享内核 |
| `@layouts/` | `src/layouts/` | 布局组件 |
| `@lib/` | `src/lib/` | 基础设施 |
| `@store/` | `src/store/` | 全局状态 |
| `@types/` | `src/types/` | 全局类型 |

### 10.3 与后端对齐对照表

| 前端 | 后端 | 说明 |
|------|------|------|
| `features/{module}/types/` | `modules/{module}/domain/entities/` | 类型定义 |
| `features/{module}/api/queries.ts` | `modules/{module}/api/endpoints.py` | 数据访问 |
| `features/{module}/hooks/` | `modules/{module}/application/services/` | 业务逻辑 |
| `shared/types/errors.ts` | `shared/domain/exceptions.py` | 错误类型 |
| `shared/events/eventBus.ts` | `shared/domain/events.py` | 事件机制 |
| `lib/query/queryKeys.ts` | - | 缓存键管理 |

### 10.4 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 开发指南 | `frontend/CLAUDE.md` | 命令、组件使用、设计规范 |
| 设计规范 | `frontend/DESIGN.md` | Cloudscape 组件使用 |
| 后端架构 | `backend/docs/ARCHITECTURE.md` | 后端架构规范 |
| 功能规范 | `specs/001-ai-training-platform/spec.md` | 术语标准、功能需求 |

### 10.5 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-23 | 初始版本，与后端 Modular Monolith 对齐 |
