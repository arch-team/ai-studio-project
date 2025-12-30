/**
 * 模型管理相关的TypeScript类型定义
 */

// ==================== 枚举类型 ====================

export enum ModelStatus {
  UPLOADING = 'UPLOADING',
  PROCESSING = 'PROCESSING',
  AVAILABLE = 'AVAILABLE',
  FAILED = 'FAILED',
  ARCHIVED = 'ARCHIVED',
}

export enum ModelFramework {
  PYTORCH = 'PYTORCH',
  TENSORFLOW = 'TENSORFLOW',
  ONNX = 'ONNX',
  JFLUX = 'JFLUX',
  HUGGINGFACE = 'HUGGINGFACE',
  CUSTOM = 'CUSTOM',
}

// ==================== 模型相关类型 ====================

export interface Model {
  id: number;
  name: string;
  description?: string;
  framework: ModelFramework;
  task_type?: string;
  project_id: number;
  creator_id: number;
  source_training_job_id?: number;
  tags?: string[];
  metadata?: Record<string, any>;
  latest_version?: string;
  latest_version_id?: number;
  created_at: string;
  updated_at: string;
}

export interface ModelCreateRequest {
  name: string;
  description?: string;
  framework: ModelFramework;
  task_type?: string;
  project_id: number;
  source_training_job_id?: number;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ModelUpdateRequest {
  name?: string;
  description?: string;
  task_type?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ModelListResponse {
  items: Model[];
  total: number;
  page: number;
  page_size: number;
}

export interface ModelQueryParams {
  project_id?: number;
  framework?: ModelFramework;
  task_type?: string;
  page?: number;
  page_size?: number;
}

// ==================== 模型版本相关类型 ====================

export interface ModelVersion {
  id: number;
  model_id: number;
  version: string;
  description?: string;
  status: ModelStatus;
  error_message?: string;
  storage_path: string;
  storage_size_bytes?: number;
  checksum_md5?: string;
  model_format?: string;
  model_architecture?: string;
  metrics?: Record<string, any>;
  hyperparameters?: Record<string, any>;
  dependencies?: Record<string, any>;
  is_published: boolean;
  published_at?: string;
  published_by_id?: number;
  created_at: string;
  updated_at: string;
}

export interface ModelVersionCreateRequest {
  version: string;
  description?: string;
  model_format?: string;
  model_architecture?: string;
  metrics?: Record<string, any>;
  hyperparameters?: Record<string, any>;
  dependencies?: Record<string, any>;
}

export interface ModelVersionUpdateRequest {
  description?: string;
  model_format?: string;
  model_architecture?: string;
  metrics?: Record<string, any>;
  hyperparameters?: Record<string, any>;
  dependencies?: Record<string, any>;
}

export interface ModelVersionListResponse {
  items: ModelVersion[];
}

// ==================== 文件和存储相关类型 ====================

export interface ModelFileInfo {
  name: string;
  path: string;
  size: number;
  modified_at: string;
}

export interface ModelFilesResponse {
  files: ModelFileInfo[];
}

export interface ModelStorageStats {
  total_size: number;
  file_count: number;
  version_count: number;
}
