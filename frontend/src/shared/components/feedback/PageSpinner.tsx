/**
 * 页面级加载指示器
 *
 * Task: T103 - 前端性能优化
 * 用于 React.lazy() + Suspense 的 fallback 组件。
 */

import { Box, Spinner } from "@cloudscape-design/components";

/**
 * 全屏居中加载指示器
 *
 * 作为路由级懒加载的 Suspense fallback 使用。
 */
export function PageSpinner() {
  return (
    <Box padding="xxl" textAlign="center">
      <Box margin={{ vertical: "xxxl" }}>
        <Spinner size="large" />
      </Box>
    </Box>
  );
}
