/**
 * Dataset Versions Page
 *
 * 数据集版本管理页面 - 显示版本历史、创建新版本
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Header,
  Modal,
  SpaceBetween,
  Spinner,
  Table,
} from '@cloudscape-design/components';
import { useMemo, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { PageLayout, InlineErrorState } from '@shared/components';
import { useDataset, useDatasetVersions, useCreateDatasetVersion } from '../api';
import type { DatasetVersion } from '../types';

/**
 * 格式化文件大小为可读字符串
 */
function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '-';
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
 * 格式化日期时间为中文本地化字符串
 */
function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 数据集版本管理页面
 */
export function DatasetVersionsPage() {
  const { id } = useParams<{ id: string }>();
  const datasetId = id ? parseInt(id, 10) : undefined;

  // 创建新版本弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 获取数据集详情
  const {
    data: dataset,
    isLoading: datasetLoading,
    error: datasetError,
    refetch: refetchDataset,
  } = useDataset(datasetId);

  // 获取版本列表
  const {
    data: versionsData,
    isLoading: versionsLoading,
    isError: versionsError,
    refetch,
  } = useDatasetVersions(datasetId);

  // 创建新版本 mutation
  const createVersionMutation = useCreateDatasetVersion();

  // 面包屑（数据集名加载后更新）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '数据集', href: '/datasets' },
      { text: dataset?.name ?? '数据集', href: `/datasets/${datasetId}` },
      { text: '版本历史', href: '#' },
    ],
    [dataset?.name, datasetId],
  );

  // 打开创建新版本弹窗
  const handleOpenCreateModal = useCallback(() => {
    setShowCreateModal(true);
  }, []);

  // 关闭创建新版本弹窗
  const handleCloseCreateModal = useCallback(() => {
    setShowCreateModal(false);
  }, []);

  // 执行创建新版本
  const handleCreateVersion = useCallback(async () => {
    if (!datasetId) return;
    await createVersionMutation.mutateAsync({ datasetId });
    setShowCreateModal(false);
    refetch();
  }, [datasetId, createVersionMutation, refetch]);

  // 表格列定义
  const columnDefinitions = [
    {
      id: 'version',
      header: '版本号',
      cell: (item: DatasetVersion) => item.version,
      sortingField: 'version',
    },
    {
      id: 'description',
      header: '描述',
      cell: (item: DatasetVersion) => item.description || '-',
    },
    {
      id: 'file_count',
      header: '文件数',
      cell: (item: DatasetVersion) =>
        item.file_count !== null ? item.file_count.toLocaleString() : '-',
    },
    {
      id: 'total_size_bytes',
      header: '大小',
      cell: (item: DatasetVersion) => formatFileSize(item.total_size_bytes),
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: DatasetVersion) => formatDateTime(item.created_at),
      sortingField: 'created_at',
    },
    {
      id: 'created_by_username',
      header: '创建者',
      cell: (item: DatasetVersion) => item.created_by_username || '-',
    },
  ];

  // 加载状态
  if (datasetLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态：保留 PageLayout 骨架（固定标题 + 面包屑返回出口），不裸 Container 塌缩
  // 区分"加载失败"（带重试）与"数据集不存在"（无重试，仅给返回出口）
  if (datasetError || !dataset) {
    return (
      <PageLayout title="数据集版本历史" breadcrumbs={breadcrumbs}>
        <InlineErrorState
          title={datasetError ? '加载失败' : '数据集不存在'}
          message={
            datasetError?.message ?? '未找到该数据集，它可能已被删除。'
          }
          onRetry={datasetError ? () => refetchDataset() : undefined}
        />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={`${dataset.name} - 版本历史`}
      description="数据集版本沿革，支持创建与回溯版本"
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button variant="primary" iconName="add-plus" onClick={handleOpenCreateModal}>
            创建新版本
          </Button>
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l">
      {/* 版本列表加载失败：显式报错，不静默降级为空表（F-024） */}
      {versionsError && (
        <InlineErrorState
          message="版本列表加载失败。"
          onRetry={() => refetch()}
        />
      )}

      {/* 版本列表 */}
      <Container
        header={
          <Header
            variant="h2"
            counter={`(${versionsData?.items?.length ?? 0})`}
          >
            版本列表
          </Header>
        }
      >
        <Table
          loading={versionsLoading}
          items={versionsData?.items ?? []}
          columnDefinitions={columnDefinitions}
          empty={
            // error 态抑制 empty：失败时由上方 InlineErrorState 统一报错，
            // 不再渲染"暂无版本记录"占位或"创建第一个版本" CTA，避免语义矛盾
            versionsError ? null : (
              <Box textAlign="center" padding="l">
                <SpaceBetween size="m">
                  <Box variant="p" color="text-body-secondary">
                    暂无版本记录
                  </Box>
                  <Button onClick={handleOpenCreateModal}>创建第一个版本</Button>
                </SpaceBetween>
              </Box>
            )
          }
          loadingText="加载版本列表中..."
          trackBy="id"
          variant="embedded"
        />
      </Container>

      {/* 创建新版本确认弹窗 */}
      <Modal
        visible={showCreateModal}
        onDismiss={handleCloseCreateModal}
        header="创建新版本"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={handleCloseCreateModal}>
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleCreateVersion}
                loading={createVersionMutation.isPending}
              >
                确认创建
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box>
            确定要为数据集 <b>{dataset.name}</b> 创建新版本吗？
          </Box>
          <Alert type="info">
            新版本将基于当前数据集的最新状态创建。
          </Alert>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
    </PageLayout>
  );
}

export default DatasetVersionsPage;
