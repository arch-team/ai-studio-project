/**
 * useThemeEffect Hook
 *
 * 将 UI Store 中的主题（明/暗/跟随系统）与密度偏好
 * 应用到 Cloudscape 全局样式（applyMode / applyDensity）。
 *
 * - theme = 'system' 时监听系统配色变化并实时跟随
 * - 在应用根部调用一次即可
 */

import { useEffect } from 'react';
import { applyDensity, applyMode, Density, Mode } from '@cloudscape-design/global-styles';
import { useUIStore } from '@store/slices/uiSlice';

/**
 * 应用主题与密度到 Cloudscape 全局样式。
 *
 * @example
 * ```tsx
 * function App() {
 *   useThemeEffect();
 *   return <RouterProvider router={router} />;
 * }
 * ```
 */
export function useThemeEffect(): void {
  const theme = useUIStore((s) => s.theme);
  const density = useUIStore((s) => s.density);

  // 应用配色模式（含 system 跟随）
  useEffect(() => {
    if (theme === 'system') {
      const media = window.matchMedia('(prefers-color-scheme: dark)');
      const apply = () => applyMode(media.matches ? Mode.Dark : Mode.Light);
      apply();
      media.addEventListener('change', apply);
      return () => media.removeEventListener('change', apply);
    }

    applyMode(theme === 'dark' ? Mode.Dark : Mode.Light);
    return undefined;
  }, [theme]);

  // 应用内容密度
  useEffect(() => {
    applyDensity(density === 'compact' ? Density.Compact : Density.Comfortable);
  }, [density]);
}
