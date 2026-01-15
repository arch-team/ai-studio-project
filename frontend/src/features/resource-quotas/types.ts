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
