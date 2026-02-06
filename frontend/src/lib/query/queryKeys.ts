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
 * 通用实体 Query Keys 工厂
 *
 * 生成标准 CRUD 实体的 all/lists/list/details/detail 键结构
 */
function createEntityKeys<T extends string>(entity: T) {
  return {
    all: [entity] as const,
    lists: () => [entity, 'list'] as const,
    list: (filters: Record<string, unknown>) => [entity, 'list', filters] as const,
    details: () => [entity, 'detail'] as const,
    detail: (id: string) => [entity, 'detail', id] as const,
  };
}

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
   * 训练任务 Query Keys（含额外 logs/metrics 扩展）
   */
  trainingJobs: {
    ...createEntityKeys('trainingJobs'),
    logs: (jobId: number, options?: Record<string, unknown>) =>
      ['trainingJobs', 'logs', jobId, options] as const,
    metrics: (jobId: number, options?: Record<string, unknown>) =>
      ['trainingJobs', 'metrics', jobId, options] as const,
  },

  /**
   * 数据集 Query Keys
   */
  datasets: createEntityKeys('datasets'),

  /**
   * 检查点 Query Keys
   */
  checkpoints: createEntityKeys('checkpoints'),

  /**
   * 模型 Query Keys（含版本扩展）
   */
  models: {
    ...createEntityKeys('models'),
    versionsAll: () => ['models', 'versions'] as const,
    versions: (modelId: number, options?: Record<string, unknown>) =>
      ['models', 'versions', modelId, options] as const,
  },

  /**
   * 资源配额 Query Keys
   */
  resourceQuotas: createEntityKeys('resourceQuotas'),

  /**
   * 用户 Query Keys（含 me 扩展）
   */
  users: {
    ...createEntityKeys('users'),
    me: () => ['users', 'me'] as const,
  },

  /**
   * 开发空间 Query Keys
   */
  spaces: createEntityKeys('spaces'),

  /**
   * 审计日志 Query Keys
   */
  audit: createEntityKeys('audit'),

  /**
   * 计费 Query Keys
   */
  billing: {
    all: ['billing'] as const,
    report: (filters: Record<string, unknown>) =>
      ['billing', 'report', filters] as const,
    users: (filters: Record<string, unknown>) =>
      ['billing', 'users', filters] as const,
    userDetail: (userId: string, filters: Record<string, unknown>) =>
      ['billing', 'users', userId, filters] as const,
    resources: (filters: Record<string, unknown>) =>
      ['billing', 'resources', filters] as const,
  },

  /**
   * 监控 Query Keys
   */
  monitoring: {
    all: ['monitoring'] as const,
    // 集群
    clustersAll: () => ['monitoring', 'clusters'] as const,
    clusters: (filters: Record<string, unknown>) =>
      ['monitoring', 'clusters', filters] as const,
    clusterDetail: (id: string) =>
      ['monitoring', 'clusters', id] as const,
    clusterNodes: (clusterId: string) =>
      ['monitoring', 'clusters', clusterId, 'nodes'] as const,
    clusterMetrics: (clusterId: string, filters: Record<string, unknown>) =>
      ['monitoring', 'clusters', clusterId, 'metrics', filters] as const,
    // 指标
    metricsAll: () => ['monitoring', 'metrics'] as const,
    metrics: (filters: Record<string, unknown>) =>
      ['monitoring', 'metrics', filters] as const,
    // 资源利用率
    utilizationAll: () => ['monitoring', 'utilization'] as const,
    utilization: (clusterId: string) =>
      ['monitoring', 'utilization', clusterId] as const,
    // 告警
    alertsAll: () => ['monitoring', 'alerts'] as const,
    alerts: (filters: Record<string, unknown>) =>
      ['monitoring', 'alerts', filters] as const,
  },
} as const;

/**
 * Query Key 类型导出
 */
export type QueryKeys = typeof queryKeys;
