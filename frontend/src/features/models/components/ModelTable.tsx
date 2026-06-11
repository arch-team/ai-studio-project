/**
 * Model Table Component
 *
 * 可复用的模型表格组件
 */

import {
  Box,
  Link,
  Pagination,
  SpaceBetween,
  Table,
  Header,
} from '@cloudscape-design/components';
import type { ModelSummary } from '../types';
import { MODEL_FRAMEWORK_LABELS } from '../types';
import { ModelStatusBadge } from './ModelStatusBadge';

interface ModelTableProps {
  items: ModelSummary[];
  loading?: boolean;
  totalCount?: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onModelClick?: (modelId: number) => void;
  selectable?: boolean;
  selectedItems?: ModelSummary[];
  onSelectionChange?: (items: ModelSummary[]) => void;
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
 * 模型表格组件
 */
export function ModelTable({
  items,
  loading = false,
  totalCount,
  currentPage,
  totalPages,
  onPageChange,
  onModelClick,
  selectable = false,
  selectedItems = [],
  onSelectionChange,
}: ModelTableProps) {
  const columnDefinitions = [
    {
      id: 'model_name',
      header: '模型名称',
      cell: (item: ModelSummary) => (
        <Link onFollow={() => onModelClick?.(item.id)}>{item.model_name}</Link>
      ),
      sortingField: 'model_name',
    },
    {
      id: 'version',
      header: '版本',
      cell: (item: ModelSummary) => item.version || '-',
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: ModelSummary) => <ModelStatusBadge status={item.status} />,
      sortingField: 'status',
    },
    {
      id: 'framework',
      header: '框架',
      cell: (item: ModelSummary) =>
        item.framework ? MODEL_FRAMEWORK_LABELS[item.framework] : '-',
    },
    {
      id: 'training_job_id',
      header: '训练任务',
      cell: (item: ModelSummary) =>
        item.training_job_id ? (
          <Link href={`/training-jobs/${item.training_job_id}`}>
            #{item.training_job_id}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: ModelSummary) => formatDateTime(item.created_at),
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
      selectionType={selectable ? 'multi' : undefined}
      selectedItems={selectable ? selectedItems : undefined}
      onSelectionChange={
        selectable && onSelectionChange
          ? ({ detail }) => onSelectionChange(detail.selectedItems)
          : undefined
      }
      ariaLabels={
        selectable
          ? {
              selectionGroupLabel: '模型选择',
              allItemsSelectionLabel: () => '全选',
              itemSelectionLabel: (_data, row) => `选择 ${row.model_name} ${row.version}`,
            }
          : undefined
      }
      header={
        <Header variant="h2" counter={totalCount ? `(${totalCount})` : undefined}>
          模型列表
        </Header>
      }
      empty={
        <Box textAlign="center" color="inherit" padding="xl">
          <SpaceBetween size="m">
            <b>暂无模型</b>
            <Box color="text-body-secondary">尚未注册任何模型</Box>
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

export default ModelTable;
