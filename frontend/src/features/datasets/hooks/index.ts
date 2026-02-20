/**
 * Datasets business logic hooks.
 *
 * 业务逻辑 hooks，对应后端 Application 层的 Services。
 * 封装复杂的业务逻辑，如数据转换、状态计算等。
 */

import { useMemo } from 'react';
import type { DatasetSummary, DatasetStatus } from '../types';

// 上传相关 hook
export { useDatasetUpload } from './useDatasetUpload';
export type { UseDatasetUploadReturn } from './useDatasetUpload';

/**
 * 计算数据集状态统计
 */
export function useDatasetStats(datasets: DatasetSummary[] | undefined) {
  return useMemo(() => {
    if (!datasets) {
      return {
        total: 0,
        available: 0,
        preparing: 0,
        archived: 0,
        error: 0,
        totalSizeBytes: 0,
      };
    }

    const stats = datasets.reduce(
      (acc, dataset) => {
        acc.total++;
        acc[dataset.status]++;
        acc.totalSizeBytes += dataset.total_size_bytes || 0;
        return acc;
      },
      {
        total: 0,
        available: 0,
        preparing: 0,
        archived: 0,
        error: 0,
        totalSizeBytes: 0,
      } as Record<DatasetStatus | 'total' | 'totalSizeBytes', number>
    );

    return stats;
  }, [datasets]);
}

/**
 * 格式化文件大小
 */
export function useFormatFileSize() {
  return (bytes: number | null | undefined): string => {
    if (bytes === null || bytes === undefined) return '-';

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    let size = bytes;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(unitIndex > 0 ? 2 : 0)} ${units[unitIndex]}`;
  };
}

/**
 * 检查数据集是否可编辑
 */
export function useCanEditDataset(dataset: DatasetSummary | undefined, currentUserId: number | undefined) {
  return useMemo(() => {
    if (!dataset || !currentUserId) return false;

    // 只有所有者可以编辑
    if (dataset.owner_id !== currentUserId) return false;

    // 错误状态下不可编辑
    if (dataset.status === 'error') return false;

    return true;
  }, [dataset, currentUserId]);
}

/**
 * 检查数据集是否可删除
 */
export function useCanDeleteDataset(dataset: DatasetSummary | undefined, currentUserId: number | undefined) {
  return useMemo(() => {
    if (!dataset || !currentUserId) return false;

    // 只有所有者可以删除
    if (dataset.owner_id !== currentUserId) return false;

    // 准备中的数据集不可删除
    if (dataset.status === 'preparing') return false;

    return true;
  }, [dataset, currentUserId]);
}
