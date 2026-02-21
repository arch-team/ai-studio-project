/**
 * DatasetStatusBadge 单元测试
 *
 * 测试数据集状态徽章组件的渲染行为
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { DatasetStatusBadge } from '@features/datasets/components';
import type { DatasetStatus } from '@features/datasets/types';
import { DATASET_STATUS_LABELS } from '@features/datasets/types';

describe('DatasetStatusBadge', () => {
  describe('渲染', () => {
    it.each<DatasetStatus>(['available', 'preparing', 'archived', 'error'])(
      '应正确渲染 %s 状态',
      (status) => {
        renderWithProviders(<DatasetStatusBadge status={status} />);
        expect(screen.getByText(DATASET_STATUS_LABELS[status])).toBeInTheDocument();
      }
    );

    it('应渲染 available 状态为"可用"', () => {
      renderWithProviders(<DatasetStatusBadge status="available" />);
      expect(screen.getByText('可用')).toBeInTheDocument();
    });

    it('应渲染 preparing 状态为"准备中"', () => {
      renderWithProviders(<DatasetStatusBadge status="preparing" />);
      expect(screen.getByText('准备中')).toBeInTheDocument();
    });

    it('应渲染 archived 状态为"已归档"', () => {
      renderWithProviders(<DatasetStatusBadge status="archived" />);
      expect(screen.getByText('已归档')).toBeInTheDocument();
    });

    it('应渲染 error 状态为"错误"', () => {
      renderWithProviders(<DatasetStatusBadge status="error" />);
      expect(screen.getByText('错误')).toBeInTheDocument();
    });
  });
});
