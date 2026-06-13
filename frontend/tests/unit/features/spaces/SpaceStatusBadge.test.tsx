/**
 * SpaceStatusBadge 单元测试
 *
 * 测试开发空间状态徽章组件的渲染和状态映射
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { SpaceStatusBadge } from '@features/spaces/components';
import type { SpaceStatus } from '@features/spaces/types';
import { SPACE_STATUS_LABELS } from '@features/spaces/types';

describe('SpaceStatusBadge', () => {
  describe('基本渲染', () => {
    it('应该渲染状态徽章组件', () => {
      renderWithProviders(<SpaceStatusBadge status="running" />);
      expect(screen.getByText('运行中')).toBeInTheDocument();
    });
  });

  describe('状态映射', () => {
    const statusCases: { status: SpaceStatus; label: string }[] = [
      { status: 'pending', label: '启动中' },
      { status: 'running', label: '运行中' },
      { status: 'stopped', label: '已停止' },
      { status: 'failed', label: '失败' },
      { status: 'deleted', label: '已删除' },
    ];

    it.each(statusCases)(
      '应该为 $status 状态显示正确的中文标签 "$label"',
      ({ status, label }) => {
        renderWithProviders(<SpaceStatusBadge status={status} />);
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );

    it('应该覆盖所有 SpaceStatus 类型', () => {
      const allStatuses: SpaceStatus[] = [
        'pending',
        'running',
        'stopped',
        'failed',
        'deleted',
      ];
      for (const status of allStatuses) {
        expect(SPACE_STATUS_LABELS[status]).toBeDefined();
      }
    });
  });
});
