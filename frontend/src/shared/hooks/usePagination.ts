/**
 * 分页 Hook
 *
 * 提供统一的分页状态管理和操作。
 */

import { useCallback, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

// === 类型定义 ===

export interface PaginationState {
  page: number;
  pageSize: number;
}

export interface PaginationActions {
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  reset: () => void;
}

export interface PaginationInfo {
  totalPages: number;
  totalItems: number;
  startItem: number;
  endItem: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
}

export interface UsePaginationOptions {
  defaultPage?: number;
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  syncWithUrl?: boolean;
  urlParamPrefix?: string;
}

export interface UsePaginationResult extends PaginationState, PaginationActions {
  getInfo: (total: number) => PaginationInfo;
  pageSizeOptions: number[];
}

// === 常量 ===

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// === Hook ===

/**
 * 分页状态管理 Hook
 *
 * @example
 * ```tsx
 * const pagination = usePagination({ defaultPageSize: 20, syncWithUrl: true });
 *
 * const { data } = useTrainingJobs({
 *   page: pagination.page,
 *   page_size: pagination.pageSize,
 * });
 *
 * const info = pagination.getInfo(data?.total ?? 0);
 *
 * return (
 *   <Pagination
 *     currentPageIndex={pagination.page}
 *     pagesCount={info.totalPages}
 *     onChange={({ detail }) => pagination.setPage(detail.currentPageIndex)}
 *   />
 * );
 * ```
 */
export function usePagination(options: UsePaginationOptions = {}): UsePaginationResult {
  const {
    defaultPage = 1,
    defaultPageSize = 20,
    pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
    syncWithUrl = false,
    urlParamPrefix = '',
  } = options;

  const [searchParams, setSearchParams] = useSearchParams();

  // URL 参数名
  const pageParam = urlParamPrefix ? `${urlParamPrefix}_page` : 'page';
  const pageSizeParam = urlParamPrefix ? `${urlParamPrefix}_size` : 'page_size';

  // 从 URL 或默认值初始化
  const initialPage = syncWithUrl
    ? parseInt(searchParams.get(pageParam) || String(defaultPage), 10)
    : defaultPage;
  const initialPageSize = syncWithUrl
    ? parseInt(searchParams.get(pageSizeParam) || String(defaultPageSize), 10)
    : defaultPageSize;

  const [page, setPageState] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  // 更新 URL 参数
  const updateUrl = useCallback(
    (newPage: number, newPageSize: number) => {
      if (!syncWithUrl) return;

      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev);
        newParams.set(pageParam, String(newPage));
        newParams.set(pageSizeParam, String(newPageSize));
        return newParams;
      });
    },
    [syncWithUrl, setSearchParams, pageParam, pageSizeParam]
  );

  const setPage = useCallback(
    (newPage: number) => {
      setPageState(newPage);
      updateUrl(newPage, pageSize);
    },
    [pageSize, updateUrl]
  );

  const setPageSize = useCallback(
    (newSize: number) => {
      setPageSizeState(newSize);
      // 改变页大小时重置到第一页
      setPageState(1);
      updateUrl(1, newSize);
    },
    [updateUrl]
  );

  const nextPage = useCallback(() => {
    setPage(page + 1);
  }, [page, setPage]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
    }
  }, [page, setPage]);

  const reset = useCallback(() => {
    setPageState(defaultPage);
    setPageSizeState(defaultPageSize);
    updateUrl(defaultPage, defaultPageSize);
  }, [defaultPage, defaultPageSize, updateUrl]);

  const getInfo = useCallback(
    (total: number): PaginationInfo => {
      const totalPages = Math.ceil(total / pageSize) || 1;
      const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
      const endItem = Math.min(page * pageSize, total);

      return {
        totalPages,
        totalItems: total,
        startItem,
        endItem,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1,
      };
    },
    [page, pageSize]
  );

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    nextPage,
    prevPage,
    reset,
    getInfo,
    pageSizeOptions,
  };
}

/**
 * 计算分页偏移量
 */
export function calculateOffset(page: number, pageSize: number): number {
  return (page - 1) * pageSize;
}

/**
 * 从偏移量计算页码
 */
export function calculatePage(offset: number, pageSize: number): number {
  return Math.floor(offset / pageSize) + 1;
}

/**
 * 生成页码数组
 *
 * @example
 * generatePageNumbers(5, 10) // [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
 * generatePageNumbers(5, 20, 5) // [1, 2, 3, 4, 5, '...', 20]
 */
export function generatePageNumbers(
  currentPage: number,
  totalPages: number,
  maxVisible: number = 7
): (number | '...')[] {
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages: (number | '...')[] = [];
  const sidePages = Math.floor((maxVisible - 3) / 2);

  // 始终显示第一页
  pages.push(1);

  if (currentPage <= sidePages + 2) {
    // 当前页靠近开头
    for (let i = 2; i <= maxVisible - 2; i++) {
      pages.push(i);
    }
    pages.push('...');
  } else if (currentPage >= totalPages - sidePages - 1) {
    // 当前页靠近结尾
    pages.push('...');
    for (let i = totalPages - maxVisible + 3; i < totalPages; i++) {
      pages.push(i);
    }
  } else {
    // 当前页在中间
    pages.push('...');
    for (let i = currentPage - sidePages; i <= currentPage + sidePages; i++) {
      pages.push(i);
    }
    pages.push('...');
  }

  // 始终显示最后一页
  pages.push(totalPages);

  return pages;
}
