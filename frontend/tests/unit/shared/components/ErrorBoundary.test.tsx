/**
 * ErrorBoundary 组件测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorBoundary } from "@shared/components/feedback";

// 抛出错误的测试组件
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("测试错误");
  }
  return <div>正常渲染</div>;
}

describe("ErrorBoundary", () => {
  // 抑制 React 错误边界的 console.error 输出
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("应正常渲染子组件", () => {
    render(
      <ErrorBoundary>
        <div>子组件内容</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("子组件内容")).toBeInTheDocument();
  });

  it("应在捕获错误时显示默认错误 UI", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("页面出现了问题")).toBeInTheDocument();
    expect(screen.getByText("测试错误")).toBeInTheDocument();
    expect(screen.getByText("重试")).toBeInTheDocument();
    expect(screen.getByText("刷新页面")).toBeInTheDocument();
  });

  it("应支持自定义 fallback 节点", () => {
    render(
      <ErrorBoundary fallback={<div>自定义错误页面</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("自定义错误页面")).toBeInTheDocument();
    expect(screen.queryByText("页面出现了问题")).not.toBeInTheDocument();
  });

  it("应支持自定义 fallbackRender 函数", () => {
    render(
      <ErrorBoundary
        fallbackRender={({ error, resetError }) => (
          <div>
            <span>错误: {error.message}</span>
            <button onClick={resetError}>恢复</button>
          </div>
        )}
      >
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("错误: 测试错误")).toBeInTheDocument();
    expect(screen.getByText("恢复")).toBeInTheDocument();
  });

  it("应支持自定义标题", () => {
    render(
      <ErrorBoundary title="自定义标题">
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("自定义标题")).toBeInTheDocument();
  });

  it("应调用 onError 回调上报错误", () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ message: "测试错误" }),
      expect.objectContaining({ componentStack: expect.any(String) }),
    );
  });

  it("点击重试应重置错误状态", () => {
    // 使用一个可控制的组件
    let shouldThrow = true;

    function ConditionalError() {
      if (shouldThrow) {
        throw new Error("可恢复错误");
      }
      return <div>恢复成功</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalError />
      </ErrorBoundary>,
    );

    // 验证错误页面
    expect(screen.getByText("页面出现了问题")).toBeInTheDocument();

    // 修复错误
    shouldThrow = false;

    // 点击重试
    fireEvent.click(screen.getByText("重试"));

    // 重新渲染
    rerender(
      <ErrorBoundary>
        <ConditionalError />
      </ErrorBoundary>,
    );

    expect(screen.getByText("恢复成功")).toBeInTheDocument();
  });
});
