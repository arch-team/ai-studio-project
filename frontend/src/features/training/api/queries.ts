/**
 * TanStack Query hooks for Training Jobs.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type {
  TrainingJobFilters,
  CreateTrainingJobRequest,
  UpdateTrainingJobRequest,
  CreateCheckpointRequest,
} from '../types';
import {
  fetchTrainingJobs,
  fetchTrainingJob,
  createTrainingJob,
  updateTrainingJob,
  deleteTrainingJob,
  pauseTrainingJob,
  resumeTrainingJob,
  fetchTrainingJobCheckpoints,
  createCheckpoint,
  fetchTrainingJobLogs,
  fetchTrainingJobMetrics,
} from './trainingJobApi';

// === Query Hooks ===

/**
 * Fetch paginated list of training jobs.
 */
export function useTrainingJobs(filters: TrainingJobFilters = {}) {
  return useQuery({
    queryKey: queryKeys.trainingJobs.list(filters as Record<string, unknown>),
    queryFn: () => fetchTrainingJobs(filters),
  });
}

/**
 * Fetch a single training job by ID.
 */
export function useTrainingJob(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.trainingJobs.detail(String(id!)),
    queryFn: () => fetchTrainingJob(id!),
    enabled: id !== undefined,
  });
}

/**
 * Fetch checkpoints for a training job.
 */
export function useTrainingJobCheckpoints(jobId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.checkpoints.list({ training_job_id: jobId }),
    queryFn: () => fetchTrainingJobCheckpoints(jobId!),
    enabled: jobId !== undefined,
  });
}

/**
 * Fetch logs for a training job with polling support.
 */
export function useTrainingJobLogs(
  jobId: number | undefined,
  options?: {
    pod_name?: string;
    since?: string;
    limit?: number;
    next_token?: string;
  },
  pollInterval?: number
) {
  return useQuery({
    queryKey: ['trainingJobs', 'logs', jobId, options],
    queryFn: () => fetchTrainingJobLogs(jobId!, options),
    enabled: jobId !== undefined,
    refetchInterval: pollInterval,
  });
}

/**
 * Fetch metrics for a training job with polling support.
 */
export function useTrainingJobMetrics(
  jobId: number | undefined,
  options?: {
    metric_names?: string[];
    start_time?: string;
    end_time?: string;
    step?: number;
  },
  pollInterval?: number
) {
  return useQuery({
    queryKey: ['trainingJobs', 'metrics', jobId, options],
    queryFn: () => fetchTrainingJobMetrics(jobId!, options),
    enabled: jobId !== undefined,
    refetchInterval: pollInterval,
  });
}

// === Mutation Hooks ===

/**
 * Create a new training job.
 */
export function useCreateTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTrainingJobRequest) => createTrainingJob(data),
    onSuccess: () => {
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

/**
 * Update an existing training job.
 */
export function useUpdateTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTrainingJobRequest }) =>
      updateTrainingJob(id, data),
    onSuccess: (result) => {
      // Update cache for this specific job
      queryClient.setQueryData(queryKeys.trainingJobs.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

/**
 * Delete a training job.
 */
export function useDeleteTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteTrainingJob(id),
    onSuccess: (_result, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.trainingJobs.detail(String(id)) });
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

/**
 * Pause a running training job.
 */
export function usePauseTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => pauseTrainingJob(id),
    onSuccess: (result) => {
      // Update cache for this specific job
      queryClient.setQueryData(queryKeys.trainingJobs.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

/**
 * Resume a paused training job.
 */
export function useResumeTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => resumeTrainingJob(id),
    onSuccess: (result) => {
      // Update cache for this specific job
      queryClient.setQueryData(queryKeys.trainingJobs.detail(String(result.id)), result);
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

/**
 * Create a manual checkpoint.
 */
export function useCreateCheckpoint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, data }: { jobId: number; data?: CreateCheckpointRequest }) =>
      createCheckpoint(jobId, data),
    onSuccess: (_result, { jobId }) => {
      // Invalidate checkpoints list
      queryClient.invalidateQueries({
        queryKey: queryKeys.checkpoints.list({ training_job_id: jobId }),
      });
      // Invalidate job detail (checkpoints_count may change)
      queryClient.invalidateQueries({
        queryKey: queryKeys.trainingJobs.detail(String(jobId)),
      });
    },
  });
}
