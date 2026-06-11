/**
 * Spaces hooks 单元测试
 *
 * 测试开发空间业务逻辑 hooks（契约对齐后：状态机 pending/running/stopped/failed/deleted）
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import {
  useSpaceStats,
  useCanStartSpace,
  useCanStopSpace,
  useCanDeleteSpace,
} from '@features/spaces/hooks';
import type { SpaceSummary } from '@features/spaces/types';

// 创建模拟空间数据（与后端 SpaceResponse 契约一致）
function createMockSpace(overrides: Partial<SpaceSummary> = {}): SpaceSummary {
  return {
    id: 'a1b2c3d4-0000-0000-0000-000000000001',
    space_name: 'test-space',
    owner_id: 1,
    instance_type: 'ml.g5.xlarge',
    space_type: 'jupyter',
    status: 'running',
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useSpaceStats', () => {
  it('undefined 输入应该返回全零统计', () => {
    const { result } = renderHook(() => useSpaceStats(undefined));
    expect(result.current.total).toBe(0);
    expect(result.current.pending).toBe(0);
    expect(result.current.running).toBe(0);
    expect(result.current.stopped).toBe(0);
    expect(result.current.failed).toBe(0);
    expect(result.current.deleted).toBe(0);
  });

  it('空数组应该返回全零统计', () => {
    const { result } = renderHook(() => useSpaceStats([]));
    expect(result.current.total).toBe(0);
  });

  it('应该正确统计各状态数量', () => {
    const spaces = [
      createMockSpace({ id: 'id-1', status: 'running' }),
      createMockSpace({ id: 'id-2', status: 'running' }),
      createMockSpace({ id: 'id-3', status: 'stopped' }),
      createMockSpace({ id: 'id-4', status: 'pending' }),
      createMockSpace({ id: 'id-5', status: 'failed' }),
      createMockSpace({ id: 'id-6', status: 'deleted' }),
    ];

    const { result } = renderHook(() => useSpaceStats(spaces));
    expect(result.current.total).toBe(6);
    expect(result.current.running).toBe(2);
    expect(result.current.stopped).toBe(1);
    expect(result.current.pending).toBe(1);
    expect(result.current.failed).toBe(1);
    expect(result.current.deleted).toBe(1);
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

  it('创建中（pending）的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'pending' });
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

  it('创建中（pending）的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'pending' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(false);
  });

  it('已删除的空间应该返回 false', () => {
    const space = createMockSpace({ status: 'deleted' });
    const { result } = renderHook(() => useCanDeleteSpace(space));
    expect(result.current).toBe(false);
  });
});
