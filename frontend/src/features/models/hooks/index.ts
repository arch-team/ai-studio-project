/**
 * Models module business logic hooks.
 */

import { useMemo } from 'react';

// 导入类型 - 由于 models 模块可能还没有完整的类型定义，我们在这里定义接口
export interface ModelSummary {
  id: number;
  model_name: string;
  version: string;
  status: ModelStatus;
  framework: string;
  training_job_id: number;
  created_at: string;
  registry_status?: 'pending' | 'synced' | 'failed';
  metrics?: Record<string, number>;
}

export type ModelStatus =
  | 'training'
  | 'registered'
  | 'approved'
  | 'deployed'
  | 'archived'
  | 'rejected';

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
        approved: 0,
        deployed: 0,
        archived: 0,
        rejected: 0,
      };
    }

    return models.reduce(
      (acc, model) => {
        acc.total++;
        acc[model.status]++;
        return acc;
      },
      {
        total: 0,
        training: 0,
        registered: 0,
        approved: 0,
        deployed: 0,
        archived: 0,
        rejected: 0,
      } as Record<ModelStatus | 'total', number>
    );
  }, [models]);
}

/**
 * 检查模型是否可审批
 */
export function useCanApproveModel(model: ModelSummary | undefined) {
  return useMemo(() => {
    if (!model) return false;
    return model.status === 'registered';
  }, [model]);
}

/**
 * 检查模型是否可部署
 */
export function useCanDeployModel(model: ModelSummary | undefined) {
  return useMemo(() => {
    if (!model) return false;
    return model.status === 'approved';
  }, [model]);
}

/**
 * 检查模型是否可归档
 */
export function useCanArchiveModel(model: ModelSummary | undefined) {
  return useMemo(() => {
    if (!model) return false;
    return model.status === 'approved' || model.status === 'deployed';
  }, [model]);
}

/**
 * 检查模型是否已同步到 Registry
 */
export function useIsRegistrySynced(model: ModelSummary | undefined): boolean {
  return useMemo(() => {
    if (!model) return false;
    return model.registry_status === 'synced';
  }, [model]);
}

/**
 * 获取模型的主要指标
 */
export function useModelMainMetric(model: ModelSummary | undefined): { name: string; value: number } | null {
  return useMemo(() => {
    if (!model || !model.metrics) return null;

    // 优先返回 accuracy，其次 loss，其次 f1_score
    const priorityMetrics = ['accuracy', 'loss', 'f1_score'];

    for (const metric of priorityMetrics) {
      if (metric in model.metrics) {
        return { name: metric, value: model.metrics[metric] };
      }
    }

    // 返回第一个可用的指标
    const firstKey = Object.keys(model.metrics)[0];
    if (firstKey) {
      return { name: firstKey, value: model.metrics[firstKey] };
    }

    return null;
  }, [model]);
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
 * 按版本排序模型
 */
export function useSortedModelVersions(models: ModelSummary[] | undefined) {
  return useMemo(() => {
    if (!models) return [];

    return [...models].sort((a, b) => {
      // 解析版本号 (假设格式为 v1.0.0)
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
  }, [models]);
}

/**
 * 获取模型的生命周期阶段描述
 */
export function useModelLifecycleStage(status: ModelStatus): string {
  const stages: Record<ModelStatus, string> = {
    training: '训练中',
    registered: '待审批',
    approved: '已审批',
    deployed: '已部署',
    archived: '已归档',
    rejected: '已拒绝',
  };
  return stages[status];
}
