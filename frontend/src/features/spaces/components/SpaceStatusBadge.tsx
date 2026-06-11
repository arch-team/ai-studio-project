/**
 * Space Status Badge Component
 *
 * 开发空间状态徽章组件 - 基于 Cloudscape StatusIndicator
 */

import type { StatusIndicatorProps } from '@cloudscape-design/components';
import { StatusBadge } from '@shared/components/StatusBadge';
import type { SpaceStatus } from '../types';
import { SPACE_STATUS_LABELS } from '../types';

// 状态到 StatusIndicator 类型的映射
const SPACE_STATUS_TYPE_MAP: Record<SpaceStatus, StatusIndicatorProps['type']> = {
  pending: 'in-progress',
  running: 'success',
  stopped: 'stopped',
  failed: 'error',
  deleted: 'stopped',
};

interface SpaceStatusBadgeProps {
  status: SpaceStatus;
}

/**
 * 开发空间状态徽章
 */
export function SpaceStatusBadge({ status }: SpaceStatusBadgeProps) {
  return (
    <StatusBadge<SpaceStatus>
      status={status}
      typeMap={SPACE_STATUS_TYPE_MAP}
      labelMap={SPACE_STATUS_LABELS}
    />
  );
}
