/**
 * IDE Frame Component
 *
 * IDE 嵌入组件 - 通过 iframe 嵌入 SageMaker Studio URL
 */

import {
  Box,
  Button,
  SpaceBetween,
  Spinner,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';

interface IDEFrameProps {
  /** SageMaker Studio 或 JupyterLab URL */
  url: string;
  /** iframe 标题 (无障碍) */
  title?: string;
  /** 是否默认全屏模式 */
  fullscreen?: boolean;
}

/**
 * 验证 URL 协议是否安全
 */
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

/**
 * IDE 嵌入组件
 */
export function IDEFrame({
  url,
  title = '开发环境',
  fullscreen: initialFullscreen = false,
}: IDEFrameProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(initialFullscreen);

  const handleLoad = useCallback(() => {
    setIsLoading(false);
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    setIsFullscreen((prev) => !prev);
  }, []);

  // URL 无效时显示错误
  if (!url || !isValidUrl(url)) {
    return (
      <Box textAlign="center" padding="xl">
        <StatusIndicator type="error">
          无效的 IDE 地址，请检查开发空间状态
        </StatusIndicator>
      </Box>
    );
  }

  return (
    <SpaceBetween size="s">
      {/* 工具栏 */}
      <Box float="right">
        <SpaceBetween direction="horizontal" size="xs">
          <Button
            iconName={isFullscreen ? 'shrink' : 'expand'}
            onClick={handleToggleFullscreen}
            ariaLabel={isFullscreen ? '退出全屏' : '全屏模式'}
          >
            {isFullscreen ? '退出全屏' : '全屏'}
          </Button>
          <Button
            iconName="external"
            href={url}
            target="_blank"
            ariaLabel="在新窗口打开"
          >
            新窗口打开
          </Button>
        </SpaceBetween>
      </Box>

      {/* 加载指示器 */}
      {isLoading && (
        <Box textAlign="center" padding="l">
          <Spinner size="large" />
          <Box margin={{ top: 's' }} color="text-body-secondary">
            正在加载开发环境...
          </Box>
        </Box>
      )}

      {/* iframe */}
      <Box>
        <iframe
          src={url}
          title={title}
          onLoad={handleLoad}
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"
          style={{
            width: '100%',
            height: isFullscreen ? 'calc(100vh - 120px)' : '600px',
            border: 'none',
            display: isLoading ? 'none' : 'block',
          }}
        />
      </Box>
    </SpaceBetween>
  );
}
