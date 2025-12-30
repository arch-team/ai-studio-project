/**
 * 训练任务工具函数
 */

import { TrainingJobStatus } from '../types/training';

/**
 * 状态颜色映射
 */
export const statusColors: Record<TrainingJobStatus, string> = {
  [TrainingJobStatus.PENDING]: 'bg-gray-100 text-gray-800',
  [TrainingJobStatus.QUEUED]: 'bg-blue-100 text-blue-800',
  [TrainingJobStatus.RUNNING]: 'bg-green-100 text-green-800',
  [TrainingJobStatus.COMPLETED]: 'bg-emerald-100 text-emerald-800',
  [TrainingJobStatus.FAILED]: 'bg-red-100 text-red-800',
  [TrainingJobStatus.CANCELLED]: 'bg-orange-100 text-orange-800',
  [TrainingJobStatus.TIMEOUT]: 'bg-yellow-100 text-yellow-800',
};

/**
 * 状态显示文本
 */
export const statusLabels: Record<TrainingJobStatus, string> = {
  [TrainingJobStatus.PENDING]: '待启动',
  [TrainingJobStatus.QUEUED]: '排队中',
  [TrainingJobStatus.RUNNING]: '运行中',
  [TrainingJobStatus.COMPLETED]: '已完成',
  [TrainingJobStatus.FAILED]: '失败',
  [TrainingJobStatus.CANCELLED]: '已取消',
  [TrainingJobStatus.TIMEOUT]: '超时',
};

/**
 * 判断任务是否处于活跃状态
 */
export function isJobActive(status: TrainingJobStatus): boolean {
  return [TrainingJobStatus.PENDING, TrainingJobStatus.QUEUED, TrainingJobStatus.RUNNING].includes(
    status
  );
}

/**
 * 判断任务是否处于终止状态
 */
export function isJobTerminal(status: TrainingJobStatus): boolean {
  return [
    TrainingJobStatus.COMPLETED,
    TrainingJobStatus.FAILED,
    TrainingJobStatus.CANCELLED,
    TrainingJobStatus.TIMEOUT,
  ].includes(status);
}

/**
 * 格式化持续时间
 */
export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

/**
 * 格式化时间戳
 */
export function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return '-';

  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 计算资源总量
 */
export function calculateTotalResources(config: {
  node_count: number;
  gpu_per_node: number;
  cpu_per_node: number;
  memory_per_node_gb: number;
}): {
  totalGpus: number;
  totalCpus: number;
  totalMemoryGb: number;
} {
  return {
    totalGpus: config.node_count * config.gpu_per_node,
    totalCpus: config.node_count * config.cpu_per_node,
    totalMemoryGb: config.node_count * config.memory_per_node_gb,
  };
}

/**
 * 获取框架显示名称
 */
export const frameworkLabels: Record<string, string> = {
  PYTORCH: 'PyTorch',
  TENSORFLOW: 'TensorFlow',
  JFLUX: 'JFlux',
  DEEPSPEED: 'DeepSpeed',
  MEGATRON: 'Megatron',
};

/**
 * 获取任务类型显示名称
 */
export const jobTypeLabels: Record<string, string> = {
  SINGLE_NODE: '单节点',
  DATA_PARALLEL: '数据并行',
  MODEL_PARALLEL: '模型并行',
  HYBRID_PARALLEL: '混合并行',
};
