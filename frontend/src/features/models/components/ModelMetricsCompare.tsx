/**
 * Model Metrics Compare Component
 *
 * 模型版本指标对比组件
 */

import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  Table,
} from '@cloudscape-design/components';
import type { VersionComparison, MetricsDiff, HyperparameterChange } from '../types';

interface ModelMetricsCompareProps {
  comparison: VersionComparison;
  version1: string;
  version2: string;
}

/**
 * 格式化差异百分比
 */
function formatDiffPercent(diff: MetricsDiff): string {
  if (diff.diff_percent === null) return '-';
  const sign = diff.diff_percent >= 0 ? '+' : '';
  return `${sign}${diff.diff_percent.toFixed(2)}%`;
}

/**
 * 获取差异颜色
 */
function getDiffColor(
  diff: MetricsDiff,
  metricName: string
): 'text-status-success' | 'text-status-error' | 'inherit' {
  // 对于 loss 类指标，负数是好的；对于 accuracy 类指标，正数是好的
  const isLowerBetter = metricName.toLowerCase().includes('loss') ||
    metricName.toLowerCase().includes('error');

  if (diff.diff_percent === null || Math.abs(diff.diff_percent) < 0.1) {
    return 'inherit';
  }

  if (isLowerBetter) {
    return diff.diff_percent < 0 ? 'text-status-success' : 'text-status-error';
  } else {
    return diff.diff_percent > 0 ? 'text-status-success' : 'text-status-error';
  }
}

/**
 * 指标对比表格
 */
function MetricsTable({
  metricsDiff,
  version1,
  version2,
}: {
  metricsDiff: Record<string, MetricsDiff>;
  version1: string;
  version2: string;
}) {
  const items = Object.entries(metricsDiff).map(([name, diff]) => ({
    name,
    ...diff,
  }));

  if (items.length === 0) {
    return (
      <Box textAlign="center" color="text-body-secondary" padding="l">
        暂无可对比的指标
      </Box>
    );
  }

  return (
    <Table
      columnDefinitions={[
        {
          id: 'name',
          header: '指标名称',
          cell: (item) => <Box fontWeight="bold">{item.name}</Box>,
        },
        {
          id: 'v1_value',
          header: version1,
          cell: (item) => item.v1?.toFixed(6) ?? '-',
        },
        {
          id: 'v2_value',
          header: version2,
          cell: (item) => item.v2?.toFixed(6) ?? '-',
        },
        {
          id: 'diff',
          header: '变化',
          cell: (item) => (
            <Box color={getDiffColor(item, item.name)}>
              {formatDiffPercent(item)}
            </Box>
          ),
        },
      ]}
      items={items}
      variant="embedded"
    />
  );
}

/**
 * 超参数变更表格
 */
function HyperparametersTable({
  changes,
  version1,
  version2,
}: {
  changes: HyperparameterChange[];
  version1: string;
  version2: string;
}) {
  if (changes.length === 0) {
    return (
      <Box textAlign="center" color="text-body-secondary" padding="l">
        超参数无变化
      </Box>
    );
  }

  return (
    <Table
      columnDefinitions={[
        {
          id: 'param',
          header: '参数名称',
          cell: (item: HyperparameterChange) => (
            <Box fontWeight="bold">{item.param}</Box>
          ),
        },
        {
          id: 'v1_value',
          header: version1,
          cell: (item: HyperparameterChange) => (
            <code>{item.v1_value !== undefined ? String(item.v1_value) : '-'}</code>
          ),
        },
        {
          id: 'v2_value',
          header: version2,
          cell: (item: HyperparameterChange) => (
            <code>{item.v2_value !== undefined ? String(item.v2_value) : '-'}</code>
          ),
        },
        {
          id: 'change_type',
          header: '变更类型',
          cell: (item: HyperparameterChange) => {
            const typeLabels: Record<string, string> = {
              added: '新增',
              removed: '移除',
              modified: '修改',
            };
            const typeColors: Record<string, 'text-status-success' | 'text-status-error' | 'text-status-warning'> = {
              added: 'text-status-success',
              removed: 'text-status-error',
              modified: 'text-status-warning',
            };
            return (
              <Box color={typeColors[item.change_type]}>
                {typeLabels[item.change_type] || item.change_type}
              </Box>
            );
          },
        },
      ]}
      items={changes}
      variant="embedded"
    />
  );
}

/**
 * 模型指标对比组件
 */
export function ModelMetricsCompare({
  comparison,
  version1,
  version2,
}: ModelMetricsCompareProps) {
  return (
    <SpaceBetween size="l">
      {/* 版本信息 */}
      <Container header={<Header variant="h2">版本对比</Header>}>
        <ColumnLayout columns={2} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">版本 1</Box>
            <Box fontWeight="bold">{version1}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">版本 2</Box>
            <Box fontWeight="bold">{version2}</Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* 指标对比 */}
      <Container header={<Header variant="h2">指标对比</Header>}>
        <MetricsTable
          metricsDiff={comparison.metrics_diff}
          version1={version1}
          version2={version2}
        />
      </Container>

      {/* 超参数变更 */}
      <Container header={<Header variant="h2">超参数变更</Header>}>
        <HyperparametersTable
          changes={comparison.hyperparameters_changes || []}
          version1={version1}
          version2={version2}
        />
      </Container>
    </SpaceBetween>
  );
}

export default ModelMetricsCompare;
