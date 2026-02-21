/**
 * TrainingStatusBadge 单元测试
 *
 * 测试状态徽章组件的渲染和状态映射
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { TrainingStatusBadge } from '@features/training/components';
import type { JobStatus } from '@features/training/types';
import { JOB_STATUS_LABELS } from '@features/training/types';

describe('TrainingStatusBadge', () => {
  describe('基本渲染', () => {
    it('应该渲染状态徽章组件', () => {
      renderWithProviders(<TrainingStatusBadge status="running" />);
      expect(screen.getByText('运行中')).toBeInTheDocument();
    });
  });

  describe('状态映射', () => {
    const statusCases: { status: JobStatus; label: string }[] = [
      { status: 'submitted', label: '已提交' },
      { status: 'running', label: '运行中' },
      { status: 'paused', label: '已暂停' },
      { status: 'preempted', label: '被抢占' },
      { status: 'completed', label: '已完成' },
      { status: 'failed', label: '已失败' },
    ];

    it.each(statusCases)(
      '应该为 $status 状态显示正确的中文标签 "$label"',
      ({ status, label }) => {
        renderWithProviders(<TrainingStatusBadge status={status} />);
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );

    it('应该覆盖所有 JobStatus 类型', () => {
      const allStatuses: JobStatus[] = [
        'submitted',
        'running',
        'paused',
        'preempted',
        'completed',
        'failed',
      ];
      // 确保 JOB_STATUS_LABELS 包含所有状态
      for (const status of allStatuses) {
        expect(JOB_STATUS_LABELS[status]).toBeDefined();
      }
    });
  });
});
