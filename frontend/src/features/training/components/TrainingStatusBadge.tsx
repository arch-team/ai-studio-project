/**
 * Training Status Badge Component
 *
 * 显示训练任务状态的徽章组件
 */

import type { StatusIndicatorProps } from '@cloudscape-design/components';
import { StatusBadge } from '@shared/components';
import type { JobStatus } from '../types';
import { JOB_STATUS_LABELS } from '../types';

const STATUS_TYPE_MAP: Record<JobStatus, StatusIndicatorProps['type']> = {
  submitted: 'pending',
  running: 'in-progress',
  paused: 'warning',
  preempted: 'warning',
  completed: 'success',
  failed: 'error',
};

export function TrainingStatusBadge({ status }: { status: JobStatus }) {
  return <StatusBadge status={status} typeMap={STATUS_TYPE_MAP} labelMap={JOB_STATUS_LABELS} />;
}

export default TrainingStatusBadge;
