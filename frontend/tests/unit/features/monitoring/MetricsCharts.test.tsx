/**
 * Metrics Charts Tests
 *
 * Task: T067 - 实时指标图表组件
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { MetricsCharts } from '@features/monitoring';
import type { MetricSeries, ResourceUtilization } from '@features/monitoring';

// Mock data - 时间序列数据
const mockMetricSeries: MetricSeries[] = [
  {
    metric_name: 'cpu_utilization',
    labels: { cluster: 'cluster-1' },
    data_points: [
      { timestamp: '2024-01-15T10:00:00Z', value: 45.5 },
      { timestamp: '2024-01-15T10:05:00Z', value: 52.3 },
      { timestamp: '2024-01-15T10:10:00Z', value: 48.7 },
      { timestamp: '2024-01-15T10:15:00Z', value: 55.1 },
    ],
  },
  {
    metric_name: 'gpu_utilization',
    labels: { cluster: 'cluster-1' },
    data_points: [
      { timestamp: '2024-01-15T10:00:00Z', value: 78.2 },
      { timestamp: '2024-01-15T10:05:00Z', value: 82.5 },
      { timestamp: '2024-01-15T10:10:00Z', value: 75.8 },
      { timestamp: '2024-01-15T10:15:00Z', value: 80.1 },
    ],
  },
];

// Mock data - 资源利用率数据
const mockResourceUtilization: ResourceUtilization[] = [
  {
    resource_type: 'cpu',
    total: 1000,
    used: 650,
    available: 350,
    utilization_percentage: 65,
    unit: 'cores',
  },
  {
    resource_type: 'memory',
    total: 2048,
    used: 1536,
    available: 512,
    utilization_percentage: 75,
    unit: 'GB',
  },
  {
    resource_type: 'gpu',
    total: 64,
    used: 48,
    available: 16,
    utilization_percentage: 75,
    unit: 'cards',
  },
];

describe('MetricsCharts', () => {
  describe('基本渲染', () => {
    it('should render chart container', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="资源利用率"
          data={mockMetricSeries}
        />
      );
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });

    it('should render chart title', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="CPU 使用率趋势"
          data={mockMetricSeries}
        />
      );
      expect(screen.getByText('CPU 使用率趋势')).toBeInTheDocument();
    });
  });

  describe('折线图 (Line Chart)', () => {
    it('should render line chart for time series data', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="资源使用趋势"
          data={mockMetricSeries}
        />
      );
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });
  });

  describe('柱状图 (Bar Chart)', () => {
    it('should render bar chart for resource comparison', () => {
      renderWithProviders(
        <MetricsCharts
          type="bar"
          title="资源对比"
          utilizationData={mockResourceUtilization}
        />
      );
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });
  });

  describe('饼图 (Pie Chart)', () => {
    it('should render pie chart for distribution', () => {
      renderWithProviders(
        <MetricsCharts
          type="pie"
          title="资源分布"
          utilizationData={mockResourceUtilization}
        />
      );
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });
  });

  describe('空数据处理', () => {
    it('should show empty state when no data', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="无数据图表"
          data={[]}
        />
      );
      expect(screen.getByText(/暂无数据/i)).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should display loading spinner when loading', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="测试图表"
          data={mockMetricSeries}
          loading={true}
        />
      );
      // "加载中" 出现在标题和 StatusIndicator 中，使用 getAllByText
      expect(screen.getAllByText(/加载中/i).length).toBeGreaterThan(0);
    });
  });

  describe('图表配置', () => {
    it('should accept custom height', () => {
      renderWithProviders(
        <MetricsCharts
          type="line"
          title="自定义高度"
          data={mockMetricSeries}
          height={400}
        />
      );
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });
  });
});
