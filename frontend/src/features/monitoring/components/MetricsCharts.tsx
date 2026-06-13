/**
 * Metrics Charts Component
 *
 * Task: T067 - 实时指标图表组件
 * 可复用的监控图表组件 - 支持折线图、柱状图、饼图
 * 使用 Cloudscape Design System 内置图表组件
 */

import { useMemo } from 'react';
import {
  Box,
  Container,
  Header,
  LineChart,
  BarChart,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { MetricSeries, ResourceUtilization } from '../types';
import {
  formatUtilizationBarData,
  formatUtilizationCompareData,
} from './chartData';

// 指标名称映射
const METRIC_LABELS: Record<string, string> = {
  cpu_utilization: 'CPU 利用率',
  memory_utilization: '内存利用率',
  gpu_utilization: 'GPU 利用率',
  network_in_bytes: '网络入流量',
  network_out_bytes: '网络出流量',
  disk_read_bytes: '磁盘读取',
  disk_write_bytes: '磁盘写入',
};

// 注意：图表不再硬编码 hex 颜色数组。Cloudscape 图表组件在省略 series.color 时
// 默认采用品牌分类色板 token（colorChartsPaletteCategorical*，见 brandTheme.ts /
// design-tokens.md §3），自动适配明暗模式。F-013 同源修复：删除 CHART_COLORS。
// 资源利用率数据转换（formatUtilization*）已拆至 ./chartData，本文件只导出组件。

interface MetricsChartsProps {
  /** 图表类型 */
  type: 'line' | 'bar' | 'pie';
  /** 图表标题 */
  title: string;
  /** 时间序列数据 (用于折线图) */
  data?: MetricSeries[];
  /** 资源利用率数据 (用于柱状图/饼图) */
  utilizationData?: ResourceUtilization[];
  /** 图表高度 */
  height?: number;
  /** 是否加载中 */
  loading?: boolean;
}

/**
 * 将 MetricSeries 转换为 LineChart 数据格式
 */
function formatLineChartData(data: MetricSeries[]): Array<{
  title: string;
  type: 'line';
  data: { x: Date; y: number }[];
}> {
  // 不传 color：交由 Cloudscape 分类色板 token 自动着色（F-013 同源）
  return data.map((series) => ({
    title: METRIC_LABELS[series.metric_name] || series.metric_name,
    type: 'line' as const,
    data: series.data_points.map((point) => ({
      x: new Date(point.timestamp),
      y: point.value,
    })),
  }));
}

/**
 * 可复用的监控图表组件
 */
export function MetricsCharts({
  type,
  title,
  data = [],
  utilizationData = [],
  height = 300,
  loading = false,
}: MetricsChartsProps) {
  // 准备图表数据（柱状/对比均走 0-100% 利用率量纲，F-009/F-010）
  const lineSeries = useMemo(() => formatLineChartData(data), [data]);
  const barSeries = useMemo(() => formatUtilizationBarData(utilizationData), [utilizationData]);
  const compareSeries = useMemo(() => formatUtilizationCompareData(utilizationData), [utilizationData]);

  // 计算 X 轴范围 (折线图)
  const xDomain = useMemo(() => {
    if (lineSeries.length === 0 || lineSeries[0].data.length === 0) {
      return undefined;
    }
    const allDates = lineSeries.flatMap((s) => s.data.map((d) => d.x));
    return [new Date(Math.min(...allDates.map((d) => d.getTime()))), new Date(Math.max(...allDates.map((d) => d.getTime())))] as [Date, Date];
  }, [lineSeries]);

  // 渲染加载状态
  if (loading) {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <Box textAlign="center" padding="l">
          <StatusIndicator type="loading">加载中...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  // 检查是否有数据
  const hasData =
    (type === 'line' && data.length > 0 && data.some((s) => s.data_points.length > 0)) ||
    ((type === 'bar' || type === 'pie') && utilizationData.length > 0);

  // 渲染空数据状态
  if (!hasData) {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无数据
        </Box>
      </Container>
    );
  }

  // 渲染折线图
  if (type === 'line') {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <LineChart
          series={lineSeries}
          xDomain={xDomain}
          xScaleType="time"
          i18nStrings={{
            xTickFormatter: (x) =>
              x instanceof Date
                ? x.toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : String(x),
            yTickFormatter: (y) => `${y.toFixed(1)}%`,
          }}
          height={height}
          hideFilter
          empty={<Box textAlign="center">暂无数据</Box>}
        />
      </Container>
    );
  }

  // 渲染柱状图（资源利用率对比，0-100% 量纲，F-009）
  if (type === 'bar') {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <BarChart
          series={barSeries}
          xScaleType="categorical"
          yDomain={[0, 100]}
          i18nStrings={{
            yTickFormatter: (y) => `${y}%`,
          }}
          height={height}
          hideFilter
          empty={<Box textAlign="center">暂无数据</Box>}
        />
      </Container>
    );
  }

  // 渲染资源利用率对比（原"资源分布"饼图，F-010：异量纲不可求占比，改为同量纲柱状对比）
  if (type === 'pie') {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <BarChart
          series={compareSeries}
          xScaleType="categorical"
          yDomain={[0, 100]}
          i18nStrings={{
            yTickFormatter: (y) => `${y}%`,
          }}
          height={height}
          hideFilter
          empty={<Box textAlign="center">暂无数据</Box>}
        />
      </Container>
    );
  }

  return null;
}

export default MetricsCharts;
