/**
 * Spaces hooks 单元测试
 *
 * 测试开发空间业务逻辑 hooks
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import {
  useSpaceStats,
  useCanStartSpace,
  useCanStopSpace,
  useCanOpenSpace,
  useCanDeleteSpace,
  useSpaceRunningDuration,
} from '@features/spaces/hooks';
import type { SpaceSummary } from '@features/spaces/types';

// 创建模拟空间数据
function createMockSpace(overrides: Partial<SpaceSummary> = {}): SpaceSummary {
  return {
    id: 1,
    name: 'test-space',
    description: null,
    space_type: 'jupyter',
    status: 'running',
    instance_type: 'ml.g5.xlarge',
    instance_size: 'small',
    owner_id: 1,
    owner_username: 'testuser',
    url: 'https://jupyter.example.com/1',
    created_at: '2025-01-01T00:00:00Z',
    started_at: '2025-01-01T01:00:00Z',
    stopped_at: null,
    last_activity_at: '2025-01-01T02:00:00Z',
    ...overrides,
  };
}

describe('useSpaceStats', () => {
  it('undefined 输入应该返回全零统计', () => {
    const { result } = renderHook(() => useSpaceStats(undefined));
    expect(result.current.total).toBe(0);
    expect(result.current.running).toBe(0);
    expect(result.current.stopped).toBe(0);
    expect(result.current.creating).toBe(0);
    expect(result.current.failed).toBe(0);
    expect(result.current.deleting).toBe(0);
  });

  it('空数组应该返回全零统计', () => {
    const { result } = renderHook(() => useSpaceStats([]));
    expect(result.current.total).toBe(0);
  });

  it('应该正确统计各状态数量', () => {
    const spaces = [
      createMockSpace({ id: 1, status: 'running' }),
      createMockSpace({ id: 2, status: 'running' }),
      createMockSpace({ id: 3, status: 'stopped' }),
      createMockSpace({ id: 4, status: 'creating' }),
      createMockSpace({ id: 5, status: 'failed' }),
      createMockSpace({ id: 6, status: 'deleting' }),
    ];

    const { result } = renderHook(() => useSpaceStats(spaces));
    expect(result.current.total).toBe(6);
    expect(result.current.running).toBe(2);
    expect(result.current.stopped).toBe(1);
    expect(result.current.creating).toBe(1);
    expect(result.current.failed).toBe(1);
    expect(result.current.deleting).toBe(1);
  });
});

describe('useCanStartSpace', () => {
  it('undefined 空间应该返回 false', () => {
    const { result } = renderHook(() => useCanStartSpace(undefined));
    expect(result.current).toBe(false);
  });

  it('已停止的空间应该返回 true', () => {
    const space = createMockSpace({ status: 'stopped' });
    const { result } = renderHook(() => useCanStartSpace(space));
    expect(result.current).toBe(true);
  });

  it('运行中的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'running' });
    const { result } = renderHook(() => useCanStartSpace(space));
    expect(result.current).toBe(false);
  });

  it('创建中的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'creating' });
    const { result } = renderHook(() => useCanStartSpace(space));
    expect(result.current).toBe(false);
  });
});

describe('useCanStopSpace', () => {
  it('undefined 空间应该返回 false', () => {
    const { result } = renderHook(() => useCanStopSpace(undefined));
    expect(result.current).toBe(false);
  });

  it('运行中的空间应该返回 true', () => {
    const space = createMockSpace({ status: 'running' });
    const { result } = renderHook(() => useCanStopSpace(space));
    expect(result.current).toBe(true);
  });

  it('已停止的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'stopped' });
    const { result } = renderHook(() => useCanStopSpace(space));
    expect(result.current).toBe(false);
  });
});

describe('useCanOpenSpace', () => {
  it('undefined 空间应该返回 false', () => {
    const { result } = renderHook(() => useCanOpenSpace(undefined));
    expect(result.current).toBe(false);
  });

  it('运行中且有 URL 的空间应该返回 true', () => {
    const space = createMockSpace({
      status: 'running',
      url: 'https://jupyter.example.com',
    });
    const { result } = renderHook(() => useCanOpenSpace(space));
    expect(result.current).toBe(true);
  });

  it('运行中但无 URL 的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'running', url: null });
    const { result } = renderHook(() => useCanOpenSpace(space));
    expect(result.current).toBe(false);
  });

  it('已停止的空间应该返回 false', () => {
    const space = createMockSpace({
      status: 'stopped',
      url: 'https://jupyter.example.com',
    });
    const { result } = renderHook(() => useCanOpenSpace(space));
    expect(result.current).toBe(false);
  });
});

describe('useCanDeleteSpace', () => {
  it('undefined 空间应该返回 false', () => {
    const { result } = renderHook(() => useCanDeleteSpace(undefined));
    expect(result.current).toBe(false);
  });

  it('已停止的空间应该返回 true', () => {
    const space = createMockSpace({ status: 'stopped' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(true);
  });

  it('失败的空间应该返回 true', () => {
    const space = createMockSpace({ status: 'failed' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(true);
  });

  it('运行中的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'running' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(false);
  });

  it('创建中的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'creating' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(false);
  });

  it('删除中的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'deleting' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(false);
  });
});

describe('useSpaceRunningDuration', () => {
  it('undefined 空间应该返回 "-"', () => {
    const { result } = renderHook(() => useSpaceRunningDuration(undefined));
    expect(result.current).toBe('-');
  });

  it('未启动的空间应该返回 "-"', () => {
    const space = createMockSpace({ started_at: null, status: 'stopped' });
    const { result } = renderHook(() => useSpaceRunningDuration(space));
    expect(result.current).toBe('-');
  });

  it('非运行状态的空间应该返回 "-"', () => {
    const space = createMockSpace({
      started_at: '2025-01-01T00:00:00Z',
      status: 'stopped',
    });
    const { result } = renderHook(() => useSpaceRunningDuration(space));
    expect(result.current).toBe('-');
  });

  it('运行中的空间应该返回时长字符串', () => {
    // 设置 started_at 为 2 小时 30 分钟前
    const twoHoursAgo = new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString();
    const space = createMockSpace({
      started_at: twoHoursAgo,
      status: 'running',
    });
    const { result } = renderHook(() => useSpaceRunningDuration(space));
    expect(result.current).toMatch(/2小时 \d+分钟/);
  });

  it('运行不到一小时应该只显示分钟', () => {
    const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    const space = createMockSpace({
      started_at: thirtyMinutesAgo,
      status: 'running',
    });
    const { result } = renderHook(() => useSpaceRunningDuration(space));
    expect(result.current).toMatch(/^\d+分钟$/);
  });
});
