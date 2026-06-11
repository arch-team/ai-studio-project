/**
 * usePagination / calculateOffset / calculatePage / generatePageNumbers 单元测试
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import {
  usePagination,
  calculateOffset,
  calculatePage,
  generatePageNumbers,
} from '@shared/hooks';

// MemoryRouter 包装器
function createWrapper(initialEntries: string[] = ['/']) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      MemoryRouter,
      { initialEntries },
      children
    );
  }
  return Wrapper;
}

// === usePagination ===

describe('usePagination', () => {
  it('应使用默认值初始化', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
    expect(result.current.pageSizeOptions).toEqual([10, 20, 50, 100]);
  });

  it('应使用自定义默认值初始化', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () =>
        usePagination({
          defaultPage: 2,
          defaultPageSize: 50,
          pageSizeOptions: [25, 50, 100],
        }),
      { wrapper }
    );

    expect(result.current.page).toBe(2);
    expect(result.current.pageSize).toBe(50);
    expect(result.current.pageSizeOptions).toEqual([25, 50, 100]);
  });

  it('setPage 应更新页码', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    act(() => {
      result.current.setPage(3);
    });

    expect(result.current.page).toBe(3);
  });

  it('setPageSize 应更新页大小并重置到第一页', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    act(() => {
      result.current.setPage(5);
    });
    expect(result.current.page).toBe(5);

    act(() => {
      result.current.setPageSize(50);
    });
    expect(result.current.pageSize).toBe(50);
    expect(result.current.page).toBe(1);
  });

  it('nextPage 应增加页码', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.page).toBe(2);
  });

  it('prevPage 应减少页码', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    act(() => {
      result.current.setPage(3);
    });

    act(() => {
      result.current.prevPage();
    });

    expect(result.current.page).toBe(2);
  });

  it('prevPage 在第一页时不应减少', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePagination(), { wrapper });

    act(() => {
      result.current.prevPage();
    });

    expect(result.current.page).toBe(1);
  });

  it('reset 应恢复为默认值', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => usePagination({ defaultPage: 1, defaultPageSize: 20 }),
      { wrapper }
    );

    act(() => {
      result.current.setPage(5);
      result.current.setPageSize(50);
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
  });

  // === getInfo ===

  describe('getInfo', () => {
    it('应正确计算分页信息', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => usePagination({ defaultPageSize: 10 }),
        { wrapper }
      );

      const info = result.current.getInfo(100);

      expect(info.totalPages).toBe(10);
      expect(info.totalItems).toBe(100);
      expect(info.startItem).toBe(1);
      expect(info.endItem).toBe(10);
      expect(info.hasNextPage).toBe(true);
      expect(info.hasPrevPage).toBe(false);
    });

    it('应正确处理中间页', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => usePagination({ defaultPageSize: 10 }),
        { wrapper }
      );

      act(() => {
        result.current.setPage(5);
      });

      const info = result.current.getInfo(100);

      expect(info.startItem).toBe(41);
      expect(info.endItem).toBe(50);
      expect(info.hasNextPage).toBe(true);
      expect(info.hasPrevPage).toBe(true);
    });

    it('应正确处理最后一页', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => usePagination({ defaultPageSize: 10 }),
        { wrapper }
      );

      act(() => {
        result.current.setPage(10);
      });

      const info = result.current.getInfo(95);

      expect(info.totalPages).toBe(10);
      expect(info.startItem).toBe(91);
      expect(info.endItem).toBe(95);
      expect(info.hasNextPage).toBe(false);
      expect(info.hasPrevPage).toBe(true);
    });

    it('应正确处理空数据 (total = 0)', () => {
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => usePagination({ defaultPageSize: 10 }),
        { wrapper }
      );

      const info = result.current.getInfo(0);

      expect(info.totalPages).toBe(1);
      expect(info.totalItems).toBe(0);
      expect(info.startItem).toBe(0);
      expect(info.endItem).toBe(0);
      expect(info.hasNextPage).toBe(false);
      expect(info.hasPrevPage).toBe(false);
    });
  });
});

// === calculateOffset ===

describe('calculateOffset', () => {
  it('应正确计算偏移量', () => {
    expect(calculateOffset(1, 20)).toBe(0);
    expect(calculateOffset(2, 20)).toBe(20);
    expect(calculateOffset(3, 10)).toBe(20);
    expect(calculateOffset(5, 50)).toBe(200);
  });
});

// === calculatePage ===

describe('calculatePage', () => {
  it('应从偏移量正确计算页码', () => {
    expect(calculatePage(0, 20)).toBe(1);
    expect(calculatePage(20, 20)).toBe(2);
    expect(calculatePage(40, 20)).toBe(3);
    expect(calculatePage(25, 10)).toBe(3);
  });
});

// === generatePageNumbers ===

describe('generatePageNumbers', () => {
  it('总页数小于等于 maxVisible 时应返回所有页码', () => {
    expect(generatePageNumbers(1, 5)).toEqual([1, 2, 3, 4, 5]);
    expect(generatePageNumbers(3, 7)).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });

  it('当前页靠近开头时应正确生成省略号', () => {
    const pages = generatePageNumbers(2, 20, 7);
    expect(pages[0]).toBe(1);
    expect(pages[pages.length - 1]).toBe(20);
    expect(pages).toContain('...');
  });

  it('当前页靠近结尾时应正确生成省略号', () => {
    const pages = generatePageNumbers(19, 20, 7);
    expect(pages[0]).toBe(1);
    expect(pages[pages.length - 1]).toBe(20);
    expect(pages).toContain('...');
  });

  it('当前页在中间时应生成两个省略号', () => {
    const pages = generatePageNumbers(10, 20, 7);
    expect(pages[0]).toBe(1);
    expect(pages[pages.length - 1]).toBe(20);
    const ellipsisCount = pages.filter((p) => p === '...').length;
    expect(ellipsisCount).toBe(2);
  });

  it('总页数为 1 时应只返回 [1]', () => {
    expect(generatePageNumbers(1, 1)).toEqual([1]);
  });
});
