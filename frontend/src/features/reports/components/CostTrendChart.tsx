/**
 * Cost Trend Chart Component (T077)
 *
 * 成本趋势图表组件 - 使用 Cloudscape LineChart 展示成本随时间变化的趋势
 * 支持多条成本曲线（计算、存储、网络、其他、总计）
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
import type { DailyCost } from '../types';

// 成本类别颜色配置
const COST_SERIES_COLORS = {
  total: '#0073bb',
  compute: '#3184c2',
  storage: '#1d8102',
  network: '#9469d6',
  other: '#879596',
} as const;

// 成本类别显示名称
const COST_SERIES_LABELS = {
  total: '总计',
  compute: '计算',
  storage: '存储',
  network: '网络',
  other: '其他',
} as const;

type CostSeriesKey = keyof typeof COST_SERIES_COLORS;

export interface CostTrendChartProps {
  /** 每日成本数据 */
  data: DailyCost[];
  /** 图表标题 */
  title?: string;
  /** 图表高度 (px) */
  height?: number;
  /** 是否显示图例 */
  showLegend?: boolean;
  /** 是否处于加载状态 */
  loading?: boolean;
}

/**
 * 格式化日期为 MM-DD 格式
 */
function formatDateLabel(dateString: string): string {
  const date = new Date(dateString);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}-${day}`;
}

/**
 * 格式化货币显示
 */
function formatCurrency(value: number): string {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  if (value < 0.01 && value > 0) {
    return `$${value.toExponential(2)}`;
  }
  return `$${value.toFixed(2)}`;
}

/**
 * 将 DailyCost 数据转换为 LineChart 数据点格式
 */
function transformToChartData(
  data: DailyCost[],
  key: CostSeriesKey
): { x: string; y: number }[] {
  return data.map((item) => {
    let value: number;
    switch (key) {
      case 'total':
        value = item.total_cost_usd;
        break;
      case 'compute':
        value = item.compute_cost_usd;
        break;
      case 'storage':
        value = item.storage_cost_usd;
        break;
      case 'network':
        value = item.network_cost_usd;
        break;
      case 'other':
        value = item.other_cost_usd;
        break;
      default:
        value = 0;
    }
    return {
      x: item.date,
      y: value,
    };
  });
}

/**
 * 构建图表 Series 配置
 */
function buildChartSeries(data: DailyCost[]): Array<{
  title: string;
  type: 'line';
  data: { x: string; y: number }[];
  color: string;
}> {
  const seriesKeys: CostSeriesKey[] = ['total', 'compute', 'storage', 'network', 'other'];

  return seriesKeys
    .map((key) => ({
      title: COST_SERIES_LABELS[key],
      type: 'line' as const,
      data: transformToChartData(data, key),
      color: COST_SERIES_COLORS[key],
    }))
    .filter((series) => series.data.some((point) => point.y > 0));
}

/**
 * 计算 Y 轴范围
 */
function calculateYDomain(data: DailyCost[]): [number, number] {
  if (data.length === 0) return [0, 100];

  const maxValue = Math.max(
    ...data.map((d) =>
      Math.max(
        d.total_cost_usd,
        d.compute_cost_usd,
        d.storage_cost_usd,
        d.network_cost_usd,
        d.other_cost_usd
      )
    )
  );

  const minValue = Math.min(
    ...data.flatMap((d) =>
      [
        d.total_cost_usd,
        d.compute_cost_usd,
        d.storage_cost_usd,
        d.network_cost_usd,
        d.other_cost_usd,
      ].filter((v) => v > 0)
    )
  );

  // 添加 10% 的边距
  const padding = (maxValue - (minValue || 0)) * 0.1 || maxValue * 0.1 || 10;
  return [Math.max(0, (minValue || 0) - padding), maxValue + padding];
}

/**
 * 成本趋势图表组件
 */
export function CostTrendChart({
  data,
  title = '成本趋势',
  height = 300,
  showLegend = true,
  loading = false,
}: CostTrendChartProps) {
  // 构建图表数据
  const chartSeries = useMemo(() => buildChartSeries(data), [data]);

  // 计算 Y 轴范围
  const yDomain = useMemo(() => calculateYDomain(data), [data]);

  // 获取 X 轴数据（日期列表）
  const xDomain = useMemo(() => data.map((d) => d.date), [data]);

  // 渲染加载状态
  if (loading) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="cost-trend-chart"
      >
        <Box textAlign="center" padding="l">
          <StatusIndicator type="loading">加载成本数据...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  // 渲染空数据状态
  if (!data || data.length === 0) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="cost-trend-chart"
      >
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无成本数据
        </Box>
      </Container>
    );
  }

  // 无有效数据的状态
  if (chartSeries.length === 0) {
    return (
      <Container
        header={<Header variant="h2">{title}</Header>}
        data-testid="cost-trend-chart"
      >
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无有效成本数据
        </Box>
      </Container>
    );
  }

  return (
    <Container
      header={
        <Header variant="h2" description="按日期展示各类成本变化趋势">
          {title}
        </Header>
      }
      data-testid="cost-trend-chart"
    >
      <SpaceBetween size="m">
        <LineChart
          series={chartSeries}
          xDomain={xDomain}
          yDomain={yDomain}
          xScaleType="categorical"
          i18nStrings={{
            xTickFormatter: (x) => formatDateLabel(x as string),
            yTickFormatter: (y) => formatCurrency(y as number),
            detailPopoverDismissAriaLabel: '关闭',
            legendAriaLabel: '图例',
            chartAriaRoleDescription: '成本趋势图表',
          }}
          height={height}
          hideFilter={!showLegend}
          hideLegend={!showLegend}
          empty={<Box textAlign="center">暂无数据</Box>}
          noMatch={<Box textAlign="center">无匹配数据</Box>}
          ariaLabel={title}
          ariaDescription="展示计算、存储、网络、其他和总计成本随时间的变化趋势"
        />
      </SpaceBetween>
    </Container>
  );
}

export default CostTrendChart;
