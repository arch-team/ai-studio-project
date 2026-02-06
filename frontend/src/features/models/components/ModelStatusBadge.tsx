/**
 * Model Status Badge Component
 *
 * 显示模型状态的徽章组件
 */

import type { StatusIndicatorProps } from '@cloudscape-design/components';
import { StatusBadge } from '@shared/components';
import type { ModelStatus } from '../types';
import { MODEL_STATUS_LABELS } from '../types';

const STATUS_TYPE_MAP: Record<ModelStatus, StatusIndicatorProps['type']> = {
  training: 'in-progress',
  registered: 'success',
  deployed: 'success',
  archived: 'stopped',
  failed: 'error',
};

export function ModelStatusBadge({ status }: { status: ModelStatus }) {
  return <StatusBadge status={status} typeMap={STATUS_TYPE_MAP} labelMap={MODEL_STATUS_LABELS} />;
}

export default ModelStatusBadge;
