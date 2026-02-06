/**
 * Space API client functions.
 */

import { apiClient } from '@shared/api/client';
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
      space_type: filters.space_type,
      status: filters.status,
      owner_id: filters.owner_id,
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
export async function fetchSpace(id: number): Promise<SpaceDetail> {
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
  id: number,
  data: UpdateSpaceRequest
): Promise<SpaceDetail> {
  return apiClient.patch<SpaceDetail>(`/spaces/${id}`, data);
}

/**
 * Delete a space.
 */
export async function deleteSpace(id: number): Promise<void> {
  return apiClient.delete(`/spaces/${id}`);
}

/**
 * Start a stopped space.
 */
export async function startSpace(id: number): Promise<SpaceDetail> {
  return apiClient.post<SpaceDetail>(`/spaces/${id}/start`);
}

/**
 * Stop a running space.
 */
export async function stopSpace(id: number): Promise<SpaceDetail> {
  return apiClient.post<SpaceDetail>(`/spaces/${id}/stop`);
}

/**
 * Open space URL (redirect to JupyterLab/VS Code).
 */
export async function openSpace(id: number): Promise<{ url: string }> {
  return apiClient.post<{ url: string }>(`/spaces/${id}/open`);
}
