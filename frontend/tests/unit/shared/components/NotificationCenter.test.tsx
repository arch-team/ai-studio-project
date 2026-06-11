/**
 * NotificationCenter Tests
 *
 * 验证全局通知中心订阅 'notification:show' 事件并渲染 Flashbar，
 * 这是修复「通知发出无消费者」缺陷的核心组件。
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, act, fireEvent, cleanup } from '@testing-library/react';
import { NotificationCenter } from '@shared/components';
import { eventBus } from '@shared/events';

describe('NotificationCenter', () => {
  beforeEach(() => {
    eventBus.clearAllSubscriptions();
    eventBus.clearHistory();
  });

  afterEach(() => {
    cleanup();
  });

  it('应在收到 notification:show 事件后显示消息', async () => {
    render(<NotificationCenter />);

    act(() => {
      eventBus.publish('notification:show', { type: 'success', message: '任务创建成功' });
    });

    expect(await screen.findByText('任务创建成功')).toBeInTheDocument();
  });

  it('应支持同时显示多条通知', async () => {
    render(<NotificationCenter />);

    act(() => {
      eventBus.publish('notification:show', { type: 'info', message: '消息一' });
      eventBus.publish('notification:show', { type: 'warning', message: '消息二' });
    });

    expect(await screen.findByText('消息一')).toBeInTheDocument();
    expect(await screen.findByText('消息二')).toBeInTheDocument();
  });

  it('error 类型通知默认不自动消失', async () => {
    render(<NotificationCenter />);

    act(() => {
      eventBus.publish('notification:show', { type: 'error', message: '操作失败' });
    });

    expect(await screen.findByText('操作失败')).toBeInTheDocument();

    // 等待一段时间后仍应存在（error 强制常驻，不设置自动消失计时器）
    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(screen.getByText('操作失败')).toBeInTheDocument();
  });

  it('非 error 通知应渲染为可关闭（dismissible）项', async () => {
    // 注: Cloudscape Flashbar 在 jsdom 下的退出动画不会真正移除 DOM 节点，
    // 故此处验证通知项渲染为带关闭按钮的可消除项（行为边界），
    // 自动消失与移除属于 Flashbar 组件自身职责。
    render(<NotificationCenter />);

    act(() => {
      eventBus.publish('notification:show', { type: 'success', message: '成功消息' });
    });

    expect(await screen.findByText('成功消息')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '关闭通知' })).toBeInTheDocument();
  });

  it('点击关闭按钮应触发消除（不抛错）', async () => {
    render(<NotificationCenter />);

    act(() => {
      eventBus.publish('notification:show', { type: 'info', message: '可关闭通知' });
    });
    expect(await screen.findByText('可关闭通知')).toBeInTheDocument();

    const dismissButton = screen.getByRole('button', { name: '关闭通知' });
    // 点击触发 onDismiss 回调，组件内部从 items 列表移除该项
    expect(() => fireEvent.click(dismissButton)).not.toThrow();
  });
});
