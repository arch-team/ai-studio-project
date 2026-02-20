/**
 * Dataset Status Badge Component
 *
 * 显示数据集状态的徽章组件
 */

import type { StatusIndicatorProps } from '@cloudscape-design/components';
import { StatusBadge } from '@shared/components';
import type { DatasetStatus } from '../types';
import { DATASET_STATUS_LABELS } from '../types';

const STATUS_TYPE_MAP: Record<DatasetStatus, StatusIndicatorProps['type']> = {
  available: 'success',
  preparing: 'in-progress',
  archived: 'stopped',
  error: 'error',
};

export function DatasetStatusBadge({ status }: { status: DatasetStatus }) {
  return <StatusBadge status={status} typeMap={STATUS_TYPE_MAP} labelMap={DATASET_STATUS_LABELS} />;
}

export default DatasetStatusBadge;
