/**
 * Training Job Detail Page
 *
 * 训练任务详情页面 - 显示任务配置、状态、检查点和操作
 */

import {
  Box,
  BreadcrumbGroup,
  Button,
  ColumnLayout,
  Container,
  Header,
  KeyValuePairs,
  Modal,
  SpaceBetween,
  Spinner,
  Table,
  Tabs,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useTrainingJob,
  useTrainingJobCheckpoints,
  usePauseTrainingJob,
  useResumeTrainingJob,
  useDeleteTrainingJob,
} from '../api';
import { TrainingStatusBadge } from '../components';
import type { Checkpoint } from '../types';
import {
  JOB_PRIORITY_LABELS,
  DISTRIBUTION_STRATEGY_LABELS,
} from '../types';

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
    second: '2-digit',
  });
}

/**
 * 格式化持续时间
 */
function formatDuration(startTime: string | null, endTime: string | null): string {
  if (!startTime) return '-';
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${hours}h ${minutes}m`;
}

/**
 * 检查点表格列定义
 */
const checkpointColumns = [
  {
    id: 'checkpoint_name',
    header: '检查点名称',
    cell: (item: Checkpoint) => item.checkpoint_name,
  },
  {
    id: 'epoch',
    header: 'Epoch',
    cell: (item: Checkpoint) => item.epoch ?? '-',
  },
  {
    id: 'step',
    header: 'Step',
    cell: (item: Checkpoint) => item.step ?? '-',
  },
  {
    id: 'storage_path',
    header: '存储路径',
    cell: (item: Checkpoint) => (
      <Box fontSize="body-s">
        <code>{item.storage_path}</code>
      </Box>
    ),
  },
  {
    id: 'size_bytes',
    header: '大小',
    cell: (item: Checkpoint) => {
      if (!item.size_bytes) return '-';
      const mb = item.size_bytes / (1024 * 1024);
      return mb >= 1024
        ? `${(mb / 1024).toFixed(2)} GB`
        : `${mb.toFixed(2)} MB`;
    },
  },
  {
    id: 'created_at',
    header: '创建时间',
    cell: (item: Checkpoint) => formatDateTime(item.created_at),
  },
];

/**
 * 训练任务详情页面
 */
export function TrainingJobDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const jobId = id ? parseInt(id, 10) : undefined;

  // 删除确认弹窗
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // 获取任务详情
  const { data: job, isLoading, error, refetch } = useTrainingJob(jobId);

  // 获取检查点列表
  const { data: checkpointsData, isLoading: checkpointsLoading } =
    useTrainingJobCheckpoints(jobId);

  // Mutations
  const pauseMutation = usePauseTrainingJob();
  const resumeMutation = useResumeTrainingJob();
  const deleteMutation = useDeleteTrainingJob();

  // 判断是否可以暂停
  const canPause = job?.status === 'running';
  // 判断是否可以恢复
  const canResume = job?.status === 'paused' || job?.status === 'preempted';
  // 判断是否可以删除
  const canDelete = job?.status !== 'running';

  // 暂停任务
  const handlePause = useCallback(async () => {
    if (!jobId) return;
    await pauseMutation.mutateAsync(jobId);
    refetch();
  }, [jobId, pauseMutation, refetch]);

  // 恢复任务
  const handleResume = useCallback(async () => {
    if (!jobId) return;
    await resumeMutation.mutateAsync(jobId);
    refetch();
  }, [jobId, resumeMutation, refetch]);

  // 删除任务
  const handleDelete = useCallback(async () => {
    if (!jobId) return;
    await deleteMutation.mutateAsync(jobId);
    setShowDeleteModal(false);
    navigate('/training-jobs');
  }, [jobId, deleteMutation, navigate]);

  // 加载状态
  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态
  if (error || !job) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          {error?.message || '任务不存在'}
        </Box>
      </Container>
    );
  }

  return (
    <SpaceBetween size="l">
      {/* 面包屑导航 */}
      <BreadcrumbGroup
        items={[
          { text: '训练任务', href: '/training-jobs' },
          { text: job.job_name, href: '#' },
        ]}
        onFollow={(e) => {
          e.preventDefault();
          if (e.detail.href !== '#') {
            navigate(e.detail.href);
          }
        }}
      />

      {/* 页面标题和操作 */}
      <Header
        variant="h1"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button iconName="refresh" onClick={() => refetch()}>
              刷新
            </Button>
            {canPause && (
              <Button
                onClick={handlePause}
                loading={pauseMutation.isPending}
              >
                暂停
              </Button>
            )}
            {canResume && (
              <Button
                variant="primary"
                onClick={handleResume}
                loading={resumeMutation.isPending}
              >
                恢复
              </Button>
            )}
            <Button
              onClick={() => setShowDeleteModal(true)}
              disabled={!canDelete}
            >
              删除
            </Button>
          </SpaceBetween>
        }
      >
        {job.job_name}
      </Header>

      {/* 概览信息 */}
      <Container header={<Header variant="h2">概览</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">状态</Box>
            <TrainingStatusBadge status={job.status} />
          </div>
          <div>
            <Box variant="awsui-key-label">优先级</Box>
            <Box>{JOB_PRIORITY_LABELS[job.priority]}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">分布式策略</Box>
            <Box>
              {job.distribution_strategy
                ? DISTRIBUTION_STRATEGY_LABELS[job.distribution_strategy]
                : '-'}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">持续时间</Box>
            <Box>{formatDuration(job.started_at, job.completed_at)}</Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* 进度信息 */}
      {(job.current_epoch != null || job.current_step != null) && (
        <Container header={<Header variant="h2">训练进度</Header>}>
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">当前 Epoch</Box>
              <Box>
                {job.current_epoch ?? '-'} / {job.total_epochs ?? '-'}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">当前 Step</Box>
              <Box>{job.current_step ?? '-'}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">检查点数量</Box>
              <Box>{job.checkpoints_count ?? 0}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">完成度</Box>
              <Box>
                {job.current_epoch != null && job.total_epochs != null
                  ? `${Math.round((job.current_epoch / job.total_epochs) * 100)}%`
                  : '-'}
              </Box>
            </div>
          </ColumnLayout>
        </Container>
      )}

      {/* 详细信息标签页 */}
      <Tabs
        tabs={[
          {
            id: 'config',
            label: '配置信息',
            content: (
              <Container>
                <KeyValuePairs
                  columns={2}
                  items={[
                    { label: '任务 ID', value: String(job.id) },
                    { label: '任务名称', value: job.job_name },
                    { label: '描述', value: job.description || '-' },
                    { label: '实例类型', value: job.instance_type || '-' },
                    { label: '节点数量', value: String(job.node_count) },
                    { label: '每节点 GPU', value: String(job.gpu_per_node) },
                    {
                      label: '总 GPU 数',
                      value: String(job.node_count * job.gpu_per_node),
                    },
                    { label: '容器镜像', value: job.image_uri || '-' },
                    { label: '训练脚本', value: job.entry_point || '-' },
                    { label: '创建时间', value: formatDateTime(job.created_at) },
                    { label: '开始时间', value: formatDateTime(job.started_at) },
                    { label: '完成时间', value: formatDateTime(job.completed_at) },
                  ]}
                />
              </Container>
            ),
          },
          {
            id: 'checkpoints',
            label: `检查点 (${checkpointsData?.items?.length || 0})`,
            content: (
              <Table
                columnDefinitions={checkpointColumns}
                items={checkpointsData?.items || []}
                loading={checkpointsLoading}
                loadingText="加载检查点..."
                variant="embedded"
                empty={
                  <Box textAlign="center" color="inherit" padding="l">
                    暂无检查点
                  </Box>
                }
              />
            ),
          },
          {
            id: 'logs',
            label: '日志',
            content: (
              <Box padding="l" color="text-body-secondary">
                日志功能开发中...
              </Box>
            ),
          },
          {
            id: 'metrics',
            label: '训练指标',
            content: (
              <Box padding="l" color="text-body-secondary">
                指标监控功能开发中...
              </Box>
            ),
          },
        ]}
      />

      {/* 删除确认弹窗 */}
      <Modal
        visible={showDeleteModal}
        onDismiss={() => setShowDeleteModal(false)}
        header="确认删除"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => setShowDeleteModal(false)}
              >
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleDelete}
                loading={deleteMutation.isPending}
              >
                确认删除
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        确定要删除训练任务 <b>{job.job_name}</b> 吗？此操作不可恢复。
      </Modal>
    </SpaceBetween>
  );
}

export default TrainingJobDetailPage;
