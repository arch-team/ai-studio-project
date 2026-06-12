/**
 * Space API client functions.
 *
 * 契约对齐后端 src/modules/spaces/api/endpoints.py：
 * Space ID 为 UUID 字符串；后端无独立 /open 端点。
 */

import { apiClient } from '@shared/api';
import type {
  SpaceDetail,
  SpaceListResponse,
  SpaceFilters,
  CreateSpaceRequest,
  UpdateSpaceRequest,
} from '../types';

/**
 * Fetch paginated list of spaces.
 */
export async function fetchSpaces(
  filters: SpaceFilters = {}
): Promise<SpaceListResponse> {
  return apiClient.get<SpaceListResponse>('/spaces', {
    params: {
      status: filters.status,
      page: filters.page,
      page_size: filters.page_size,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Fetch a single space by ID.
 */
export async function fetchSpace(id: string): Promise<SpaceDetail> {
  return apiClient.get<SpaceDetail>(`/spaces/${id}`);
}

/**
 * Create a new space.
 */
export async function createSpace(
  data: CreateSpaceRequest
): Promise<SpaceDetail> {
  return apiClient.post<SpaceDetail>('/spaces', data);
}

/**
 * Update an existing space.
 */
export async function updateSpace(
  id: string,
  data: UpdateSpaceRequest
): Promise<SpaceDetail> {
  return apiClient.patch<SpaceDetail>(`/spaces/${id}`, data);
}

/**
 * Delete a space.
 */
export async function deleteSpace(id: string): Promise<void> {
  return apiClient.delete(`/spaces/${id}`);
}

/**
 * Start a stopped space.
 */
export async function startSpace(id: string): Promise<SpaceDetail> {
  return apiClient.post<SpaceDetail>(`/spaces/${id}/start`);
}

/**
 * 签发空间 IDE 的免登录访问 URL（约 5 分钟内有效，仅供即时跳转）.
 */
export async function fetchSpaceAccessUrl(
  id: string
): Promise<{ url: string }> {
  return apiClient.post<{ url: string }>(`/spaces/${id}/access-url`);
}

/**
 * Stop a running space.
 */
export async function stopSpace(id: string): Promise<SpaceDetail> {
  return apiClient.post<SpaceDetail>(`/spaces/${id}/stop`);
}
