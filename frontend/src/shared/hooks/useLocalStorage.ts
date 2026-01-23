/**
 * LocalStorage Hooks
 *
 * 提供类型安全的 localStorage 操作。
 */

import { useCallback, useEffect, useState } from 'react';

/**
 * localStorage Hook
 *
 * @example
 * ```tsx
 * const [theme, setTheme, removeTheme] = useLocalStorage('theme', 'light');
 *
 * return (
 *   <Button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
 *     切换主题
 *   </Button>
 * );
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // 获取初始值
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // 监听其他标签页的 storage 变化
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === key && event.newValue !== null) {
        try {
          setStoredValue(JSON.parse(event.newValue) as T);
        } catch {
          setStoredValue(event.newValue as unknown as T);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key]);

  // 设置值
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // 移除值
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [initialValue, key]);

  return [storedValue, setValue, removeValue];
}

/**
 * sessionStorage Hook
 *
 * 与 useLocalStorage 相同，但使用 sessionStorage。
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.sessionStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting sessionStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.sessionStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing sessionStorage key "${key}":`, error);
    }
  }, [initialValue, key]);

  return [storedValue, setValue, removeValue];
}

/**
 * 用户偏好设置 Hook
 *
 * 专门用于存储用户偏好设置的高级 Hook。
 *
 * @example
 * ```tsx
 * const preferences = useUserPreferences({
 *   tablePageSize: 20,
 *   sidebarCollapsed: false,
 *   theme: 'system',
 * });
 *
 * return (
 *   <Button onClick={() => preferences.set('sidebarCollapsed', !preferences.value.sidebarCollapsed)}>
 *     切换侧边栏
 *   </Button>
 * );
 * ```
 */
export function useUserPreferences<T extends Record<string, unknown>>(defaultPreferences: T) {
  const [value, setValue, removeValue] = useLocalStorage<T>(
    'user_preferences',
    defaultPreferences
  );

  const set = useCallback(
    <K extends keyof T>(key: K, newValue: T[K]) => {
      setValue((prev) => ({ ...prev, [key]: newValue }));
    },
    [setValue]
  );

  const reset = useCallback(() => {
    setValue(defaultPreferences);
  }, [defaultPreferences, setValue]);

  return {
    value,
    set,
    reset,
    clear: removeValue,
  };
}
