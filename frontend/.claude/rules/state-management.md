> **职责**: 状态管理规范 - React Query (服务端)、Zustand (客户端)、表单状态、EventBus 联动

# 状态管理规范 (State Management Standards)

---

## 0. 速查卡片

### 状态类型决策表

| 数据类型 | 推荐方案 | 示例 |
|---------|---------|------|
| 服务端数据 | React Query (TanStack Query) | 训练任务列表、数据集详情 |
| 全局 UI 状态 | Zustand (⚠️ 禁止持久化敏感数据) | 主题、侧边栏展开状态 |
| 用户会话 | Zustand (内存，不持久化) | 登录状态、Token |
| 表单状态 | React Hook Form + Zod | 创建任务表单、配置表单 |
| URL 状态 | React Router | 路由参数、查询参数 |
| 组件局部状态 | useState | 下拉菜单开关 |
| 复杂组件状态 | useReducer | 多步骤向导 |

### 文件位置速查

| 状态类型 | 位置 |
|---------|------|
| Query Keys 工厂 | `lib/query/queryKeys.ts` |
| Feature Query Hooks | `features/{module}/api/queries.ts` |
| 全局 Store | `store/slices/{store}Slice.ts` |
| Auth Store | `features/auth/store/` (特殊，可跨模块导入) |
| Feature 类型 | `features/{module}/types/index.ts` |

---

## 1. React Query (服务端状态)

### 1.1 全局 Query Keys 工厂

> **本项目使用集中式 queryKeys 工厂**，统一管理所有模块的缓存键

```typescript
// lib/query/queryKeys.ts
export const queryKeys = {
  trainingJobs: {
    all: ['training-jobs'] as const,
    lists: () => [...queryKeys.trainingJobs.all, 'list'] as const,
    list: (filters: TrainingJobFilters) => [...queryKeys.trainingJobs.lists(), filters] as const,
    details: () => [...queryKeys.trainingJobs.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.trainingJobs.details(), id] as const,
  },
  // datasets, models 等其他模块遵循相同结构 (all/lists/list/details/detail)
};
```

### 1.2 Query Hook 模板

```typescript
// features/{module}/api/queries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';

export function useTrainingJobs(filters: TrainingJobFilters = {}) {
  return useQuery({
    queryKey: queryKeys.trainingJobs.list(filters),
    queryFn: () => fetchTrainingJobs(filters),
  });
}

export function useTrainingJob(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.trainingJobs.detail(String(id!)),
    queryFn: () => fetchTrainingJob(id!),
    enabled: id !== undefined,
  });
}

export function useCreateTrainingJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTrainingJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}
```

### 1.3 乐观更新模式

```typescript
export function useUpdateTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTrainingJob,
    onMutate: async (newJob) => {
      // 1. 取消正在进行的查询
      await queryClient.cancelQueries({ queryKey: queryKeys.trainingJobs.detail(newJob.id) });
      // 2. 保存旧数据
      const previous = queryClient.getQueryData(queryKeys.trainingJobs.detail(newJob.id));
      // 3. 乐观更新
      queryClient.setQueryData(queryKeys.trainingJobs.detail(newJob.id), newJob);
      return { previous };
    },
    onError: (_err, _newJob, context) => {
      // 回滚
      queryClient.setQueryData(queryKeys.trainingJobs.detail(_newJob.id), context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}
```

### 1.4 全局错误处理配置

> 错误类型体系（ErrorCode, AppError）定义详见 [architecture.md](architecture.md) §6.3

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

---

## 2. Zustand (客户端状态)

### 2.1 Auth Store（内存存储 - 安全）

> **安全说明**: Token 禁止存入 localStorage，推荐 httpOnly Cookie 或内存存储。详见 [security.md](security.md) §2。

```typescript
// features/auth/store/authStore.ts
// ⚠️ Token 仅保存在内存中，不使用 persist，刷新页面后需重新认证
export const useAuthStore = create<AuthState>()((set) => ({
  user: null, token: null, isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setToken: (token) => set({ token }),
  logout: () => set({ user: null, token: null, isAuthenticated: false }),
}));
```

### 2.2 UI Store（持久化非敏感状态）

```typescript
// store/slices/uiSlice.ts — persist 中间件包装模式
// 非敏感 UI 状态使用 persist 中间件，key 为 'ui-storage'
export const useUIStore = create<UIState>()(
  persist((set) => ({ /* theme, sidebarCollapsed, ... */ }), { name: 'ui-storage' })
);
```

### 2.3 Selector Hooks（性能关键）

```typescript
// 细粒度 selector - 避免不必要的重渲染
// 按「数据 / actions」分离，避免 action 变化触发数据消费组件重渲染
export const useAuth = () => useAuthStore((s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }));
export const useAuthActions = () => useAuthStore((s) => ({ setUser: s.setUser, logout: s.logout }));
```

---

## 3. React Hook Form + Zod (表单状态)

```typescript
// features/training/components/CreateJobForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const createJobSchema = z.object({
  job_name: z.string().min(1, '请输入任务名称').max(128, '名称不超过128字符'),
  instance_type: z.string().min(1, '请选择实例类型'),
  instance_count: z.number().min(1).max(64),
});

type CreateJobFormData = z.infer<typeof createJobSchema>;

// useForm 配置核心: zodResolver 绑定 + mutateAsync 提交
const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CreateJobFormData>({
  resolver: zodResolver(createJobSchema),
});
// JSX: <form onSubmit={handleSubmit(onSubmit)}> + Cloudscape Form 组件
```

---

## 4. EventBus 联动

> 模块间通信模式决策（何时用 EventBus vs Query Invalidation vs Shared Store）详见 [architecture.md](architecture.md) §4.1

### 4.1 EventMap 定义

```typescript
// shared/events/eventBus.ts
export interface EventMap {
  'training-job:created': { jobId: number; jobName: string };  // 对象 payload
  'auth:logged-out': void;                                      // 无 payload
  'notification:show': { type: 'success' | 'error'; message: string }; // 联合类型 payload
  // 其他事件 (training-job:completed/failed, dataset:deleted, auth:logged-in) 遵循相同模式
}
```

### 4.2 发布事件

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

### 4.3 订阅事件 + Query Invalidation 联动

```typescript
// features/monitoring/hooks/useMonitoringSubscription.ts
import { useEventSubscription } from '@shared/events';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';

export function useMonitoringSubscription() {
  const queryClient = useQueryClient();

  // 训练任务完成时，自动刷新监控数据
  useEventSubscription('training-job:completed', () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
  });
  // 其他事件 (dataset:deleted 等) 同理: useEventSubscription + invalidateQueries
}
```

---

## 5. 最佳实践

```typescript
// ❌ 错误 - 把所有东西都放全局
const useStore = create((set) => ({
  modalOpen: false,        // 应该是组件状态 (useState)
  formData: {},            // 应该用 React Hook Form
  users: [],               // 应该用 React Query
  currentPage: 1,          // 应该用 URL 状态 (searchParams)
}));

// ✅ 正确 - 只把真正需要全局共享的放 Zustand
const useUIStore = create((set) => ({
  sidebarOpen: true,       // 确实需要跨组件共享
  theme: 'light',          // 确实需要跨组件共享
}));
```

> Zustand 细粒度 Selector 示例见 §2.3
