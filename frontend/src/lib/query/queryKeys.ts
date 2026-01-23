/**
 * Query Keys Factory
 *
 * Task: T020 - 配置 TanStack Query
 * TDD Step 2: Green - 实现代码
 *
 * 使用工厂模式创建类型安全的 Query Keys
 * 遵循 TanStack Query 的 Query Key Factory 最佳实践
 *
 * @see https://tanstack.com/query/v5/docs/react/guides/query-keys
 */

/**
 * Query Keys 工厂
 *
 * 层级结构:
 * - all: 顶级键，用于 invalidateQueries 整个实体
 * - lists(): 列表查询基础键
 * - list(filters): 带过滤条件的列表查询键
 * - details(): 详情查询基础键
 * - detail(id): 特定实体详情查询键
 */
export const queryKeys = {
  /**
   * 训练任务 Query Keys
   */
  trainingJobs: {
    all: ['trainingJobs'] as const,
    lists: () => [...queryKeys.trainingJobs.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.trainingJobs.lists(), filters] as const,
    details: () => [...queryKeys.trainingJobs.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.trainingJobs.details(), id] as const,
    // 训练任务日志
    logs: (jobId: number, options?: Record<string, unknown>) =>
      [...queryKeys.trainingJobs.all, 'logs', jobId, options] as const,
    // 训练任务指标
    metrics: (jobId: number, options?: Record<string, unknown>) =>
      [...queryKeys.trainingJobs.all, 'metrics', jobId, options] as const,
  },

  /**
   * 数据集 Query Keys
   */
  datasets: {
    all: ['datasets'] as const,
    lists: () => [...queryKeys.datasets.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.datasets.lists(), filters] as const,
    details: () => [...queryKeys.datasets.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.datasets.details(), id] as const,
  },

  /**
   * 检查点 Query Keys
   */
  checkpoints: {
    all: ['checkpoints'] as const,
    lists: () => [...queryKeys.checkpoints.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.checkpoints.lists(), filters] as const,
    details: () => [...queryKeys.checkpoints.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.checkpoints.details(), id] as const,
  },

  /**
   * 模型 Query Keys
   */
  models: {
    all: ['models'] as const,
    lists: () => [...queryKeys.models.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.models.lists(), filters] as const,
    details: () => [...queryKeys.models.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.models.details(), id] as const,
    // 模型版本
    versionsAll: () => [...queryKeys.models.all, 'versions'] as const,
    versions: (modelId: number, options?: Record<string, unknown>) =>
      [...queryKeys.models.versionsAll(), modelId, options] as const,
  },

  /**
   * 资源配额 Query Keys
   */
  resourceQuotas: {
    all: ['resourceQuotas'] as const,
    lists: () => [...queryKeys.resourceQuotas.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.resourceQuotas.lists(), filters] as const,
    details: () => [...queryKeys.resourceQuotas.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.resourceQuotas.details(), id] as const,
  },

  /**
   * 用户 Query Keys
   */
  users: {
    all: ['users'] as const,
    me: () => [...queryKeys.users.all, 'me'] as const,
    lists: () => [...queryKeys.users.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.users.lists(), filters] as const,
    details: () => [...queryKeys.users.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
  },

  /**
   * 开发空间 Query Keys
   */
  spaces: {
    all: ['spaces'] as const,
    lists: () => [...queryKeys.spaces.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.spaces.lists(), filters] as const,
    details: () => [...queryKeys.spaces.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.spaces.details(), id] as const,
  },

  /**
   * 审计日志 Query Keys
   */
  audit: {
    all: ['audit'] as const,
    lists: () => [...queryKeys.audit.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.audit.lists(), filters] as const,
    details: () => [...queryKeys.audit.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.audit.details(), id] as const,
  },

  /**
   * 计费 Query Keys
   */
  billing: {
    all: ['billing'] as const,
    report: (filters: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'report', filters] as const,
    users: (filters: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'users', filters] as const,
    userDetail: (userId: string, filters: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'users', userId, filters] as const,
    resources: (filters: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'resources', filters] as const,
  },

  /**
   * 监控 Query Keys
   */
  monitoring: {
    all: ['monitoring'] as const,
    // 集群
    clustersAll: () => [...queryKeys.monitoring.all, 'clusters'] as const,
    clusters: (filters: Record<string, unknown>) =>
      [...queryKeys.monitoring.clustersAll(), filters] as const,
    clusterDetail: (id: string) =>
      [...queryKeys.monitoring.clustersAll(), id] as const,
    clusterNodes: (clusterId: string) =>
      [...queryKeys.monitoring.clustersAll(), clusterId, 'nodes'] as const,
    clusterMetrics: (clusterId: string, filters: Record<string, unknown>) =>
      [...queryKeys.monitoring.clustersAll(), clusterId, 'metrics', filters] as const,
    // 指标
    metricsAll: () => [...queryKeys.monitoring.all, 'metrics'] as const,
    metrics: (filters: Record<string, unknown>) =>
      [...queryKeys.monitoring.metricsAll(), filters] as const,
    // 资源利用率
    utilizationAll: () => [...queryKeys.monitoring.all, 'utilization'] as const,
    utilization: (clusterId: string) =>
      [...queryKeys.monitoring.utilizationAll(), clusterId] as const,
    // 告警
    alertsAll: () => [...queryKeys.monitoring.all, 'alerts'] as const,
    alerts: (filters: Record<string, unknown>) =>
      [...queryKeys.monitoring.alertsAll(), filters] as const,
  },
} as const;

/**
 * Query Key 类型导出
 */
export type QueryKeys = typeof queryKeys;
