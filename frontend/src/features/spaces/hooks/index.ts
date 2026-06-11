/**
 * Spaces business logic hooks.
 */

import { useMemo } from 'react';
import type { SpaceSummary, SpaceStatus } from '../types';

/**
 * 计算开发空间状态统计
 */
export function useSpaceStats(spaces: SpaceSummary[] | undefined) {
  return useMemo(() => {
    if (!spaces) {
      return {
        total: 0,
        pending: 0,
        running: 0,
        stopped: 0,
        failed: 0,
        deleted: 0,
      };
    }

    const stats = spaces.reduce(
      (acc, space) => {
        acc.total++;
        acc[space.status]++;
        return acc;
      },
      {
        total: 0,
        pending: 0,
        running: 0,
        stopped: 0,
        failed: 0,
        deleted: 0,
      } as Record<SpaceStatus | 'total', number>
    );

    return stats;
  }, [spaces]);
}

/**
 * 检查空间是否可启动
 */
export function useCanStartSpace(space: SpaceSummary | undefined) {
  return useMemo(() => {
    if (!space) return false;
    return space.status === 'stopped';
  }, [space]);
}

/**
 * 检查空间是否可停止
 */
export function useCanStopSpace(space: SpaceSummary | undefined) {
  return useMemo(() => {
    if (!space) return false;
    return space.status === 'running';
  }, [space]);
}

/**
 * 检查空间是否可删除
 */
export function useCanDeleteSpace(space: SpaceSummary | undefined) {
  return useMemo(() => {
    if (!space) return false;
    // 只有已停止或失败的空间可以删除
    return space.status === 'stopped' || space.status === 'failed';
  }, [space]);
}
