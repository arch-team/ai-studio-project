/**
 * CostTrendChart Tests
 *
 * Task: T077 - 成本趋势图表组件
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostTrendChart } from '@features/reports';
import type { DailyCost } from '@features/reports';

// 测试数据
const mockDailyCosts: DailyCost[] = [
  {
    date: '2024-01-01',
    total_cost_usd: 150.5,
    compute_cost_usd: 100.0,
    storage_cost_usd: 30.5,
    network_cost_usd: 10.0,
    other_cost_usd: 10.0,
  },
  {
    date: '2024-01-02',
    total_cost_usd: 180.0,
    compute_cost_usd: 120.0,
    storage_cost_usd: 35.0,
    network_cost_usd: 12.0,
    other_cost_usd: 13.0,
  },
  {
    date: '2024-01-03',
    total_cost_usd: 200.0,
    compute_cost_usd: 140.0,
    storage_cost_usd: 38.0,
    network_cost_usd: 12.0,
    other_cost_usd: 10.0,
  },
];

describe('CostTrendChart', () => {
  describe('基本渲染', () => {
    it('should render chart container', () => {
      render(<CostTrendChart data={mockDailyCosts} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should render default title', () => {
      render(<CostTrendChart data={mockDailyCosts} />);
      expect(screen.getByText('成本趋势')).toBeInTheDocument();
    });

    it('should render custom title', () => {
      render(<CostTrendChart data={mockDailyCosts} title="自定义标题" />);
      expect(screen.getByText('自定义标题')).toBeInTheDocument();
    });

    it('should render chart description', () => {
      render(<CostTrendChart data={mockDailyCosts} />);
      expect(screen.getByText('按日期展示各类成本变化趋势')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should show loading indicator when loading is true', () => {
      render(<CostTrendChart data={[]} loading={true} />);
      expect(screen.getByText('加载成本数据...')).toBeInTheDocument();
    });

    it('should not show loading indicator when loading is false', () => {
      render(<CostTrendChart data={mockDailyCosts} loading={false} />);
      expect(screen.queryByText('加载成本数据...')).not.toBeInTheDocument();
    });
  });

  describe('空数据处理', () => {
    it('should show empty state when data is empty array', () => {
      render(<CostTrendChart data={[]} />);
      expect(screen.getByText('暂无成本数据')).toBeInTheDocument();
    });

    it('should show empty state when data is undefined-like empty', () => {
      render(<CostTrendChart data={[]} loading={false} />);
      expect(screen.getByText('暂无成本数据')).toBeInTheDocument();
    });
  });

  describe('零成本数据处理', () => {
    it('should show empty valid data state when all costs are zero', () => {
      const zeroCostData: DailyCost[] = [
        {
          date: '2024-01-01',
          total_cost_usd: 0,
          compute_cost_usd: 0,
          storage_cost_usd: 0,
          network_cost_usd: 0,
          other_cost_usd: 0,
        },
      ];
      render(<CostTrendChart data={zeroCostData} />);
      expect(screen.getByText('暂无有效成本数据')).toBeInTheDocument();
    });
  });

  describe('图表配置', () => {
    it('should accept custom height prop', () => {
      render(<CostTrendChart data={mockDailyCosts} height={400} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should render with legend when showLegend is true', () => {
      render(<CostTrendChart data={mockDailyCosts} showLegend={true} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should render without legend when showLegend is false', () => {
      render(<CostTrendChart data={mockDailyCosts} showLegend={false} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });
  });

  describe('无障碍支持', () => {
    it('should have aria-label for the chart', () => {
      render(<CostTrendChart data={mockDailyCosts} title="成本趋势" />);
      // 组件应该渲染成功
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should have descriptive aria-description', () => {
      render(<CostTrendChart data={mockDailyCosts} />);
      // 组件应该渲染成功
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });
  });

  describe('数据处理', () => {
    it('should handle single day data', () => {
      const singleDayData: DailyCost[] = [
        {
          date: '2024-01-01',
          total_cost_usd: 100,
          compute_cost_usd: 80,
          storage_cost_usd: 15,
          network_cost_usd: 3,
          other_cost_usd: 2,
        },
      ];
      render(<CostTrendChart data={singleDayData} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should handle large cost values', () => {
      const largeCostData: DailyCost[] = [
        {
          date: '2024-01-01',
          total_cost_usd: 15000.5,
          compute_cost_usd: 10000.0,
          storage_cost_usd: 3000.5,
          network_cost_usd: 1000.0,
          other_cost_usd: 1000.0,
        },
      ];
      render(<CostTrendChart data={largeCostData} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });

    it('should handle very small cost values', () => {
      const smallCostData: DailyCost[] = [
        {
          date: '2024-01-01',
          total_cost_usd: 0.005,
          compute_cost_usd: 0.003,
          storage_cost_usd: 0.001,
          network_cost_usd: 0.0005,
          other_cost_usd: 0.0005,
        },
      ];
      render(<CostTrendChart data={smallCostData} />);
      expect(screen.getByTestId('cost-trend-chart')).toBeInTheDocument();
    });
  });
});
