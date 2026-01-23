/**
 * Audit business logic hooks.
 */

import { useMemo } from 'react';
import type { AuditLog, AuditAction, AuditResult } from '../types';

/**
 * 计算审计日志统计
 */
export function useAuditStats(logs: AuditLog[] | undefined) {
  return useMemo(() => {
    if (!logs) {
      return {
        total: 0,
        success: 0,
        failure: 0,
        partial: 0,
        byAction: {} as Record<AuditAction, number>,
      };
    }

    const stats = logs.reduce(
      (acc, log) => {
        acc.total++;
        acc[log.result]++;
        acc.byAction[log.action] = (acc.byAction[log.action] || 0) + 1;
        return acc;
      },
      {
        total: 0,
        success: 0,
        failure: 0,
        partial: 0,
        byAction: {} as Record<AuditAction, number>,
      } as {
        total: number;
        byAction: Record<AuditAction, number>;
      } & Record<AuditResult, number>
    );

    return stats;
  }, [logs]);
}

/**
 * 格式化变更记录为可读字符串
 */
export function useFormatChanges() {
  return (
    changes: Record<string, { old: unknown; new: unknown }> | null
  ): string[] => {
    if (!changes) return [];

    return Object.entries(changes).map(([field, { old: oldValue, new: newValue }]) => {
      const oldStr = oldValue === null ? '空' : String(oldValue);
      const newStr = newValue === null ? '空' : String(newValue);
      return `${field}: ${oldStr} → ${newStr}`;
    });
  };
}

/**
 * 格式化时间为相对时间
 */
export function useFormatRelativeTime() {
  return (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();

    const seconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  };
}

/**
 * 生成审计日志摘要
 */
export function useAuditLogSummary() {
  return (log: AuditLog): string => {
    const user = log.username || '系统';
    const action = log.action;
    const resource = log.resource_name || log.resource_id || '未知资源';

    return `${user} ${action} 了 ${resource}`;
  };
}
