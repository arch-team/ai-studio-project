/**
 * Billing module type definitions.
 * Maps to backend schemas: src/modules/billing/
 *
 * 计费管理模块 - 成本统计和账单查询
 */

// === Enums ===

export type BillingPeriod = 'daily' | 'weekly' | 'monthly' | 'yearly';

export type CostCategory =
  | 'compute'
  | 'storage'
  | 'network'
  | 'data_transfer'
  | 'other';

export type ResourceCostType = 'training_job' | 'space' | 'storage' | 'cluster';

// === Cost Types ===

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
  cost_usd: number;
  percentage: number;
  details: CostDetail[];
}

export interface CostDetail {
  resource_type: ResourceCostType;
  resource_id: string;
  resource_name: string;
  cost_usd: number;
  usage_quantity: number;
  usage_unit: string;
  rate_per_unit: number;
}

export interface DailyCost {
  date: string;
  total_cost_usd: number;
  compute_cost_usd: number;
  storage_cost_usd: number;
  other_cost_usd: number;
}

export interface UserCostSummary {
  user_id: number;
  username: string;
  total_cost_usd: number;
  training_jobs_cost_usd: number;
  spaces_cost_usd: number;
  storage_cost_usd: number;
  training_jobs_count: number;
  total_gpu_hours: number;
}

export interface ResourceCost {
  id: number;
  resource_type: ResourceCostType;
  resource_id: string;
  resource_name: string;
  owner_id: number;
  owner_username: string | null;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  instance_type: string | null;
  gpu_count: number | null;
  compute_cost_usd: number;
  storage_cost_usd: number;
  total_cost_usd: number;
  created_at: string;
}

// === Filter Types ===

export interface CostFilters {
  period?: BillingPeriod;
  start_date?: string;
  end_date?: string;
  user_id?: number;
  resource_type?: ResourceCostType;
  category?: CostCategory;
}

export interface ResourceCostFilters {
  resource_type?: ResourceCostType;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  min_cost?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'total_cost_usd' | 'created_at' | 'duration_seconds';
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface CostReportResponse {
  summary: CostSummary;
  breakdown: CostBreakdown[];
  daily_costs: DailyCost[];
}

export interface UserCostListResponse {
  items: UserCostSummary[];
  total: number;
  total_cost_usd: number;
}

export interface ResourceCostListResponse {
  items: ResourceCost[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  total_cost_usd: number;
}

// === UI Helper Types ===

export const BILLING_PERIOD_LABELS: Record<BillingPeriod, string> = {
  daily: '按天',
  weekly: '按周',
  monthly: '按月',
  yearly: '按年',
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

export const RESOURCE_COST_TYPE_LABELS: Record<ResourceCostType, string> = {
  training_job: '训练任务',
  space: '开发空间',
  storage: '存储',
  cluster: '集群',
};
