/**
 * Card组件
 *
 * 通用卡片容器组件
 */

import React from 'react';

export interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  actions,
  footer,
  children,
  className = '',
  padding = 'md',
  hover = false,
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };

  const hoverClasses = hover ? 'hover:shadow-lg transition-shadow' : '';

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 shadow-sm ${hoverClasses} ${className}`}
    >
      {(title || subtitle || actions) && (
        <div className={`border-b border-gray-200 ${paddingClasses[padding]}`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
            {actions && <div className="ml-4">{actions}</div>}
          </div>
        </div>
      )}
      <div className={paddingClasses[padding]}>{children}</div>
      {footer && (
        <div className={`border-t border-gray-200 ${paddingClasses[padding]} bg-gray-50 rounded-b-lg`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
