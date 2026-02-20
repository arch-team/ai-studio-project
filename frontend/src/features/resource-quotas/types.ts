/**
 * Resource Quotas Module Types
 *
 * 包含资源限制配置和配额使用量的类型定义
 */

// ===== ResourceQuota 实体类型 (与后端 Kueue 同步) =====

export interface ResourceQuota {
  id: number;
  name: string;
  description: string | null;
  quota_type: "user" | "team" | "project";
  max_cpu_cores: number;
  reserved_cpu_cores: number;
  max_gpu_count: number;
  reserved_gpu_count: number;
  gpu_types: string[] | null;
  max_memory_gb: number;
  reserved_memory_gb: number;
  max_storage_gb: number | null;
  max_concurrent_jobs: number;
  max_total_jobs: number | null;
  max_spot_instances: number;
  status: "active" | "suspended" | "expired";
  valid_from: string;
  valid_until: string | null;
  created_at: string;
  // 使用量 (从 Kueue 同步)
  used_cpu_cores?: number;
  used_gpu_count?: number;
  used_memory_gb?: number;
  current_concurrent_jobs?: number;
}

export interface QuotaUsage {
  type: "cpu" | "gpu" | "memory" | "jobs";
  used: number;
  reserved: number;
  max: number;
  unit: string;
}

// ===== Resource Limit Config 类型 =====

/**
 * Resource Limit Config Types
 */

export type UserRole = 'admin' | 'project_manager' | 'engineer' | 'viewer';
export type Priority = 'high' | 'medium' | 'low';

export interface ResourceLimitConfig {
  id: number;
  config_name: string;
  role: UserRole;
  project_id: number | null;
  max_gpu_per_job: number;
  max_cpu_per_job: number;
  max_memory_gb_per_job: number;
  max_storage_gb_per_job: number;
  max_nodes_per_job: number;
  priority_default: Priority;
  created_at: string;
  updated_at: string;
}

export interface ResourceLimitConfigListResponse {
  items: ResourceLimitConfig[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ResourceLimitConfigFilters {
  role?: UserRole;
  page?: number;
  page_size?: number;
}

/**
 * 创建资源限制配置请求
 */
export interface CreateResourceLimitConfigRequest {
  config_name: string;
  role: UserRole;
  project_id?: number | null;
  max_gpu_per_job: number;
  max_cpu_per_job: number;
  max_memory_gb_per_job: number;
  max_storage_gb_per_job: number;
  max_nodes_per_job: number;
  priority_default: Priority;
}

/**
 * 更新资源限制配置请求
 */
export interface UpdateResourceLimitConfigRequest {
  config_name?: string;
  role?: UserRole;
  project_id?: number | null;
  max_gpu_per_job?: number;
  max_cpu_per_job?: number;
  max_memory_gb_per_job?: number;
  max_storage_gb_per_job?: number;
  max_nodes_per_job?: number;
  priority_default?: Priority;
}

/**
 * 角色显示标签
 */
export const ROLE_LABELS: Record<UserRole, string> = {
  admin: '管理员',
  project_manager: '项目经理',
  engineer: '工程师',
  viewer: '查看者',
};

/**
 * 优先级显示标签
 */
export const PRIORITY_LABELS: Record<Priority, string> = {
  high: '高',
  medium: '中',
  low: '低',
};

/**
 * 优先级状态颜色
 */
export const PRIORITY_STATUS: Record<Priority, 'success' | 'warning' | 'info'> = {
  high: 'success',
  medium: 'warning',
  low: 'info',
};
