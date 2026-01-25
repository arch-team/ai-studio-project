/**
 * Model versions business logic hooks.
 */

import { useMemo } from 'react';
import type { ModelVersionSummary } from '../types';

/**
 * 按版本排序模型版本列表（最新版本在前）
 */
export function useSortedModelVersions(versions: ModelVersionSummary[] | undefined) {
  return useMemo(() => {
    if (!versions) return [];

    return [...versions].sort((a, b) => {
      // 解析版本号 (假设格式为 v1.0.0 或 1.0.0)
      const parseVersion = (v: string) => {
        const match = v.match(/v?(\d+)\.(\d+)\.(\d+)/);
        if (match) {
          return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
        }
        return [0, 0, 0];
      };

      const [aMajor, aMinor, aPatch] = parseVersion(a.version);
      const [bMajor, bMinor, bPatch] = parseVersion(b.version);

      if (aMajor !== bMajor) return bMajor - aMajor;
      if (aMinor !== bMinor) return bMinor - aMinor;
      return bPatch - aPatch;
    });
  }, [versions]);
}

/**
 * 获取最新版本
 */
export function useLatestVersion(versions: ModelVersionSummary[] | undefined): ModelVersionSummary | null {
  const sorted = useSortedModelVersions(versions);
  return sorted.length > 0 ? sorted[0] : null;
}

/**
 * 获取版本数量统计
 */
export function useVersionStats(versions: ModelVersionSummary[] | undefined) {
  return useMemo(() => {
    if (!versions) {
      return {
        total: 0,
        registered: 0,
        deployed: 0,
        archived: 0,
      };
    }

    return versions.reduce(
      (acc, v) => {
        acc.total++;
        if (v.status === 'registered') acc.registered++;
        if (v.status === 'deployed') acc.deployed++;
        if (v.status === 'archived') acc.archived++;
        return acc;
      },
      { total: 0, registered: 0, deployed: 0, archived: 0 }
    );
  }, [versions]);
}

/**
 * 检查是否可以回滚到指定版本
 */
export function useCanRollbackToVersion(
  targetVersion: string,
  currentVersion: string | undefined,
  versions: ModelVersionSummary[] | undefined
): boolean {
  return useMemo(() => {
    if (!currentVersion || !versions) return false;
    if (targetVersion === currentVersion) return false;

    const version = versions.find((v) => v.version === targetVersion);
    if (!version) return false;

    // 只能回滚到已注册或已部署的版本
    return version.status === 'registered' || version.status === 'deployed';
  }, [targetVersion, currentVersion, versions]);
}

/**
 * 计算版本之间的指标变化
 */
export function useVersionMetricsDiff(
  v1Metrics: Record<string, unknown> | null | undefined,
  v2Metrics: Record<string, unknown> | null | undefined
) {
  return useMemo(() => {
    if (!v1Metrics || !v2Metrics) return {};

    const allKeys = new Set([
      ...Object.keys(v1Metrics),
      ...Object.keys(v2Metrics),
    ]);

    const diff: Record<string, { v1: number | null; v2: number | null; change: number | null }> = {};

    allKeys.forEach((key) => {
      const v1 = typeof v1Metrics[key] === 'number' ? (v1Metrics[key] as number) : null;
      const v2 = typeof v2Metrics[key] === 'number' ? (v2Metrics[key] as number) : null;

      let change: number | null = null;
      if (v1 !== null && v2 !== null && v1 !== 0) {
        change = ((v2 - v1) / Math.abs(v1)) * 100;
      }

      diff[key] = { v1, v2, change };
    });

    return diff;
  }, [v1Metrics, v2Metrics]);
}
