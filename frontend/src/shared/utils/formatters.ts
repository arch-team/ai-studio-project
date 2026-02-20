/**
 * 共享格式化工具函数
 *
 * 提供跨模块使用的日期、数字等格式化函数，消除各模块重复定义。
 */

/**
 * 格式化日期时间（完整格式：年-月-日 时:分:秒）
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 格式化日期时间（简短格式：月-日 时:分）
 */
export function formatDateTimeShort(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化持续时间
 */
export function formatDuration(startTime: string | null, endTime: string | null): string {
  if (!startTime) return '-';
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${hours}h ${minutes}m`;
}

/**
 * 格式化货币
 */
export function formatCurrency(value: number): string {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(2)}`;
}

/**
 * 格式化数字，保留指定小数位
 */
export function formatNumber(value: number | undefined | null, decimals: number = 2): string {
  if (value === undefined || value === null) {
    return '-';
  }
  return value.toFixed(decimals);
}

/**
 * 格式化文件大小（字节 → 可读格式）
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '-';
  const mb = bytes / (1024 * 1024);
  return mb >= 1024
    ? `${(mb / 1024).toFixed(2)} GB`
    : `${mb.toFixed(2)} MB`;
}
