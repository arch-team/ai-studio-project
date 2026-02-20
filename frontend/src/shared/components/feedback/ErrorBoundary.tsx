/**
 * 全局错误边界组件 - 捕获 React 组件树中的 JavaScript 错误。
 *
 * 显示友好的错误页面，防止整个应用崩溃。
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

import { Box, Button, Container, Header, SpaceBetween } from "@cloudscape-design/components";

interface ErrorBoundaryProps {
  /** 子组件 */
  children: ReactNode;
  /** 自定义 fallback UI */
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误到控制台 (生产环境应上报到错误监控服务)
    console.error("[ErrorBoundary]", error, errorInfo.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <Box padding="xxl">
        <Container
          header={<Header variant="h1">页面出现了问题</Header>}
        >
          <SpaceBetween size="l">
            <Box variant="p" color="text-body-secondary">
              应用遇到了意外错误。您可以尝试重试或刷新页面。
            </Box>
            {this.state.error && (
              <Box variant="code" fontSize="body-s" color="text-status-error">
                {this.state.error.message}
              </Box>
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
