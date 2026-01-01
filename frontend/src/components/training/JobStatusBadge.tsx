/**
 * 训练任务状态徽章组件
 *
 * 展示训练任务的状态,使用不同颜色和图标表示不同状态
 */

import React from 'react';

export type JobStatus =
  | 'PENDING'
  | 'QUEUED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'TIMEOUT';

interface JobStatusBadgeProps {
  status: JobStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

// 状态配置:颜色、标签和图标
const STATUS_CONFIG: Record<
  JobStatus,
  {
    color: string;
    bgColor: string;
    label: string;
    icon: string;
  }
> = {
  PENDING: {
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    label: '等待中',
    icon: '⏳',
  },
  QUEUED: {
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    label: '已排队',
    icon: '📋',
  },
  RUNNING: {
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    label: '运行中',
    icon: '▶️',
  },
  COMPLETED: {
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-100',
    label: '已完成',
    icon: '✅',
  },
  FAILED: {
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    label: '失败',
    icon: '❌',
  },
  CANCELLED: {
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    label: '已取消',
    icon: '🚫',
  },
  TIMEOUT: {
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    label: '超时',
    icon: '⏰',
  },
};

// 尺寸配置
const SIZE_CONFIG = {
  sm: {
    padding: 'px-2 py-0.5',
    text: 'text-xs',
    icon: 'text-xs',
  },
  md: {
    padding: 'px-3 py-1',
    text: 'text-sm',
    icon: 'text-sm',
  },
  lg: {
    padding: 'px-4 py-1.5',
    text: 'text-base',
    icon: 'text-base',
  },
};

export const JobStatusBadge: React.FC<JobStatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const config = STATUS_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];

  if (!config) {
    console.warn(`Unknown status: ${status}`);
    return null;
  }

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${sizeConfig.padding}
        ${sizeConfig.text}
        ${config.color}
        ${config.bgColor}
      `}
    >
      {showIcon && (
        <span className={`mr-1 ${sizeConfig.icon}`}>{config.icon}</span>
      )}
      {config.label}
    </span>
  );
};

/**
 * 判断状态是否为活跃状态(仍在进行中)
 */
export const isActiveStatus = (status: JobStatus): boolean => {
  return ['PENDING', 'QUEUED', 'RUNNING'].includes(status);
};

/**
 * 判断状态是否为终止状态(已结束)
 */
export const isTerminalStatus = (status: JobStatus): boolean => {
  return ['COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT'].includes(status);
};

/**
 * 判断状态是否为成功状态
 */
export const isSuccessStatus = (status: JobStatus): boolean => {
  return status === 'COMPLETED';
};

/**
 * 判断状态是否为失败状态
 */
export const isFailureStatus = (status: JobStatus): boolean => {
  return ['FAILED', 'TIMEOUT'].includes(status);
};

export default JobStatusBadge;
