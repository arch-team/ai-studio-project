/**
 * Training Status Badge Component
 *
 * 显示训练任务状态的徽章组件
 */

import { StatusIndicator, StatusIndicatorProps } from '@cloudscape-design/components';
import type { JobStatus } from '../types';
import { JOB_STATUS_LABELS } from '../types';

// 状态到 StatusIndicator 类型的映射
const statusTypeMap: Record<JobStatus, StatusIndicatorProps['type']> = {
  submitted: 'pending',
  running: 'in-progress',
  paused: 'warning',
  preempted: 'warning',
  completed: 'success',
  failed: 'error',
};

interface TrainingStatusBadgeProps {
  status: JobStatus;
}

/**
 * 训练任务状态徽章
 */
export function TrainingStatusBadge({ status }: TrainingStatusBadgeProps) {
  const type = statusTypeMap[status] || 'info';
  const label = JOB_STATUS_LABELS[status] || status;

  return <StatusIndicator type={type}>{label}</StatusIndicator>;
}

export default TrainingStatusBadge;
