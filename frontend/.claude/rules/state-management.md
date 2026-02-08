> **职责**: 状态管理规范 - React Query (服务端)、Zustand (客户端)、表单状态、EventBus 联动

# 状态管理规范 (State Management Standards)

---

## 0. 速查卡片

### 状态类型决策表

| 数据类型 | 推荐方案 | 示例 |
|---------|---------|------|
| 服务端数据 | React Query (TanStack Query) | 训练任务列表、数据集详情 |
| 全局 UI 状态 | Zustand | 主题、侧边栏展开状态 |
| 用户会话 | Zustand (内存，不持久化) | 登录状态、Token |
| 表单状态 | React Hook Form + Zod | 创建任务表单、配置表单 |
| URL 状态 | React Router | 路由参数、查询参数 |
| 组件局部状态 | useState | 下拉菜单开关 |
| 复杂组件状态 | useReducer | 多步骤向导 |

### 决策流程图

```
数据来自 API？ ──是──► React Query (TanStack Query)
      │
     否
      ↓
需要反映在 URL？ ──是──► React Router (searchParams)
      │
     否
      ↓
需要跨组件共享？ ──是──► Zustand Store
      │                    ↓
     否              需要持久化？ ──是──► Zustand + persist (⚠️ 禁止持久化敏感数据)
      ↓
组件状态复杂？ ──是──► useReducer
      │
     否
      ↓
useState
```

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
  datasets: {
    all: ['datasets'] as const,
    lists: () => [...queryKeys.datasets.all, 'list'] as const,
    list: (filters: DatasetFilters) => [...queryKeys.datasets.lists(), filters] as const,
    details: () => [...queryKeys.datasets.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.datasets.details(), id] as const,
  },
  models: {
    all: ['models'] as const,
    lists: () => [...queryKeys.models.all, 'list'] as const,
    list: (filters: ModelFilters) => [...queryKeys.models.lists(), filters] as const,
    details: () => [...queryKeys.models.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.models.details(), id] as const,
  },
  // ... 其他模块
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

---

## 2. Zustand (客户端状态)

### 2.1 Auth Store（内存存储 - 安全）

> **安全说明**: Token 等敏感数据**禁止**存入 localStorage（XSS 可读取）。
> 推荐 httpOnly Cookie（需后端配合）或内存存储。详见 [security.md](security.md) §2。

```typescript
// features/auth/store/authStore.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

// Token 仅保存在内存中，刷新页面后需重新认证（更安全）
export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setToken: (token) => set({ token }),
  logout: () => set({ user: null, token: null, isAuthenticated: false }),
}));
```

### 2.2 UI Store（持久化非敏感状态）

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

### 2.3 Selector Hooks（性能关键）

```typescript
// 细粒度 selector - 避免不必要的重渲染
export const useAuth = () =>
  useAuthStore((state) => ({
    user: state.user,
    isAuthenticated: state.isAuthenticated,
  }));

export const useAuthToken = () => useAuthStore((state) => state.token);

export const useAuthActions = () =>
  useAuthStore((state) => ({
    setUser: state.setUser,
    setToken: state.setToken,
    logout: state.logout,
  }));
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

export function CreateJobForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CreateJobFormData>({
    resolver: zodResolver(createJobSchema),
  });

  const createJob = useCreateTrainingJob();

  const onSubmit = async (data: CreateJobFormData) => {
    await createJob.mutateAsync(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Cloudscape Form 组件 */}
    </form>
  );
}
```

---

## 4. EventBus 联动

> 模块间通信模式决策（何时用 EventBus vs Query Invalidation vs Shared Store）详见 [architecture.md](architecture.md) §4.1

### 4.1 EventMap 定义

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

  // 数据集删除时，自动刷新相关列表
  useEventSubscription('dataset:deleted', () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.datasets.lists() });
  });
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

```typescript
// ❌ 错误 - 在组件中直接获取整个 store
const { user, token, theme, sidebar } = useAuthStore();

// ✅ 正确 - 使用细粒度 selector 只订阅需要的字段
const user = useAuthStore((s) => s.user);
const theme = useUIStore((s) => s.theme);
```
