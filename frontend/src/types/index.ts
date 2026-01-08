/**
 * Shared TypeScript type definitions.
 */

// Training Job types
export interface TrainingJob {
  id: string;
  name: string;
  status: TrainingJobStatus;
  framework: 'pytorch' | 'tensorflow';
  distributedStrategy: 'ddp' | 'fsdp' | 'deepspeed';
  nodeCount: number;
  gpuPerNode: number;
  priority: 'critical' | 'high' | 'normal';
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  teamId: string;
}

export type TrainingJobStatus =
  | 'submitted'
  | 'pending'
  | 'running'
  | 'paused'
  | 'preempted'
  | 'completed'
  | 'failed'
  | 'cancelled';

// Dataset types
export interface Dataset {
  id: string;
  name: string;
  description?: string;
  size: number;
  format: string;
  storageLocation: string;
  createdAt: string;
  updatedAt: string;
  teamId: string;
}

// Resource types
export interface ResourceQuota {
  id: string;
  teamId: string;
  gpuLimit: number;
  gpuUsed: number;
  memoryLimitGb: number;
  memoryUsedGb: number;
  storageLimitTb: number;
  storageUsedTb: number;
}

// Space types
export interface Space {
  id: string;
  name: string;
  type: 'jupyterlab' | 'vscode';
  status: 'running' | 'stopped' | 'starting' | 'stopping';
  instanceType: string;
  createdAt: string;
  userId: string;
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface ApiError {
  detail: string;
  code?: string;
}
