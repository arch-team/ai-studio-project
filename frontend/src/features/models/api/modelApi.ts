/**
 * Model API functions.
 * RESTful API calls to backend /api/v1/models endpoints.
 */

import type {
  ModelListResponse,
  ModelDetail,
  ModelFilters,
  CreateModelRequest,
  UpdateModelRequest,
  ModelVersionsResponse,
} from '../types';

const API_BASE = '/api/v1';

/**
 * Get authorization header from localStorage.
 */
function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
  };
}

/**
 * Build URL with query parameters.
 */
function buildUrl(path: string, params?: Record<string, unknown>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((v) => url.searchParams.append(key, String(v)));
        } else {
          url.searchParams.set(key, String(value));
        }
      }
    });
  }
  return url.toString();
}

/**
 * Handle API response and errors.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `HTTP Error: ${response.status}`);
  }
  return response.json();
}

// === List and Query ===

/**
 * Fetch paginated list of models.
 */
export async function fetchModels(filters: ModelFilters = {}): Promise<ModelListResponse> {
  const url = buildUrl('/models', {
    page: filters.page,
    page_size: filters.page_size,
    status: filters.status,
    framework: filters.framework,
    training_job_id: filters.training_job_id,
    owner_id: filters.owner_id,
    sort_by: filters.sort_by,
    sort_order: filters.sort_order,
  });

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<ModelListResponse>(response);
}

/**
 * Fetch a single model by ID.
 */
export async function fetchModel(id: number): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models/${id}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<ModelDetail>(response);
}

/**
 * Fetch model versions history with optional comparison.
 */
export async function fetchModelVersions(
  id: number,
  options?: {
    compare_v1?: string;
    compare_v2?: string;
  }
): Promise<ModelVersionsResponse> {
  const url = buildUrl(`/models/${id}/versions`, options);

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<ModelVersionsResponse>(response);
}

// === Create and Update ===

/**
 * Register a new model from checkpoint.
 */
export async function registerModel(data: CreateModelRequest): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<ModelDetail>(response);
}

/**
 * Update an existing model.
 */
export async function updateModel(
  id: number,
  data: UpdateModelRequest
): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<ModelDetail>(response);
}

// === Model Actions ===

/**
 * Archive a model.
 */
export async function archiveModel(id: number): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models/${id}/archive`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  return handleResponse<ModelDetail>(response);
}

/**
 * Restore an archived model.
 */
export async function restoreModel(id: number): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models/${id}/restore`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  return handleResponse<ModelDetail>(response);
}

/**
 * Rollback model to a specific version.
 */
export async function rollbackModelVersion(
  id: number,
  targetVersion: string
): Promise<ModelDetail> {
  const response = await fetch(`${API_BASE}/models/${id}/rollback`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ target_version: targetVersion }),
  });

  return handleResponse<ModelDetail>(response);
}

/**
 * Batch archive multiple models.
 */
export async function batchArchiveModels(
  ids: number[]
): Promise<{ success: number[]; failed: number[] }> {
  const response = await fetch(`${API_BASE}/models/batch/archive`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ model_ids: ids }),
  });

  return handleResponse<{ success: number[]; failed: number[] }>(response);
}
