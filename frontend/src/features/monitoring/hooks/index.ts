/**
 * Monitoring business logic hooks.
 */

import { useMemo } from 'react';
import type {
  ClusterSummary,
  NodeSummary,
  ResourceUtilization,
  Alert,
  ClusterHealthStatus,
} from '../types';

/**
 * 计算集群总体统计
 */
export function useClusterStats(clusters: ClusterSummary[] | undefined) {
  return useMemo(() => {
    if (!clusters) {
      return {
        total: 0,
        active: 0,
        unhealthy: 0,
        totalNodes: 0,
        availableNodes: 0,
        totalGPUs: 0,
        availableGPUs: 0,
      };
    }

    return clusters.reduce(
      (acc, cluster) => {
        acc.total++;
        if (cluster.status === 'active') acc.active++;
        if (cluster.health_status === 'unhealthy') acc.unhealthy++;
        acc.totalNodes += cluster.total_nodes;
        acc.availableNodes += cluster.available_nodes;
        acc.totalGPUs += cluster.total_gpu_count || 0;
        acc.availableGPUs += cluster.available_gpu_count || 0;
        return acc;
      },
      {
        total: 0,
        active: 0,
        unhealthy: 0,
        totalNodes: 0,
        availableNodes: 0,
        totalGPUs: 0,
        availableGPUs: 0,
      }
    );
  }, [clusters]);
}

/**
 * 计算节点健康状态统计
 */
export function useNodeStats(nodes: NodeSummary[] | undefined) {
  return useMemo(() => {
    if (!nodes) {
      return {
        total: 0,
        ready: 0,
        notReady: 0,
        unknown: 0,
      };
    }

    return nodes.reduce(
      (acc, node) => {
        acc.total++;
        if (node.status === 'ready') acc.ready++;
        else if (node.status === 'not_ready') acc.notReady++;
        else acc.unknown++;
        return acc;
      },
      { total: 0, ready: 0, notReady: 0, unknown: 0 }
    );
  }, [nodes]);
}

/**
 * 格式化资源利用率
 */
export function useFormatUtilization() {
  return (utilization: ResourceUtilization): string => {
    const { used, total, unit, utilization_percentage: pct } = utilization;
    return `${used.toFixed(1)} / ${total.toFixed(1)} ${unit} (${pct.toFixed(1)}%)`;
  };
}

/**
 * 获取资源利用率状态颜色
 */
export function useUtilizationColor() {
  return (percentage: number): 'green' | 'pending' | 'red' => {
    if (percentage < 60) return 'green';
    if (percentage < 85) return 'pending';
    return 'red';
  };
}

/**
 * 计算告警统计
 */
export function useAlertStats(alerts: Alert[] | undefined) {
  return useMemo(() => {
    if (!alerts) {
      return {
        total: 0,
        critical: 0,
        warning: 0,
        info: 0,
        firing: 0,
        resolved: 0,
        acknowledged: 0,
      };
    }

    return alerts.reduce(
      (acc, alert) => {
        acc.total++;
        acc[alert.severity]++;
        acc[alert.status]++;
        return acc;
      },
      {
        total: 0,
        critical: 0,
        warning: 0,
        info: 0,
        firing: 0,
        resolved: 0,
        acknowledged: 0,
      }
    );
  }, [alerts]);
}

/**
 * 计算集群整体健康状态
 */
export function useOverallHealthStatus(
  clusters: ClusterSummary[] | undefined
): ClusterHealthStatus {
  return useMemo(() => {
    if (!clusters || clusters.length === 0) return 'unknown' as ClusterHealthStatus;

    const hasUnhealthy = clusters.some((c) => c.health_status === 'unhealthy');
    if (hasUnhealthy) return 'unhealthy';

    const hasDegraded = clusters.some((c) => c.health_status === 'degraded');
    if (hasDegraded) return 'degraded';

    return 'healthy';
  }, [clusters]);
}

/**
 * 格式化字节数为可读字符串
 */
export function useFormatBytes() {
  return (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    let size = bytes;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(unitIndex > 0 ? 2 : 0)} ${units[unitIndex]}`;
  };
}
