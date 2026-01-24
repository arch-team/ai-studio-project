/**
 * Template Hooks
 *
 * 业务逻辑相关的 hooks
 */

import { useMemo } from 'react';
import type { JobTemplateDetail, JobTemplateSummary } from '../types';

/**
 * 计算模板统计信息
 */
export function useTemplateStats(templates: JobTemplateSummary[] | undefined) {
  return useMemo(() => {
    if (!templates) {
      return { total: 0, totalUsage: 0, averageUsage: 0 };
    }

    const total = templates.length;
    const totalUsage = templates.reduce((acc, t) => acc + t.usage_count, 0);
    const averageUsage = total > 0 ? Math.round(totalUsage / total) : 0;

    return { total, totalUsage, averageUsage };
  }, [templates]);
}

/**
 * 检查用户是否可以编辑模板
 */
export function useCanEditTemplate(
  template: JobTemplateDetail | undefined,
  currentUserId: number | undefined
): boolean {
  return useMemo(() => {
    if (!template || !currentUserId) return false;
    return template.owner_id === currentUserId;
  }, [template, currentUserId]);
}

/**
 * 获取模板显示名称
 */
export function useTemplateDisplayName(
  template: JobTemplateDetail | undefined
): string {
  return useMemo(() => {
    if (!template) return '-';
    return template.description
      ? `${template.name} - ${template.description}`
      : template.name;
  }, [template]);
}
