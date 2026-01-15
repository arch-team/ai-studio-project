/**
 * Model Status Badge Component
 *
 * 显示模型状态的徽章组件
 */

import { StatusIndicator, StatusIndicatorProps } from '@cloudscape-design/components';
import type { ModelStatus } from '../types';
import { MODEL_STATUS_LABELS } from '../types';

// 状态到 StatusIndicator 类型的映射
const statusTypeMap: Record<ModelStatus, StatusIndicatorProps['type']> = {
  training: 'in-progress',
  registered: 'success',
  deployed: 'success',
  archived: 'stopped',
  failed: 'error',
};

interface ModelStatusBadgeProps {
  status: ModelStatus;
}

/**
 * 模型状态徽章
 */
export function ModelStatusBadge({ status }: ModelStatusBadgeProps) {
  const type = statusTypeMap[status] || 'info';
  const label = MODEL_STATUS_LABELS[status] || status;

  return <StatusIndicator type={type}>{label}</StatusIndicator>;
}

export default ModelStatusBadge;
