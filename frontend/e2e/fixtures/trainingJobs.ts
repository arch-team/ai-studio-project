/**
 * E2E 测试固件 - 训练任务数据
 *
 * 用于 Playwright E2E 测试的 Mock 数据
 */

import type { TrainingJobSummary, TrainingJobDetail } from '../../src/features/training/types';

/**
 * 训练任务摘要列表 Mock 数据
 */
export const mockTrainingJobs: TrainingJobSummary[] = [
  {
    id: 1,
    job_name: 'llama2-finetune-001',
    display_name: 'LLaMA 2 微调训练',
    owner_id: 1,
    owner_username: 'admin',
    status: 'running',
    priority: 'high',
    instance_type: 'ml.p4d.24xlarge',
    node_count: 4,
    gpu_per_node: 8,
    distribution_strategy: 'fsdp',
    current_epoch: 3,
    total_epochs: 10,
    latest_loss: 0.342,
    checkpoints_count: 3,
    submitted_at: '2024-01-15T08:00:00Z',
    started_at: '2024-01-15T08:05:00Z',
    completed_at: null,
    created_at: '2024-01-15T07:55:00Z',
    duration_seconds: 7200,
    estimated_cost_usd: 256.5,
  },
  {
    id: 2,
    job_name: 'bert-pretrain-002',
    display_name: 'BERT 预训练',
    owner_id: 2,
    owner_username: 'developer',
    status: 'completed',
    priority: 'medium',
    instance_type: 'ml.p4d.24xlarge',
    node_count: 2,
    gpu_per_node: 8,
    distribution_strategy: 'ddp',
    current_epoch: 5,
    total_epochs: 5,
    latest_loss: 0.125,
    checkpoints_count: 5,
    submitted_at: '2024-01-14T10:00:00Z',
    started_at: '2024-01-14T10:10:00Z',
    completed_at: '2024-01-14T22:30:00Z',
    created_at: '2024-01-14T09:50:00Z',
    duration_seconds: 44400,
    estimated_cost_usd: 512.0,
  },
  {
    id: 3,
    job_name: 'gpt-train-003',
    display_name: 'GPT 训练任务',
    owner_id: 1,
    owner_username: 'admin',
    status: 'paused',
    priority: 'medium',
    instance_type: 'ml.g5.12xlarge',
    node_count: 2,
    gpu_per_node: 4,
    distribution_strategy: 'ddp',
    current_epoch: 4,
    total_epochs: 10,
    latest_loss: 0.456,
    checkpoints_count: 2,
    submitted_at: '2024-01-13T14:00:00Z',
    started_at: '2024-01-13T14:05:00Z',
    completed_at: null,
    created_at: '2024-01-13T13:55:00Z',
    duration_seconds: 14400,
    estimated_cost_usd: 95.0,
  },
  {
    id: 4,
    job_name: 'failed-job-004',
    display_name: '失败的训练任务',
    owner_id: 1,
    owner_username: 'admin',
    status: 'failed',
    priority: 'low',
    instance_type: 'ml.g5.12xlarge',
    node_count: 1,
    gpu_per_node: 4,
    distribution_strategy: 'ddp',
    current_epoch: 2,
    total_epochs: 10,
    latest_loss: 1.234,
    checkpoints_count: 1,
    submitted_at: '2024-01-12T10:00:00Z',
    started_at: '2024-01-12T10:05:00Z',
    completed_at: '2024-01-12T10:30:00Z',
    created_at: '2024-01-12T09:55:00Z',
    duration_seconds: 1500,
    estimated_cost_usd: 15.0,
  },
  {
    id: 5,
    job_name: 'preempted-job-005',
    display_name: '被抢占的任务',
    owner_id: 2,
    owner_username: 'developer',
    status: 'preempted',
    priority: 'low',
    instance_type: 'ml.p4d.24xlarge',
    node_count: 4,
    gpu_per_node: 8,
    distribution_strategy: 'fsdp',
    current_epoch: 6,
    total_epochs: 20,
    latest_loss: 0.289,
    checkpoints_count: 4,
    submitted_at: '2024-01-11T08:00:00Z',
    started_at: '2024-01-11T08:10:00Z',
    completed_at: null,
    created_at: '2024-01-11T07:55:00Z',
    duration_seconds: 21600,
    estimated_cost_usd: 180.0,
  },
];

/**
 * 根据 ID 获取训练任务详情
 */
export function getMockTrainingJobDetail(id: number): TrainingJobDetail | null {
  const summary = mockTrainingJobs.find((job) => job.id === id);
  if (!summary) return null;

  return {
    ...summary,
    description: `${summary.display_name || summary.job_name} 的详细描述信息`,
    hyperpod_status: summary.status === 'running' ? 'InService' : null,
    kueue_workload_name: `workload-${summary.job_name}`,
    kueue_status: summary.status === 'running' ? 'Admitted' : null,
    image_uri: 'public.ecr.aws/pytorch-training:2.0.0-gpu-py310-cu118-ubuntu20.04',
    tasks_per_node: 1,
    entry_point: 'train.py',
    entrypoint_command: ['python', 'train.py'],
    environment_variables: { NCCL_DEBUG: 'INFO', CUDA_VISIBLE_DEVICES: '0,1,2,3' },
    dataset_id: 1,
    dataset_name: 'training-dataset-v1',
    data_mount_path: '/opt/ml/input/data',
    checkpoint_mount_path: '/opt/ml/checkpoints',
    hyperparameters: { warmup_steps: 1000, weight_decay: 0.01, learning_rate: 0.0001 },
    max_epochs: summary.total_epochs,
    batch_size: 32,
    learning_rate: 0.0001,
    distribution_strategy: summary.distribution_strategy || 'ddp',
    mixed_precision: true,
    use_spot_instances: false,
    total_pods: summary.node_count,
    running_pods: summary.status === 'running' ? summary.node_count : 0,
    failed_pods: summary.status === 'failed' ? 1 : 0,
    preemption_count: summary.status === 'preempted' ? 1 : 0,
    current_step: (summary.current_epoch || 0) * 1000,
    latest_accuracy: summary.status === 'completed' ? 0.92 : null,
    total_gpu_hours:
      ((summary.duration_seconds || 0) / 3600) * summary.node_count * summary.gpu_per_node,
    error_message: summary.status === 'failed' ? 'CUDA OOM: 显存不足' : null,
    failure_reason: summary.status === 'failed' ? 'ResourceExhausted' : null,
    hyperpod_job_arn: `arn:aws:sagemaker:us-west-2:123456789012:training-job/${summary.job_name}`,
    updated_at: new Date().toISOString(),
  };
}

/**
 * 根据状态筛选任务
 */
export function filterJobsByStatus(status: string): TrainingJobSummary[] {
  if (!status || status === 'all') return mockTrainingJobs;
  return mockTrainingJobs.filter((job) => job.status === status);
}

/**
 * 根据优先级筛选任务
 */
export function filterJobsByPriority(priority: string): TrainingJobSummary[] {
  if (!priority || priority === 'all') return mockTrainingJobs;
  return mockTrainingJobs.filter((job) => job.priority === priority);
}

/**
 * 生成分页响应
 */
export function createPaginatedResponse(
  items: TrainingJobSummary[],
  page: number = 1,
  pageSize: number = 20,
) {
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const paginatedItems = items.slice(start, end);

  return {
    items: paginatedItems,
    total: items.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(items.length / pageSize),
  };
}
