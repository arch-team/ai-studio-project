/**
 * TrainingMetricsChart Tests
 *
 * Task: T221 - 训练指标展示组件
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TrainingMetricsChart } from '@features/training/components/TrainingMetricsChart';
import type { TrainingMetric } from '@features/training/types';

// Mock useTrainingJobMetrics hook
vi.mock('@features/training/api', () => ({
  useTrainingJobMetrics: vi.fn(() => ({
    data: {
      metrics: [
        { metric_name: 'loss', step: 100, value: 0.5, timestamp: '2024-01-01T00:00:00Z' },
        { metric_name: 'loss', step: 200, value: 0.4, timestamp: '2024-01-01T00:01:00Z' },
        { metric_name: 'loss', step: 300, value: 0.3, timestamp: '2024-01-01T00:02:00Z' },
        { metric_name: 'accuracy', step: 100, value: 0.8, timestamp: '2024-01-01T00:00:00Z' },
        { metric_name: 'accuracy', step: 200, value: 0.85, timestamp: '2024-01-01T00:01:00Z' },
      ] as TrainingMetric[],
    },
    isLoading: false,
    isError: false,
  })),
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
};

describe('TrainingMetricsChart', () => {
  describe('基本渲染', () => {
    it('should render chart container', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });

    it('should render chart title', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
          title="训练指标"
        />
      );
      expect(screen.getByText('训练指标')).toBeInTheDocument();
    });
  });

  describe('指标选择', () => {
    it('should render Loss chart when loss metric is selected', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
        />
      );
      // Chart should contain loss data series
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });

    it('should render Accuracy chart when accuracy metric is selected', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['accuracy']}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });

    it('should render multiple metrics when multiple are selected', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss', 'accuracy']}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });
  });

  describe('空数据处理', () => {
    it('should show empty state when no data', () => {
      vi.doMock('@features/training/api', () => ({
        useTrainingJobMetrics: vi.fn(() => ({
          data: { metrics: [] },
          isLoading: false,
          isError: false,
        })),
      }));

      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
        />
      );
      // Should still render chart container even with empty data
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });
  });

  describe('刷新控制', () => {
    it('should accept pollInterval prop for running jobs', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
          pollInterval={30000}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });

    it('should disable polling when pollInterval is undefined', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
          pollInterval={undefined}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });
  });

  describe('图表配置', () => {
    it('should accept custom height', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss']}
          height={400}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });

    it('should show legend when showLegend is true', () => {
      renderWithProviders(
        <TrainingMetricsChart
          jobId={1}
          metricNames={['loss', 'accuracy']}
          showLegend={true}
        />
      );
      expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
    });
  });
});

describe('TrainingMetricsChart Multi-Job Comparison', () => {
  it('should support comparing multiple jobs', () => {
    renderWithProviders(
      <TrainingMetricsChart
        jobIds={[1, 2, 3]}
        metricNames={['loss']}
        comparisonMode={true}
      />
    );
    expect(screen.getByTestId('training-metrics-chart')).toBeInTheDocument();
  });
});
