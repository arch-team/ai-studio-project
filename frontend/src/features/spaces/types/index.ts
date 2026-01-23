/**
 * Spaces (Development Spaces) module type definitions.
 * Maps to backend schemas: src/modules/spaces/
 */

// === Enums ===

export type SpaceStatus = 'creating' | 'running' | 'stopped' | 'failed' | 'deleting';

export type SpaceType = 'jupyter' | 'vscode' | 'custom';

export type InstanceSize = 'small' | 'medium' | 'large' | 'xlarge';

// === Space Types ===

export interface SpaceSummary {
  id: number;
  name: string;
  description: string | null;
  space_type: SpaceType;
  status: SpaceStatus;
  instance_type: string;
  instance_size: InstanceSize;
  owner_id: number;
  owner_username: string | null;
  url: string | null;
  created_at: string;
  started_at: string | null;
  stopped_at: string | null;
  last_activity_at: string | null;
}

export interface SpaceDetail extends SpaceSummary {
  // 资源配置
  cpu_cores: number;
  memory_gb: number;
  gpu_count: number;
  gpu_type: string | null;
  storage_gb: number;

  // 环境配置
  image_uri: string;
  environment_variables: Record<string, string> | null;

  // 挂载配置
  datasets_mounted: number[];
  fsx_mount_path: string | null;

  // 运行信息
  pod_name: string | null;
  pod_status: string | null;

  // 费用估算
  estimated_cost_per_hour: number | null;
  total_running_hours: number | null;
  total_cost_usd: number | null;

  updated_at: string;
}

// === Request Types ===

export interface CreateSpaceRequest {
  name: string;
  description?: string | null;
  space_type: SpaceType;
  instance_type: string;
  instance_size?: InstanceSize;
  image_uri?: string;
  environment_variables?: Record<string, string> | null;
  storage_gb?: number;
  datasets_to_mount?: number[];
}

export interface UpdateSpaceRequest {
  name?: string;
  description?: string | null;
  environment_variables?: Record<string, string> | null;
}

// === Filter Types ===

export interface SpaceFilters {
  space_type?: SpaceType;
  status?: SpaceStatus;
  owner_id?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'name' | 'last_activity_at';
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
  creating: '创建中',
  running: '运行中',
  stopped: '已停止',
  failed: '失败',
  deleting: '删除中',
};

export const SPACE_STATUS_COLORS: Record<
  SpaceStatus,
  'blue' | 'green' | 'grey' | 'red' | 'pending'
> = {
  creating: 'blue',
  running: 'green',
  stopped: 'grey',
  failed: 'red',
  deleting: 'pending',
};

export const SPACE_TYPE_LABELS: Record<SpaceType, string> = {
  jupyter: 'JupyterLab',
  vscode: 'VS Code Server',
  custom: '自定义',
};

export const INSTANCE_SIZE_LABELS: Record<InstanceSize, string> = {
  small: '小型 (2 vCPU, 8 GB)',
  medium: '中型 (4 vCPU, 16 GB)',
  large: '大型 (8 vCPU, 32 GB)',
  xlarge: '超大型 (16 vCPU, 64 GB)',
};
