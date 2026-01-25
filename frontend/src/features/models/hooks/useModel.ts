/**
 * Model business logic hooks.
 */

import { useMemo } from 'react';
import type { ModelSummary, ModelStatus } from '../types';

/**
 * 计算模型状态统计
 */
export function useModelStats(models: ModelSummary[] | undefined) {
  return useMemo(() => {
    if (!models) {
      return {
        total: 0,
        training: 0,
        registered: 0,
        deployed: 0,
        archived: 0,
        failed: 0,
      };
    }

    return models.reduce(
      (acc, model) => {
        acc.total++;
        if (acc[model.status] !== undefined) {
          acc[model.status]++;
        }
        return acc;
      },
      {
        total: 0,
        training: 0,
        registered: 0,
        deployed: 0,
        archived: 0,
        failed: 0,
      } as Record<ModelStatus | 'total', number>
    );
  }, [models]);
}

/**
 * 检查模型是否可部署
 */
export function useCanDeployModel(status: ModelStatus | undefined): boolean {
  return useMemo(() => {
    if (!status) return false;
    return status === 'registered';
  }, [status]);
}

/**
 * 检查模型是否可归档
 */
export function useCanArchiveModel(status: ModelStatus | undefined): boolean {
  return useMemo(() => {
    if (!status) return false;
    return status === 'registered' || status === 'deployed';
  }, [status]);
}

/**
 * 检查模型是否已同步到 Registry
 */
export function useIsRegistrySynced(registryArn: string | null | undefined): boolean {
  return useMemo(() => {
    return !!registryArn;
  }, [registryArn]);
}

/**
 * 获取模型的主要指标
 */
export function useModelMainMetric(
  metrics: Record<string, unknown> | null | undefined
): { name: string; value: number } | null {
  return useMemo(() => {
    if (!metrics) return null;

    // 优先返回 accuracy，其次 loss，其次 f1_score
    const priorityMetrics = ['accuracy', 'loss', 'f1_score'];

    for (const metric of priorityMetrics) {
      if (metric in metrics && typeof metrics[metric] === 'number') {
        return { name: metric, value: metrics[metric] as number };
      }
    }

    // 返回第一个可用的数字指标
    const firstKey = Object.keys(metrics).find(
      (k) => typeof metrics[k] === 'number'
    );
    if (firstKey) {
      return { name: firstKey, value: metrics[firstKey] as number };
    }

    return null;
  }, [metrics]);
}

/**
 * 格式化指标值
 */
export function useFormatMetricValue() {
  return (name: string, value: number): string => {
    if (name === 'accuracy' || name === 'f1_score') {
      return `${(value * 100).toFixed(2)}%`;
    }
    if (name === 'loss') {
      return value.toFixed(4);
    }
    return value.toFixed(2);
  };
}

/**
 * 获取模型的生命周期阶段描述
 */
export function useModelLifecycleStage(status: ModelStatus | undefined): string {
  const stages: Record<ModelStatus, string> = {
    training: '训练中',
    registered: '已注册',
    deployed: '已部署',
    archived: '已归档',
    failed: '已失败',
  };
  return status ? stages[status] : '-';
}
