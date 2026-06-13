/**
 * Monitoring API client functions.
 */

import { apiClient } from '@shared/api';
import type {
  ClusterListResponse,
  ClusterDetail,
  ClusterFilters,
  NodeListResponse,
  MetricSeries,
  MetricFilters,
  ResourceUtilization,
  AlertListResponse,
  AlertFilters,
} from '../types';

/**
 * 后端 GET /clusters/{id}/metrics 实际响应形状。
 *
 * 后端返回 ClusterMetricsResponse（单对象，含 cluster_name + metrics 列表），
 * 每个 metric 形如 MetricSeries（{ metric_name, data_points }）。
 * 此前误声明为 ClusterMetrics[]（形状完全不同），现按真实契约修正。
 */
interface ClusterMetricsResponse {
  cluster_name: string;
  metrics: MetricSeries[];
}

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
 *
 * 后端返回 ClusterMetricsResponse（含 metrics 列表），此处解出 metrics 返回
 * MetricSeries[]，与调用方对「指标序列列表」的预期一致。
 */
export async function fetchClusterMetrics(
  clusterId: number,
  filters: MetricFilters = {}
): Promise<MetricSeries[]> {
  const response = await apiClient.get<ClusterMetricsResponse>(`/clusters/${clusterId}/metrics`, {
    params: {
      start_time: filters.start_time,
      end_time: filters.end_time,
      step: filters.step,
    },
  });
  return response.metrics ?? [];
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
