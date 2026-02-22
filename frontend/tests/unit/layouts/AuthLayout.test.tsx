/**
 * AuthLayout 布局组件测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuthLayout } from '@layouts/AuthLayout';

describe('AuthLayout', () => {
  it('应渲染平台标题', () => {
    render(
      <AuthLayout>
        <div>子组件</div>
      </AuthLayout>,
    );
    expect(screen.getByText('AI Training Platform')).toBeInTheDocument();
  });

  it('应渲染子组件', () => {
    render(
      <AuthLayout>
        <div>登录表单</div>
      </AuthLayout>,
    );
    expect(screen.getByText('登录表单')).toBeInTheDocument();
  });

  it('应渲染多个子组件', () => {
    render(
      <AuthLayout>
        <div>标题</div>
        <div>表单</div>
        <div>底部</div>
      </AuthLayout>,
    );
    expect(screen.getByText('标题')).toBeInTheDocument();
    expect(screen.getByText('表单')).toBeInTheDocument();
    expect(screen.getByText('底部')).toBeInTheDocument();
  });
});
