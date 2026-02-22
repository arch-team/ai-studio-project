/**
 * Dataset Detail Page
 *
 * 数据集详情页面 - 展示数据集基本信息和版本列表
 */

import {
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  KeyValuePairs,
  Pagination,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import { useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDataset, useDatasetVersions } from '../api';
import { formatDateTime } from '@shared/utils';
import {
  DATASET_STATUS_LABELS,
  DATASET_TYPE_LABELS,
  STORAGE_TYPE_LABELS,
  VISIBILITY_LABELS,
} from '../types';
import type { DatasetStatus, DatasetVersion } from '../types';

// 状态 → StatusIndicator type 映射
const STATUS_INDICATOR_TYPE: Record<DatasetStatus, 'success' | 'info' | 'stopped' | 'error'> = {
  available: 'success',
  preparing: 'info',
  archived: 'stopped',
  error: 'error',
};

/**
 * 格式化文件大小
 */
function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === 0) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * 数据集详情页面
 */
export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const datasetId = id ? Number(id) : undefined;

  const { data: dataset, isLoading, error } = useDataset(datasetId);
  const { data: versions, isLoading: loadingVersions } = useDatasetVersions(datasetId);

  // 版本列表分页
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const handlePageChange = useCallback(
    ({ detail }: { detail: { currentPageIndex: number } }) => {
      setCurrentPage(detail.currentPageIndex);
    },
    [],
  );

  // 版本表格列定义
  const versionColumnDefinitions = [
    {
      id: 'version',
      header: '版本号',
      cell: (item: DatasetVersion) => item.version,
      width: 120,
    },
    {
      id: 'description',
      header: '描述',
      cell: (item: DatasetVersion) => item.description || '-',
    },
    {
      id: 'storage_uri',
      header: '存储路径',
      cell: (item: DatasetVersion) => item.storage_uri,
    },
    {
      id: 'size',
      header: '大小',
      cell: (item: DatasetVersion) => formatBytes(item.total_size_bytes),
      width: 120,
    },
    {
      id: 'file_count',
      header: '文件数',
      cell: (item: DatasetVersion) => item.file_count ?? '-',
      width: 100,
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: DatasetVersion) => formatDateTime(item.created_at),
      width: 180,
    },
  ];

  // 加载状态
  if (isLoading) {
    return (
      <Container>
        <Box textAlign="center" padding="xl">
          <StatusIndicator type="loading">加载中...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  // 错误状态
  if (error) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          加载失败: {error.message}
        </Box>
      </Container>
    );
  }

  // 数据集不存在
  if (!dataset) {
    return (
      <Container>
        <Box textAlign="center" padding="xl">
          数据集不存在
        </Box>
      </Container>
    );
  }

  // 计算版本分页
  const allVersionItems = versions?.items ?? [];
  const paginatedVersions = allVersionItems.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );
  const totalPages = Math.max(1, Math.ceil(allVersionItems.length / pageSize));

  return (
    <SpaceBetween size="l">
      {/* 页面标题 */}
      <Header
        variant="h1"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={() => navigate('/datasets')}>返回列表</Button>
            <Button onClick={() => navigate(`/datasets/${id}/versions`)}>
              版本管理
            </Button>
          </SpaceBetween>
        }
      >
        {dataset.name}
      </Header>

      {/* 基本信息 */}
      <Container header={<Header variant="h2">基本信息</Header>}>
        <ColumnLayout columns={2} variant="text-grid">
          <KeyValuePairs
            items={[
              { label: '名称', value: dataset.name },
              { label: '描述', value: dataset.description || '-' },
              {
                label: '状态',
                value: (
                  <StatusIndicator type={STATUS_INDICATOR_TYPE[dataset.status]}>
                    {DATASET_STATUS_LABELS[dataset.status]}
                  </StatusIndicator>
                ),
              },
              { label: '版本', value: dataset.version },
            ]}
          />
          <KeyValuePairs
            items={[
              { label: '数据类型', value: DATASET_TYPE_LABELS[dataset.dataset_type] },
              { label: '存储类型', value: STORAGE_TYPE_LABELS[dataset.storage_type] },
              { label: '可见性', value: VISIBILITY_LABELS[dataset.visibility] },
              { label: '存储路径', value: dataset.storage_uri },
            ]}
          />
        </ColumnLayout>
      </Container>

      {/* 统计信息 */}
      <Container header={<Header variant="h2">统计信息</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <SpaceBetween size="xxs">
            <Box variant="awsui-key-label">文件大小</Box>
            <Box variant="h3">{formatBytes(dataset.total_size_bytes)}</Box>
          </SpaceBetween>
          <SpaceBetween size="xxs">
            <Box variant="awsui-key-label">文件数量</Box>
            <Box variant="h3">{dataset.file_count ?? '-'}</Box>
          </SpaceBetween>
          <SpaceBetween size="xxs">
            <Box variant="awsui-key-label">关联训练任务</Box>
            <Box variant="h3">{dataset.training_jobs_count}</Box>
          </SpaceBetween>
          <SpaceBetween size="xxs">
            <Box variant="awsui-key-label">创建时间</Box>
            <Box>{formatDateTime(dataset.created_at)}</Box>
          </SpaceBetween>
        </ColumnLayout>
      </Container>

      {/* 版本列表 */}
      <Table
        columnDefinitions={versionColumnDefinitions}
        items={paginatedVersions}
        loading={loadingVersions}
        loadingText="加载中..."
        variant="container"
        header={
          <Header
            variant="h2"
            counter={`(${allVersionItems.length})`}
          >
            版本历史
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无版本记录</b>
              <Box color="text-body-secondary">数据集尚未创建任何版本</Box>
            </SpaceBetween>
          </Box>
        }
        pagination={
          totalPages > 1 ? (
            <Pagination
              currentPageIndex={currentPage}
              pagesCount={totalPages}
              onChange={handlePageChange}
            />
          ) : undefined
        }
      />
    </SpaceBetween>
  );
}

export default DatasetDetailPage;
