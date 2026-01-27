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
  PieChart,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { MetricSeries, ResourceUtilization } from '../types';

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

// 资源类型映射
const RESOURCE_LABELS: Record<string, string> = {
  cpu: 'CPU',
  memory: '内存',
  gpu: 'GPU',
  storage: '存储',
};

// 图表颜色
const CHART_COLORS = [
  '#0972d3', // aws-blue
  '#067f68', // green
  '#c33d69', // red
  '#7d8998', // grey
  '#9469d6', // purple
];

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
  return data.map((series, index) => ({
    title: METRIC_LABELS[series.metric_name] || series.metric_name,
    type: 'line' as const,
    data: series.data_points.map((point) => ({
      x: new Date(point.timestamp),
      y: point.value,
    })),
    color: CHART_COLORS[index % CHART_COLORS.length],
  }));
}

/**
 * 将 ResourceUtilization 转换为 BarChart 数据格式
 */
function formatBarChartData(
  data: ResourceUtilization[]
): Array<{
  title: string;
  type: 'bar';
  data: { x: string; y: number }[];
}> {
  return [
    {
      title: '已使用',
      type: 'bar' as const,
      data: data.map((item) => ({
        x: RESOURCE_LABELS[item.resource_type] || item.resource_type,
        y: item.used,
      })),
    },
    {
      title: '可用',
      type: 'bar' as const,
      data: data.map((item) => ({
        x: RESOURCE_LABELS[item.resource_type] || item.resource_type,
        y: item.available,
      })),
    },
  ];
}

/**
 * 将 ResourceUtilization 转换为 PieChart 数据格式
 */
function formatPieChartData(
  data: ResourceUtilization[]
): Array<{
  title: string;
  value: number;
  color?: string;
}> {
  return data.map((item, index) => ({
    title: `${RESOURCE_LABELS[item.resource_type] || item.resource_type} (${item.utilization_percentage}%)`,
    value: item.used,
    color: CHART_COLORS[index % CHART_COLORS.length],
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
  // 准备图表数据
  const lineSeries = useMemo(() => formatLineChartData(data), [data]);
  const barSeries = useMemo(() => formatBarChartData(utilizationData), [utilizationData]);
  const pieSeries = useMemo(() => formatPieChartData(utilizationData), [utilizationData]);

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

  // 渲染柱状图
  if (type === 'bar') {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <BarChart
          series={barSeries}
          xScaleType="categorical"
          i18nStrings={{
            yTickFormatter: (y) => String(y),
          }}
          height={height}
          hideFilter
          stackedBars
          empty={<Box textAlign="center">暂无数据</Box>}
        />
      </Container>
    );
  }

  // 渲染饼图
  if (type === 'pie') {
    return (
      <Container header={<Header variant="h2">{title}</Header>} data-testid="metrics-chart">
        <PieChart
          data={pieSeries}
          size="medium"
          variant="donut"
          hideFilter
          hideLegend={false}
          empty={<Box textAlign="center">暂无数据</Box>}
        />
      </Container>
    );
  }

  return null;
}

export default MetricsCharts;
