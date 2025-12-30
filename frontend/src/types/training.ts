/**
 * 训练任务类型定义
 */

// 训练任务状态
export enum TrainingJobStatus {
  PENDING = 'PENDING',
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  TIMEOUT = 'TIMEOUT',
}

// 训练任务类型
export enum TrainingJobType {
  SINGLE_NODE = 'SINGLE_NODE',
  DATA_PARALLEL = 'DATA_PARALLEL',
  MODEL_PARALLEL = 'MODEL_PARALLEL',
  HYBRID_PARALLEL = 'HYBRID_PARALLEL',
}

// 训练框架
export enum FrameworkType {
  PYTORCH = 'PYTORCH',
  TENSORFLOW = 'TENSORFLOW',
  JFLUX = 'JFLUX',
  DEEPSPEED = 'DEEPSPEED',
  MEGATRON = 'MEGATRON',
}

// 训练任务配置
export interface TrainingJobConfig {
  id: number;
  job_id: number;

  // 资源配置
  node_count: number;
  gpu_per_node: number;
  cpu_per_node: number;
  memory_per_node_gb: number;
  gpu_type: string | null;

  // 容器配置
  docker_image: string;
  command: string[];
  args: string[] | null;
  env_vars: Record<string, string> | null;

  // 数据配置
  dataset_path: string | null;
  checkpoint_path: string | null;
  output_path: string;

  // 训练配置
  hyperparameters: Record<string, any> | null;
  distributed_config: Record<string, any> | null;

  // 执行配置
  timeout_seconds: number | null;
  max_retries: number;
}

// 训练任务
export interface TrainingJob {
  id: number;
  name: string;
  description: string | null;
  status: TrainingJobStatus;
  job_type: TrainingJobType;
  framework: FrameworkType;

  // 关联
  project_id: number;
  creator_id: number;

  // K8S信息
  k8s_namespace: string;
  k8s_job_name: string | null;
  k8s_pod_names: string[] | null;

  // 时间戳
  queued_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;

  // 错误信息
  error_message: string | null;

  // 配置(可选)
  config?: TrainingJobConfig;
}

// 训练任务状态响应
export interface TrainingJobStatusResponse {
  id: number;
  name: string;
  status: string;
  is_active: boolean;
  is_terminal: boolean;

  // 时间信息
  queued_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;

  // K8S信息
  k8s_job_name: string | null;
  k8s_status?: {
    active: number;
    succeeded: number;
    failed: number;
    start_time: string | null;
    completion_time: string | null;
    conditions: any[];
  };
  pods?: Array<{
    name: string;
    phase: string;
    start_time: string | null;
  }>;

  // 错误信息
  error_message: string | null;
  k8s_error?: string;
}

// 训练任务列表响应
export interface TrainingJobListResponse {
  total: number;
  items: TrainingJob[];
  page: number;
  page_size: number;
}

// 训练任务创建请求
export interface TrainingJobCreateRequest {
  name: string;
  description?: string;
  job_type: TrainingJobType;
  framework: FrameworkType;
  project_id: number;
  config: {
    // 资源配置
    node_count?: number;
    gpu_per_node?: number;
    cpu_per_node?: number;
    memory_per_node_gb?: number;
    gpu_type?: string;

    // 容器配置
    docker_image: string;
    command: string[];
    args?: string[];
    env_vars?: Record<string, string>;

    // 数据配置
    dataset_path?: string;
    checkpoint_path?: string;
    output_path: string;

    // 训练配置
    hyperparameters?: Record<string, any>;
    distributed_config?: Record<string, any>;

    // 执行配置
    timeout_seconds?: number;
    max_retries?: number;
  };
}

// 训练任务更新请求
export interface TrainingJobUpdateRequest {
  name?: string;
  description?: string;
}

// 训练任务查询参数
export interface TrainingJobQueryParams {
  project_id?: number;
  status_filter?: string;
  page?: number;
  page_size?: number;
}
