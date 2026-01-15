/**
 * Resource Limit Config API
 */

import type {
  ResourceLimitConfigListResponse,
  ResourceLimitConfigFilters,
} from './types';

const API_BASE = '/api/v1';

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
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch resource limit configs: ${response.status}`);
  }

  return response.json();
}
