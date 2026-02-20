/**
 * 资源限制配置 API
 *
 * 使用共享 apiClient，与其他模块保持一致。
 */

import { apiClient } from '@shared/api';
import type {
  ResourceLimitConfig,
  ResourceLimitConfigListResponse,
  ResourceLimitConfigFilters,
  CreateResourceLimitConfigRequest,
  UpdateResourceLimitConfigRequest,
} from '../types';

/**
 * 获取资源限制配置列表
 */
export async function fetchResourceLimitConfigs(
  filters: ResourceLimitConfigFilters = {}
): Promise<ResourceLimitConfigListResponse> {
  const params: Record<string, string> = {};
  if (filters.role) params.role = filters.role;
  if (filters.page) params.page = String(filters.page);
  if (filters.page_size) params.page_size = String(filters.page_size);

  return apiClient.get<ResourceLimitConfigListResponse>('/resource-limit-configs', { params });
}

/**
 * 创建资源限制配置
 */
export async function createResourceLimitConfig(
  data: CreateResourceLimitConfigRequest
): Promise<ResourceLimitConfig> {
  return apiClient.post<ResourceLimitConfig>('/resource-limit-configs', data);
}

/**
 * 更新资源限制配置
 */
export async function updateResourceLimitConfig(
  id: number,
  data: UpdateResourceLimitConfigRequest
): Promise<ResourceLimitConfig> {
  return apiClient.put<ResourceLimitConfig>(`/resource-limit-configs/${id}`, data);
}
