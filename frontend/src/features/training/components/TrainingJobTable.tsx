/**
 * Training Job Table Component
 *
 * 可复用的训练任务表格组件
 */

import {
  Box,
  Link,
  Pagination,
  SpaceBetween,
  Table,
  Header,
} from '@cloudscape-design/components';
import type { TrainingJobSummary, JobPriority } from '../types';
import { JOB_PRIORITY_LABELS } from '../types';
import { TrainingStatusBadge } from './TrainingStatusBadge';

interface TrainingJobTableProps {
  items: TrainingJobSummary[];
  loading?: boolean;
  totalCount?: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onJobClick?: (jobId: number) => void;
  selectable?: boolean;
  selectedItems?: TrainingJobSummary[];
  onSelectionChange?: (items: TrainingJobSummary[]) => void;
  /** 列表加载失败时为 true：抑制 empty 空态文案，避免与错误提示同屏（F-022） */
  hasError?: boolean;
}

// 优先级颜色映射
const priorityColorMap: Record<JobPriority, 'text-status-success' | 'text-status-warning' | 'text-status-info'> = {
  high: 'text-status-success',
  medium: 'text-status-warning',
  low: 'text-status-info',
};

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
 * 训练任务表格组件
 */
export function TrainingJobTable({
  items,
  loading = false,
  totalCount,
  currentPage,
  totalPages,
  onPageChange,
  onJobClick,
  selectable = false,
  selectedItems = [],
  onSelectionChange,
  hasError = false,
}: TrainingJobTableProps) {
  const columnDefinitions = [
    {
      id: 'job_name',
      header: '任务名称',
      cell: (item: TrainingJobSummary) => (
        <Link onFollow={() => onJobClick?.(item.id)}>{item.job_name}</Link>
      ),
      sortingField: 'job_name',
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: TrainingJobSummary) => <TrainingStatusBadge status={item.status} />,
      sortingField: 'status',
    },
    {
      id: 'priority',
      header: '优先级',
      cell: (item: TrainingJobSummary) => (
        <Box color={priorityColorMap[item.priority]}>
          {JOB_PRIORITY_LABELS[item.priority]}
        </Box>
      ),
      sortingField: 'priority',
    },
    {
      id: 'distribution_strategy',
      header: '分布式策略',
      cell: (item: TrainingJobSummary) =>
        item.distribution_strategy?.toUpperCase() || '-',
    },
    {
      id: 'node_count',
      header: '节点数',
      cell: (item: TrainingJobSummary) => item.node_count,
    },
    {
      id: 'gpu_per_node',
      header: 'GPU/节点',
      cell: (item: TrainingJobSummary) => item.gpu_per_node,
    },
    {
      id: 'progress',
      header: '进度',
      cell: (item: TrainingJobSummary) => {
        if (item.current_epoch != null && item.total_epochs != null) {
          const percent = Math.round((item.current_epoch / item.total_epochs) * 100);
          return `${item.current_epoch}/${item.total_epochs} (${percent}%)`;
        }
        return '-';
      },
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: TrainingJobSummary) => formatDateTime(item.created_at),
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
      header={
        <Header variant="h2" counter={totalCount ? `(${totalCount})` : undefined}>
          训练任务
        </Header>
      }
      empty={
        // error 态抑制 empty 文案（F-022）：失败时仅中性占位，不与"加载失败"提示同屏矛盾
        hasError ? (
          <Box textAlign="center" color="text-body-secondary" padding="xl">
            无法显示训练任务列表
          </Box>
        ) : (
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无训练任务</b>
              <Box color="text-body-secondary">尚未创建任何训练任务</Box>
            </SpaceBetween>
          </Box>
        )
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

export default TrainingJobTable;
