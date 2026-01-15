/**
 * Training Job API functions.
 * RESTful API calls to backend /api/v1/training-jobs endpoints.
 */

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
 * Fetch paginated list of training jobs.
 */
export async function fetchTrainingJobs(
  filters: TrainingJobFilters = {}
): Promise<TrainingJobListResponse> {
  const url = buildUrl('/training-jobs', {
    page: filters.page,
    page_size: filters.page_size,
    status: filters.status,
    priority: filters.priority,
    owner_id: filters.owner_id,
    sort_by: filters.sort_by,
    sort_order: filters.sort_order,
  });

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingJobListResponse>(response);
}

/**
 * Fetch a single training job by ID.
 */
export async function fetchTrainingJob(id: number): Promise<TrainingJobDetail> {
  const response = await fetch(`${API_BASE}/training-jobs/${id}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingJobDetail>(response);
}

// === Create, Update, Delete ===

/**
 * Create a new training job.
 */
export async function createTrainingJob(
  data: CreateTrainingJobRequest
): Promise<TrainingJobDetail> {
  const response = await fetch(`${API_BASE}/training-jobs`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<TrainingJobDetail>(response);
}

/**
 * Update an existing training job.
 */
export async function updateTrainingJob(
  id: number,
  data: UpdateTrainingJobRequest
): Promise<TrainingJobDetail> {
  const response = await fetch(`${API_BASE}/training-jobs/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<TrainingJobDetail>(response);
}

/**
 * Delete (soft) a training job.
 */
export async function deleteTrainingJob(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/training-jobs/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
  }
}

// === Job Control Actions ===

/**
 * Pause a running training job.
 */
export async function pauseTrainingJob(id: number): Promise<TrainingJobDetail> {
  const response = await fetch(`${API_BASE}/training-jobs/${id}/pause`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingJobDetail>(response);
}

/**
 * Resume a paused training job.
 */
export async function resumeTrainingJob(id: number): Promise<TrainingJobDetail> {
  const response = await fetch(`${API_BASE}/training-jobs/${id}/resume`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingJobDetail>(response);
}

// === Checkpoints ===

/**
 * Fetch checkpoints for a training job.
 */
export async function fetchTrainingJobCheckpoints(
  jobId: number
): Promise<CheckpointListResponse> {
  const response = await fetch(`${API_BASE}/training-jobs/${jobId}/checkpoints`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<CheckpointListResponse>(response);
}

/**
 * Create a manual checkpoint for a training job.
 */
export async function createCheckpoint(
  jobId: number,
  data?: CreateCheckpointRequest
): Promise<Checkpoint> {
  const response = await fetch(`${API_BASE}/training-jobs/${jobId}/checkpoints`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data || {}),
  });

  return handleResponse<Checkpoint>(response);
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
  const url = buildUrl(`/training-jobs/${jobId}/logs`, options);

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingLogsResponse>(response);
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
  const url = buildUrl(`/training-jobs/${jobId}/metrics`, {
    metric_names: options?.metric_names,
    start_time: options?.start_time,
    end_time: options?.end_time,
    step: options?.step,
  });

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<TrainingMetricsResponse>(response);
}
