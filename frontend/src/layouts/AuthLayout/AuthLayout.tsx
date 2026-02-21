/**
 * AuthLayout 组件
 *
 * 用于登录等非主布局页面的居中布局容器
 */

import { Box, SpaceBetween } from "@cloudscape-design/components";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <Box padding={{ top: "xxxl", horizontal: "s" }}>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div style={{ width: "100%", maxWidth: 480 }}>
          <SpaceBetween size="l">
            <Box textAlign="center">
              <Box variant="h1" fontSize="heading-xl">
                AI Training Platform
              </Box>
            </Box>
            {children}
          </SpaceBetween>
        </div>
      </div>
    </Box>
  );
}
