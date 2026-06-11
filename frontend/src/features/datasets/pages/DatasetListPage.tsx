/**
 * Dataset List Page
 *
 * 数据集列表页面 - 显示、过滤和管理数据集
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
import { useDatasets } from '../api';
import { DatasetTable } from '../components';
import type {
  DatasetFilters,
  StorageType,
  DatasetType,
  DatasetStatus,
  DatasetVisibility,
} from '../types';
import {
  STORAGE_TYPE_LABELS,
  DATASET_TYPE_LABELS,
  DATASET_STATUS_LABELS,
  VISIBILITY_LABELS,
} from '../types';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '数据集', href: '/datasets' },
];

// 存储类型过滤选项
const storageTypeOptions = [
  { label: '全部存储类型', value: '' },
  ...Object.entries(STORAGE_TYPE_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 数据类型过滤选项
const datasetTypeOptions = [
  { label: '全部数据类型', value: '' },
  ...Object.entries(DATASET_TYPE_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 状态过滤选项
const statusOptions = [
  { label: '全部状态', value: '' },
  ...Object.entries(DATASET_STATUS_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 可见性过滤选项
const visibilityOptions = [
  { label: '全部可见性', value: '' },
  ...Object.entries(VISIBILITY_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 默认过滤条件
const defaultFilters: DatasetFilters = {
  page: 1,
  page_size: 20,
};

/**
 * 数据集列表页面
 */
export function DatasetListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<DatasetFilters>(defaultFilters);
  const [selectedStorageType, setSelectedStorageType] = useState<string>('');
  const [selectedDatasetType, setSelectedDatasetType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedVisibility, setSelectedVisibility] = useState<string>('');

  // 构建查询参数
  const queryFilters: DatasetFilters = {
    ...filters,
    storage_type: selectedStorageType
      ? (selectedStorageType as StorageType)
      : undefined,
    dataset_type: selectedDatasetType
      ? (selectedDatasetType as DatasetType)
      : undefined,
    status: selectedStatus ? (selectedStatus as DatasetStatus) : undefined,
    visibility: selectedVisibility
      ? (selectedVisibility as DatasetVisibility)
      : undefined,
  };

  // 获取数据集列表
  const { data, isLoading, error, refetch } = useDatasets(queryFilters);

  // 处理分页变化
  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  // 处理存储类型过滤变化
  const handleStorageTypeChange = useCallback((value: string) => {
    setSelectedStorageType(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理数据类型过滤变化
  const handleDatasetTypeChange = useCallback((value: string) => {
    setSelectedDatasetType(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理状态过滤变化
  const handleStatusChange = useCallback((value: string) => {
    setSelectedStatus(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 处理可见性过滤变化
  const handleVisibilityChange = useCallback((value: string) => {
    setSelectedVisibility(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 跳转到数据集详情
  const handleDatasetClick = useCallback(
    (datasetId: number) => {
      navigate(`/datasets/${datasetId}`);
    },
    [navigate]
  );

  // 跳转到创建页面
  const handleCreateClick = useCallback(() => {
    navigate('/datasets/create');
  }, [navigate]);

  return (
    <PageLayout
      title="数据集管理"
      description="注册、版本化并管理训练数据集"
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button variant="primary" iconName="add-plus" onClick={handleCreateClick}>
            注册数据集
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
              storageTypeOptions.find(
                (opt) => opt.value === selectedStorageType
              ) || storageTypeOptions[0]
            }
            onChange={({ detail }) =>
              handleStorageTypeChange(detail.selectedOption.value || '')
            }
            options={storageTypeOptions}
            placeholder="选择存储类型"
          />
          <Select
            selectedOption={
              datasetTypeOptions.find(
                (opt) => opt.value === selectedDatasetType
              ) || datasetTypeOptions[0]
            }
            onChange={({ detail }) =>
              handleDatasetTypeChange(detail.selectedOption.value || '')
            }
            options={datasetTypeOptions}
            placeholder="选择数据类型"
          />
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
              visibilityOptions.find(
                (opt) => opt.value === selectedVisibility
              ) || visibilityOptions[0]
            }
            onChange={({ detail }) =>
              handleVisibilityChange(detail.selectedOption.value || '')
            }
            options={visibilityOptions}
            placeholder="选择可见性"
          />
        </SpaceBetween>
      </Container>

      {/* 数据集表格 */}
      <DatasetTable
        items={data?.items || []}
        loading={isLoading}
        totalCount={data?.total}
        currentPage={filters.page || 1}
        totalPages={data?.total_pages || 1}
        onPageChange={handlePageChange}
        onDatasetClick={handleDatasetClick}
      />
    </SpaceBetween>
    </PageLayout>
  );
}

export default DatasetListPage;
