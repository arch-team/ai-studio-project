/**
 * Template Table Component
 *
 * 模板列表表格组件
 */

import {
  Badge,
  Box,
  Button,
  Header,
  Link,
  Pagination,
  Table,
} from '@cloudscape-design/components';
import type { JobTemplateSummary } from '../types';
import { VISIBILITY_COLORS, VISIBILITY_LABELS } from '../types';

interface TemplateTableProps {
  items: JobTemplateSummary[];
  loading?: boolean;
  totalCount?: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onTemplateClick?: (templateId: number) => void;
  onUseTemplate?: (templateId: number) => void;
  selectable?: boolean;
  selectedItems?: JobTemplateSummary[];
  onSelectionChange?: (items: JobTemplateSummary[]) => void;
}

/**
 * 模板列表表格
 */
export function TemplateTable({
  items,
  loading = false,
  totalCount,
  currentPage,
  totalPages,
  onPageChange,
  onTemplateClick,
  onUseTemplate,
  selectable = false,
  selectedItems = [],
  onSelectionChange,
}: TemplateTableProps) {
  const columnDefinitions = [
    {
      id: 'name',
      header: '模板名称',
      cell: (item: JobTemplateSummary) => (
        <Link onFollow={() => onTemplateClick?.(item.id)}>{item.name}</Link>
      ),
      sortingField: 'name',
    },
    {
      id: 'visibility',
      header: '可见性',
      cell: (item: JobTemplateSummary) => (
        <Badge color={VISIBILITY_COLORS[item.visibility]}>
          {VISIBILITY_LABELS[item.visibility]}
        </Badge>
      ),
    },
    {
      id: 'usage_count',
      header: '使用次数',
      cell: (item: JobTemplateSummary) => item.usage_count,
      sortingField: 'usage_count',
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: JobTemplateSummary) =>
        new Date(item.created_at).toLocaleDateString('zh-CN'),
      sortingField: 'created_at',
    },
    {
      id: 'actions',
      header: '操作',
      cell: (item: JobTemplateSummary) => (
        <Button variant="link" onClick={() => onUseTemplate?.(item.id)}>
          使用此模板
        </Button>
      ),
    },
  ];

  return (
    <Table
      columnDefinitions={columnDefinitions}
      items={items}
      loading={loading}
      loadingText="加载中..."
      variant="container"
      selectionType={selectable ? 'multi' : undefined}
      selectedItems={selectable ? selectedItems : undefined}
      onSelectionChange={
        selectable && onSelectionChange
          ? ({ detail }) => onSelectionChange(detail.selectedItems)
          : undefined
      }
      header={
        <Header variant="h2" counter={totalCount !== undefined ? `(${totalCount})` : undefined}>
          任务模板
        </Header>
      }
      empty={
        <Box textAlign="center" color="inherit" padding="l">
          <Box variant="p" color="inherit">
            暂无模板
          </Box>
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
