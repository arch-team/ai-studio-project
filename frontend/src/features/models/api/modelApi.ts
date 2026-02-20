/**
 * Model API functions.
 * RESTful API calls to backend /api/v1/models endpoints.
 */

import { apiClient } from '@shared/api';
import type {
  ModelListResponse,
  ModelDetail,
  ModelFilters,
  CreateModelRequest,
  UpdateModelRequest,
  ModelVersionsResponse,
} from '../types';

// === List and Query ===

/**
 * Fetch paginated list of models.
 */
export async function fetchModels(filters: ModelFilters = {}): Promise<ModelListResponse> {
  return apiClient.get<ModelListResponse>('/models', {
    params: {
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status,
      framework: filters.framework,
      training_job_id: filters.training_job_id,
      owner_id: filters.owner_id,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Fetch a single model by ID.
 */
export async function fetchModel(id: number): Promise<ModelDetail> {
  return apiClient.get<ModelDetail>(`/models/${id}`);
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
  return apiClient.get<ModelVersionsResponse>(`/models/${id}/versions`, {
    params: options,
  });
}

// === Create and Update ===

/**
 * Register a new model from checkpoint.
 */
export async function registerModel(data: CreateModelRequest): Promise<ModelDetail> {
  return apiClient.post<ModelDetail>('/models', data);
}

/**
 * Update an existing model.
 */
export async function updateModel(
  id: number,
  data: UpdateModelRequest
): Promise<ModelDetail> {
  return apiClient.put<ModelDetail>(`/models/${id}`, data);
}

// === Model Actions ===

/**
 * Archive a model.
 */
export async function archiveModel(id: number): Promise<ModelDetail> {
  return apiClient.post<ModelDetail>(`/models/${id}/archive`);
}

/**
 * Restore an archived model.
 */
export async function restoreModel(id: number): Promise<ModelDetail> {
  return apiClient.post<ModelDetail>(`/models/${id}/restore`);
}

/**
 * Rollback model to a specific version.
 */
export async function rollbackModelVersion(
  id: number,
  targetVersion: string
): Promise<ModelDetail> {
  return apiClient.post<ModelDetail>(`/models/${id}/rollback`, { target_version: targetVersion });
}

/**
 * Batch archive multiple models.
 */
export async function batchArchiveModels(
  ids: number[]
): Promise<{ success: number[]; failed: number[] }> {
  return apiClient.post<{ success: number[]; failed: number[] }>('/models/batch/archive', { model_ids: ids });
}
