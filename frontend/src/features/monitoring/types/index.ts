/**
 * Monitoring module type definitions.
 * Maps to backend schemas: src/modules/monitoring/
 *
 * 监控模块 - 集群状态、资源利用率、训练指标
 */

// === Enums ===

export type ClusterStatus = 'creating' | 'active' | 'updating' | 'deleting' | 'failed';

export type ClusterHealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export type NodeStatus = 'ready' | 'not_ready' | 'unknown';

export type MetricType = 'gauge' | 'counter' | 'histogram';

// === Cluster Types ===

export interface ClusterSummary {
  id: number;
  cluster_name: string;
  cluster_arn: string;
  region: string;
  status: ClusterStatus;
  health_status: ClusterHealthStatus | null;
  total_nodes: number;
  available_nodes: number;
  total_gpu_count: number | null;
  available_gpu_count: number | null;
  total_cpu_cores: number | null;
  available_cpu_cores: number | null;
  last_sync_at: string | null;
  created_at: string;
}

export interface ClusterDetail extends ClusterSummary {
  vpc_id: string;
  instance_groups: InstanceGroup[];
  total_memory_gb: number | null;
  available_memory_gb: number | null;
  fsx_filesystem_id: string | null;
  fsx_mount_point: string | null;
  prometheus_endpoint: string | null;
  grafana_workspace_id: string | null;
  running_jobs_count: number;
  pending_jobs_count: number;
  updated_at: string;
}

export interface InstanceGroup {
  instance_group_name: string;
  instance_type: string;
  instance_count: number;
  available_count: number;
  capacity_type: 'on_demand' | 'spot';
  spot_interruption_behavior?: 'stop' | 'terminate' | 'hibernate';
}

// === Node Types ===

export interface NodeSummary {
  node_name: string;
  instance_type: string;
  instance_group: string;
  status: NodeStatus;
  cpu_capacity: number;
  cpu_used: number;
  memory_capacity_gb: number;
  memory_used_gb: number;
  gpu_capacity: number;
  gpu_used: number;
  pod_count: number;
  age: string;
}

// === Metrics Types ===

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricSeries {
  metric_name: string;
  labels: Record<string, string>;
  data_points: MetricDataPoint[];
}

export interface ClusterMetrics {
  cluster_id: number;
  timestamp: string;
  cpu_utilization: number;
  memory_utilization: number;
  gpu_utilization: number | null;
  network_in_bytes: number;
  network_out_bytes: number;
  disk_read_bytes: number;
  disk_write_bytes: number;
}

export interface ResourceUtilization {
  resource_type: 'cpu' | 'memory' | 'gpu' | 'storage';
  total: number;
  used: number;
  available: number;
  utilization_percentage: number;
  unit: string;
}

// === Alert Types ===

export interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;
  resource_type: string;
  resource_id: string;
  fired_at: string;
  resolved_at: string | null;
  status: 'firing' | 'resolved' | 'acknowledged';
}

// === Filter Types ===

export interface ClusterFilters {
  status?: ClusterStatus;
  health_status?: ClusterHealthStatus;
  region?: string;
}

export interface MetricFilters {
  metric_names?: string[];
  start_time?: string;
  end_time?: string;
  step?: number; // seconds
}

export interface AlertFilters {
  severity?: 'critical' | 'warning' | 'info';
  status?: 'firing' | 'resolved' | 'acknowledged';
  resource_type?: string;
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

// === Response Types ===

export interface ClusterListResponse {
  items: ClusterSummary[];
  total: number;
}

export interface NodeListResponse {
  items: NodeSummary[];
  total: number;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === UI Helper Types ===

export const CLUSTER_STATUS_LABELS: Record<ClusterStatus, string> = {
  creating: '创建中',
  active: '活跃',
  updating: '更新中',
  deleting: '删除中',
  failed: '失败',
};

export const CLUSTER_STATUS_COLORS: Record<
  ClusterStatus,
  'blue' | 'green' | 'pending' | 'red' | 'grey'
> = {
  creating: 'blue',
  active: 'green',
  updating: 'pending',
  deleting: 'grey',
  failed: 'red',
};

export const CLUSTER_HEALTH_LABELS: Record<ClusterHealthStatus, string> = {
  healthy: '健康',
  degraded: '降级',
  unhealthy: '不健康',
};

export const CLUSTER_HEALTH_COLORS: Record<ClusterHealthStatus, 'green' | 'pending' | 'red'> = {
  healthy: 'green',
  degraded: 'pending',
  unhealthy: 'red',
};

export const NODE_STATUS_LABELS: Record<NodeStatus, string> = {
  ready: '就绪',
  not_ready: '未就绪',
  unknown: '未知',
};

export const NODE_STATUS_COLORS: Record<NodeStatus, 'green' | 'red' | 'grey'> = {
  ready: 'green',
  not_ready: 'red',
  unknown: 'grey',
};

export const ALERT_SEVERITY_LABELS: Record<Alert['severity'], string> = {
  critical: '严重',
  warning: '警告',
  info: '信息',
};

export const ALERT_SEVERITY_COLORS: Record<Alert['severity'], 'red' | 'pending' | 'blue'> = {
  critical: 'red',
  warning: 'pending',
  info: 'blue',
};
