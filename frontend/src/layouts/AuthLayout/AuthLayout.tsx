/**
 * AuthLayout 组件
 *
 * 登录等非主布局页面的品牌化全屏容器:
 * - 深空渐变背景（复用品牌 heroHeaderBackground，登录页固定深色氛围）
 * - 居中品牌区（Logo + 平台名 + 价值主张）+ 表单卡片
 *
 * 说明: 全屏渐变背景与深色背景上的文字反色无对应 Cloudscape 组件，
 * 此处使用最小内联样式实现（仅限本品牌容器），表单等一切控件仍为 Cloudscape。
 */

import { Box, SpaceBetween } from "@cloudscape-design/components";
import {
  BRAND_LOGO_ALT,
  BRAND_LOGO_SRC,
  heroHeaderBackground,
} from "@shared/theme";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: heroHeaderBackground("dark"),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 16px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 440 }}>
        <SpaceBetween size="l">
          <Box textAlign="center">
            <SpaceBetween size="s">
              <img
                src={BRAND_LOGO_SRC}
                alt={BRAND_LOGO_ALT}
                width={56}
                height={56}
              />
              <Box variant="h1" fontSize="heading-xl">
                <span style={{ color: "#FFFFFF" }}>AI Training Platform</span>
              </Box>
              <span style={{ color: "rgba(255, 255, 255, 0.78)" }}>
                企业级分布式 AI 训练平台 · SageMaker HyperPod 驱动
              </span>
            </SpaceBetween>
          </Box>

          {children}

          <Box textAlign="center">
            <span style={{ color: "rgba(255, 255, 255, 0.55)", fontSize: 12 }}>
              基于 PyTorch DDP / FSDP / DeepSpeed 的大规模训练调度
            </span>
          </Box>
        </SpaceBetween>
      </div>
    </div>
  );
}
