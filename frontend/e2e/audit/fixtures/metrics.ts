/**
 * 审计用指标/报表类 fixture（dashboard / monitoring / reports）
 *
 * 形状对照:
 *   - src/features/monitoring/types/index.ts
 *     (ClusterListResponse / ResourceUtilization[] / AlertListResponse / MetricSeries[])
 *   - src/features/reports/types/index.ts
 *     (ResourceUsageResponse / CostAnalysisResponse)
 *
 * API 路径对照:
 *   GET /clusters | /monitoring/utilization | /monitoring/alerts | /monitoring/metrics
 *   GET /reports/resource-usage | /reports/cost-analysis
 *
 * 注意：/monitoring/utilization 与 /monitoring/metrics 返回**裸数组**而非
 * { items } 对象——若落入 catch-all 兜底，图表组件 .map 会崩溃，
 * 因此必须在 manifest 中显式声明。
 * 数值全部确定性写死（无 Math.random），保证截图跨次运行可复现。
 */

// === dashboard: 首页任务统计 ===

/**
 * HomePage 以 page_size=1 发起 5 个统计查询（总数 + 4 个状态），仅消费 total 字段，
 * items 留空避免误导。总数 26 与状态和 24 的差额代表 preempted/submitted 任务（首页不展示）。
 */
function jobStat(total: number) {
  return { items: [], total, page: 1, page_size: 1 };
}

export const dashboardJobStats = {
  all: jobStat(26),
  running: jobStat(3),
  completed: jobStat(18),
  failed: jobStat(2),
  paused: jobStat(1),
};

/** 按 status 查询参数返回对应统计（default 状态动态解析） */
export function resolveDashboardJobStats(url: string): unknown {
  const status = new URL(url).searchParams.get('status');
  switch (status) {
    case 'running':
      return dashboardJobStats.running;
    case 'completed':
      return dashboardJobStats.completed;
    case 'failed':
      return dashboardJobStats.failed;
    case 'paused':
      return dashboardJobStats.paused;
    default:
      return dashboardJobStats.all;
  }
}

// === monitoring: 集群列表 ===

export const clusterListResponse = {
  items: [
    {
      id: 1,
      cluster_name: 'hyperpod-prod-cluster',
      cluster_arn: 'arn:aws:sagemaker:us-east-1:123456789012:cluster/hyperpod-prod',
      region: 'us-east-1',
      status: 'active',
      health_status: 'degraded',
      total_nodes: 16,
      available_nodes: 14,
      total_gpu_count: 128,
      available_gpu_count: 17,
      total_cpu_cores: 1536,
      available_cpu_cores: 584,
      last_sync_at: '2026-06-12T12:58:00Z',
      created_at: '2025-11-20T08:00:00Z',
    },
  ],
  total: 1,
};

// === monitoring: 资源利用率（裸数组）===

export const resourceUtilization = [
  { resource_type: 'cpu', total: 1536, used: 952, available: 584, utilization_percentage: 62, unit: 'vCPU' },
  { resource_type: 'memory', total: 12288, used: 5898, available: 6390, utilization_percentage: 48, unit: 'GB' },
  { resource_type: 'gpu', total: 128, used: 111, available: 17, utilization_percentage: 87, unit: '卡' },
  { resource_type: 'storage', total: 512000, used: 179200, available: 332800, utilization_percentage: 35, unit: 'GB' },
];

// === monitoring: 告警列表 ===

export const alertListResponse = {
  items: [
    {
      id: 'alert-001',
      severity: 'critical',
      title: 'GPU 节点失联：hyperpod-node-012',
      message: '节点 hyperpod-node-012 超过 5 分钟未上报心跳，已触发自动替换流程',
      source: 'hyperpod-health-monitor',
      resource_type: 'node',
      resource_id: 'hyperpod-node-012',
      fired_at: '2026-06-12T12:41:00Z',
      resolved_at: null,
      status: 'firing',
    },
    {
      id: 'alert-002',
      severity: 'warning',
      title: 'FSx 存储使用率超过 80%',
      message: 'FSx 文件系统 fs-0a1b 使用率 83.4%，建议清理过期检查点或扩容',
      source: 'storage-watcher',
      resource_type: 'storage',
      resource_id: 'fs-0a1b',
      fired_at: '2026-06-12T09:15:00Z',
      resolved_at: null,
      status: 'firing',
    },
    {
      id: 'alert-003',
      severity: 'info',
      title: '检查点保存耗时偏高',
      message: '任务 llama2-finetune-001 最近一次 checkpoint 保存耗时 312s（基线 180s）',
      source: 'training-profiler',
      resource_type: 'training_job',
      resource_id: '1',
      fired_at: '2026-06-12T11:52:00Z',
      resolved_at: null,
      status: 'firing',
    },
  ],
  total: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// === monitoring: 时间序列指标（裸数组）===

/** 2026-06-12 12:00 起每 5 分钟一个点，数值有起伏便于图表呈现 */
function buildSeries(metricName: string, values: number[]) {
  const startMs = Date.parse('2026-06-12T12:00:00Z');
  return {
    metric_name: metricName,
    labels: { cluster: 'hyperpod-prod-cluster' },
    data_points: values.map((value, i) => ({
      timestamp: new Date(startMs + i * 5 * 60 * 1000).toISOString(),
      value,
    })),
  };
}

export const metricSeriesResponse = [
  buildSeries('cpu_utilization', [42, 45, 51, 48, 55, 62, 58, 67, 71, 64, 59, 63, 57]),
  buildSeries('memory_utilization', [58, 60, 59, 63, 66, 65, 70, 72, 69, 74, 71, 68, 66]),
  buildSeries('gpu_utilization', [78, 82, 91, 87, 93, 96, 88, 85, 92, 95, 89, 84, 90]),
];

// === reports: 资源使用报表 ===

export const resourceUsageResponse = {
  summary: {
    total_gpu_hours: 1843.5,
    total_cpu_hours: 12480.0,
    total_memory_gb_hours: 98304.0,
    total_storage_gb_hours: 35840.0,
    total_jobs_count: 47,
    active_jobs_count: 3,
    completed_jobs_count: 38,
    failed_jobs_count: 6,
  },
  breakdown: [
    { resource_type: 'training_job', name: '训练任务', gpu_hours: 1620.5, cpu_hours: 9216.0, memory_gb_hours: 73728.0, storage_gb_hours: 20480.0, count: 47, percentage: 72.4 },
    { resource_type: 'space', name: '开发空间', gpu_hours: 184.0, cpu_hours: 2304.0, memory_gb_hours: 16384.0, storage_gb_hours: 5120.0, count: 9, percentage: 15.2 },
    { resource_type: 'storage', name: '存储', gpu_hours: 0, cpu_hours: 0, memory_gb_hours: 0, storage_gb_hours: 9216.0, count: 12, percentage: 7.6 },
    { resource_type: 'cluster', name: '集群常驻服务', gpu_hours: 39.0, cpu_hours: 960.0, memory_gb_hours: 8192.0, storage_gb_hours: 1024.0, count: 1, percentage: 4.8 },
  ],
  daily_usage: [
    { date: '2026-06-05', gpu_hours: 218.5, cpu_hours: 1542.0, memory_gb_hours: 12288.0, storage_gb_hours: 5120.0, job_count: 6 },
    { date: '2026-06-06', gpu_hours: 264.0, cpu_hours: 1896.0, memory_gb_hours: 14336.0, storage_gb_hours: 5120.0, job_count: 8 },
    { date: '2026-06-07', gpu_hours: 241.5, cpu_hours: 1704.0, memory_gb_hours: 13312.0, storage_gb_hours: 5120.0, job_count: 7 },
    { date: '2026-06-08', gpu_hours: 312.0, cpu_hours: 2232.0, memory_gb_hours: 16384.0, storage_gb_hours: 5120.0, job_count: 9 },
    { date: '2026-06-09', gpu_hours: 288.5, cpu_hours: 2064.0, memory_gb_hours: 15360.0, storage_gb_hours: 5120.0, job_count: 8 },
    { date: '2026-06-10', gpu_hours: 256.0, cpu_hours: 1488.0, memory_gb_hours: 12288.0, storage_gb_hours: 5120.0, job_count: 4 },
    { date: '2026-06-11', gpu_hours: 263.0, cpu_hours: 1554.0, memory_gb_hours: 14336.0, storage_gb_hours: 5120.0, job_count: 5 },
  ],
  // 按用户聚合（resource-usage 页默认 group_by=user，表格直接消费 items）
  items: [
    { dimension_key: '2', dimension_label: 'developer-li', total_gpu_hours: 612.5, total_cpu_hours: 3840.0, total_memory_gb_hours: 30720.0, job_count: 14, avg_duration_hours: 6.2 },
    { dimension_key: '3', dimension_label: 'mlops-zhang', total_gpu_hours: 488.0, total_cpu_hours: 3072.0, total_memory_gb_hours: 24576.0, job_count: 11, avg_duration_hours: 5.8 },
    { dimension_key: '4', dimension_label: 'cv-team-wang', total_gpu_hours: 376.5, total_cpu_hours: 2688.0, total_memory_gb_hours: 20480.0, job_count: 9, avg_duration_hours: 4.5 },
    { dimension_key: '5', dimension_label: 'audio-team-liu', total_gpu_hours: 244.0, total_cpu_hours: 1920.0, total_memory_gb_hours: 14336.0, job_count: 8, avg_duration_hours: 3.9 },
    { dimension_key: '1', dimension_label: 'admin', total_gpu_hours: 122.5, total_cpu_hours: 960.0, total_memory_gb_hours: 8192.0, job_count: 5, avg_duration_hours: 2.4 },
  ],
  period: { start_date: '2026-06-05', end_date: '2026-06-11' },
};

// === reports: 成本分析 ===

/** 28 天日成本（总额有起伏；storage/network/other 低位小锯齿，compute 为差值） */
const DAILY_TOTALS = [
  812.4, 876.2, 924.8, 858.6, 791.3, 743.5, 768.9,
  889.1, 942.7, 1018.3, 967.5, 902.2, 834.8, 812.6,
  948.4, 1006.9, 1094.2, 1042.8, 976.1, 884.3, 856.7,
  931.5, 988.2, 1051.6, 1003.4, 938.9, 867.2, 1029.4,
];

const COST_START_MS = Date.parse('2026-05-15T00:00:00Z');

export const dailyCosts = DAILY_TOTALS.map((total, i) => {
  const storage = 110 + (i % 5) * 3;
  const network = 50 + (i % 4) * 4;
  const other = 12 + (i % 3) * 4;
  const compute = Math.round((total - storage - network - other) * 100) / 100;
  return {
    date: new Date(COST_START_MS + i * 24 * 3600 * 1000).toISOString().slice(0, 10),
    total_cost_usd: total,
    compute_cost_usd: compute,
    storage_cost_usd: storage,
    network_cost_usd: network,
    other_cost_usd: other,
  };
});

export const costAnalysisResponse = {
  summary: {
    total_cost_usd: 24863.5,
    compute_cost_usd: 18926.4,
    storage_cost_usd: 3214.8,
    network_cost_usd: 1582.2,
    data_transfer_cost_usd: 689.1,
    other_cost_usd: 451.0,
    period_start: '2026-05-15',
    period_end: '2026-06-11',
  },
  breakdown: [
    { category: 'compute', name: '计算资源（GPU/CPU 实例）', cost_usd: 18926.4, percentage: 76.1, item_count: 47 },
    { category: 'storage', name: '存储（FSx/S3/EBS）', cost_usd: 3214.8, percentage: 12.9, item_count: 12 },
    { category: 'network', name: '网络（VPC/ELB）', cost_usd: 1582.2, percentage: 6.4, item_count: 4 },
    { category: 'data_transfer', name: '数据传输', cost_usd: 689.1, percentage: 2.8, item_count: 6 },
    { category: 'other', name: '其他', cost_usd: 451.0, percentage: 1.8, item_count: 3 },
  ],
  daily_costs: dailyCosts,
  period: { start_date: '2026-05-15', end_date: '2026-06-11' },
};
