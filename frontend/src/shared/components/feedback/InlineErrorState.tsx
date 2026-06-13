/**
 * InlineErrorState 组件
 *
 * 统一的页面内联错误状态——在 PageLayout 骨架内部渲染，
 * 保留页面 Header/面包屑/操作区，提供 Cloudscape Alert + 重试入口。
 *
 * 用于 query 错误场景,替代各页面 early-return 的裸 Container 错误块。
 * 错误态绝不静默降级为空数据；失败时应抑制 empty 态内容。
 */

import { Alert, Button } from '@cloudscape-design/components';

export interface InlineErrorStateProps {
  /** 错误描述（通常为 error.message） */
  message?: string;
  /** 错误标题,默认"加载失败" */
  title?: string;
  /** 重试回调；提供时渲染"重试"按钮（通常传 query 的 refetch） */
  onRetry?: () => void;
}

export function InlineErrorState({
  message,
  title = '加载失败',
  onRetry,
}: InlineErrorStateProps) {
  return (
    <Alert
      type="error"
      header={title}
      action={onRetry ? <Button onClick={onRetry}>重试</Button> : undefined}
    >
      {message ?? '发生未知错误,请稍后重试。'}
    </Alert>
  );
}
