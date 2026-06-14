/**
 * Cost Trend Chart Component (T077)
 *
 * 成本趋势图表组件 - 使用 Cloudscape LineChart 展示成本随时间变化的趋势
 * 仅展示分项成本曲线（计算、存储、网络、其他）；总成本由页面 KPI 卡单独展示，
 * 不混入分项折线图，避免聚合值压垮分项量纲（F-012）。
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
import { buildCostTrendSeries, calculateCostYDomain } from './chartData';

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
 * 成本趋势图表组件
 */
export function CostTrendChart({
  data,
  title = '成本趋势',
  height = 300,
  showLegend = true,
  loading = false,
}: CostTrendChartProps) {
  // 构建图表数据（仅分项，剔除「总计」聚合值，F-012）
  const chartSeries = useMemo(() => buildCostTrendSeries(data), [data]);

  // 计算 Y 轴范围（仅基于分项）
  const yDomain = useMemo(() => calculateCostYDomain(data), [data]);

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
          ariaDescription="展示计算、存储、网络、其他各分项成本随时间的变化趋势"
        />
      </SpaceBetween>
    </Container>
  );
}

export default CostTrendChart;
