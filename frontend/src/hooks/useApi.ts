/**
 * Custom hooks for API data fetching with TanStack Query.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { TrainingJob, Dataset, ResourceQuota, Space, PaginatedResponse } from '../types';

// Query keys
export const queryKeys = {
  trainingJobs: ['trainingJobs'] as const,
  trainingJob: (id: string) => ['trainingJobs', id] as const,
  datasets: ['datasets'] as const,
  dataset: (id: string) => ['datasets', id] as const,
  quotas: ['quotas'] as const,
  spaces: ['spaces'] as const,
  space: (id: string) => ['spaces', id] as const,
};

// Training Jobs hooks
export function useTrainingJobs(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...queryKeys.trainingJobs, { page, pageSize }],
    queryFn: () =>
      apiClient.get<PaginatedResponse<TrainingJob>>('/training/jobs', {
        params: { page: String(page), page_size: String(pageSize) },
      }),
  });
}

export function useTrainingJob(id: string) {
  return useQuery({
    queryKey: queryKeys.trainingJob(id),
    queryFn: () => apiClient.get<TrainingJob>(`/training/jobs/${id}`),
    enabled: !!id,
  });
}

// Datasets hooks
export function useDatasets(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...queryKeys.datasets, { page, pageSize }],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Dataset>>('/datasets', {
        params: { page: String(page), page_size: String(pageSize) },
      }),
  });
}

// Resource Quotas hooks
export function useResourceQuotas() {
  return useQuery({
    queryKey: queryKeys.quotas,
    queryFn: () => apiClient.get<ResourceQuota[]>('/resources/quotas'),
  });
}

// Spaces hooks
export function useSpaces() {
  return useQuery({
    queryKey: queryKeys.spaces,
    queryFn: () => apiClient.get<Space[]>('/spaces'),
  });
}

export function useCreateSpace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; type: 'jupyterlab' | 'vscode'; instanceType: string }) =>
      apiClient.post<Space>('/spaces', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces });
    },
  });
}
