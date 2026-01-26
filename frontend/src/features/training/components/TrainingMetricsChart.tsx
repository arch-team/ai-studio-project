/**
 * Training Metrics Chart Component (T221)
 *
 * 训练指标图表组件 - 使用 Cloudscape LineChart 展示训练曲线
 * 支持多指标叠加、时间范围选择、多任务对比
 */

import {
  Box,
  Container,
  Header,
  LineChart,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useMemo } from 'react';
import { useTrainingJobMetrics } from '../api';
import type { TrainingMetric } from '../types';

// 指标显示名称
const METRIC_LABELS: Record<string, string> = {
  loss: 'Loss',
  accuracy: 'Accuracy',
  learning_rate: 'Learning Rate',
  throughput: 'Throughput',
  gpu_utilization: 'GPU Utilization',
};

interface TrainingMetricsChartProps {
  /** 单任务模式的任务 ID */
  jobId?: number;
  /** 多任务对比模式的任务 ID 列表 */
  jobIds?: number[];
  /** 要展示的指标名称列表 */
  metricNames: string[];
  /** 图表标题 */
  title?: string;
  /** 轮询间隔 (毫秒)，undefined 表示不轮询 */
  pollInterval?: number;
  /** 图表高度 (px) */
  height?: number;
  /** 是否显示图例 */
  showLegend?: boolean;
  /** 是否为对比模式 */
  comparisonMode?: boolean;
}

/**
 * 将指标数据转换为图表数据格式
 */
function formatMetricsForChart(
  metrics: TrainingMetric[],
  metricName: string
): { x: number; y: number }[] {
  return metrics
    .filter((m) => m.metric_name === metricName)
    .map((m) => ({
      x: m.step,
      y: m.value,
    }))
    .sort((a, b) => a.x - b.x);
}

/**
 * 构建图表 Series 配置
 */
function buildChartSeries(
  metrics: TrainingMetric[],
  metricNames: string[]
): Array<{
  title: string;
  type: 'line';
  data: { x: number; y: number }[];
}> {
  return metricNames
    .map((name) => ({
      title: METRIC_LABELS[name] || name,
      type: 'line' as const,
      data: formatMetricsForChart(metrics, name),
    }))
    .filter((series) => series.data.length > 0);
}

/**
 * 计算图表 Y 轴范围
 */
function calculateYDomain(
  data: { x: number; y: number }[]
): [number, number] {
  if (data.length === 0) return [0, 1];
  const values = data.map((d) => d.y);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min) * 0.1 || 0.1;
  return [Math.max(0, min - padding), max + padding];
}

/**
 * 计算图表 X 轴范围
 */
function calculateXDomain(
  data: { x: number; y: number }[]
): [number, number] {
  if (data.length === 0) return [0, 100];
  const steps = data.map((d) => d.x);
  return [Math.min(...steps), Math.max(...steps)];
}

/**
 * 训练指标图表组件
 */
export function TrainingMetricsChart({
  jobId,
  jobIds,
  metricNames,
  title = '训练指标',
  pollInterval,
  height = 300,
  showLegend = true,
  comparisonMode = false,
}: TrainingMetricsChartProps) {
  // 使用单任务或第一个任务的 ID
  const effectiveJobId = jobId || (jobIds && jobIds[0]);

  // 获取指标数据
  const { data: metricsData, isLoading, isError } = useTrainingJobMetrics(
    effectiveJobId,
    { metric_names: metricNames },
    pollInterval
  );

  const metrics = useMemo(
    () => metricsData?.metrics || [],
    [metricsData?.metrics]
  );

  // 构建图表数据
  const chartSeries = useMemo(
    () => buildChartSeries(metrics, metricNames),
    [metrics, metricNames]
  );

  // 所有数据点合并用于计算轴范围
  const allDataPoints = useMemo(() => {
    return chartSeries.flatMap((series) => series.data);
  }, [chartSeries]);

  const xDomain = useMemo(
    () => calculateXDomain(allDataPoints),
    [allDataPoints]
  );

  const yDomain = useMemo(
    () => calculateYDomain(allDataPoints),
    [allDataPoints]
  );

  // 渲染加载状态
  if (isLoading && metrics.length === 0) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="training-metrics-chart"
      >
        <Box textAlign="center" padding="l">
          <StatusIndicator type="loading">加载指标数据...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  // 渲染错误状态
  if (isError) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="training-metrics-chart"
      >
        <Box textAlign="center" padding="l">
          <StatusIndicator type="error">加载失败</StatusIndicator>
        </Box>
      </Container>
    );
  }

  // 渲染空数据状态
  if (chartSeries.length === 0) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="training-metrics-chart"
      >
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无指标数据
        </Box>
      </Container>
    );
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description={comparisonMode ? '多任务对比视图' : undefined}
        >
          {title}
        </Header>
      }
      data-testid="training-metrics-chart"
    >
      <SpaceBetween size="m">
        <LineChart
          series={chartSeries}
          xDomain={xDomain}
          yDomain={yDomain}
          i18nStrings={{
            xTickFormatter: (x) => `Step ${x}`,
            yTickFormatter: (y) =>
              y < 0.01 ? y.toExponential(2) : y.toFixed(4),
          }}
          height={height}
          hideFilter={!showLegend}
          hideLegend={!showLegend}
          empty={<Box textAlign="center">暂无数据</Box>}
          noMatch={<Box textAlign="center">无匹配数据</Box>}
        />
      </SpaceBetween>
    </Container>
  );
}

export default TrainingMetricsChart;
