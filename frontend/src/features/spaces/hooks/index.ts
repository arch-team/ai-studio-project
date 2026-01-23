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
        running: 0,
        stopped: 0,
        creating: 0,
        failed: 0,
        deleting: 0,
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
        running: 0,
        stopped: 0,
        creating: 0,
        failed: 0,
        deleting: 0,
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
 * 检查空间是否可打开
 */
export function useCanOpenSpace(space: SpaceSummary | undefined) {
  return useMemo(() => {
    if (!space) return false;
    return space.status === 'running' && space.url !== null;
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

/**
 * 计算空间运行时长
 */
export function useSpaceRunningDuration(space: SpaceSummary | undefined): string {
  return useMemo(() => {
    if (!space || !space.started_at || space.status !== 'running') {
      return '-';
    }

    const started = new Date(space.started_at).getTime();
    const now = Date.now();
    const diffMs = now - started;

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`;
    }
    return `${minutes}分钟`;
  }, [space]);
}
