import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@tests/__utils__/test-utils';
import { InlineErrorState } from '@shared/components';

describe('InlineErrorState', () => {
  it('应渲染错误标题与消息', () => {
    render(<InlineErrorState message="服务器内部错误" />);
    expect(screen.getByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('服务器内部错误')).toBeInTheDocument();
  });

  it('提供 onRetry 时应渲染重试按钮并可点击', async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<InlineErrorState message="网络错误" onRetry={onRetry} />);
    const btn = screen.getByRole('button', { name: '重试' });
    await user.click(btn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('未提供 onRetry 时不渲染重试按钮', () => {
    render(<InlineErrorState message="错误" />);
    expect(screen.queryByRole('button', { name: '重试' })).not.toBeInTheDocument();
  });

  it('支持自定义标题', () => {
    render(<InlineErrorState title="资源不存在" message="找不到该任务" />);
    expect(screen.getByText('资源不存在')).toBeInTheDocument();
  });
});
