/**
 * Resource Limit Config API
 */

import type {
  ResourceLimitConfig,
  ResourceLimitConfigListResponse,
  ResourceLimitConfigFilters,
  CreateResourceLimitConfigRequest,
  UpdateResourceLimitConfigRequest,
} from './types';

const API_BASE = '/api/v1';

/**
 * 获取认证请求头
 */
function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
  };
}

/**
 * 获取资源限制配置列表
 */
export async function fetchResourceLimitConfigs(
  filters: ResourceLimitConfigFilters = {}
): Promise<ResourceLimitConfigListResponse> {
  const params = new URLSearchParams();
  if (filters.role) params.append('role', filters.role);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));

  const queryString = params.toString();
  const url = `${API_BASE}/resource-limit-configs${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch resource limit configs: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建资源限制配置
 */
export async function createResourceLimitConfig(
  data: CreateResourceLimitConfigRequest
): Promise<ResourceLimitConfig> {
  const response = await fetch(`${API_BASE}/resource-limit-configs`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create config: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新资源限制配置
 */
export async function updateResourceLimitConfig(
  id: number,
  data: UpdateResourceLimitConfigRequest
): Promise<ResourceLimitConfig> {
  const response = await fetch(`${API_BASE}/resource-limit-configs/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update config: ${response.status}`);
  }

  return response.json();
}
