/**
 * Monitoring API client functions.
 */

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

const API_BASE = '/api/v1';

// === Cluster APIs ===

/**
 * Fetch list of HyperPod clusters.
 */
export async function fetchClusters(
  filters: ClusterFilters = {}
): Promise<ClusterListResponse> {
  const params = new URLSearchParams();

  if (filters.status) params.append('status', filters.status);
  if (filters.health_status) params.append('health_status', filters.health_status);
  if (filters.region) params.append('region', filters.region);

  const response = await fetch(`${API_BASE}/clusters?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch clusters: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single cluster by ID.
 */
export async function fetchCluster(id: number): Promise<ClusterDetail> {
  const response = await fetch(`${API_BASE}/clusters/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cluster: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch nodes for a cluster.
 */
export async function fetchClusterNodes(clusterId: number): Promise<NodeListResponse> {
  const response = await fetch(`${API_BASE}/clusters/${clusterId}/nodes`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cluster nodes: ${response.statusText}`);
  }
  return response.json();
}

// === Metrics APIs ===

/**
 * Fetch cluster metrics (CPU, memory, GPU utilization).
 */
export async function fetchClusterMetrics(
  clusterId: number,
  filters: MetricFilters = {}
): Promise<ClusterMetrics[]> {
  const params = new URLSearchParams();

  if (filters.start_time) params.append('start_time', filters.start_time);
  if (filters.end_time) params.append('end_time', filters.end_time);
  if (filters.step) params.append('step', String(filters.step));

  const response = await fetch(
    `${API_BASE}/clusters/${clusterId}/metrics?${params.toString()}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch cluster metrics: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch specific metric series from Prometheus.
 */
export async function fetchMetricSeries(
  filters: MetricFilters = {}
): Promise<MetricSeries[]> {
  const params = new URLSearchParams();

  if (filters.metric_names) {
    filters.metric_names.forEach((name) => params.append('metric_names', name));
  }
  if (filters.start_time) params.append('start_time', filters.start_time);
  if (filters.end_time) params.append('end_time', filters.end_time);
  if (filters.step) params.append('step', String(filters.step));

  const response = await fetch(`${API_BASE}/monitoring/metrics?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch metric series: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch current resource utilization overview.
 */
export async function fetchResourceUtilization(
  clusterId?: number
): Promise<ResourceUtilization[]> {
  const params = new URLSearchParams();
  if (clusterId) params.append('cluster_id', String(clusterId));

  const response = await fetch(
    `${API_BASE}/monitoring/utilization?${params.toString()}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch resource utilization: ${response.statusText}`);
  }
  return response.json();
}

// === Alert APIs ===

/**
 * Fetch alerts.
 */
export async function fetchAlerts(
  filters: AlertFilters = {}
): Promise<AlertListResponse> {
  const params = new URLSearchParams();

  if (filters.severity) params.append('severity', filters.severity);
  if (filters.status) params.append('status', filters.status);
  if (filters.resource_type) params.append('resource_type', filters.resource_type);
  if (filters.start_time) params.append('start_time', filters.start_time);
  if (filters.end_time) params.append('end_time', filters.end_time);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));

  const response = await fetch(`${API_BASE}/monitoring/alerts?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch alerts: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Acknowledge an alert.
 */
export async function acknowledgeAlert(alertId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/monitoring/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to acknowledge alert: ${response.statusText}`);
  }
}
