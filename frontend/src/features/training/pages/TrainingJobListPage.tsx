/**
 * Training Job List Page
 *
 * 训练任务列表页面 - 显示、过滤和管理训练任务
 */

import {
  Box,
  Button,
  Container,
  Header,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrainingJobs } from '../api';
import { TrainingJobTable } from '../components';
import type { JobStatus, JobPriority, TrainingJobFilters } from '../types';
import { JOB_STATUS_LABELS, JOB_PRIORITY_LABELS } from '../types';

// 状态过滤选项
const statusOptions = [
  { label: '全部状态', value: '' },
  ...Object.entries(JOB_STATUS_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 优先级过滤选项
const priorityOptions = [
  { label: '全部优先级', value: '' },
  ...Object.entries(JOB_PRIORITY_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 默认过滤条件
const defaultFilters: TrainingJobFilters = {
  page: 1,
  page_size: 20,
};

/**
 * 训练任务列表页面
 */
export function TrainingJobListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<TrainingJobFilters>(defaultFilters);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedPriority, setSelectedPriority] = useState<string>('');

  // 构建查询参数
  const queryFilters: TrainingJobFilters = {
    ...filters,
    status: selectedStatus ? (selectedStatus as JobStatus) : undefined,
    priority: selectedPriority ? (selectedPriority as JobPriority) : undefined,
  };

  // 获取训练任务列表，每 30 秒自动刷新
  const { data, isLoading, error, refetch } = useTrainingJobs(queryFilters);

  // 处理分页变化
  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  // 处理状态过滤变化
  const handleStatusChange = useCallback((value: string) => {
    setSelectedStatus(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理优先级过滤变化
  const handlePriorityChange = useCallback((value: string) => {
    setSelectedPriority(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 跳转到任务详情
  const handleJobClick = useCallback(
    (jobId: number) => {
      navigate(`/training-jobs/${jobId}`);
    },
    [navigate]
  );

  // 跳转到创建页面
  const handleCreateClick = useCallback(() => {
    navigate('/training-jobs/create');
  }, [navigate]);

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
      {/* 页面标题和操作 */}
      <Header
        variant="h1"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button iconName="refresh" onClick={() => refetch()}>
              刷新
            </Button>
            <Button variant="primary" onClick={handleCreateClick}>
              创建训练任务
            </Button>
          </SpaceBetween>
        }
      >
        训练任务管理
      </Header>

      {/* 过滤器 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
          <Select
            selectedOption={
              statusOptions.find((opt) => opt.value === selectedStatus) ||
              statusOptions[0]
            }
            onChange={({ detail }) =>
              handleStatusChange(detail.selectedOption.value || '')
            }
            options={statusOptions}
            placeholder="选择状态"
          />
          <Select
            selectedOption={
              priorityOptions.find((opt) => opt.value === selectedPriority) ||
              priorityOptions[0]
            }
            onChange={({ detail }) =>
              handlePriorityChange(detail.selectedOption.value || '')
            }
            options={priorityOptions}
            placeholder="选择优先级"
          />
        </SpaceBetween>
      </Container>

      {/* 训练任务表格 */}
      <TrainingJobTable
        items={data?.items || []}
        loading={isLoading}
        totalCount={data?.total}
        currentPage={filters.page || 1}
        totalPages={data?.total_pages || 1}
        onPageChange={handlePageChange}
        onJobClick={handleJobClick}
      />
    </SpaceBetween>
  );
}

export default TrainingJobListPage;
