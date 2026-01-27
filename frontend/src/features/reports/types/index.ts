/**
 * Reports module type definitions.
 * Maps to backend schemas: src/modules/billing/
 *
 * 报表模块 - 成本分析和资源使用报表
 */

// === Enums ===

export type GroupBy = 'category' | 'user' | 'project' | 'resource_type' | 'day' | 'week' | 'month';

export type CostCategory =
  | 'compute'
  | 'storage'
  | 'network'
  | 'data_transfer'
  | 'other';

export type ResourceCostType = 'training_job' | 'space' | 'storage' | 'cluster';

// === Cost Analysis Types ===

export interface CostSummary {
  total_cost_usd: number;
  compute_cost_usd: number;
  storage_cost_usd: number;
  network_cost_usd: number;
  data_transfer_cost_usd: number;
  other_cost_usd: number;
  period_start: string;
  period_end: string;
}

export interface CostBreakdown {
  category: CostCategory;
  name: string;
  cost_usd: number;
  percentage: number;
  item_count?: number;
}

export interface DailyCost {
  date: string;
  total_cost_usd: number;
  compute_cost_usd: number;
  storage_cost_usd: number;
  network_cost_usd: number;
  other_cost_usd: number;
}

// === Resource Usage Types ===

/**
 * 资源使用汇总 (概要统计)
 */
export interface ResourceUsageSummary {
  total_gpu_hours: number;
  total_cpu_hours: number;
  total_memory_gb_hours: number;
  total_storage_gb_hours: number;
  total_jobs_count: number;
  active_jobs_count: number;
  completed_jobs_count: number;
  failed_jobs_count: number;
  // 简化版字段 (用于报表表格)
  total_job_count?: number;
}

/**
 * 资源使用项 (按维度聚合的数据行)
 * 用于报表表格展示
 */
export interface ResourceUsageItem {
  dimension_key: string;           // user_id 或 project_id 或 date
  dimension_label: string;         // 用户名 或 项目名 或 日期
  total_gpu_hours: number;
  total_cpu_hours: number;
  total_memory_gb_hours: number;
  job_count: number;
  avg_duration_hours: number;
}

export interface ResourceUsageBreakdown {
  resource_type: ResourceCostType;
  name: string;
  gpu_hours: number;
  cpu_hours: number;
  memory_gb_hours: number;
  storage_gb_hours: number;
  count: number;
  percentage: number;
}

export interface DailyResourceUsage {
  date: string;
  gpu_hours: number;
  cpu_hours: number;
  memory_gb_hours: number;
  storage_gb_hours: number;
  job_count: number;
}

// === Filter Types ===

export interface CostAnalysisFilters {
  start_date?: string;
  end_date?: string;
  group_by?: GroupBy;
  user_id?: number;
  project_id?: number;
}

export interface ResourceUsageFilters {
  start_date?: string;
  end_date?: string;
  group_by?: GroupBy;
  user_id?: number;
  resource_type?: ResourceCostType;
}

export interface ReportExportFilters {
  report_type: 'cost_analysis' | 'resource_usage';
  format: 'csv' | 'json';
  start_date?: string;
  end_date?: string;
  group_by?: GroupBy;
}

// === Response Types ===

export interface CostAnalysisResponse {
  summary: CostSummary;
  breakdown: CostBreakdown[];
  daily_costs: DailyCost[];
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * 资源使用报表响应 (完整版)
 */
export interface ResourceUsageResponse {
  summary: ResourceUsageSummary;
  breakdown: ResourceUsageBreakdown[];
  daily_usage: DailyResourceUsage[];
  period: {
    start_date: string;
    end_date: string;
  };
  // 扩展字段 (用于表格展示)
  items?: ResourceUsageItem[];
}

// === UI Helper Types ===

export const GROUP_BY_LABELS: Record<GroupBy, string> = {
  category: '按类别',
  user: '按用户',
  project: '按项目',
  resource_type: '按资源类型',
  day: '按天',
  week: '按周',
  month: '按月',
};

export const COST_CATEGORY_LABELS: Record<CostCategory, string> = {
  compute: '计算',
  storage: '存储',
  network: '网络',
  data_transfer: '数据传输',
  other: '其他',
};

export const COST_CATEGORY_COLORS: Record<CostCategory, string> = {
  compute: '#3184c2',
  storage: '#1d8102',
  network: '#9469d6',
  data_transfer: '#d45b07',
  other: '#879596',
};

export const RESOURCE_TYPE_LABELS: Record<ResourceCostType, string> = {
  training_job: '训练任务',
  space: '开发空间',
  storage: '存储',
  cluster: '集群',
};

export const RESOURCE_TYPE_COLORS: Record<ResourceCostType, string> = {
  training_job: '#3184c2',
  space: '#1d8102',
  storage: '#9469d6',
  cluster: '#d45b07',
};
