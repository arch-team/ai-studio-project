/**
 * 模型管理相关的工具函数
 */

import { ModelStatus, ModelFramework } from '@/types/model';

// ==================== 状态显示相关 ====================

/**
 * 模型状态映射
 */
export const MODEL_STATUS_MAP: Record<
  ModelStatus,
  { label: string; color: string; bgColor: string }
> = {
  [ModelStatus.UPLOADING]: {
    label: '上传中',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
  },
  [ModelStatus.PROCESSING]: {
    label: '处理中',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
  },
  [ModelStatus.AVAILABLE]: {
    label: '可用',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
  },
  [ModelStatus.FAILED]: {
    label: '失败',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
  },
  [ModelStatus.ARCHIVED]: {
    label: '已归档',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
  },
};

/**
 * 模型框架映射
 */
export const MODEL_FRAMEWORK_MAP: Record<ModelFramework, string> = {
  [ModelFramework.PYTORCH]: 'PyTorch',
  [ModelFramework.TENSORFLOW]: 'TensorFlow',
  [ModelFramework.ONNX]: 'ONNX',
  [ModelFramework.JFLUX]: 'JFlux',
  [ModelFramework.HUGGINGFACE]: 'HuggingFace',
  [ModelFramework.CUSTOM]: '自定义',
};

/**
 * 获取状态显示信息
 */
export function getStatusDisplay(status: ModelStatus) {
  return MODEL_STATUS_MAP[status] || MODEL_STATUS_MAP[ModelStatus.PROCESSING];
}

/**
 * 获取框架显示名称
 */
export function getFrameworkDisplay(framework: ModelFramework): string {
  return MODEL_FRAMEWORK_MAP[framework] || framework;
}

/**
 * 判断模型是否处于活动状态(需要监控)
 */
export function isModelActive(status: ModelStatus): boolean {
  return status === ModelStatus.UPLOADING || status === ModelStatus.PROCESSING;
}

/**
 * 判断模型版本是否可以发布
 */
export function canPublishVersion(status: ModelStatus, isPublished: boolean): boolean {
  return status === ModelStatus.AVAILABLE && !isPublished;
}

// ==================== 格式化相关 ====================

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
}

/**
 * 格式化时间戳
 */
export function formatTimestamp(timestamp: string | null | undefined): string {
  if (!timestamp) return '-';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  // 小于1分钟
  if (diffMins < 1) return '刚刚';

  // 小于1小时
  if (diffMins < 60) return `${diffMins}分钟前`;

  // 小于24小时
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}小时前`;

  // 小于7天
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}天前`;

  // 显示完整日期
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化版本号
 */
export function formatVersion(version: string | null | undefined): string {
  if (!version) return '-';
  return version.startsWith('v') ? version : `v${version}`;
}

// ==================== 验证相关 ====================

/**
 * 验证版本号格式
 */
export function validateVersion(version: string): boolean {
  // 支持语义化版本: v1.0.0, 1.0.0, v1.0, 1.0等
  const versionRegex = /^v?\d+(\.\d+)*$/;
  return versionRegex.test(version);
}

/**
 * 验证模型名称
 */
export function validateModelName(name: string): boolean {
  // 1-100字符,允许中英文、数字、下划线、中划线
  const nameRegex = /^[\u4e00-\u9fa5a-zA-Z0-9_-]{1,100}$/;
  return nameRegex.test(name);
}

// ==================== 数据转换相关 ====================

/**
 * 解析标签字符串为数组
 */
export function parseTags(tagsString: string): string[] {
  return tagsString
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);
}

/**
 * 标签数组转字符串
 */
export function stringifyTags(tags: string[] | null | undefined): string {
  if (!tags || tags.length === 0) return '';
  return tags.join(', ');
}

/**
 * 解析JSON字符串
 */
export function parseJSON<T = any>(
  jsonString: string,
  defaultValue: T
): T | string {
  try {
    return JSON.parse(jsonString) as T;
  } catch {
    return jsonString || defaultValue;
  }
}

/**
 * 对象转JSON字符串
 */
export function stringifyJSON(obj: any): string {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return '';
  }
}

// ==================== 排序相关 ====================

/**
 * 版本号比较函数
 */
export function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.replace(/^v/, '').split('.').map(Number);
  const parts2 = v2.replace(/^v/, '').split('.').map(Number);

  const maxLength = Math.max(parts1.length, parts2.length);

  for (let i = 0; i < maxLength; i++) {
    const num1 = parts1[i] || 0;
    const num2 = parts2[i] || 0;

    if (num1 > num2) return -1;
    if (num1 < num2) return 1;
  }

  return 0;
}

// ==================== 统计相关 ====================

/**
 * 计算存储空间占用百分比
 */
export function calculateStoragePercentage(
  used: number,
  total: number
): number {
  if (total === 0) return 0;
  return Math.min((used / total) * 100, 100);
}

/**
 * 获取存储警告级别
 */
export function getStorageWarningLevel(
  percentage: number
): 'safe' | 'warning' | 'danger' {
  if (percentage < 70) return 'safe';
  if (percentage < 90) return 'warning';
  return 'danger';
}
