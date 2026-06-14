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
import {
  formatUtilizationBarData,
  formatUtilizationCompareData,
} from '@features/monitoring';
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

  // === F-009/F-010 量纲严谨性回归 ===
  // baseline 审计：柱状图/饼图把百分比指标与存储绝对字节数（量级悬殊）混入同一坐标轴/同一占比维度，
  // 导致 CPU/内存/GPU 柱贴地不可见、存储独占整环。修复后所有资源统一走 0-100% 利用率量纲。
  describe('量纲严谨性 (F-009/F-010)', () => {
    // 含量级悬殊数据：CPU 用 650 核、存储用 50 万 GB 绝对值，旧实现会让百分比柱贴地
    const mixedScaleUtilization: ResourceUtilization[] = [
      { resource_type: 'cpu', total: 1000, used: 650, available: 350, utilization_percentage: 65, unit: 'cores' },
      { resource_type: 'memory', total: 2048, used: 983, available: 1065, utilization_percentage: 48, unit: 'GB' },
      { resource_type: 'gpu', total: 64, used: 56, available: 8, utilization_percentage: 87, unit: 'cards' },
      { resource_type: 'storage', total: 500000, used: 355000, available: 145000, utilization_percentage: 71, unit: 'GB' },
    ];

    it('柱状图：所有资源统一走 0-100% 利用率量纲，不再使用裸绝对值 (F-009)', () => {
      const series = formatUtilizationBarData(mixedScaleUtilization);
      // 单一系列（利用率），不再是"已使用/可用"双系列的绝对值堆叠
      expect(series).toHaveLength(1);
      const allY = series.flatMap((s) => s.data.map((d) => d.y));
      // 关键断言：每个 y 都是百分比（0-100），存储不会因 50 万的绝对值压垮其它资源
      for (const y of allY) {
        expect(y).toBeGreaterThanOrEqual(0);
        expect(y).toBeLessThanOrEqual(100);
      }
      // 四种资源都在同一张图，按利用率可直接对比
      expect(allY).toEqual([65, 48, 87, 71]);
    });

    it('饼图替代为利用率对比：所有 y 同为 0-100% 量纲，不再对异量纲求占比 (F-010)', () => {
      const series = formatUtilizationCompareData(mixedScaleUtilization);
      const allY = series.flatMap((s) => s.data.map((d) => d.y));
      for (const y of allY) {
        expect(y).toBeGreaterThanOrEqual(0);
        expect(y).toBeLessThanOrEqual(100);
      }
      expect(allY).toEqual([65, 48, 87, 71]);
    });

    it('配色不硬编码 hex：转换函数不返回任何 color 字段，交由 Cloudscape 分类色 token 注入 (F-013 同源)', () => {
      const barSeries = formatUtilizationBarData(mixedScaleUtilization);
      const compareSeries = formatUtilizationCompareData(mixedScaleUtilization);
      const serialized = JSON.stringify([barSeries, compareSeries]);
      // 不得出现硬编码 hex 色值（如 #0972d3）
      expect(serialized).not.toMatch(/#[0-9a-fA-F]{6}/);
    });

    it('x 轴用资源中文名，承载利用率对比语义', () => {
      const series = formatUtilizationBarData(mixedScaleUtilization);
      const allX = series.flatMap((s) => s.data.map((d) => d.x));
      expect(allX).toEqual(['CPU', '内存', 'GPU', '存储']);
    });
  });
});
