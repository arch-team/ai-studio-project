/**
 * Training module business logic hooks.
 *
 * 业务逻辑 hooks，对应后端 Application 层的 Services。
 * 封装复杂的业务逻辑，如状态计算、数据转换等。
 */

import { useMemo } from 'react';
import type { TrainingJobSummary, TrainingJobDetail, JobStatus, JobPriority } from '../types';

/**
 * 计算训练任务状态统计
 */
export function useTrainingJobStats(jobs: TrainingJobSummary[] | undefined) {
  return useMemo(() => {
    if (!jobs) {
      return {
        total: 0,
        submitted: 0,
        running: 0,
        paused: 0,
        preempted: 0,
        completed: 0,
        failed: 0,
        totalGpuHours: 0,
        totalCost: 0,
      };
    }

    return jobs.reduce(
      (acc, job) => {
        acc.total++;
        acc[job.status]++;
        acc.totalCost += job.estimated_cost_usd || 0;
        return acc;
      },
      {
        total: 0,
        submitted: 0,
        running: 0,
        paused: 0,
        preempted: 0,
        completed: 0,
        failed: 0,
        totalGpuHours: 0,
        totalCost: 0,
      } as Record<JobStatus | 'total' | 'totalGpuHours' | 'totalCost', number>
    );
  }, [jobs]);
}

/**
 * 检查任务是否可暂停
 */
export function useCanPauseJob(job: TrainingJobSummary | TrainingJobDetail | undefined) {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'running';
  }, [job]);
}

/**
 * 检查任务是否可恢复
 */
export function useCanResumeJob(job: TrainingJobSummary | TrainingJobDetail | undefined) {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'paused' || job.status === 'preempted';
  }, [job]);
}

/**
 * 检查任务是否可取消
 */
export function useCanCancelJob(job: TrainingJobSummary | TrainingJobDetail | undefined) {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'submitted' || job.status === 'running' || job.status === 'paused';
  }, [job]);
}

/**
 * 检查任务是否可删除
 */
export function useCanDeleteJob(job: TrainingJobSummary | TrainingJobDetail | undefined) {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'completed' || job.status === 'failed';
  }, [job]);
}

/**
 * 计算任务运行时长
 */
export function useJobDuration(job: TrainingJobSummary | TrainingJobDetail | undefined): string {
  return useMemo(() => {
    if (!job) return '-';

    const durationSeconds = job.duration_seconds;
    if (durationSeconds === null || durationSeconds === undefined) {
      // 如果任务正在运行，从 started_at 计算
      if (job.status === 'running' && job.started_at) {
        const started = new Date(job.started_at).getTime();
        const now = Date.now();
        const diffSeconds = Math.floor((now - started) / 1000);
        return formatDuration(diffSeconds);
      }
      return '-';
    }

    return formatDuration(durationSeconds);
  }, [job]);
}

/**
 * 格式化时长
 */
function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`;
  }
  if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`;
  }
  return `${secs}秒`;
}

/**
 * 计算任务进度百分比
 */
export function useJobProgress(job: TrainingJobDetail | undefined): number | null {
  return useMemo(() => {
    if (!job) return null;

    const { current_epoch, total_epochs, max_epochs } = job;
    const targetEpochs = total_epochs || max_epochs;

    if (current_epoch !== null && targetEpochs !== null && targetEpochs > 0) {
      return Math.min(100, Math.round((current_epoch / targetEpochs) * 100));
    }

    return null;
  }, [job]);
}

/**
 * 获取任务优先级排序权重
 */
export function usePriorityWeight(priority: JobPriority): number {
  const weights: Record<JobPriority, number> = {
    high: 3,
    medium: 2,
    low: 1,
  };
  return weights[priority];
}

/**
 * 检查任务是否正在运行中（广义）
 */
export function useIsJobActive(job: TrainingJobSummary | TrainingJobDetail | undefined): boolean {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'submitted' || job.status === 'running' || job.status === 'paused';
  }, [job]);
}

/**
 * 检查任务是否已完结
 */
export function useIsJobFinished(job: TrainingJobSummary | TrainingJobDetail | undefined): boolean {
  return useMemo(() => {
    if (!job) return false;
    return job.status === 'completed' || job.status === 'failed';
  }, [job]);
}

/**
 * 计算总 GPU 数量
 */
export function useTotalGpus(job: TrainingJobDetail | undefined): number {
  return useMemo(() => {
    if (!job) return 0;
    return job.node_count * job.gpu_per_node;
  }, [job]);
}
