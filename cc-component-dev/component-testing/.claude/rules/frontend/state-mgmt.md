---
paths:
  - "frontend/src/**/*.{ts,tsx}"
---

# 状态管理规范

## 分层原则

| 状态类型 | 工具 | 用途 |
|---------|------|------|
| 服务器状态 | TanStack Query | API 数据、缓存、同步、乐观更新 |
| 客户端状态 | Zustand | UI 状态、用户偏好、主题设置 |

## Query Key 工厂

使用 `@lib/query/queryKeys` 管理缓存键:

```typescript
// 键层级结构
queryKeys.trainingJobs.all          // ['trainingJobs']
queryKeys.trainingJobs.lists()      // ['trainingJobs', 'list']
queryKeys.trainingJobs.list(filters) // ['trainingJobs', 'list', filters]
queryKeys.trainingJobs.details()    // ['trainingJobs', 'detail']
queryKeys.trainingJobs.detail(id)   // ['trainingJobs', 'detail', id]

// 同样适用于: datasets, checkpoints, models, resourceQuotas, users
```

## 路径别名

| 别名 | 路径 | 用途 |
|------|------|------|
| `@/` | `src/` | 通用引用 |
| `@features/` | `src/features/` | 功能模块 |
| `@shared/` | `src/shared/` | 共享组件 |
| `@lib/` | `src/lib/` | 基础设施 |
| `@store/` | `src/store/` | 全局状态 |

## 使用示例

```typescript
// TanStack Query - 服务器状态
const { data, isLoading } = useQuery({
  queryKey: queryKeys.trainingJobs.list({ status: 'running' }),
  queryFn: () => fetchTrainingJobs({ status: 'running' }),
});

// Zustand - 客户端状态
const theme = useUIStore((state) => state.theme);
```
