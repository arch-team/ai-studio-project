/**
 * TanStack Query hooks for Models.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type { ModelFilters, CreateModelRequest, UpdateModelRequest } from '../types';
import {
  fetchModels,
  fetchModel,
  fetchModelVersions,
  registerModel,
  updateModel,
  archiveModel,
  restoreModel,
} from './modelApi';

// === Query Hooks ===

/**
 * Fetch paginated list of models.
 */
export function useModels(filters: ModelFilters = {}) {
  return useQuery({
    queryKey: queryKeys.models.list(filters as Record<string, unknown>),
    queryFn: () => fetchModels(filters),
  });
}

/**
 * Fetch a single model by ID.
 */
export function useModel(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.models.detail(String(id!)),
    queryFn: () => fetchModel(id!),
    enabled: id !== undefined,
  });
}

/**
 * Fetch model versions history.
 */
export function useModelVersions(
  id: number | undefined,
  options?: {
    compare_v1?: string;
    compare_v2?: string;
  }
) {
  return useQuery({
    queryKey: ['models', 'versions', id, options],
    queryFn: () => fetchModelVersions(id!, options),
    enabled: id !== undefined,
  });
}

// === Mutation Hooks ===

/**
 * Register a new model from checkpoint.
 */
export function useRegisterModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateModelRequest) => registerModel(data),
    onSuccess: () => {
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
    },
  });
}

/**
 * Update an existing model.
 */
export function useUpdateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateModelRequest }) =>
      updateModel(id, data),
    onSuccess: (result) => {
      // Update cache for this specific model
      queryClient.setQueryData(queryKeys.models.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
    },
  });
}

/**
 * Archive a model.
 */
export function useArchiveModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => archiveModel(id),
    onSuccess: (result) => {
      // Update cache for this specific model
      queryClient.setQueryData(queryKeys.models.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
      // Invalidate version queries
      queryClient.invalidateQueries({ queryKey: ['models', 'versions', result.id] });
    },
  });
}

/**
 * Restore an archived model.
 */
export function useRestoreModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => restoreModel(id),
    onSuccess: (result) => {
      // Update cache for this specific model
      queryClient.setQueryData(queryKeys.models.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.models.lists() });
      // Invalidate version queries
      queryClient.invalidateQueries({ queryKey: ['models', 'versions', result.id] });
    },
  });
}
