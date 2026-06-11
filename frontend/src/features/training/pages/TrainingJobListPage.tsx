/**
 * Training Job List Page
 *
 * 训练任务列表页面 - 显示、过滤和管理训练任务
 */

import {
  Alert,
  Button,
  Container,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useTrainingJobs } from '../api';
import { TrainingJobTable } from '../components';
import type { JobStatus, JobPriority, TrainingJobFilters } from '../types';
import { JOB_STATUS_LABELS, JOB_PRIORITY_LABELS } from '../types';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '训练任务', href: '/training-jobs' },
];

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
  const { data, isLoading, error, refetch } = useTrainingJobs(queryFilters, 30000);

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

  return (
    <PageLayout
      title="训练任务管理"
      description="提交、监控和管理分布式训练任务"
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button variant="primary" iconName="add-plus" onClick={handleCreateClick}>
            创建训练任务
          </Button>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {/* 错误提示（保留过滤器与重试入口） */}
        {error && (
          <Alert
            type="error"
            header="加载失败"
            action={<Button onClick={() => refetch()}>重试</Button>}
          >
            {error.message}
          </Alert>
        )}

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
    </PageLayout>
  );
}

export default TrainingJobListPage;
