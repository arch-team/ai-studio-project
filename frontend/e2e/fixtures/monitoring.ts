/**
 * 监控页 E2E 测试 Mock 数据
 *
 * 提供四个监控端点的 Mock 响应数据，与后端 dev 环境真实数据形态对齐：
 * - /clusters → 集群列表 (ai-platform-dev-hyperpod, status=active, 3 节点)
 * - /monitoring/utilization → CPU/内存/GPU 利用率
 * - /monitoring/metrics → 时间序列
 * - /monitoring/alerts → 空集 (告警子系统未实现)
 */

import type {
  ClusterSummary,
  ClusterListResponse,
  ResourceUtilization,
  MetricSeries,
  AlertListResponse,
} from '../../src/features/monitoring/types';

/**
 * Mock 集群列表 (对齐 dev 环境真实集群)
 */
export const mockClusters: ClusterSummary[] = [
  {
    id: 1,
    cluster_name: 'ai-platform-dev-hyperpod',
    cluster_arn:
      'arn:aws:sagemaker:us-east-1:123456789012:cluster/ai-platform-dev-hyperpod',
    region: 'us-east-1',
    status: 'active',
    health_status: 'healthy',
    total_nodes: 3,
    available_nodes: 3,
    total_gpu_count: 0,
    available_gpu_count: 0,
    total_cpu_cores: 12,
    available_cpu_cores: 11,
    last_sync_at: '2026-06-13T08:00:00Z',
    created_at: '2026-05-01T10:00:00Z',
  },
];

export const mockClusterListResponse: ClusterListResponse = {
  items: mockClusters,
  total: mockClusters.length,
};

/**
 * Mock 资源利用率 (对齐 dev 环境真实低利用率形态)
 */
export const mockUtilization: ResourceUtilization[] = [
  {
    resource_type: 'cpu',
    total: 12,
    used: 1,
    available: 11,
    utilization_percentage: 5,
    unit: 'cores',
  },
  {
    resource_type: 'memory',
    total: 48,
    used: 6,
    available: 42,
    utilization_percentage: 12,
    unit: 'GB',
  },
  {
    resource_type: 'gpu',
    total: 0,
    used: 0,
    available: 0,
    utilization_percentage: 0,
    unit: 'cards',
  },
];

/**
 * 生成 Mock 时间序列指标数据
 *
 * @param metricNames 指标名称列表
 * @param points 每条序列的数据点数量
 */
export function buildMockMetricSeries(
  metricNames: string[] = [
    'cpu_utilization',
    'memory_utilization',
    'gpu_utilization',
  ],
  points = 10,
): MetricSeries[] {
  const now = Date.now();
  return metricNames.map((name, seriesIndex) => ({
    metric_name: name,
    labels: { cluster: 'ai-platform-dev-hyperpod' },
    data_points: Array.from({ length: points }, (_, i) => ({
      timestamp: new Date(now - (points - i) * 60_000).toISOString(),
      // 生成确定性的、随序列偏移的数值，便于折线图渲染
      value: Number((5 + seriesIndex * 3 + i * 0.5).toFixed(2)),
    })),
  }));
}

/**
 * Mock 告警空集 (告警子系统未实现，本轮返空)
 */
export const mockEmptyAlertResponse: AlertListResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0,
};
