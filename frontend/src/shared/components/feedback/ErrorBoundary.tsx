/**
 * 全局错误边界组件 - 捕获 React 组件树中的 JavaScript 错误。
 *
 * Task: T099 - 增强错误边界
 * 功能:
 * - 显示友好的错误页面，防止整个应用崩溃
 * - 支持自定义 fallback UI
 * - 支持错误上报回调
 * - 支持重试和刷新机制
 * - 开发环境显示错误详情
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

import {
  Alert,
  Box,
  Button,
  Container,
  ExpandableSection,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";

// === 类型定义 ===

/**
 * 错误上报函数类型
 */
export type ErrorReporter = (error: Error, errorInfo: ErrorInfo) => void;

interface ErrorBoundaryProps {
  /** 子组件 */
  children: ReactNode;
  /** 自定义 fallback UI */
  fallback?: ReactNode;
  /** 自定义 fallback 渲染函数 (可访问错误信息) */
  fallbackRender?: (props: {
    error: Error;
    resetError: () => void;
  }) => ReactNode;
  /** 错误上报回调 */
  onError?: ErrorReporter;
  /** 是否显示错误详情 (默认开发环境显示) */
  showDetails?: boolean;
  /** 错误级别标题 */
  title?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

// === 组件实现 ===

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 保存错误信息
    this.setState({ errorInfo });

    // 记录错误到控制台
    console.error("[ErrorBoundary] 捕获到错误:", error);
    console.error("[ErrorBoundary] 组件栈:", errorInfo.componentStack);

    // 调用外部错误上报
    if (this.props.onError) {
      try {
        this.props.onError(error, errorInfo);
      } catch (reportError) {
        console.error("[ErrorBoundary] 错误上报失败:", reportError);
      }
    }
  }

  /**
   * 重置错误状态，尝试重新渲染子组件
   */
  private handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  /**
   * 刷新整个页面
   */
  private handleReload = (): void => {
    window.location.reload();
  };

  /**
   * 是否显示错误详情
   */
  private shouldShowDetails(): boolean {
    if (this.props.showDetails !== undefined) {
      return this.props.showDetails;
    }
    // 默认仅开发环境显示
    return import.meta.env.DEV;
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    // 自定义 fallback 渲染函数
    if (this.props.fallbackRender && this.state.error) {
      return this.props.fallbackRender({
        error: this.state.error,
        resetError: this.handleReset,
      });
    }

    // 自定义 fallback 节点
    if (this.props.fallback) {
      return this.props.fallback;
    }

    // 默认错误 UI
    const title = this.props.title || "页面出现了问题";

    return (
      <Box padding="xxl">
        <Container header={<Header variant="h1">{title}</Header>}>
          <SpaceBetween size="l">
            <Alert type="error">
              应用遇到了意外错误。您可以尝试重试或刷新页面。
            </Alert>

            {this.state.error && (
              <Box variant="code" fontSize="body-s" color="text-status-error">
                {this.state.error.message}
              </Box>
            )}

            {/* 开发环境显示错误详情 */}
            {this.shouldShowDetails() && this.state.error && (
              <ExpandableSection headerText="错误详情">
                <SpaceBetween size="s">
                  <Box variant="code" fontSize="body-s">
                    {this.state.error.stack}
                  </Box>
                  {this.state.errorInfo?.componentStack && (
                    <Box variant="code" fontSize="body-s">
                      {this.state.errorInfo.componentStack}
                    </Box>
                  )}
                </SpaceBetween>
              </ExpandableSection>
            )}

            <SpaceBetween direction="horizontal" size="s">
              <Button onClick={this.handleReset}>重试</Button>
              <Button variant="primary" onClick={this.handleReload}>
                刷新页面
              </Button>
            </SpaceBetween>
          </SpaceBetween>
        </Container>
      </Box>
    );
  }
}
