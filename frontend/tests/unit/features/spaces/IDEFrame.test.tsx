/**
 * IDEFrame 单元测试
 *
 * 测试 IDE 嵌入组件的渲染、URL 验证和交互
 */

import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { IDEFrame } from "@features/spaces/components";

describe("IDEFrame", () => {
  const validUrl = "https://sagemaker.example.com/jupyter";

  describe("基本渲染", () => {
    it("应该渲染有效 URL 的 iframe", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const iframe = document.querySelector("iframe");
      expect(iframe).toBeInTheDocument();
      expect(iframe?.src).toBe(validUrl);
    });

    it("应该显示默认标题", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const iframe = document.querySelector("iframe");
      expect(iframe?.title).toBe("开发环境");
    });

    it("应该使用自定义标题", () => {
      renderWithProviders(<IDEFrame url={validUrl} title="我的 IDE" />);
      const iframe = document.querySelector("iframe");
      expect(iframe?.title).toBe("我的 IDE");
    });

    it("应该显示加载指示器", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      expect(screen.getByText("正在加载开发环境...")).toBeInTheDocument();
    });

    it("iframe 应该有 sandbox 属性", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const iframe = document.querySelector("iframe");
      const sandboxAttr = iframe?.getAttribute("sandbox") || "";
      expect(sandboxAttr).toContain("allow-scripts");
      expect(sandboxAttr).toContain("allow-same-origin");
    });
  });

  describe("URL 验证", () => {
    it("空 URL 应该显示错误信息", () => {
      renderWithProviders(<IDEFrame url="" />);
      expect(screen.getByText(/无效的 IDE 地址/)).toBeInTheDocument();
      expect(document.querySelector("iframe")).not.toBeInTheDocument();
    });

    it("无效 URL 应该显示错误信息", () => {
      renderWithProviders(<IDEFrame url="not-a-url" />);
      expect(screen.getByText(/无效的 IDE 地址/)).toBeInTheDocument();
    });

    it("javascript: 协议应该被拒绝", () => {
      renderWithProviders(<IDEFrame url="javascript:alert(1)" />);
      expect(screen.getByText(/无效的 IDE 地址/)).toBeInTheDocument();
    });

    it("http: 协议应该被接受", () => {
      renderWithProviders(<IDEFrame url="http://localhost:8888/lab" />);
      const iframe = document.querySelector("iframe");
      expect(iframe).toBeInTheDocument();
    });

    it("https: 协议应该被接受", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const iframe = document.querySelector("iframe");
      expect(iframe).toBeInTheDocument();
    });
  });

  describe("工具栏交互", () => {
    it("应该渲染全屏切换按钮", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      expect(screen.getByText("全屏")).toBeInTheDocument();
    });

    it("应该渲染新窗口打开按钮", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      expect(screen.getByText("新窗口打开")).toBeInTheDocument();
    });

    it("点击全屏按钮应该切换全屏状态", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const fullscreenButton = screen.getByText("全屏");
      fireEvent.click(fullscreenButton);
      expect(screen.getByText("退出全屏")).toBeInTheDocument();
    });

    it("默认全屏模式应该显示退出全屏按钮", () => {
      renderWithProviders(<IDEFrame url={validUrl} fullscreen={true} />);
      expect(screen.getByText("退出全屏")).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("加载完成后应该隐藏加载指示器", () => {
      renderWithProviders(<IDEFrame url={validUrl} />);
      const iframe = document.querySelector("iframe");
      expect(iframe).toBeInTheDocument();

      // 模拟 iframe 加载完成
      fireEvent.load(iframe!);
      expect(screen.queryByText("正在加载开发环境...")).not.toBeInTheDocument();
    });
  });
});
