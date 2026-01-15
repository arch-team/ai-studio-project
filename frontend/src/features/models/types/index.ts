/**
 * Models module type definitions.
 * Maps to backend schemas: src/api/v1/schemas/model.py
 */

// === Enums ===

export type ModelFramework = 'pytorch' | 'tensorflow' | 'jax' | 'other';

export type ModelStatus =
  | 'training'
  | 'registered'
  | 'deployed'
  | 'archived'
  | 'failed';

// === Model Types ===

export interface ModelSummary {
  id: number;
  model_name: string;
  version: string;
  display_name: string | null;
  owner_id: number;
  training_job_id: number | null;
  status: ModelStatus;
  framework: ModelFramework;
  metrics: Record<string, unknown> | null;
  tags: string[] | null;
  created_at: string;
  registered_at: string | null;
}

export interface ModelDetail {
  id: number;
  model_name: string;
  version: string;
  display_name: string | null;
  description: string | null;
  owner_id: number;

  // Relationships
  training_job_id: number | null;
  checkpoint_id: number | null;

  // Storage
  model_uri: string | null;
  model_path: string | null;
  registry_arn: string | null;
  registry_status: string | null;

  // Training info
  metrics: Record<string, unknown> | null;
  hyperparameters: Record<string, unknown> | null;

  // Framework
  framework: ModelFramework;
  framework_version: string | null;

  // Status
  status: ModelStatus;

  // Metadata
  size_bytes: number | null;
  model_format: string | null;
  tags: string[] | null;

  // Timestamps
  created_at: string;
  updated_at: string;
  registered_at: string | null;
  archived_at: string | null;
}

// === Request Types ===

export interface CreateModelRequest {
  training_job_id: number;
  checkpoint_id: number;
  model_name: string;
  display_name?: string | null;
  description?: string | null;
  framework?: ModelFramework;
  framework_version?: string | null;
  metrics?: Record<string, unknown> | null;
  hyperparameters?: Record<string, unknown> | null;
  tags?: string[] | null;
}

export interface UpdateModelRequest {
  display_name?: string | null;
  description?: string | null;
  tags?: string[] | null;
}

// === Filter Types ===

export interface ModelFilters {
  status?: ModelStatus | ModelStatus[];
  framework?: ModelFramework;
  training_job_id?: number;
  owner_id?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'version' | 'model_name';
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface ModelListResponse {
  items: ModelSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === Version Comparison Types ===

export interface MetricsDiff {
  v1: number | null;
  v2: number | null;
  diff: number | null;
  diff_percent: number | null;
}

export interface HyperparameterChange {
  param: string;
  v1_value: unknown;
  v2_value: unknown;
  change_type: 'added' | 'removed' | 'modified';
}

export interface VersionComparison {
  metrics_diff: Record<string, MetricsDiff>;
  hyperparams_changed: string[];
  hyperparameters_changes?: HyperparameterChange[];
  framework_changed: boolean;
  tags_added: string[];
  tags_removed: string[];
}

export interface ModelVersionSummary {
  id: number;
  version: string;
  status: ModelStatus;
  metrics: Record<string, unknown> | null;
  hyperparameters: Record<string, unknown> | null;
  created_at: string;
  registered_at: string | null;
}

// Alias for component usage (extends ModelVersionSummary with optional checkpoint_id)
export interface ModelVersion {
  id: number;
  version: string;
  status: ModelStatus | string;
  checkpoint_id?: number | null;
  metrics: Record<string, unknown> | null;
  hyperparameters: Record<string, unknown> | null;
  created_at: string;
  registered_at: string | null;
}

export interface ModelVersionsResponse {
  model_name: string;
  versions: ModelVersionSummary[];
  comparison: VersionComparison | null;
}

// === UI Helper Types ===

export const MODEL_STATUS_LABELS: Record<ModelStatus, string> = {
  training: '训练中',
  registered: '已注册',
  deployed: '已部署',
  archived: '已归档',
  failed: '已失败',
};

export const MODEL_STATUS_COLORS: Record<
  ModelStatus,
  'grey' | 'blue' | 'green' | 'red' | 'pending' | 'stopped'
> = {
  training: 'blue',
  registered: 'green',
  deployed: 'green',
  archived: 'grey',
  failed: 'red',
};

export const MODEL_FRAMEWORK_LABELS: Record<ModelFramework, string> = {
  pytorch: 'PyTorch',
  tensorflow: 'TensorFlow',
  jax: 'JAX',
  other: '其他',
};

// Registry sync status helper
export type RegistrySyncStatus = 'synced' | 'pending' | 'failed' | 'not_registered';

export const REGISTRY_SYNC_STATUS_LABELS: Record<RegistrySyncStatus, string> = {
  synced: '已同步',
  pending: '同步中',
  failed: '同步失败',
  not_registered: '未注册',
};

export const REGISTRY_SYNC_STATUS_COLORS: Record<
  RegistrySyncStatus,
  'green' | 'blue' | 'red' | 'grey'
> = {
  synced: 'green',
  pending: 'blue',
  failed: 'red',
  not_registered: 'grey',
};

/**
 * Derive registry sync status from model detail.
 */
export function getRegistrySyncStatus(model: ModelDetail): RegistrySyncStatus {
  if (!model.registry_arn) {
    return 'not_registered';
  }
  if (model.registry_status === 'synced' || model.registry_status === 'Registered') {
    return 'synced';
  }
  if (model.registry_status === 'pending' || model.registry_status === 'InProgress') {
    return 'pending';
  }
  if (model.registry_status === 'failed' || model.registry_status === 'Failed') {
    return 'failed';
  }
  return 'synced'; // Default to synced if registry_arn exists
}
