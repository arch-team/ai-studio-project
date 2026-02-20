/**
 * Monitoring API client functions.
 */

import { apiClient } from '@shared/api';
import type {
  ClusterListResponse,
  ClusterDetail,
  ClusterFilters,
  NodeListResponse,
  ClusterMetrics,
  MetricSeries,
  MetricFilters,
  ResourceUtilization,
  AlertListResponse,
  AlertFilters,
} from '../types';

// === Cluster APIs ===

/**
 * Fetch list of HyperPod clusters.
 */
export async function fetchClusters(
  filters: ClusterFilters = {}
): Promise<ClusterListResponse> {
  return apiClient.get<ClusterListResponse>('/clusters', {
    params: {
      status: filters.status,
      health_status: filters.health_status,
      region: filters.region,
    },
  });
}

/**
 * Fetch a single cluster by ID.
 */
export async function fetchCluster(id: number): Promise<ClusterDetail> {
  return apiClient.get<ClusterDetail>(`/clusters/${id}`);
}

/**
 * Fetch nodes for a cluster.
 */
export async function fetchClusterNodes(clusterId: number): Promise<NodeListResponse> {
  return apiClient.get<NodeListResponse>(`/clusters/${clusterId}/nodes`);
}

// === Metrics APIs ===

/**
 * Fetch cluster metrics (CPU, memory, GPU utilization).
 */
export async function fetchClusterMetrics(
  clusterId: number,
  filters: MetricFilters = {}
): Promise<ClusterMetrics[]> {
  return apiClient.get<ClusterMetrics[]>(`/clusters/${clusterId}/metrics`, {
    params: {
      start_time: filters.start_time,
      end_time: filters.end_time,
      step: filters.step,
    },
  });
}

/**
 * Fetch specific metric series from Prometheus.
 */
export async function fetchMetricSeries(
  filters: MetricFilters = {}
): Promise<MetricSeries[]> {
  return apiClient.get<MetricSeries[]>('/monitoring/metrics', {
    params: {
      metric_names: filters.metric_names,
      start_time: filters.start_time,
      end_time: filters.end_time,
      step: filters.step,
    },
  });
}

/**
 * Fetch current resource utilization overview.
 */
export async function fetchResourceUtilization(
  clusterId?: number
): Promise<ResourceUtilization[]> {
  return apiClient.get<ResourceUtilization[]>('/monitoring/utilization', {
    params: { cluster_id: clusterId },
  });
}

// === Alert APIs ===

/**
 * Fetch alerts.
 */
export async function fetchAlerts(
  filters: AlertFilters = {}
): Promise<AlertListResponse> {
  return apiClient.get<AlertListResponse>('/monitoring/alerts', {
    params: {
      severity: filters.severity,
      status: filters.status,
      resource_type: filters.resource_type,
      start_time: filters.start_time,
      end_time: filters.end_time,
      page: filters.page,
      page_size: filters.page_size,
    },
  });
}

/**
 * Acknowledge an alert.
 */
export async function acknowledgeAlert(alertId: string): Promise<void> {
  return apiClient.post(`/monitoring/alerts/${alertId}/acknowledge`);
}
