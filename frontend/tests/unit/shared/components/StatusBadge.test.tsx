/**
 * StatusBadge 组件测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '@shared/components/StatusBadge';

// 测试用状态映射
type TestStatus = 'active' | 'inactive' | 'pending';

const typeMap: Record<TestStatus, 'success' | 'error' | 'pending'> = {
  active: 'success',
  inactive: 'error',
  pending: 'pending',
};

const labelMap: Record<TestStatus, string> = {
  active: '活跃',
  inactive: '不活跃',
  pending: '等待中',
};

describe('StatusBadge', () => {
  it('应正确渲染状态文本', () => {
    render(
      <StatusBadge<TestStatus>
        status="active"
        typeMap={typeMap}
        labelMap={labelMap}
      />,
    );
    expect(screen.getByText('活跃')).toBeInTheDocument();
  });

  it('应为不同状态渲染不同标签', () => {
    const { rerender } = render(
      <StatusBadge<TestStatus>
        status="inactive"
        typeMap={typeMap}
        labelMap={labelMap}
      />,
    );
    expect(screen.getByText('不活跃')).toBeInTheDocument();

    rerender(
      <StatusBadge<TestStatus>
        status="pending"
        typeMap={typeMap}
        labelMap={labelMap}
      />,
    );
    expect(screen.getByText('等待中')).toBeInTheDocument();
  });

  it('应对未知状态显示原始状态文本', () => {
    render(
      <StatusBadge
        status="unknown_status"
        typeMap={{} as Record<string, 'info'>}
        labelMap={{} as Record<string, string>}
      />,
    );
    expect(screen.getByText('unknown_status')).toBeInTheDocument();
  });
});
