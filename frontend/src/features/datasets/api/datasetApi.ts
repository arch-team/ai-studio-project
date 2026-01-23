/**
 * Dataset API client functions.
 */

import type {
  DatasetDetail,
  DatasetListResponse,
  DatasetFilters,
  CreateDatasetRequest,
  UpdateDatasetRequest,
} from '../types';

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
 * Fetch paginated list of datasets.
 */
export async function fetchDatasets(
  filters: DatasetFilters = {}
): Promise<DatasetListResponse> {
  const params = new URLSearchParams();

  if (filters.storage_type) params.append('storage_type', filters.storage_type);
  if (filters.dataset_type) params.append('dataset_type', filters.dataset_type);
  if (filters.status) params.append('status', filters.status);
  if (filters.visibility) params.append('visibility', filters.visibility);
  if (filters.owner_id) params.append('owner_id', String(filters.owner_id));
  if (filters.search) params.append('search', filters.search);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(`${API_BASE}/datasets?${params.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single dataset by ID.
 */
export async function fetchDataset(id: number): Promise<DatasetDetail> {
  const response = await fetch(`${API_BASE}/datasets/${id}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch dataset: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new dataset.
 */
export async function createDataset(
  data: CreateDatasetRequest
): Promise<DatasetDetail> {
  const response = await fetch(`${API_BASE}/datasets`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create dataset: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update an existing dataset.
 */
export async function updateDataset(
  id: number,
  data: UpdateDatasetRequest
): Promise<DatasetDetail> {
  const response = await fetch(`${API_BASE}/datasets/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update dataset: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Delete a dataset.
 */
export async function deleteDataset(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/datasets/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to delete dataset: ${response.statusText}`);
  }
}

/**
 * Archive a dataset.
 */
export async function archiveDataset(id: number): Promise<DatasetDetail> {
  const response = await fetch(`${API_BASE}/datasets/${id}/archive`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to archive dataset: ${response.statusText}`);
  }
  return response.json();
}
