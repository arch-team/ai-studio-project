# AI 训练平台前端架构规范

> **架构模式**: Feature-Sliced Design + Modular Architecture
>
> 技术栈、命令、路径别名等基础信息请参见 `CLAUDE.md`

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

### 1.1 架构模式

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

### 1.2 核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **模块自治** | 每个模块拥有独立的类型、API、hooks、组件 | 模块内 CRUD 完全独立 |
| **显式依赖** | 模块间依赖必须通过公共 API (index.ts) | 禁止导入内部文件 |
| **最小知识** | 模块只暴露必要的接口 | 内部实现对外不可见 |
| **单向依赖** | 禁止循环依赖 | 使用事件或共享接口解耦 |
| **后端对齐** | 前端模块划分与后端 Modular Monolith 一致 | 同名模块、同类型定义 |

### 1.3 模块划分

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

### 2.1 模块内部分层

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

### 2.2 依赖方向

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

```typescript
// ✅ 共享内核
import { AppError, ErrorCode } from '@shared/types/errors';
import { apiClient } from '@shared/api/client';
import { usePagination, useDebounce } from '@shared/hooks';
import { eventBus, useEventSubscription } from '@shared/events';

// ✅ Query Keys
import { queryKeys } from '@lib/query';

// ✅ Auth 特殊依赖 (唯一例外)
import { useAuthStore } from '@features/auth';

// ✅ 通过模块公开 API 导入
import { TrainingJobSummary, useTrainingJobs } from '@features/training';
```

### 3.3 禁止的依赖

```typescript
// ❌ 直接导入其他模块内部文件
import { fetchTrainingJobs } from '@features/training/api/trainingJobApi';

// ❌ 直接导入其他模块类型定义内部文件
import { TrainingJobSummary } from '@features/training/types/index';

// ❌ Types 层导入任何外部模块 (绝对禁止)
// features/training/types/index.ts
import { DatasetStatus } from '@features/datasets/types';
```

---

## 4. 模块间通信方式

### 4.1 通信模式决策矩阵

| 场景 | 推荐模式 | 实现方式 | 示例事件 |
|------|---------|---------|---------|
| 异步通知 | **Event Bus** | `shared/events/eventBus.ts` | `training-job:completed` |
| 共享状态 | **Shared Store** | `features/auth/store` | 用户认证状态 |
| 缓存失效联动 | **Query Invalidation** | TanStack Query | 删除任务 → 刷新模型列表 |
| 共享类型/工具 | **Shared Kernel** | `shared/` | ErrorCode, apiClient |

### 4.2 事件驱动通信

**定义事件类型**:
```typescript
// shared/events/eventBus.ts
export interface EventMap {
  'training-job:created': { jobId: number; jobName: string };
  'training-job:completed': { jobId: number; duration: number };
  'training-job:failed': { jobId: number; error: string };
  'dataset:deleted': { datasetId: number };
  'auth:logged-in': { userId: number };
  'auth:logged-out': void;
  'notification:show': { type: 'success' | 'error'; message: string };
}
```

**发布事件**:
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

**订阅事件**:
```typescript
// features/audit/hooks/useAuditSubscription.ts
import { useEventSubscription } from '@shared/events';

export function useAuditSubscription() {
  useEventSubscription('training-job:created', (event) => {
    console.log('Training job created:', event.payload);
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
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
    },
  });
}
```

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

### 5.2 `index.ts` 导出规则

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

**禁止直接导出内部实现细节**:
```typescript
// ❌ 禁止
export { fetchTrainingJobs } from './api/trainingJobApi';
```

### 5.3 类型定义规范

```typescript
// features/{module}/types/index.ts

// === Enums ===
export type JobStatus = 'submitted' | 'running' | 'completed' | 'failed';

// === Entity Types (对应后端 Domain Entity) ===
export interface TrainingJobSummary {
  id: number;
  job_name: string;
  status: JobStatus;
}

export interface TrainingJobDetail extends TrainingJobSummary {
  // 详情特有字段
}

// === Request/Response Types ===
export interface CreateTrainingJobRequest {
  job_name: string;
}

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
│   ├── usePagination.ts
│   ├── useDebounce.ts
│   ├── useLocalStorage.ts
│   └── index.ts
├── events/
│   ├── eventBus.ts        # 事件总线实现
│   ├── useEvent.ts        # 事件 React hooks
│   └── index.ts
└── index.ts
```

### 6.2 共享内核约束

- 只包含**技术基础设施**和**跨模块抽象**
- **禁止**包含任何业务逻辑
- 所有模块可以自由导入 `shared/` 内容

### 6.3 错误类型体系

```typescript
// shared/types/errors.ts
export enum ErrorCode {
  UNKNOWN = 'UNKNOWN',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  JOB_NOT_FOUND = 'JOB_NOT_FOUND',
  JOB_QUOTA_EXCEEDED = 'JOB_QUOTA_EXCEEDED',
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

### 7.2 Query Hook 模板

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

### 7.3 Zustand Store 模板

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

### 8.4 错误码映射

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
        {
          group: ['@features/*/api/*', '!@features/*/api/index'],
          message: '请通过 @features/{module}/api 导入',
        },
        {
          group: ['@features/*/types/*', '!@features/*/types/index'],
          message: '请通过 @features/{module}/types 导入',
        },
      ],
    },
  ],
}
```

### 9.2 运行合规检查

```bash
npm run lint            # ESLint 检查
npx tsc --noEmit        # TypeScript 类型检查
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

### 10.2 与后端对齐对照表

| 前端 | 后端 | 说明 |
|------|------|------|
| `features/{module}/types/` | `modules/{module}/domain/entities/` | 类型定义 |
| `features/{module}/api/queries.ts` | `modules/{module}/api/endpoints.py` | 数据访问 |
| `features/{module}/hooks/` | `modules/{module}/application/services/` | 业务逻辑 |
| `shared/types/errors.ts` | `shared/domain/exceptions.py` | 错误类型 |
| `shared/events/eventBus.ts` | `shared/domain/events.py` | 事件机制 |

---

## 11. 测试架构

> 完整测试规范请参见 [`TESTING.md`](./TESTING.md)

### 11.1 测试分层

| 层级 | 目录 | 职责 |
|------|------|------|
| **Unit** | `tests/unit/` | 组件、Hooks、Store 单元测试 |
| **Integration** | `tests/integration/` | API 集成 (MSW)、页面集成 |
| **E2E** | `e2e/` | 完整用户流程 (Playwright) |

### 11.2 测试工具

- **MSW**: API Mock，位于 `tests/__utils__/mocks/handlers/`
- **test-utils**: 渲染包装器，位于 `tests/__utils__/test-utils.tsx`
- **Mock Stores**: 状态 Mock，位于 `tests/__utils__/mocks/stores/`
- **路径别名**: `@tests/` → `tests/`
