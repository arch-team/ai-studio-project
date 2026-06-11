/**
 * ErrorPage Component
 *
 * 全屏错误状态页（404 / 403 等），居中布局:
 * - 超大错误码（display-l）建立视觉锚点
 * - 标题 + 解释文案 + 行动按钮（返回首页 / 返回上一页）
 *
 * 让「迷路」的用户一眼明白发生了什么、下一步去哪里。
 */

import {
  Box,
  Button,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';

export interface ErrorPageProps {
  /** 大号错误码，如 "404" */
  code: string;
  /** 错误标题 */
  title: string;
  /** 解释性描述 */
  description: string;
  /** 主操作跳转目标，默认首页 */
  homeHref?: string;
}

/**
 * ErrorPage 组件
 *
 * @example
 * ```tsx
 * <ErrorPage
 *   code="404"
 *   title="页面未找到"
 *   description="您访问的页面不存在，请检查 URL 是否正确。"
 * />
 * ```
 */
export function ErrorPage({ code, title, description, homeHref = '/' }: ErrorPageProps) {
  const navigate = useNavigate();

  return (
    <Box padding={{ vertical: 'xxxl', horizontal: 'l' }} textAlign="center">
      <SpaceBetween size="l" alignItems="center">
        <Box fontSize="display-l" fontWeight="bold" color="text-status-inactive">
          {code}
        </Box>
        <SpaceBetween size="xs" alignItems="center">
          <Box variant="h1">{title}</Box>
          <Box variant="p" color="text-body-secondary">
            {description}
          </Box>
        </SpaceBetween>
        <SpaceBetween size="xs" direction="horizontal">
          <Button onClick={() => navigate(-1)}>返回上一页</Button>
          <Button variant="primary" onClick={() => navigate(homeHref)}>
            返回首页
          </Button>
        </SpaceBetween>
      </SpaceBetween>
    </Box>
  );
}
