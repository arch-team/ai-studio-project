/**
 * 通用状态徽章组件
 *
 * 基于 Cloudscape StatusIndicator 的泛型封装，
 * 供各模块的状态徽章组件复用。
 */

import { StatusIndicator, StatusIndicatorProps } from '@cloudscape-design/components';

interface StatusBadgeProps<S extends string> {
  status: S;
  typeMap: Record<S, StatusIndicatorProps['type']>;
  labelMap: Record<S, string>;
}

export function StatusBadge<S extends string>({ status, typeMap, labelMap }: StatusBadgeProps<S>) {
  const type = typeMap[status] || 'info';
  const label = labelMap[status] || status;
  return <StatusIndicator type={type}>{label}</StatusIndicator>;
}
