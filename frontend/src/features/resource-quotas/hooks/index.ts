/**
 * Resource Quotas module business logic hooks.
 */

import { useMemo } from "react";

// 类型定义
export interface ResourceQuota {
  id: number;
  name: string;
  description: string | null;
  quota_type: "user" | "team" | "project";
  max_cpu_cores: number;
  reserved_cpu_cores: number;
  max_gpu_count: number;
  reserved_gpu_count: number;
  gpu_types: string[] | null;
  max_memory_gb: number;
  reserved_memory_gb: number;
  max_storage_gb: number | null;
  max_concurrent_jobs: number;
  max_total_jobs: number | null;
  max_spot_instances: number;
  status: "active" | "suspended" | "expired";
  valid_from: string;
  valid_until: string | null;
  created_at: string;
  // 使用量 (从 Kueue 同步)
  used_cpu_cores?: number;
  used_gpu_count?: number;
  used_memory_gb?: number;
  current_concurrent_jobs?: number;
}

export interface QuotaUsage {
  type: "cpu" | "gpu" | "memory" | "jobs";
  used: number;
  reserved: number;
  max: number;
  unit: string;
}

/**
 * 计算配额使用率
 */
export function useQuotaUsage(quota: ResourceQuota | undefined): QuotaUsage[] {
  return useMemo(() => {
    if (!quota) return [];

    return [
      {
        type: "gpu",
        used: quota.used_gpu_count || 0,
        reserved: quota.reserved_gpu_count,
        max: quota.max_gpu_count,
        unit: "GPU",
      },
      {
        type: "cpu",
        used: quota.used_cpu_cores || 0,
        reserved: quota.reserved_cpu_cores,
        max: quota.max_cpu_cores,
        unit: "vCPU",
      },
      {
        type: "memory",
        used: quota.used_memory_gb || 0,
        reserved: quota.reserved_memory_gb,
        max: quota.max_memory_gb,
        unit: "GB",
      },
      {
        type: "jobs",
        used: quota.current_concurrent_jobs || 0,
        reserved: 0,
        max: quota.max_concurrent_jobs,
        unit: "个",
      },
    ];
  }, [quota]);
}

/**
 * 计算使用百分比（纯函数，非 Hook）
 */
export function getUsagePercentage(used: number, max: number): number {
  if (max <= 0) return 0;
  return Math.min(100, Math.round((used / max) * 100));
}

/**
 * 获取使用率状态颜色（纯函数，非 Hook）
 */
export function getUsageColor(percentage: number): "green" | "pending" | "red" {
  if (percentage < 60) return "green";
  if (percentage < 85) return "pending";
  return "red";
}

/**
 * 检查配额是否即将耗尽
 */
export function useIsQuotaNearLimit(quota: ResourceQuota | undefined): boolean {
  return useMemo(() => {
    if (!quota) return false;

    const gpuUsage = (quota.used_gpu_count || 0) / quota.max_gpu_count;
    const cpuUsage = (quota.used_cpu_cores || 0) / quota.max_cpu_cores;
    const jobsUsage =
      (quota.current_concurrent_jobs || 0) / quota.max_concurrent_jobs;

    // 任一资源使用超过 80% 视为接近限制
    return gpuUsage > 0.8 || cpuUsage > 0.8 || jobsUsage > 0.8;
  }, [quota]);
}

/**
 * 检查配额是否有效
 */
export function useIsQuotaValid(quota: ResourceQuota | undefined): boolean {
  return useMemo(() => {
    if (!quota) return false;
    if (quota.status !== "active") return false;

    const now = new Date();
    const validFrom = new Date(quota.valid_from);
    if (now < validFrom) return false;

    if (quota.valid_until) {
      const validUntil = new Date(quota.valid_until);
      if (now > validUntil) return false;
    }

    return true;
  }, [quota]);
}

/**
 * 计算配额剩余有效天数
 */
export function useQuotaRemainingDays(
  quota: ResourceQuota | undefined,
): number | null {
  return useMemo(() => {
    if (!quota || !quota.valid_until) return null;

    const now = new Date();
    const validUntil = new Date(quota.valid_until);
    const diffMs = validUntil.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    return diffDays > 0 ? diffDays : 0;
  }, [quota]);
}

/**
 * 检查是否可以提交新任务
 */
export function useCanSubmitJob(
  quota: ResourceQuota | undefined,
  requiredGpus: number = 1,
): boolean {
  return useMemo(() => {
    if (!quota) return false;
    if (quota.status !== "active") return false;

    const availableGpus = quota.max_gpu_count - (quota.used_gpu_count || 0);
    const availableJobs =
      quota.max_concurrent_jobs - (quota.current_concurrent_jobs || 0);

    return availableGpus >= requiredGpus && availableJobs > 0;
  }, [quota, requiredGpus]);
}

/**
 * 获取配额状态标签（纯函数，非 Hook）
 */
export function getQuotaStatusLabel(status: ResourceQuota["status"]): string {
  const labels: Record<ResourceQuota["status"], string> = {
    active: "活跃",
    suspended: "已暂停",
    expired: "已过期",
  };
  return labels[status];
}

/**
 * 获取配额类型标签（纯函数，非 Hook）
 */
export function getQuotaTypeLabel(type: ResourceQuota["quota_type"]): string {
  const labels: Record<ResourceQuota["quota_type"], string> = {
    user: "用户",
    team: "团队",
    project: "项目",
  };
  return labels[type];
}

/**
 * 格式化 GPU 类型列表（纯函数，非 Hook）
 */
export function formatGpuTypes(gpuTypes: string[] | null): string {
  if (!gpuTypes || gpuTypes.length === 0) return "所有类型";
  return gpuTypes.join(", ");
}
