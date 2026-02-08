> **职责**: 架构规范的单一真实源 - 分层规则、模块依赖、模块通信、共享内核、错误处理

# 前端架构规范 (Frontend Architecture Standards)

> **架构模式**: Feature-Sliced Design + Modular Architecture
> **适用范围**: React + TypeScript + AWS Cloudscape 前端项目

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 0.1 模块内分层依赖矩阵

| 从 ↓ 导入 → | types | api | hooks | components | pages |
|-------------|:-----:|:---:|:-----:|:----------:|:-----:|
| **pages** | ✅ | ✅ | ✅ | ✅ | - |
| **components** | ✅ | ✅ | ✅ | - | ❌ |
| **hooks** | ✅ | ✅ | - | ❌ | ❌ |
| **api** | ✅ | - | ❌ | ❌ | ❌ |
| **types** | - | ❌ | ❌ | ❌ | ❌ |

**图例**: ✅ 允许 | ❌ 禁止

**核心规则**: 依赖只能从上层指向下层，Types 层是最底层

### 0.2 跨模块依赖速查

```
┌────────────────────────────────────────────────────────┐
│          Feature Module 依赖速查                       │
├────────────────────────────────────────────────────────┤
│ ✅ 允许                                                │
│   • 导入 @shared/* 任意内容                            │
│   • 导入 @lib/query (queryKeys)                       │
│   • 导入 @features/auth (useAuthStore) [唯一例外]     │
│   • 通过 index.ts 导入其他模块公开 API                  │
│   • 通过 EventBus 发布/订阅事件                        │
├────────────────────────────────────────────────────────┤
│ ❌ 禁止                                                │
│   • Types 层导入任何外部模块                           │
│   • 直接导入其他模块的内部文件                          │
│   • 模块间直接依赖实现细节                              │
│   • features/A 直接导入 features/B 内部                │
├────────────────────────────────────────────────────────┤
│ 🔄 模块间通信                                          │
│   • 优先: EventBus (异步解耦)                          │
│   • 备选: Query Invalidation (缓存联动)                │
│   • 禁止: 直接导入其他模块实现                          │
└────────────────────────────────────────────────────────┘
```

### 0.3 模块结构模板

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
│   └── index.ts           # 组件导出
├── pages/
│   ├── {Entity}ListPage.tsx
│   ├── {Entity}DetailPage.tsx
│   └── index.ts           # 页面导出
└── index.ts               # 模块公共 API
```

### 0.4 陷阱 ⚠️

- ❌ Types 层导入外部模块 → ✅ Types 保持零外部依赖
- ❌ 直接导入 `@features/training/api/trainingJobApi` → ✅ 通过 `@features/training` 导入
- ❌ 模块间直接调用 → ✅ 使用 EventBus 或 Query Invalidation

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

> 业务模块完整列表及后端对应关系详见 [project-config.md](../project-config.md) §功能模块

**`shared` (共享内核)**: 技术基础设施和跨模块抽象，禁止包含业务逻辑（详见 §6）

---

## 2. 分层规则

### 2.1 模块内部分层

> 分层结构和依赖矩阵详见 §0.1，模块结构模板详见 §0.3

### 2.2 依赖方向

> 跨模块依赖速查详见 §0.2

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

事件驱动通信通过 `shared/events/eventBus.ts` 实现，支持类型安全的发布/订阅模式。

**核心概念**: `EventMap` 接口定义所有事件类型 → `useEventPublisher` 发布事件 → `useEventSubscription` 订阅事件

> EventBus 完整实现（EventMap 定义、发布/订阅 Hooks、Query Invalidation 联动示例）详见 [state-management.md](state-management.md) §4

---

## 5. 模块导出规则

### 5.1 `index.ts` 导出规范

**模式**: 按层级顺序 `export * from './types' | './api' | './hooks' | './components' | './pages'`

**禁止**: 直接导出内部实现（如 `export { fetchTrainingJobs } from './api/trainingJobApi'`）

### 5.2 类型定义规范

`features/{module}/types/index.ts` 应包含以下类型分类：

| 分类 | 说明 | 命名模式 |
|------|------|---------|
| 枚举类型 | 状态、类别等联合类型 | `type JobStatus = 'submitted' \| ...` |
| Entity Types | 对应后端 Domain Entity | `{Entity}Summary`, `{Entity}Detail` |
| Request/Response | API 请求和响应 | `Create{Entity}Request`, `{Entity}ListResponse` |
| Filter Types | 列表查询参数 | `{Entity}Filters` |
| UI Helper Constants | 状态标签映射等 | `{ENTITY}_STATUS_LABELS` |

> `{Entity}Detail` 继承 `{Entity}Summary`，`ListResponse` 包含 `items`, `total`, `page`, `page_size`

---

## 6. 共享内核规范

### 6.1 共享内核结构

> 目录结构详见 [project-structure.md](project-structure.md) §0 中 `shared/` 部分

**核心子模块**: `types/`(错误类型) · `api/`(客户端) · `hooks/`(通用 Hooks) · `events/`(事件总线)

### 6.2 共享内核约束

- 只包含**技术基础设施**和**跨模块抽象**
- **禁止**包含任何业务逻辑
- 所有模块可以自由导入 `shared/` 内容

### 6.3 错误类型体系

```typescript
// shared/types/errors.ts
export enum ErrorCode { UNKNOWN, VALIDATION_ERROR, NOT_FOUND, JOB_NOT_FOUND, /* ... */ }
export class AppError extends Error {
  readonly code: ErrorCode;
  readonly details?: Record<string, unknown>;
  static fromApiResponse(response: ApiErrorResponse): AppError;
}
```

---

## 7. 错误处理规范

### 7.1 错误处理层级

```
┌─────────────────────────────────────────┐
│           Global Error Boundary          │  ← 捕获未处理异常
├─────────────────────────────────────────┤
│          Query Error Handler             │  ← API 错误处理
├─────────────────────────────────────────┤
│         Component Error Handling         │  ← 局部错误显示
└─────────────────────────────────────────┘
```

### 7.2 API 错误处理

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

### 7.3 错误码映射

> Query 层错误处理配置（QueryClient retry 策略、mutation 全局 onError）详见 [state-management.md](state-management.md) §1.4

| 错误码 | HTTP 状态码 | 场景 |
|--------|-------------|------|
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `VALIDATION_ERROR` | 422 | 参数验证失败 |
| `QUOTA_EXCEEDED` | 429 | 配额不足 |
| `UNAUTHORIZED` | 401 | 未认证 |
| `FORBIDDEN` | 403 | 无权限 |

---

## 8. 架构合规检查 (ESLint)

### 8.1 ESLint 规则

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

---

## 附录: 与后端对齐对照表

| 前端 | 后端 | 说明 |
|------|------|------|
| `features/{module}/types/` | `modules/{module}/domain/entities/` | 类型定义 |
| `features/{module}/api/queries.ts` | `modules/{module}/api/endpoints.py` | 数据访问 |
| `features/{module}/hooks/` | `modules/{module}/application/services/` | 业务逻辑 |
| `shared/types/errors.ts` | `shared/domain/exceptions.py` | 错误类型 |
| `shared/events/eventBus.ts` | `shared/domain/events.py` | 事件机制 |
