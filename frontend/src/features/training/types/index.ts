/**
 * Training module type definitions.
 * Maps to backend schemas: src/api/v1/schemas/training_job.py
 */

// === Enums ===

export type JobStatus =
  | 'submitted'
  | 'running'
  | 'paused'
  | 'preempted'
  | 'completed'
  | 'failed';

export type JobPriority = 'high' | 'medium' | 'low';

export type DistributionStrategy = 'ddp' | 'fsdp' | 'deepspeed' | 'horovod';

export type CheckpointType = 'epoch' | 'step' | 'best' | 'final' | 'manual';

export type StorageTier = 'nvme' | 'fsx' | 's3';

export type CheckpointStatus = 'available' | 'archived' | 'deleted';

// === Training Job Types ===

export interface TrainingJobSummary {
  id: number;
  job_name: string;
  display_name: string | null;
  owner_id: number;
  owner_username: string | null;
  status: JobStatus;
  priority: JobPriority;
  instance_type: string;
  node_count: number;
  gpu_per_node: number;
  distribution_strategy: DistributionStrategy | null;
  current_epoch: number | null;
  total_epochs: number | null;
  latest_loss: number | null;
  checkpoints_count: number;
  submitted_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  duration_seconds: number | null;
  estimated_cost_usd: number | null;
}

export interface TrainingJobDetail {
  // Basic info
  id: number;
  job_name: string;
  display_name: string | null;
  description: string | null;
  owner_id: number;
  owner_username: string | null;

  // Status info
  status: JobStatus;
  hyperpod_status: string | null;
  kueue_workload_name: string | null;
  kueue_status: string | null;

  // Compute config
  image_uri: string;
  instance_type: string;
  node_count: number;
  gpu_per_node: number;
  tasks_per_node: number;
  entry_point: string | null;
  entrypoint_command: string[];

  // Environment
  environment_variables: Record<string, string> | null;
  dataset_id: number | null;
  dataset_name: string | null;
  data_mount_path: string | null;
  checkpoint_mount_path: string | null;

  // Training config
  hyperparameters: Record<string, unknown> | null;
  max_epochs: number | null;
  total_epochs: number | null;
  batch_size: number | null;
  learning_rate: number | null;
  distribution_strategy: DistributionStrategy;
  priority: JobPriority;
  mixed_precision: boolean;
  use_spot_instances: boolean;

  // Pod stats
  total_pods: number | null;
  running_pods: number;
  failed_pods: number;
  preemption_count: number;

  // Training progress
  current_epoch: number | null;
  current_step: number | null;
  latest_loss: number | null;
  latest_accuracy: number | null;

  // Time stats
  submitted_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  total_gpu_hours: number | null;

  // Cost
  estimated_cost_usd: number | null;

  // Error info
  error_message: string | null;
  failure_reason: string | null;

  // Admin-only field
  hyperpod_job_arn: string | null;

  // Metadata
  checkpoints_count: number;
  created_at: string;
  updated_at: string;
}

// === Request Types ===

export interface CreateTrainingJobRequest {
  job_name: string;
  display_name?: string | null;
  description?: string | null;
  image_uri: string;
  entry_point?: string | null;
  instance_type: string;
  node_count: number;
  gpu_per_node?: number;
  tasks_per_node?: number;
  entrypoint_command?: string[];
  environment_variables?: Record<string, string> | null;
  dataset_id?: number | null;
  data_mount_path?: string;
  checkpoint_mount_path?: string;
  checkpoint_interval?: number | null;
  hyperparameters?: Record<string, unknown> | null;
  max_epochs?: number | null;
  batch_size?: number | null;
  learning_rate?: number | null;
  distribution_strategy?: DistributionStrategy;
  priority?: JobPriority;
  mixed_precision?: boolean;
  use_spot_instances?: boolean;
}

export interface UpdateTrainingJobRequest {
  display_name?: string | null;
  description?: string | null;
  priority?: JobPriority;
}

// === Filter Types ===

export interface TrainingJobFilters {
  status?: JobStatus | JobStatus[];
  priority?: JobPriority;
  owner_id?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'submitted_at' | 'priority';
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface TrainingJobListResponse {
  items: TrainingJobSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === Checkpoint Types ===

export interface Checkpoint {
  id: number;
  training_job_id: number;
  checkpoint_name: string;
  storage_path: string;
  checkpoint_type: CheckpointType;
  epoch: number | null;
  step: number | null;
  size_bytes: number | null;
  loss: number | null;
  accuracy: number | null;
  storage_tier: StorageTier;
  status: CheckpointStatus;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface CheckpointListResponse {
  items: Checkpoint[];
  checkpoints: Checkpoint[];
}

export interface CreateCheckpointRequest {
  checkpoint_name?: string | null;
}

// === Log Types ===

export interface LogEntry {
  timestamp: string;
  pod_name: string;
  message: string;
}

export interface TrainingLogsResponse {
  logs: LogEntry[];
  next_token: string | null;
}

// === Metrics Types ===

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  labels: Record<string, string> | null;
}

export interface MetricSeries {
  metric_name: string;
  data_points: MetricDataPoint[];
}

export interface TrainingMetricsResponse {
  metrics: TrainingMetric[];
}

export interface TrainingMetric {
  metric_name: string;
  step: number;
  value: number;
  timestamp: string | null;
}

// === UI Helper Types ===

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  submitted: '已提交',
  running: '运行中',
  paused: '已暂停',
  preempted: '被抢占',
  completed: '已完成',
  failed: '已失败',
};

export const JOB_STATUS_COLORS: Record<
  JobStatus,
  'grey' | 'blue' | 'green' | 'red' | 'pending' | 'stopped'
> = {
  submitted: 'grey',
  running: 'green',
  paused: 'stopped',
  preempted: 'pending',
  completed: 'green',
  failed: 'red',
};

export const JOB_PRIORITY_LABELS: Record<JobPriority, string> = {
  high: '高',
  medium: '中',
  low: '低',
};

export const DISTRIBUTION_STRATEGY_LABELS: Record<DistributionStrategy, string> = {
  ddp: 'PyTorch DDP',
  fsdp: 'PyTorch FSDP',
  deepspeed: 'DeepSpeed ZeRO',
  horovod: 'Horovod',
};

export const INSTANCE_TYPES = [
  'ml.p4d.24xlarge',
  'ml.p4de.24xlarge',
  'ml.p5.48xlarge',
  'ml.g5.xlarge',
  'ml.g5.2xlarge',
  'ml.g5.4xlarge',
  'ml.g5.8xlarge',
  'ml.g5.12xlarge',
  'ml.g5.16xlarge',
  'ml.g5.24xlarge',
  'ml.g5.48xlarge',
] as const;

export type InstanceType = (typeof INSTANCE_TYPES)[number];
