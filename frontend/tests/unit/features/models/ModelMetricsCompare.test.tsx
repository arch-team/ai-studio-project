/**
 * ModelMetricsCompare 单元测试
 *
 * 测试模型版本指标对比组件的渲染
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { ModelMetricsCompare } from '@features/models/components';
import type { VersionComparison } from '@features/models/types';

// 有指标差异的对比数据
const mockComparisonWithMetrics: VersionComparison = {
  metrics_diff: {
    accuracy: {
      v1: 0.85,
      v2: 0.92,
      diff: 0.07,
      diff_percent: 8.24,
    },
    loss: {
      v1: 0.35,
      v2: 0.22,
      diff: -0.13,
      diff_percent: -37.14,
    },
  },
  hyperparams_changed: ['learning_rate', 'batch_size'],
  hyperparameters_changes: [
    {
      param: 'learning_rate',
      v1_value: 0.001,
      v2_value: 0.0005,
      change_type: 'modified',
    },
    {
      param: 'batch_size',
      v1_value: 32,
      v2_value: 64,
      change_type: 'modified',
    },
    {
      param: 'warmup_steps',
      v1_value: undefined,
      v2_value: 1000,
      change_type: 'added',
    },
  ],
  framework_changed: false,
  tags_added: ['production'],
  tags_removed: ['experimental'],
};

// 无指标的对比数据
const mockEmptyComparison: VersionComparison = {
  metrics_diff: {},
  hyperparams_changed: [],
  hyperparameters_changes: [],
  framework_changed: false,
  tags_added: [],
  tags_removed: [],
};

// diff_percent 为 null 的情况
const mockComparisonWithNullDiff: VersionComparison = {
  metrics_diff: {
    accuracy: {
      v1: null,
      v2: 0.92,
      diff: null,
      diff_percent: null,
    },
  },
  hyperparams_changed: [],
  hyperparameters_changes: [],
  framework_changed: false,
  tags_added: [],
  tags_removed: [],
};

describe('ModelMetricsCompare', () => {
  describe('基本渲染', () => {
    it('应该渲染版本对比标题', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('版本对比')).toBeInTheDocument();
    });

    it('应该显示两个版本号', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      // 版本号在版本对比区和表头中都会出现
      expect(screen.getAllByText('v1.0.0').length).toBeGreaterThan(0);
      expect(screen.getAllByText('v2.0.0').length).toBeGreaterThan(0);
    });

    it('应该渲染指标对比区域', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('指标对比')).toBeInTheDocument();
    });

    it('应该渲染超参数变更区域', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('超参数变更')).toBeInTheDocument();
    });
  });

  describe('指标对比', () => {
    it('应该显示指标名称', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('accuracy')).toBeInTheDocument();
      expect(screen.getByText('loss')).toBeInTheDocument();
    });

    it('应该显示变化百分比（正数带+号）', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('+8.24%')).toBeInTheDocument();
      expect(screen.getByText('-37.14%')).toBeInTheDocument();
    });

    it('无指标时应该显示暂无可对比的指标', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockEmptyComparison}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('暂无可对比的指标')).toBeInTheDocument();
    });

    it('diff_percent 为 null 时应显示横杠', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithNullDiff}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      // formatDiffPercent 返回 '-'
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThan(0);
    });
  });

  describe('超参数变更', () => {
    it('应该显示超参数名称', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('learning_rate')).toBeInTheDocument();
      expect(screen.getByText('batch_size')).toBeInTheDocument();
      expect(screen.getByText('warmup_steps')).toBeInTheDocument();
    });

    it('应该显示变更类型（中文标签）', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockComparisonWithMetrics}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getAllByText('修改').length).toBeGreaterThan(0);
      expect(screen.getByText('新增')).toBeInTheDocument();
    });

    it('无超参数变更时应该显示提示', () => {
      renderWithProviders(
        <ModelMetricsCompare
          comparison={mockEmptyComparison}
          version1="v1.0.0"
          version2="v2.0.0"
        />
      );
      expect(screen.getByText('超参数无变化')).toBeInTheDocument();
    });
  });
});
