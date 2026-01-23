/**
 * TanStack Query hooks for Datasets.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type {
  DatasetFilters,
  CreateDatasetRequest,
  UpdateDatasetRequest,
} from '../types';
import {
  fetchDatasets,
  fetchDataset,
  createDataset,
  updateDataset,
  deleteDataset,
  archiveDataset,
} from './datasetApi';

// === Query Hooks ===

/**
 * Fetch paginated list of datasets.
 */
export function useDatasets(filters: DatasetFilters = {}) {
  return useQuery({
    queryKey: queryKeys.datasets.list(filters as Record<string, unknown>),
    queryFn: () => fetchDatasets(filters),
  });
}

/**
 * Fetch a single dataset by ID.
 */
export function useDataset(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.datasets.detail(String(id!)),
    queryFn: () => fetchDataset(id!),
    enabled: id !== undefined,
  });
}

// === Mutation Hooks ===

/**
 * Create a new dataset.
 */
export function useCreateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateDatasetRequest) => createDataset(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.datasets.lists() });
    },
  });
}

/**
 * Update an existing dataset.
 */
export function useUpdateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateDatasetRequest }) =>
      updateDataset(id, data),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.datasets.detail(String(result.id)), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.datasets.lists() });
    },
  });
}

/**
 * Delete a dataset.
 */
export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteDataset(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.datasets.detail(String(id)) });
      queryClient.invalidateQueries({ queryKey: queryKeys.datasets.lists() });
    },
  });
}

/**
 * Archive a dataset.
 */
export function useArchiveDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => archiveDataset(id),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.datasets.detail(String(result.id)), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.datasets.lists() });
    },
  });
}
