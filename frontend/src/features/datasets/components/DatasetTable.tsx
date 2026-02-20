/**
 * Dataset Table Component
 *
 * 可复用的数据集表格组件
 */

import {
  Box,
  Link,
  Pagination,
  SpaceBetween,
  Table,
  Header,
} from '@cloudscape-design/components';
import type { DatasetSummary } from '../types';
import {
  DATASET_TYPE_LABELS,
  STORAGE_TYPE_LABELS,
  VISIBILITY_LABELS,
} from '../types';
import { DatasetStatusBadge } from './DatasetStatusBadge';

interface DatasetTableProps {
  items: DatasetSummary[];
  loading?: boolean;
  totalCount?: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onDatasetClick?: (datasetId: number) => void;
}

/**
 * 格式化文件大小（字节 → KB/MB/GB/TB 可读格式）
 */
function formatSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '-';
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const base = 1024;
  // 计算合适的单位级别
  const unitIndex = Math.min(
    Math.floor(Math.log(bytes) / Math.log(base)),
    units.length - 1
  );
  const value = bytes / Math.pow(base, unitIndex);

  // B 和 KB 不显示小数，MB/GB/TB 保留两位小数
  const formatted = unitIndex <= 1 ? Math.round(value).toString() : value.toFixed(2);
  return `${formatted} ${units[unitIndex]}`;
}

/**
 * 格式化日期时间
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
 * 数据集表格组件
 */
export function DatasetTable({
  items,
  loading = false,
  totalCount,
  currentPage,
  totalPages,
  onPageChange,
  onDatasetClick,
}: DatasetTableProps) {
  const columnDefinitions = [
    {
      id: 'name',
      header: '数据集名称',
      cell: (item: DatasetSummary) => (
        <Link onFollow={() => onDatasetClick?.(item.id)}>{item.name}</Link>
      ),
      sortingField: 'name',
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: DatasetSummary) => <DatasetStatusBadge status={item.status} />,
      sortingField: 'status',
    },
    {
      id: 'dataset_type',
      header: '数据类型',
      cell: (item: DatasetSummary) => DATASET_TYPE_LABELS[item.dataset_type],
      sortingField: 'dataset_type',
    },
    {
      id: 'storage_type',
      header: '存储类型',
      cell: (item: DatasetSummary) => STORAGE_TYPE_LABELS[item.storage_type],
      sortingField: 'storage_type',
    },
    {
      id: 'total_size_bytes',
      header: '大小',
      cell: (item: DatasetSummary) => formatSize(item.total_size_bytes),
      sortingField: 'total_size_bytes',
    },
    {
      id: 'file_count',
      header: '文件数',
      cell: (item: DatasetSummary) =>
        item.file_count !== null && item.file_count !== undefined
          ? item.file_count.toLocaleString('zh-CN')
          : '-',
    },
    {
      id: 'visibility',
      header: '可见性',
      cell: (item: DatasetSummary) => VISIBILITY_LABELS[item.visibility],
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: DatasetSummary) => formatDateTime(item.created_at),
      sortingField: 'created_at',
    },
  ];

  return (
    <Table
      columnDefinitions={columnDefinitions}
      items={items}
      loading={loading}
      loadingText="加载中..."
      sortingDisabled
      variant="container"
      header={
        <Header variant="h2" counter={totalCount ? `(${totalCount})` : undefined}>
          数据集
        </Header>
      }
      empty={
        <Box textAlign="center" color="inherit" padding="xl">
          <SpaceBetween size="m">
            <b>暂无数据集</b>
            <Box color="text-body-secondary">尚未创建任何数据集</Box>
          </SpaceBetween>
        </Box>
      }
      pagination={
        totalPages > 1 ? (
          <Pagination
            currentPageIndex={currentPage}
            pagesCount={totalPages}
            onChange={({ detail }) => onPageChange(detail.currentPageIndex)}
          />
        ) : undefined
      }
    />
  );
}

export default DatasetTable;
