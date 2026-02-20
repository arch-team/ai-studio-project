/**
 * 数据集文件上传组件
 *
 * 提供拖拽上传区域、文件选择、上传进度展示、取消/重试功能。
 * 使用 Cloudscape Design System 组件构建，禁止自定义 CSS。
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import Box from '@cloudscape-design/components/box';
import Button from '@cloudscape-design/components/button';
import ProgressBar from '@cloudscape-design/components/progress-bar';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Icon from '@cloudscape-design/components/icon';

import { useDatasetUpload } from '../hooks/useDatasetUpload';
import type { UploadProgress } from '../types';

// === 类型定义 ===

/** 组件 Props */
interface DatasetUploaderProps {
  /** 上传完成回调 */
  onUploadComplete?: (fileInfo: { name: string; size: number }) => void;
  /** 是否禁用上传 */
  disabled?: boolean;
}

/** 文件选择信息 */
interface SelectedFile {
  file: File;
  name: string;
  size: number;
}

// === 工具函数 ===

/**
 * 格式化文件大小为可读字符串
 */
function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(unitIndex > 0 ? 2 : 0)} ${units[unitIndex]}`;
}

/**
 * 根据上传状态返回 StatusIndicator 类型和文案
 */
function getStatusConfig(status: UploadProgress['status']): {
  type: 'pending' | 'in-progress' | 'loading' | 'success' | 'error' | 'stopped';
  label: string;
} {
  switch (status) {
    case 'idle':
      return { type: 'pending', label: '等待上传' };
    case 'uploading':
      return { type: 'in-progress', label: '正在上传' };
    case 'completing':
      return { type: 'loading', label: '正在合并分片' };
    case 'completed':
      return { type: 'success', label: '上传完成' };
    case 'error':
      return { type: 'error', label: '上传失败' };
    case 'cancelled':
      return { type: 'stopped', label: '已取消' };
  }
}

// === 子组件 ===

/**
 * 拖拽上传区域
 *
 * 支持点击选择文件和拖拽文件，
 * 拖拽悬停时通过 Container variant 变化提供视觉反馈。
 */
function DropZone({
  onFileSelect,
  disabled = false,
}: {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (!disabled) {
        setIsDragOver(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setIsDragOver(false);

      if (disabled) return;

      const droppedFile = event.dataTransfer.files[0];
      if (droppedFile) {
        onFileSelect(droppedFile);
      }
    },
    [disabled, onFileSelect]
  );

  const handleButtonClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        onFileSelect(file);
      }
      // 清空 input 值，以支持重复选择同一文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    [onFileSelect]
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if ((event.key === 'Enter' || event.key === ' ') && !disabled) {
        event.preventDefault();
        handleButtonClick();
      }
    },
    [disabled, handleButtonClick]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="拖拽文件到此处上传，或点击选择文件"
      aria-disabled={disabled}
      onKeyDown={handleKeyDown}
    >
      <Container variant={isDragOver ? 'stacked' : 'default'}>
        <Box textAlign="center" padding={{ vertical: 'xl' }}>
          <SpaceBetween size="s" direction="vertical" alignItems="center">
            <Box variant="p" color="text-body-secondary">
              <Icon name="upload" size="big" />
            </Box>
            <Box variant="p" color="text-body-secondary">
              {isDragOver ? '释放文件以开始上传' : '将文件拖拽到此处'}
            </Box>
            <Box variant="p" color="text-body-secondary">
              或
            </Box>
            <Button
              disabled={disabled}
              onClick={handleButtonClick}
              iconName="upload"
            >
              选择文件
            </Button>
          </SpaceBetween>
        </Box>
      </Container>
      {/* 隐藏的原生文件选择 input（仅用于触发系统文件对话框） */}
      <input
        ref={fileInputRef}
        type="file"
        hidden
        onChange={handleFileChange}
        aria-hidden="true"
        tabIndex={-1}
      />
    </div>
  );
}

/**
 * 上传进度展示区域
 *
 * 显示文件信息、进度条、状态指示和操作按钮（取消/重试/重新选择）
 */
function UploadProgressDisplay({
  selectedFile,
  progress,
  onCancel,
  onRetry,
  onReset,
}: {
  selectedFile: SelectedFile;
  progress: UploadProgress;
  onCancel: () => void;
  onRetry: () => void;
  onReset: () => void;
}) {
  const statusConfig = getStatusConfig(progress.status);
  const isUploading =
    progress.status === 'uploading' || progress.status === 'completing';
  const isTerminal =
    progress.status === 'completed' ||
    progress.status === 'error' ||
    progress.status === 'cancelled';

  return (
    <Container
      header={
        <Header
          variant="h3"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              {isUploading && (
                <Button onClick={onCancel} variant="link">
                  取消
                </Button>
              )}
              {progress.status === 'error' && (
                <Button onClick={onRetry} iconName="refresh">
                  重试
                </Button>
              )}
              {isTerminal && (
                <Button onClick={onReset} variant="link">
                  重新选择
                </Button>
              )}
            </SpaceBetween>
          }
        >
          文件上传
        </Header>
      }
    >
      <SpaceBetween size="m">
        {/* 文件信息 */}
        <SpaceBetween size="xxs">
          <Box variant="p">
            <Box variant="span" fontWeight="bold">
              文件名:
            </Box>{' '}
            {selectedFile.name}
          </Box>
          <Box variant="p">
            <Box variant="span" fontWeight="bold">
              文件大小:
            </Box>{' '}
            {formatFileSize(selectedFile.size)}
          </Box>
        </SpaceBetween>

        {/* 进度条 */}
        <ProgressBar
          value={progress.percentage}
          label="上传进度"
          description={
            isUploading
              ? `${formatFileSize(progress.loaded)} / ${formatFileSize(progress.total)}`
              : undefined
          }
          status={
            progress.status === 'error'
              ? 'error'
              : progress.status === 'completed'
                ? 'success'
                : 'in-progress'
          }
          resultText={
            progress.status === 'completed'
              ? '上传完成'
              : progress.status === 'error'
                ? '上传失败'
                : undefined
          }
        />

        {/* 状态指示 */}
        <StatusIndicator type={statusConfig.type}>
          {statusConfig.label}
          {progress.error ? `: ${progress.error}` : ''}
        </StatusIndicator>
      </SpaceBetween>
    </Container>
  );
}

// === 主组件 ===

/**
 * 数据集文件上传组件
 *
 * 包含两个状态视图:
 * 1. 未选择文件时: 显示拖拽上传区域（DropZone）
 * 2. 已选择文件时: 显示上传进度（UploadProgressDisplay）
 *
 * 使用 useDatasetUpload hook 管理分片上传逻辑。
 */
export function DatasetUploader({
  onUploadComplete,
  disabled = false,
}: DatasetUploaderProps) {
  const { progress, upload, cancel, reset } = useDatasetUpload();
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);

  // 使用 ref 存储回调，避免回调变化触发不必要的 effect
  const onUploadCompleteRef = useRef(onUploadComplete);
  onUploadCompleteRef.current = onUploadComplete;

  // 监听上传完成状态，触发回调
  useEffect(() => {
    if (progress.status === 'completed' && selectedFile) {
      onUploadCompleteRef.current?.({
        name: selectedFile.name,
        size: selectedFile.size,
      });
    }
  }, [progress.status, selectedFile]);

  /** 处理文件选择（选择后自动开始上传） */
  const handleFileSelect = useCallback(
    (file: File) => {
      const fileInfo: SelectedFile = {
        file,
        name: file.name,
        size: file.size,
      };
      setSelectedFile(fileInfo);
      // 异步上传，不阻塞 UI
      void upload(file);
    },
    [upload]
  );

  /** 处理取消上传 */
  const handleCancel = useCallback(() => {
    cancel();
  }, [cancel]);

  /** 处理重试（重新上传当前选中的文件） */
  const handleRetry = useCallback(() => {
    if (selectedFile) {
      reset();
      void upload(selectedFile.file);
    }
  }, [selectedFile, reset, upload]);

  /** 处理重新选择文件（重置所有状态） */
  const handleReset = useCallback(() => {
    reset();
    setSelectedFile(null);
  }, [reset]);

  // 未选择文件时显示拖拽上传区域
  if (!selectedFile) {
    return <DropZone onFileSelect={handleFileSelect} disabled={disabled} />;
  }

  // 已选择文件时显示上传进度
  return (
    <UploadProgressDisplay
      selectedFile={selectedFile}
      progress={progress}
      onCancel={handleCancel}
      onRetry={handleRetry}
      onReset={handleReset}
    />
  );
}

export default DatasetUploader;
