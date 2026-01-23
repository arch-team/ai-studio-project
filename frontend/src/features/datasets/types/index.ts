/**
 * Datasets module type definitions.
 * Maps to backend schemas: src/modules/datasets/
 */

// === Enums ===

export type StorageType = 'fsx' | 's3' | 'efs';

export type DatasetType = 'image' | 'text' | 'audio' | 'video' | 'tabular' | 'custom';

export type DatasetStatus = 'available' | 'preparing' | 'archived' | 'error';

export type DatasetVisibility = 'public' | 'private' | 'restricted';

// === Dataset Types ===

export interface DatasetSummary {
  id: number;
  name: string;
  description: string | null;
  version: string;
  storage_type: StorageType;
  storage_uri: string;
  total_size_bytes: number | null;
  file_count: number | null;
  dataset_type: DatasetType;
  data_format: string | null;
  tags: string[] | null;
  visibility: DatasetVisibility;
  owner_id: number;
  owner_username: string | null;
  status: DatasetStatus;
  created_at: string;
  updated_at: string;
  last_accessed_at: string | null;
}

export interface DatasetDetail extends DatasetSummary {
  // 关联的训练任务数量
  training_jobs_count: number;
}

// === Request Types ===

export interface CreateDatasetRequest {
  name: string;
  description?: string | null;
  version?: string;
  storage_type: StorageType;
  storage_uri: string;
  dataset_type: DatasetType;
  data_format?: string | null;
  tags?: string[] | null;
  visibility?: DatasetVisibility;
}

export interface UpdateDatasetRequest {
  name?: string;
  description?: string | null;
  tags?: string[] | null;
  visibility?: DatasetVisibility;
  status?: DatasetStatus;
}

// === Filter Types ===

export interface DatasetFilters {
  storage_type?: StorageType;
  dataset_type?: DatasetType;
  status?: DatasetStatus;
  visibility?: DatasetVisibility;
  owner_id?: number;
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'name' | 'total_size_bytes';
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface DatasetListResponse {
  items: DatasetSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === UI Helper Types ===

export const DATASET_STATUS_LABELS: Record<DatasetStatus, string> = {
  available: '可用',
  preparing: '准备中',
  archived: '已归档',
  error: '错误',
};

export const DATASET_STATUS_COLORS: Record<
  DatasetStatus,
  'green' | 'blue' | 'grey' | 'red'
> = {
  available: 'green',
  preparing: 'blue',
  archived: 'grey',
  error: 'red',
};

export const STORAGE_TYPE_LABELS: Record<StorageType, string> = {
  fsx: 'FSx for Lustre',
  s3: 'Amazon S3',
  efs: 'Amazon EFS',
};

export const DATASET_TYPE_LABELS: Record<DatasetType, string> = {
  image: '图像',
  text: '文本',
  audio: '音频',
  video: '视频',
  tabular: '表格',
  custom: '自定义',
};

export const VISIBILITY_LABELS: Record<DatasetVisibility, string> = {
  public: '公开',
  private: '私有',
  restricted: '受限',
};
