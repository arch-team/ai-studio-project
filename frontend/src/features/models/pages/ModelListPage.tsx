/**
 * Model List Page
 *
 * 模型列表页面 - 显示、过滤和管理模型
 */

import {
  Alert,
  Button,
  Container,
  FormField,
  Input,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useModels, useBatchArchiveModels } from '../api';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '模型管理', href: '/models' },
];
import { ModelTable } from '../components';
import type { ModelStatus, ModelFramework, ModelFilters, ModelSummary } from '../types';
import { MODEL_STATUS_LABELS, MODEL_FRAMEWORK_LABELS } from '../types';

// 状态过滤选项
const statusOptions = [
  { label: '全部状态', value: '' },
  ...Object.entries(MODEL_STATUS_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 框架过滤选项
const frameworkOptions = [
  { label: '全部框架', value: '' },
  ...Object.entries(MODEL_FRAMEWORK_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 默认过滤条件
const defaultFilters: ModelFilters = {
  page: 1,
  page_size: 20,
};

/**
 * 模型列表页面
 */
export function ModelListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ModelFilters>(defaultFilters);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedFramework, setSelectedFramework] = useState<string>('');
  const [trainingJobIdFilter, setTrainingJobIdFilter] = useState<string>('');
  const [selectedItems, setSelectedItems] = useState<ModelSummary[]>([]);

  // 批量归档 mutation
  const batchArchiveMutation = useBatchArchiveModels();

  // 构建查询参数
  const queryFilters: ModelFilters = {
    ...filters,
    status: selectedStatus ? (selectedStatus as ModelStatus) : undefined,
    framework: selectedFramework ? (selectedFramework as ModelFramework) : undefined,
    training_job_id: trainingJobIdFilter ? parseInt(trainingJobIdFilter, 10) : undefined,
  };

  // 获取模型列表
  const { data, isLoading, error, refetch } = useModels(queryFilters);

  // 处理分页变化
  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  // 处理状态过滤变化
  const handleStatusChange = useCallback((value: string) => {
    setSelectedStatus(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理框架过滤变化
  const handleFrameworkChange = useCallback((value: string) => {
    setSelectedFramework(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理训练任务 ID 过滤变化
  const handleTrainingJobIdChange = useCallback((value: string) => {
    // 只允许数字输入
    if (value === '' || /^\d+$/.test(value)) {
      setTrainingJobIdFilter(value);
      setFilters((prev) => ({ ...prev, page: 1 }));
    }
  }, []);

  // 跳转到模型详情
  const handleModelClick = useCallback(
    (modelId: number) => {
      navigate(`/models/${modelId}`);
    },
    [navigate]
  );

  // 批量归档
  const handleBatchArchive = useCallback(async () => {
    if (selectedItems.length === 0) return;
    const ids = selectedItems.map((item) => item.id);
    await batchArchiveMutation.mutateAsync(ids);
    setSelectedItems([]);
    refetch();
  }, [selectedItems, batchArchiveMutation, refetch]);

  return (
    <PageLayout
      title="模型管理"
      description="管理训练产出的模型及其版本"
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          {selectedItems.length > 0 && (
            <Button
              onClick={handleBatchArchive}
              loading={batchArchiveMutation.isPending}
            >
              批量归档 ({selectedItems.length})
            </Button>
          )}
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l">
      {/* 错误提示 */}
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
              frameworkOptions.find((opt) => opt.value === selectedFramework) ||
              frameworkOptions[0]
            }
            onChange={({ detail }) =>
              handleFrameworkChange(detail.selectedOption.value || '')
            }
            options={frameworkOptions}
            placeholder="选择框架"
          />
          <FormField label="训练任务 ID">
            <Input
              value={trainingJobIdFilter}
              onChange={({ detail }) => handleTrainingJobIdChange(detail.value)}
              placeholder="输入任务 ID"
              type="number"
            />
          </FormField>
        </SpaceBetween>
      </Container>

      {/* 模型表格 */}
      <ModelTable
        items={data?.items || []}
        loading={isLoading}
        totalCount={data?.total}
        currentPage={filters.page || 1}
        totalPages={data?.total_pages || 1}
        onPageChange={handlePageChange}
        onModelClick={handleModelClick}
        selectable
        selectedItems={selectedItems}
        onSelectionChange={setSelectedItems}
      />
    </SpaceBetween>
    </PageLayout>
  );
}

export default ModelListPage;
