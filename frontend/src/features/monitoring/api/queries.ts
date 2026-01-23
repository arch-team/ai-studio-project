/**
 * TanStack Query hooks for Monitoring.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type { ClusterFilters, MetricFilters, AlertFilters } from '../types';
import {
  fetchClusters,
  fetchCluster,
  fetchClusterNodes,
  fetchClusterMetrics,
  fetchMetricSeries,
  fetchResourceUtilization,
  fetchAlerts,
  acknowledgeAlert,
} from './monitoringApi';

// === Cluster Query Hooks ===

/**
 * Fetch list of HyperPod clusters.
 */
export function useClusters(filters: ClusterFilters = {}) {
  return useQuery({
    queryKey: queryKeys.monitoring.clusters(filters as Record<string, unknown>),
    queryFn: () => fetchClusters(filters),
    // 集群状态每 30 秒刷新一次
    refetchInterval: 30000,
  });
}

/**
 * Fetch a single cluster by ID.
 */
export function useCluster(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.monitoring.clusterDetail(String(id!)),
    queryFn: () => fetchCluster(id!),
    enabled: id !== undefined,
    refetchInterval: 30000,
  });
}

/**
 * Fetch nodes for a cluster.
 */
export function useClusterNodes(clusterId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.monitoring.clusterNodes(String(clusterId!)),
    queryFn: () => fetchClusterNodes(clusterId!),
    enabled: clusterId !== undefined,
    refetchInterval: 30000,
  });
}

// === Metrics Query Hooks ===

/**
 * Fetch cluster metrics with automatic refresh.
 */
export function useClusterMetrics(
  clusterId: number | undefined,
  filters: MetricFilters = {},
  pollInterval?: number
) {
  return useQuery({
    queryKey: queryKeys.monitoring.clusterMetrics(String(clusterId!), filters as Record<string, unknown>),
    queryFn: () => fetchClusterMetrics(clusterId!, filters),
    enabled: clusterId !== undefined,
    refetchInterval: pollInterval || 60000, // 默认每分钟刷新
  });
}

/**
 * Fetch specific metric series from Prometheus.
 */
export function useMetricSeries(filters: MetricFilters = {}, pollInterval?: number) {
  return useQuery({
    queryKey: queryKeys.monitoring.metrics(filters as Record<string, unknown>),
    queryFn: () => fetchMetricSeries(filters),
    enabled: (filters.metric_names?.length ?? 0) > 0,
    refetchInterval: pollInterval || 60000,
  });
}

/**
 * Fetch current resource utilization overview.
 */
export function useResourceUtilization(clusterId?: number) {
  return useQuery({
    queryKey: queryKeys.monitoring.utilization(clusterId ? String(clusterId) : 'all'),
    queryFn: () => fetchResourceUtilization(clusterId),
    refetchInterval: 30000,
  });
}

// === Alert Query Hooks ===

/**
 * Fetch alerts.
 */
export function useAlerts(filters: AlertFilters = {}) {
  return useQuery({
    queryKey: queryKeys.monitoring.alerts(filters as Record<string, unknown>),
    queryFn: () => fetchAlerts(filters),
    refetchInterval: 30000,
  });
}

/**
 * Acknowledge an alert.
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => acknowledgeAlert(alertId),
    onSuccess: () => {
      // 刷新告警列表
      queryClient.invalidateQueries({ queryKey: queryKeys.monitoring.alertsAll() });
    },
  });
}
