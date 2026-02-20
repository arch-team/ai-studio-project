/**
 * 日期范围计算工具函数
 *
 * 将 Cloudscape DateRangePicker 的值转换为 API 可用的时间范围参数。
 * 消除各页面（监控、成本分析、资源报表）中的重复实现。
 */

import type { DateRangePickerProps } from '@cloudscape-design/components';

/**
 * 时间单位到毫秒的映射
 */
const UNIT_TO_MS: Record<string, number> = {
  minute: 60 * 1000,
  hour: 60 * 60 * 1000,
  day: 24 * 60 * 60 * 1000,
  week: 7 * 24 * 60 * 60 * 1000,
  month: 30 * 24 * 60 * 60 * 1000,
};

/**
 * 计算时间范围（返回 ISO 字符串格式）
 *
 * @param dateRange - Cloudscape DateRangePicker 的值
 * @param defaultHours - 默认时间范围（小时），用于 dateRange 为 null 时
 */
export function calculateTimeRange(
  dateRange: DateRangePickerProps.Value | null,
  defaultHours: number = 1,
): { startTime: string; endTime: string } {
  const now = new Date();
  let startTime: Date;
  let endTime: Date = now;

  if (!dateRange) {
    startTime = new Date(now.getTime() - defaultHours * 60 * 60 * 1000);
  } else if (dateRange.type === 'relative') {
    const { amount, unit } = dateRange;
    const ms = UNIT_TO_MS[unit] || UNIT_TO_MS.day;
    startTime = new Date(now.getTime() - amount * ms);
  } else {
    startTime = new Date(dateRange.startDate);
    endTime = new Date(dateRange.endDate);
  }

  return {
    startTime: startTime.toISOString(),
    endTime: endTime.toISOString(),
  };
}

/**
 * 计算日期范围（返回 YYYY-MM-DD 格式）
 *
 * @param dateRange - Cloudscape DateRangePicker 的值
 * @param defaultDays - 默认日期范围（天），用于 dateRange 为 null 时
 */
export function calculateDateRange(
  dateRange: DateRangePickerProps.Value | null,
  defaultDays: number = 30,
): { startDate: string; endDate: string } {
  const now = new Date();
  let startDate: Date;
  let endDate: Date = now;

  if (!dateRange) {
    startDate = new Date(now.getTime() - defaultDays * 24 * 60 * 60 * 1000);
  } else if (dateRange.type === 'relative') {
    const { amount, unit } = dateRange;
    const ms = UNIT_TO_MS[unit] || UNIT_TO_MS.day;
    startDate = new Date(now.getTime() - amount * ms);
  } else {
    startDate = new Date(dateRange.startDate);
    endDate = new Date(dateRange.endDate);
  }

  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
  };
}
