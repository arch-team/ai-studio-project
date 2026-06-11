/**
 * useDebounce / useDebouncedCallback / useThrottledCallback / useDebouncedSearch 单元测试
 */

import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  useDebounce,
  useDebouncedCallback,
  useThrottledCallback,
  useDebouncedSearch,
} from '@shared/hooks';

// === useDebounce ===

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('应返回初始值', () => {
    const { result } = renderHook(() => useDebounce('hello', 500));
    expect(result.current).toBe('hello');
  });

  it('应在延迟后更新防抖值', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'hello' } }
    );

    rerender({ value: 'world' });
    // 延迟未到，仍为旧值
    expect(result.current).toBe('hello');

    act(() => vi.advanceTimersByTime(500));
    expect(result.current).toBe('world');
  });

  it('应在延迟内多次变更时只取最后一次值', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } }
    );

    rerender({ value: 'b' });
    act(() => vi.advanceTimersByTime(100));

    rerender({ value: 'c' });
    act(() => vi.advanceTimersByTime(100));

    rerender({ value: 'd' });
    // 还未到 300ms
    expect(result.current).toBe('a');

    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBe('d');
  });

  it('应支持数字类型', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 200),
      { initialProps: { value: 0 } }
    );

    rerender({ value: 42 });
    expect(result.current).toBe(0);

    act(() => vi.advanceTimersByTime(200));
    expect(result.current).toBe(42);
  });

  it('当 delay 变更时应重置定时器', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    rerender({ value: 'world', delay: 500 });
    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBe('hello');

    // 改变 delay 会重置
    rerender({ value: 'world', delay: 200 });
    act(() => vi.advanceTimersByTime(200));
    expect(result.current).toBe('world');
  });
});

// === useDebouncedCallback ===

describe('useDebouncedCallback', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('应在延迟后调用回调', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current('arg1');
    });

    expect(callback).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(300));
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('arg1');
  });

  it('应在多次调用时只执行最后一次', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current('a');
      result.current('b');
      result.current('c');
    });

    act(() => vi.advanceTimersByTime(300));
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('c');
  });

  it('应在组件卸载时清除定时器', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => {
      result.current('test');
    });

    unmount();
    act(() => vi.advanceTimersByTime(300));
    expect(callback).not.toHaveBeenCalled();
  });
});

// === useThrottledCallback ===

describe('useThrottledCallback', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('应立即执行第一次调用', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottledCallback(callback, 300));

    act(() => {
      result.current('first');
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('first');
  });

  it('应在节流期间内忽略后续调用，但保证最后一次被执行', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottledCallback(callback, 300));

    act(() => {
      result.current('first');
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // 在节流期间再次调用
    act(() => {
      result.current('second');
    });
    // 尚未过节流期，不会立即调用
    expect(callback).toHaveBeenCalledTimes(1);

    // 等待节流期结束，最后一次调用应被执行
    act(() => vi.advanceTimersByTime(300));
    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenLastCalledWith('second');
  });

  it('应在节流期后允许再次调用', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottledCallback(callback, 300));

    act(() => {
      result.current('first');
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // 等节流期结束
    act(() => vi.advanceTimersByTime(300));

    act(() => {
      result.current('second');
    });
    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenLastCalledWith('second');
  });

  it('应在组件卸载时清除定时器', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useThrottledCallback(callback, 300));

    act(() => {
      result.current('first');
    });
    act(() => {
      result.current('second');
    });

    unmount();
    act(() => vi.advanceTimersByTime(300));
    // 第一次立即执行，卸载后的定时器不应再触发
    expect(callback).toHaveBeenCalledTimes(1);
  });
});

// === useDebouncedSearch ===

describe('useDebouncedSearch', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('应返回初始空值', () => {
    const { result } = renderHook(() => useDebouncedSearch(300));
    expect(result.current.value).toBe('');
    expect(result.current.debouncedValue).toBe('');
    expect(result.current.isDebouncing).toBe(false);
  });

  it('应在 setValue 后标记正在防抖', () => {
    const { result } = renderHook(() => useDebouncedSearch(300));

    act(() => {
      result.current.setValue('search');
    });

    expect(result.current.value).toBe('search');
    expect(result.current.isDebouncing).toBe(true);
    expect(result.current.debouncedValue).toBe('');
  });

  it('应在延迟后同步防抖值', () => {
    const { result } = renderHook(() => useDebouncedSearch(300));

    act(() => {
      result.current.setValue('search');
    });

    act(() => vi.advanceTimersByTime(300));

    expect(result.current.debouncedValue).toBe('search');
    expect(result.current.isDebouncing).toBe(false);
  });

  it('clear 应清除值', () => {
    const { result } = renderHook(() => useDebouncedSearch(300));

    act(() => {
      result.current.setValue('search');
    });
    act(() => vi.advanceTimersByTime(300));

    act(() => {
      result.current.clear();
    });

    expect(result.current.value).toBe('');
  });

  it('应使用默认延迟 300ms', () => {
    const { result } = renderHook(() => useDebouncedSearch());

    act(() => {
      result.current.setValue('test');
    });

    act(() => vi.advanceTimersByTime(200));
    expect(result.current.isDebouncing).toBe(true);

    act(() => vi.advanceTimersByTime(100));
    expect(result.current.isDebouncing).toBe(false);
    expect(result.current.debouncedValue).toBe('test');
  });
});
