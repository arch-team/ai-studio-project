/**
 * 资源配额 E2E 测试 Mock 数据
 */

import type {
  ResourceLimitConfig,
  ResourceLimitConfigListResponse,
} from '../../src/features/resource-quotas/types';

/**
 * Mock 资源限制配置列表
 */
export const mockResourceLimitConfigs: ResourceLimitConfig[] = [
  {
    id: 1,
    config_name: '管理员配额',
    role: 'admin',
    project_id: null,
    max_gpu_per_job: 8,
    max_cpu_per_job: 64,
    max_memory_gb_per_job: 256,
    max_storage_gb_per_job: 1000,
    max_nodes_per_job: 4,
    priority_default: 'high',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
  },
  {
    id: 2,
    config_name: '工程师配额',
    role: 'engineer',
    project_id: null,
    max_gpu_per_job: 4,
    max_cpu_per_job: 32,
    max_memory_gb_per_job: 128,
    max_storage_gb_per_job: 500,
    max_nodes_per_job: 2,
    priority_default: 'medium',
    created_at: '2026-01-16T10:00:00Z',
    updated_at: '2026-01-16T10:00:00Z',
  },
  {
    id: 3,
    config_name: '项目经理配额',
    role: 'project_manager',
    project_id: null,
    max_gpu_per_job: 2,
    max_cpu_per_job: 16,
    max_memory_gb_per_job: 64,
    max_storage_gb_per_job: 200,
    max_nodes_per_job: 1,
    priority_default: 'low',
    created_at: '2026-01-17T10:00:00Z',
    updated_at: '2026-01-17T10:00:00Z',
  },
  {
    id: 4,
    config_name: '查看者配额',
    role: 'viewer',
    project_id: null,
    max_gpu_per_job: 1,
    max_cpu_per_job: 8,
    max_memory_gb_per_job: 32,
    max_storage_gb_per_job: 100,
    max_nodes_per_job: 1,
    priority_default: 'low',
    created_at: '2026-01-18T10:00:00Z',
    updated_at: '2026-01-18T10:00:00Z',
  },
];

/**
 * 创建分页响应
 */
export function createResourceLimitConfigResponse(
  items: ResourceLimitConfig[] = mockResourceLimitConfigs,
  page: number = 1,
  pageSize: number = 20,
): ResourceLimitConfigListResponse {
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const paginatedItems = items.slice(start, end);

  return {
    items: paginatedItems,
    total: items.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(items.length / pageSize),
  };
}

/**
 * 生成唯一的配置名称（用于测试创建）
 */
export function generateTestConfigName(): string {
  const timestamp = Date.now();
  return `e2e-test-config-${timestamp}`;
}
