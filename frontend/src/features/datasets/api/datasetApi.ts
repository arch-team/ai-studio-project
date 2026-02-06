/**
 * Dataset API client functions.
 */

import { apiClient } from '@shared/api/client';
import type {
  DatasetDetail,
  DatasetListResponse,
  DatasetFilters,
  CreateDatasetRequest,
  UpdateDatasetRequest,
} from '../types';

/**
 * Fetch paginated list of datasets.
 */
export async function fetchDatasets(
  filters: DatasetFilters = {}
): Promise<DatasetListResponse> {
  return apiClient.get<DatasetListResponse>('/datasets', {
    params: {
      storage_type: filters.storage_type,
      dataset_type: filters.dataset_type,
      status: filters.status,
      visibility: filters.visibility,
      owner_id: filters.owner_id,
      search: filters.search,
      page: filters.page,
      page_size: filters.page_size,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Fetch a single dataset by ID.
 */
export async function fetchDataset(id: number): Promise<DatasetDetail> {
  return apiClient.get<DatasetDetail>(`/datasets/${id}`);
}

/**
 * Create a new dataset.
 */
export async function createDataset(
  data: CreateDatasetRequest
): Promise<DatasetDetail> {
  return apiClient.post<DatasetDetail>('/datasets', data);
}

/**
 * Update an existing dataset.
 */
export async function updateDataset(
  id: number,
  data: UpdateDatasetRequest
): Promise<DatasetDetail> {
  return apiClient.patch<DatasetDetail>(`/datasets/${id}`, data);
}

/**
 * Delete a dataset.
 */
export async function deleteDataset(id: number): Promise<void> {
  return apiClient.delete(`/datasets/${id}`);
}

/**
 * Archive a dataset.
 */
export async function archiveDataset(id: number): Promise<DatasetDetail> {
  return apiClient.post<DatasetDetail>(`/datasets/${id}/archive`);
}
