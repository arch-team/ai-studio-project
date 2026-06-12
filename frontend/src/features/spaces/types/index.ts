/**
 * Spaces (Development Spaces) module type definitions.
 * Maps to backend schemas: src/modules/spaces/api/schemas/
 *
 * 契约对齐说明（与后端 requests.py / responses.py 一一对应）:
 * - id 为 UUID 字符串（Space 是唯一使用 str ID 的实体）
 * - 字段名: space_name / storage_size_gb
 * - 状态机: pending → running / stopped / failed / deleted
 */

// === Enums ===

export type SpaceStatus = 'pending' | 'running' | 'stopped' | 'failed' | 'deleted';

export type SpaceType = 'jupyter' | 'vscode' | 'rstudio';

export type SpaceInstanceType =
  | 'ml.t3.medium'
  | 'ml.t3.large'
  | 'ml.g4dn.xlarge'
  | 'ml.g5.xlarge'
  | 'ml.g5.2xlarge';

// === Space Types ===

export interface SpaceSummary {
  id: string;
  space_name: string;
  owner_id: number;
  instance_type: SpaceInstanceType;
  space_type: SpaceType;
  status: SpaceStatus;
  created_at: string;
}

export interface SpaceDetail extends SpaceSummary {
  storage_size_gb: number;
  lifecycle_config_arn: string | null;
  sagemaker_space_arn: string | null;
  updated_at: string;
  deleted_at: string | null;
}

// === Request Types ===

export interface CreateSpaceRequest {
  space_name: string;
  instance_type?: SpaceInstanceType;
  space_type?: SpaceType;
  storage_size_gb?: number;
}

export interface UpdateSpaceRequest {
  space_name?: string;
  instance_type?: SpaceInstanceType;
}

// === Filter Types ===

export interface SpaceFilters {
  status?: SpaceStatus;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'space_name';
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface SpaceListResponse {
  items: SpaceSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === UI Helper Types ===

export const SPACE_STATUS_LABELS: Record<SpaceStatus, string> = {
  pending: '启动中',
  running: '运行中',
  stopped: '已停止',
  failed: '失败',
  deleted: '已删除',
};

export const SPACE_STATUS_COLORS: Record<
  SpaceStatus,
  'blue' | 'green' | 'grey' | 'red' | 'pending'
> = {
  pending: 'blue',
  running: 'green',
  stopped: 'grey',
  failed: 'red',
  deleted: 'grey',
};

export const SPACE_TYPE_LABELS: Record<SpaceType, string> = {
  jupyter: 'JupyterLab',
  vscode: 'Code Editor (VS Code)',
  rstudio: 'RStudio',
};

export const INSTANCE_TYPE_LABELS: Record<SpaceInstanceType, string> = {
  'ml.t3.medium': 'ml.t3.medium (2 vCPU, 4 GB)',
  'ml.t3.large': 'ml.t3.large (2 vCPU, 8 GB)',
  'ml.g4dn.xlarge': 'ml.g4dn.xlarge (4 vCPU, 16 GB, 1x NVIDIA T4)',
  'ml.g5.xlarge': 'ml.g5.xlarge (4 vCPU, 16 GB, 1x NVIDIA A10G)',
  'ml.g5.2xlarge': 'ml.g5.2xlarge (8 vCPU, 32 GB, 1x NVIDIA A10G)',
};
