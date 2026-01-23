/**
 * 防抖和节流 Hooks
 */

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * 防抖值 Hook
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 *
 * // 只在 debouncedSearchTerm 变化时发起请求
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     searchApi(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 * ```
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * 防抖回调 Hook
 *
 * @example
 * ```tsx
 * const debouncedSearch = useDebouncedCallback((term: string) => {
 *   searchApi(term);
 * }, 300);
 *
 * return <Input onChange={(e) => debouncedSearch(e.detail.value)} />;
 * ```
 */
export function useDebouncedCallback<T extends (...args: Parameters<T>) => ReturnType<T>>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  );
}

/**
 * 节流回调 Hook
 *
 * @example
 * ```tsx
 * const throttledScroll = useThrottledCallback(() => {
 *   console.log('Scroll event');
 * }, 100);
 *
 * useEffect(() => {
 *   window.addEventListener('scroll', throttledScroll);
 *   return () => window.removeEventListener('scroll', throttledScroll);
 * }, [throttledScroll]);
 * ```
 */
export function useThrottledCallback<T extends (...args: Parameters<T>) => ReturnType<T>>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeSinceLastRun >= delay) {
        lastRun.current = now;
        callback(...args);
      } else {
        // 确保最后一次调用会被执行
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastRun);
      }
    },
    [callback, delay]
  );
}

/**
 * 防抖搜索输入 Hook
 *
 * 组合了搜索状态和防抖逻辑。
 *
 * @example
 * ```tsx
 * const { value, debouncedValue, setValue, clear, isDebouncing } =
 *   useDebouncedSearch(300);
 *
 * const { data } = useSearch({ query: debouncedValue });
 *
 * return (
 *   <Input
 *     value={value}
 *     onChange={(e) => setValue(e.detail.value)}
 *     placeholder={isDebouncing ? '搜索中...' : '搜索'}
 *   />
 * );
 * ```
 */
export function useDebouncedSearch(delay: number = 300) {
  const [value, setValue] = useState('');
  const debouncedValue = useDebounce(value, delay);
  const isDebouncing = value !== debouncedValue;

  const clear = useCallback(() => {
    setValue('');
  }, []);

  return {
    value,
    debouncedValue,
    setValue,
    clear,
    isDebouncing,
  };
}
