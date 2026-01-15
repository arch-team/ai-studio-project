/**
 * Model Version Table Component
 *
 * 模型版本历史表格组件
 */

import {
  Box,
  Button,
  Checkbox,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import type { ModelVersionSummary } from '../types';

interface ModelVersionTableProps {
  versions: ModelVersionSummary[];
  loading?: boolean;
  selectedVersions: string[];
  onSelectionChange: (versions: string[]) => void;
  onCompare: () => void;
  maxSelections?: number;
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
 * 模型版本表格组件
 */
export function ModelVersionTable({
  versions,
  loading = false,
  selectedVersions,
  onSelectionChange,
  onCompare,
  maxSelections = 2,
}: ModelVersionTableProps) {
  const handleCheckboxChange = (version: string, checked: boolean) => {
    if (checked) {
      if (selectedVersions.length < maxSelections) {
        onSelectionChange([...selectedVersions, version]);
      }
    } else {
      onSelectionChange(selectedVersions.filter((v) => v !== version));
    }
  };

  const columnDefinitions = [
    {
      id: 'select',
      header: '选择',
      cell: (item: ModelVersionSummary) => (
        <Checkbox
          checked={selectedVersions.includes(item.version)}
          onChange={({ detail }) =>
            handleCheckboxChange(item.version, detail.checked)
          }
          disabled={
            !selectedVersions.includes(item.version) &&
            selectedVersions.length >= maxSelections
          }
        />
      ),
      width: 60,
    },
    {
      id: 'version',
      header: '版本',
      cell: (item: ModelVersionSummary) => (
        <Box fontWeight="bold">{item.version}</Box>
      ),
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: ModelVersionSummary) => {
        const statusMap: Record<string, 'success' | 'warning' | 'error' | 'stopped'> = {
          registered: 'success',
          deployed: 'success',
          archived: 'stopped',
          failed: 'error',
        };
        return (
          <StatusIndicator type={statusMap[item.status] || 'info'}>
            {item.status}
          </StatusIndicator>
        );
      },
    },
    {
      id: 'metrics_summary',
      header: '关键指标',
      cell: (item: ModelVersionSummary) => {
        if (!item.metrics || Object.keys(item.metrics).length === 0) {
          return '-';
        }
        // 显示前两个指标
        const entries = Object.entries(item.metrics).slice(0, 2);
        return entries
          .map(([key, value]) => `${key}: ${Number(value).toFixed(4)}`)
          .join(', ');
      },
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: ModelVersionSummary) => formatDateTime(item.created_at),
    },
  ];

  return (
    <SpaceBetween size="m">
      <Box float="right">
        <Button
          onClick={onCompare}
          disabled={selectedVersions.length !== 2}
        >
          对比版本 ({selectedVersions.length}/2)
        </Button>
      </Box>
      <Table
        columnDefinitions={columnDefinitions}
        items={versions}
        loading={loading}
        loadingText="加载版本历史..."
        variant="embedded"
        empty={
          <Box textAlign="center" color="inherit" padding="l">
            暂无版本历史
          </Box>
        }
      />
    </SpaceBetween>
  );
}

export default ModelVersionTable;
