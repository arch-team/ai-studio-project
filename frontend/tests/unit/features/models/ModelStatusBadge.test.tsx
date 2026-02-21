/**
 * ModelStatusBadge 单元测试
 *
 * 测试模型状态徽章组件的渲染和状态映射
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { ModelStatusBadge } from '@features/models/components';
import type { ModelStatus } from '@features/models/types';
import { MODEL_STATUS_LABELS } from '@features/models/types';

describe('ModelStatusBadge', () => {
  describe('基本渲染', () => {
    it('应该渲染状态徽章组件', () => {
      renderWithProviders(<ModelStatusBadge status="registered" />);
      expect(screen.getByText('已注册')).toBeInTheDocument();
    });
  });

  describe('状态映射', () => {
    const statusCases: { status: ModelStatus; label: string }[] = [
      { status: 'training', label: '训练中' },
      { status: 'registered', label: '已注册' },
      { status: 'deployed', label: '已部署' },
      { status: 'archived', label: '已归档' },
      { status: 'failed', label: '已失败' },
    ];

    it.each(statusCases)(
      '应该为 $status 状态显示正确的中文标签 "$label"',
      ({ status, label }) => {
        renderWithProviders(<ModelStatusBadge status={status} />);
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );

    it('应该覆盖所有 ModelStatus 类型', () => {
      const allStatuses: ModelStatus[] = [
        'training',
        'registered',
        'deployed',
        'archived',
        'failed',
      ];
      for (const status of allStatuses) {
        expect(MODEL_STATUS_LABELS[status]).toBeDefined();
      }
    });
  });
});
