# 前端架构 (Feature-Sliced Design)

**更新时间**: 2026-01-26 10:30
**版本**: 1.0.0

## 功能模块 (11个)

| 模块 | 路径 | 核心组件 | 状态 |
|------|------|---------|------|
| `auth` | `features/auth/` | authStore | ✅ |
| `training` | `features/training/` | TrainingJobTable, TrainingJobForm | ✅ |
| `models` | `features/models/` | ModelTable, ModelVersionTable | ✅ |
| `datasets` | `features/datasets/` | - | 📋 |
| `templates` | `features/templates/` | TemplateTable, PopularTemplates | ✅ |
| `spaces` | `features/spaces/` | - | 📋 |
| `audit` | `features/audit/` | - | 📋 |
| `monitoring` | `features/monitoring/` | - | 📋 |
| `billing` | `features/billing/` | - | 📋 |
| `resource-quotas` | `features/resource-quotas/` | ResourceQuotasPage | ✅ |

### 模块标准结构

```
features/{module}/
├── types/              # TypeScript 类型
│   └── index.ts
├── api/                # API 层
│   ├── {module}Api.ts  # fetch 函数
│   ├── queries.ts      # TanStack Query hooks
│   └── index.ts
├── hooks/              # 业务逻辑 hooks
│   └── index.ts
├── components/         # UI 组件
│   ├── *.tsx
│   └── index.ts
├── pages/              # 页面组件
│   ├── *Page.tsx
│   └── index.ts
└── index.ts            # 模块公共 API
```

## 路由结构

| 路径 | 页面 | 守卫 |
|------|------|------|
| `/` | HomePage | Auth |
| `/login` | LoginPage | - |
| `/training-jobs` | TrainingJobListPage | Auth |
| `/training-jobs/create` | CreateTrainingJobPage | Auth |
| `/training-jobs/:id` | TrainingJobDetailPage | Auth |
| `/models` | ModelListPage | Auth |
| `/models/:id` | ModelDetailPage | Auth |
| `/models/:id/versions` | ModelVersionsPage | Auth |
| `/job-templates` | TemplateListPage | Auth |
| `/job-templates/:id` | TemplateDetailPage | Auth |
| `/datasets` | DatasetsPage | Auth |
| `/datasets/:id` | DatasetDetailPage | Auth |
| `/checkpoints` | CheckpointsPage | Auth |
| `/resource-quotas` | ResourceQuotasPage | Auth |
| `/admin` | AdminPage | Auth + RoleGuard(admin) |
| `/reports` | ReportsPage | Auth + RoleGuard(admin\|team_lead) |
| `/ide` | IDEPage | Auth |
| `/404` | NotFoundPage | - |
| `/unauthorized` | UnauthorizedPage | - |

### 路由守卫

```typescript
// app/router/guards/AuthGuard.tsx
<AuthGuard>
  <Outlet />
</AuthGuard>

// app/router/guards/RoleGuard.tsx
<RoleGuard allowedRoles={['admin', 'team_lead']}>
  <Outlet />
</RoleGuard>
```

## 状态管理

### 三层状态分离

```
┌─────────────────────────────────────┐
│ TanStack Query (服务器状态)          │
│ - 训练任务、模型、数据集等列表/详情   │
│ - 自动缓存、失效、重新获取            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Zustand (全局客户端状态)             │
│ - UI 状态: sidebarOpen, breadcrumbs │
│ - 认证状态: isAuthenticated, user   │
│ - 通知: notifications               │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 自定义 Hooks (派生状态)              │
│ - useTrainingJobStats (统计)        │
│ - useCanPauseJob (权限判断)         │
│ - useJobDuration (计算)             │
└─────────────────────────────────────┘
```

### TanStack Query Keys 工厂

```typescript
// lib/query/queryKeys.ts
queryKeys = {
  trainingJobs: {
    all: ['trainingJobs'],
    lists: () => [...queryKeys.trainingJobs.all, 'list'],
    list: (filters) => [...queryKeys.trainingJobs.lists(), filters],
    details: () => [...queryKeys.trainingJobs.all, 'detail'],
    detail: (id) => [...queryKeys.trainingJobs.details(), id],
    logs: (jobId, options) => [..., 'logs', jobId, options],
    metrics: (jobId, options) => [..., 'metrics', jobId, options],
  },
  models: { ... },
  datasets: { ... },
  checkpoints: { ... },
  // ...
}
```

### Zustand Stores

```typescript
// store/slices/uiSlice.ts
interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  breadcrumbs: BreadcrumbItem[];
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
}

// store/slices/notificationSlice.ts
interface NotificationState {
  notifications: Notification[];
  addNotification: (n: Notification) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

// features/auth/store/authStore.ts
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  login: (user: User) => void;
  logout: () => void;
}
```

## 事件总线

### EventMap 类型定义

```typescript
// shared/events/eventBus.ts
type EventMap = {
  // 训练任务
  'training-job:created': TrainingJobCreatedEvent;
  'training-job:status-changed': TrainingJobStatusChangedEvent;
  'training-job:completed': TrainingJobCompletedEvent;

  // 数据集
  'dataset:created': DatasetCreatedEvent;
  'dataset:deleted': DatasetDeletedEvent;

  // 空间
  'space:started': SpaceStartedEvent;
  'space:stopped': SpaceStoppedEvent;

  // 配额
  'quota:exceeded': QuotaExceededEvent;

  // 认证
  'auth:logged-in': UserLoggedInEvent;
  'auth:logged-out': UserLoggedOutEvent;

  // 通知
  'notification:show': NotificationEvent;
}
```

### API

```typescript
EventBus.subscribe<K>(eventType, handler): Unsubscribe
EventBus.once<K>(eventType, handler): Unsubscribe
EventBus.publish<K>(eventType, payload, source): void
EventBus.publishAsync<K>(eventType, payload, source): Promise<void>
EventBus.getHistory(eventType?): DomainEvent[]
EventBus.clearHistory(): void
EventBus.getSubscriberCount(eventType?): number
```

### React Hook

```typescript
// shared/events/useEvent.ts
function useEvent<K extends keyof EventMap>(
  eventType: K,
  handler: (event: EventMap[K]) => void
): void
```

## 共享组件

### API 客户端

```typescript
// shared/api/client.ts
class ApiClient {
  constructor(baseUrl?: string);
  setAuthToken(token: string): void;
  clearAuthToken(): void;

  get<T>(path, config?): Promise<T>;
  post<T>(path, body?, config?): Promise<T>;
  put<T>(path, body?, config?): Promise<T>;
  patch<T>(path, body?, config?): Promise<T>;
  delete<T>(path, config?): Promise<T>;

  download(path, config?): Promise<Blob>;
  upload<T>(path, file, fieldName?, data?, config?): Promise<T>;
}

// 特性: 超时(30s)、指数退避重试、网络错误自动重试
```

### 错误处理

```typescript
// shared/types/errors.ts
enum ErrorCode {
  // 通用 (1xxx)
  UNKNOWN = 1000,
  VALIDATION_ERROR = 1001,
  NOT_FOUND = 1002,
  // ...

  // 训练任务 (2xxx)
  JOB_NOT_FOUND = 2000,
  JOB_QUOTA_EXCEEDED = 2003,
  // ...

  // 数据集 (3xxx)
  // 检查点 (4xxx)
  // 模型 (5xxx)
  // 资源配额 (6xxx)
  // 开发空间 (7xxx)
  // 集群 (8xxx)
  // 网络 (9xxx)
}

class AppError extends Error {
  code: ErrorCode;
  status: number;
  details?: Record<string, unknown>;
  fieldErrors?: FieldError[];
  traceId?: string;

  is(code: ErrorCode): boolean;
  isValidationError(): boolean;
  isUnauthorized(): boolean;
  isForbidden(): boolean;
  isNotFound(): boolean;
  isNetworkError(): boolean;

  static fromApiResponse(response, cause?): AppError;
  static fromResponse(response): Promise<AppError>;
}
```

### 通用 Hooks

```typescript
// shared/hooks/
useEntity<T>(id, fetcher)       // 实体操作
usePagination(options)          // 分页逻辑
useDebounce<T>(value, delay)    // 防抖
useLocalStorage<T>(key, init)   // 本地存储
```

## 布局系统

```typescript
// layouts/MainLayout/
<AppLayout>
  <TopNavigation />     // 固定头部 + 用户菜单
  <Navigation />        // 侧边栏菜单
  <BreadcrumbGroup />   // 面包屑
  <Content>
    <Outlet />          // 页面内容
  </Content>
</AppLayout>
```

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | TypeScript | 5.3+ |
| 框架 | React | 18.2 |
| 构建 | Vite | 5.0+ |
| 路由 | React Router | 6.21 |
| 状态 | Zustand | 4.4.7 |
| 数据 | TanStack Query | 5.17 |
| UI | AWS Cloudscape | 3.0.0 |
| 测试 | Vitest + Testing Library | - |
| E2E | Playwright | 1.57+ |
| Lint | ESLint | 8.56 |

## 命令参考

```bash
npm run dev           # 开发服务器
npm run build         # 生产构建
npm test              # 单元测试
npm run test:coverage # 覆盖率
npm run test:e2e      # E2E 测试
npm run lint          # ESLint
```

## 关键文件路径

| 用途 | 路径 |
|------|------|
| 应用入口 | `frontend/src/app/main.tsx` |
| 路由配置 | `frontend/src/app/router/index.tsx` |
| 全局 Providers | `frontend/src/app/providers/index.tsx` |
| Query Keys | `frontend/src/lib/query/queryKeys.ts` |
| API 客户端 | `frontend/src/shared/api/client.ts` |
| 事件总线 | `frontend/src/shared/events/eventBus.ts` |
| 错误类型 | `frontend/src/shared/types/errors.ts` |
| E2E 测试 | `frontend/e2e/tests/` |
