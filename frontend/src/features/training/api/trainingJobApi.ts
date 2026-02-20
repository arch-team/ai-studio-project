/**
 * Training Job API functions.
 * RESTful API calls to backend /api/v1/training-jobs endpoints.
 */

import { apiClient } from '@shared/api';
import type {
  TrainingJobListResponse,
  TrainingJobDetail,
  TrainingJobFilters,
  CreateTrainingJobRequest,
  UpdateTrainingJobRequest,
  CheckpointListResponse,
  CreateCheckpointRequest,
  Checkpoint,
  TrainingLogsResponse,
  TrainingMetricsResponse,
} from '../types';

// === List and Query ===

/**
 * Fetch paginated list of training jobs.
 */
export async function fetchTrainingJobs(
  filters: TrainingJobFilters = {}
): Promise<TrainingJobListResponse> {
  return apiClient.get<TrainingJobListResponse>('/training-jobs', {
    params: {
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status,
      priority: filters.priority,
      owner_id: filters.owner_id,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Fetch a single training job by ID.
 */
export async function fetchTrainingJob(id: number): Promise<TrainingJobDetail> {
  return apiClient.get<TrainingJobDetail>(`/training-jobs/${id}`);
}

// === Create, Update, Delete ===

/**
 * Create a new training job.
 */
export async function createTrainingJob(
  data: CreateTrainingJobRequest
): Promise<TrainingJobDetail> {
  return apiClient.post<TrainingJobDetail>('/training-jobs', data);
}

/**
 * Update an existing training job.
 */
export async function updateTrainingJob(
  id: number,
  data: UpdateTrainingJobRequest
): Promise<TrainingJobDetail> {
  return apiClient.put<TrainingJobDetail>(`/training-jobs/${id}`, data);
}

/**
 * Delete (soft) a training job.
 */
export async function deleteTrainingJob(id: number): Promise<void> {
  return apiClient.delete(`/training-jobs/${id}`);
}

// === Job Control Actions ===

/**
 * Pause a running training job.
 */
export async function pauseTrainingJob(id: number): Promise<TrainingJobDetail> {
  return apiClient.post<TrainingJobDetail>(`/training-jobs/${id}/pause`);
}

/**
 * Resume a paused training job.
 */
export async function resumeTrainingJob(id: number): Promise<TrainingJobDetail> {
  return apiClient.post<TrainingJobDetail>(`/training-jobs/${id}/resume`);
}

// === Checkpoints ===

/**
 * Fetch checkpoints for a training job.
 */
export async function fetchTrainingJobCheckpoints(
  jobId: number
): Promise<CheckpointListResponse> {
  return apiClient.get<CheckpointListResponse>(`/training-jobs/${jobId}/checkpoints`);
}

/**
 * Create a manual checkpoint for a training job.
 */
export async function createCheckpoint(
  jobId: number,
  data?: CreateCheckpointRequest
): Promise<Checkpoint> {
  return apiClient.post<Checkpoint>(`/training-jobs/${jobId}/checkpoints`, data || {});
}

// === Logs and Metrics ===

/**
 * Fetch training logs for a job.
 */
export async function fetchTrainingJobLogs(
  jobId: number,
  options?: {
    pod_name?: string;
    since?: string;
    limit?: number;
    next_token?: string;
  }
): Promise<TrainingLogsResponse> {
  return apiClient.get<TrainingLogsResponse>(`/training-jobs/${jobId}/logs`, {
    params: options,
  });
}

/**
 * Fetch training metrics for a job.
 */
export async function fetchTrainingJobMetrics(
  jobId: number,
  options?: {
    metric_names?: string[];
    start_time?: string;
    end_time?: string;
    step?: number;
  }
): Promise<TrainingMetricsResponse> {
  return apiClient.get<TrainingMetricsResponse>(`/training-jobs/${jobId}/metrics`, {
    params: {
      metric_names: options?.metric_names,
      start_time: options?.start_time,
      end_time: options?.end_time,
      step: options?.step,
    },
  });
}
