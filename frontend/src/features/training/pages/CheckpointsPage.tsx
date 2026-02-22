/**
 * Checkpoints Page
 *
 * 检查点列表页面 - 展示所有训练任务的检查点
 */

import {
  Box,
  Container,
  Header,
  Select,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import { useState, useCallback, useMemo } from 'react';
import { useTrainingJobs, useTrainingJobCheckpoints } from '../api';
import { formatDateTime } from '@shared/utils';
import type { Checkpoint, CheckpointStatus, CheckpointType } from '../types';

// 检查点状态标签
const CHECKPOINT_STATUS_LABELS: Record<CheckpointStatus, string> = {
  available: '可用',
  archived: '已归档',
  deleted: '已删除',
};

// 检查点状态 → StatusIndicator type 映射
const CHECKPOINT_STATUS_INDICATOR: Record<CheckpointStatus, 'success' | 'stopped' | 'error'> = {
  available: 'success',
  archived: 'stopped',
  deleted: 'error',
};

// 检查点类型标签
const CHECKPOINT_TYPE_LABELS: Record<CheckpointType, string> = {
  epoch: 'Epoch',
  step: 'Step',
  best: '最佳',
  final: '最终',
  manual: '手动',
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
 * 检查点列表页面
 */
export function CheckpointsPage() {
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(undefined);

  // 获取训练任务列表（用于筛选下拉）
  const { data: jobsData, isLoading: loadingJobs } = useTrainingJobs({ page_size: 100 });

  // 获取检查点列表
  const { data: checkpointsData, isLoading: loadingCheckpoints, error } =
    useTrainingJobCheckpoints(selectedJobId);

  // 构建训练任务选项
  const jobOptions = useMemo(() => {
    const options = [{ label: '全部任务', value: '' }];
    if (jobsData?.items) {
      jobsData.items.forEach((job) => {
        options.push({
          label: `${job.job_name} (${job.id})`,
          value: String(job.id),
        });
      });
    }
    return options;
  }, [jobsData]);

  // 处理任务选择变化
  const handleJobChange = useCallback((value: string) => {
    setSelectedJobId(value ? Number(value) : undefined);
  }, []);

  // 表格列定义
  const columnDefinitions = useMemo(
    () => [
      {
        id: 'checkpoint_name',
        header: '检查点名称',
        cell: (item: Checkpoint) => item.checkpoint_name,
      },
      {
        id: 'training_job_id',
        header: '训练任务 ID',
        cell: (item: Checkpoint) => String(item.training_job_id),
        width: 120,
      },
      {
        id: 'checkpoint_type',
        header: '类型',
        cell: (item: Checkpoint) => CHECKPOINT_TYPE_LABELS[item.checkpoint_type],
        width: 100,
      },
      {
        id: 'epoch',
        header: 'Epoch',
        cell: (item: Checkpoint) => item.epoch ?? '-',
        width: 80,
      },
      {
        id: 'step',
        header: 'Step',
        cell: (item: Checkpoint) => item.step ?? '-',
        width: 80,
      },
      {
        id: 'loss',
        header: 'Loss',
        cell: (item: Checkpoint) => (item.loss !== null ? item.loss.toFixed(4) : '-'),
        width: 100,
      },
      {
        id: 'size',
        header: '大小',
        cell: (item: Checkpoint) => formatBytes(item.size_bytes),
        width: 100,
      },
      {
        id: 'storage_tier',
        header: '存储层级',
        cell: (item: Checkpoint) => item.storage_tier.toUpperCase(),
        width: 100,
      },
      {
        id: 'status',
        header: '状态',
        cell: (item: Checkpoint) => (
          <StatusIndicator type={CHECKPOINT_STATUS_INDICATOR[item.status]}>
            {CHECKPOINT_STATUS_LABELS[item.status]}
          </StatusIndicator>
        ),
        width: 100,
      },
      {
        id: 'created_at',
        header: '创建时间',
        cell: (item: Checkpoint) => formatDateTime(item.created_at),
        width: 180,
      },
    ],
    [],
  );

  // 获取检查点列表 items
  const checkpointItems = checkpointsData?.items ?? checkpointsData?.checkpoints ?? [];

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

  return (
    <SpaceBetween size="l">
      {/* 页面标题 */}
      <Header variant="h1">检查点管理</Header>

      {/* 过滤器 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
          <Select
            selectedOption={
              jobOptions.find((opt) => opt.value === String(selectedJobId ?? '')) ||
              jobOptions[0]
            }
            onChange={({ detail }) => handleJobChange(detail.selectedOption.value || '')}
            options={jobOptions}
            placeholder="选择训练任务"
            filteringType="auto"
            loadingText="加载中..."
            statusType={loadingJobs ? 'loading' : 'finished'}
          />
        </SpaceBetween>
      </Container>

      {/* 检查点说明 */}
      {!selectedJobId && (
        <Container>
          <Box textAlign="center" color="text-body-secondary" padding="l">
            请选择一个训练任务以查看其检查点列表
          </Box>
        </Container>
      )}

      {/* 检查点表格 */}
      {selectedJobId && (
        <Table
          columnDefinitions={columnDefinitions}
          items={checkpointItems}
          loading={loadingCheckpoints}
          loadingText="加载中..."
          variant="container"
          header={
            <Header
              variant="h2"
              counter={`(${checkpointItems.length})`}
            >
              检查点列表
            </Header>
          }
          empty={
            <Box textAlign="center" color="inherit" padding="xl">
              <SpaceBetween size="m">
                <b>暂无检查点</b>
                <Box color="text-body-secondary">
                  该训练任务尚未产生检查点
                </Box>
              </SpaceBetween>
            </Box>
          }
        />
      )}
    </SpaceBetween>
  );
}

export default CheckpointsPage;
