/**
 * Job Templates Types
 *
 * 任务模板功能的类型定义
 */

// === Enums and Constants ===

export type TemplateVisibility = 'private' | 'team' | 'public';

export const VISIBILITY_LABELS: Record<TemplateVisibility, string> = {
  private: '私有',
  team: '团队',
  public: '公开',
};

export const VISIBILITY_COLORS: Record<TemplateVisibility, 'blue' | 'green' | 'grey'> = {
  private: 'grey',
  team: 'blue',
  public: 'green',
};

// === Training Config Types ===

export type DistributionStrategy = 'ddp' | 'fsdp' | 'deepspeed' | 'horovod';

export const DISTRIBUTION_STRATEGY_LABELS: Record<DistributionStrategy, string> = {
  ddp: 'PyTorch DDP',
  fsdp: 'PyTorch FSDP',
  deepspeed: 'DeepSpeed',
  horovod: 'Horovod',
};

export interface TrainingConfig {
  image: string;
  script_path?: string;
  instance_type: string;
  instance_count: number;
  distribution_strategy: DistributionStrategy;
  environment?: Record<string, string>;
  hyperparameters?: Record<string, unknown>;
}

// === Data Models ===

export interface JobTemplateSummary {
  id: number;
  name: string;
  description?: string;
  visibility: TemplateVisibility;
  usage_count: number;
  owner_id: number;
  created_at: string;
}

export interface JobTemplateDetail extends JobTemplateSummary {
  training_config: TrainingConfig;
  last_used_at?: string;
  updated_at: string;
}

// === Request Types ===

export interface CreateJobTemplateRequest {
  name: string;
  description?: string;
  visibility?: TemplateVisibility;
  training_config: TrainingConfig;
}

export interface UpdateJobTemplateRequest {
  name?: string;
  description?: string;
  visibility?: TemplateVisibility;
  training_config?: TrainingConfig;
}

export interface CreateJobFromTemplateRequest {
  job_name: string;
  display_name?: string;
  node_count?: number;
  priority?: 'high' | 'medium' | 'low';
  environment_variables?: Record<string, string>;
}

// === Filter and Pagination Types ===

export interface TemplateFilters {
  search?: string;
  visibility?: TemplateVisibility;
  page?: number;
  page_size?: number;
  sort_by?: 'usage_count' | 'created_at' | 'name';
  sort_order?: 'asc' | 'desc';
}

export interface TemplateListResponse {
  items: JobTemplateSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === Constants ===

export const DEFAULT_PAGE_SIZE = 20;

export const SORT_OPTIONS = [
  { value: 'usage_count', label: '使用次数' },
  { value: 'created_at', label: '创建时间' },
  { value: 'name', label: '名称' },
] as const;

export const INSTANCE_TYPE_OPTIONS = [
  { value: 'ml.p4d.24xlarge', label: 'ml.p4d.24xlarge (8x A100 40GB)' },
  { value: 'ml.p4de.24xlarge', label: 'ml.p4de.24xlarge (8x A100 80GB)' },
  { value: 'ml.p5.48xlarge', label: 'ml.p5.48xlarge (8x H100)' },
  { value: 'ml.g5.xlarge', label: 'ml.g5.xlarge (1x A10G)' },
  { value: 'ml.g5.12xlarge', label: 'ml.g5.12xlarge (4x A10G)' },
] as const;
