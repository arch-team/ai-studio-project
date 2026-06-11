/**
 * Space List Page
 *
 * 在线开发环境列表页面 - 显示、过滤和管理开发空间
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Link,
  Modal,
  Pagination,
  Select,
  SpaceBetween,
  Table,
} from '@cloudscape-design/components';
import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useSpaces,
  useStartSpace,
  useStopSpace,
  useDeleteSpace,
} from '../api';
import { PageLayout } from '@shared/components';
import { SpaceStatusBadge } from '../components/SpaceStatusBadge';
import type { SpaceStatus, SpaceFilters, SpaceSummary } from '../types';
import { SPACE_STATUS_LABELS, SPACE_TYPE_LABELS } from '../types';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '开发空间', href: '/spaces' },
];

// 状态过滤选项
const statusOptions = [
  { label: '全部状态', value: '' },
  ...Object.entries(SPACE_STATUS_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 默认过滤条件
const defaultFilters: SpaceFilters = {
  page: 1,
  page_size: 20,
};

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
}

/**
 * 在线开发环境列表页面
 */
export function SpaceListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<SpaceFilters>(defaultFilters);
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // 删除确认弹窗状态
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [spaceToDelete, setSpaceToDelete] = useState<SpaceSummary | null>(null);

  // 构建查询参数
  const queryFilters: SpaceFilters = useMemo(
    () => ({
      ...filters,
      status: selectedStatus ? (selectedStatus as SpaceStatus) : undefined,
    }),
    [filters, selectedStatus]
  );

  // 数据查询
  const { data, isLoading, error, refetch } = useSpaces(queryFilters);

  // Mutations
  const startMutation = useStartSpace();
  const stopMutation = useStopSpace();
  const deleteMutation = useDeleteSpace();

  // 处理分页变化
  const handlePageChange = useCallback(
    ({ detail }: { detail: { currentPageIndex: number } }) => {
      setFilters((prev) => ({ ...prev, page: detail.currentPageIndex }));
    },
    []
  );

  // 处理状态过滤变化
  const handleStatusChange = useCallback((value: string) => {
    setSelectedStatus(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  // 跳转到创建页面
  const handleCreateClick = useCallback(() => {
    navigate('/spaces/create');
  }, [navigate]);

  // 启动空间
  const handleStartSpace = useCallback(
    (id: string) => {
      startMutation.mutate(id);
    },
    [startMutation]
  );

  // 停止空间
  const handleStopSpace = useCallback(
    (id: string) => {
      stopMutation.mutate(id);
    },
    [stopMutation]
  );

  // 显示删除确认弹窗
  const handleDeleteClick = useCallback((space: SpaceSummary) => {
    setSpaceToDelete(space);
    setDeleteModalVisible(true);
  }, []);

  // 确认删除
  const handleConfirmDelete = useCallback(() => {
    if (spaceToDelete) {
      deleteMutation.mutate(spaceToDelete.id, {
        onSuccess: () => {
          setDeleteModalVisible(false);
          setSpaceToDelete(null);
        },
      });
    }
  }, [spaceToDelete, deleteMutation]);

  // 取消删除
  const handleCancelDelete = useCallback(() => {
    setDeleteModalVisible(false);
    setSpaceToDelete(null);
  }, []);

  // 表格列定义
  const columnDefinitions = useMemo(
    () => [
      {
        id: 'space_name',
        header: '名称',
        cell: (item: SpaceSummary) => (
          <Link
            onFollow={(e) => {
              e.preventDefault();
              navigate(`/spaces/${item.id}`);
            }}
          >
            {item.space_name}
          </Link>
        ),
        sortingField: 'space_name',
      },
      {
        id: 'space_type',
        header: 'IDE 类型',
        cell: (item: SpaceSummary) =>
          SPACE_TYPE_LABELS[item.space_type] || item.space_type,
      },
      {
        id: 'instance_type',
        header: '实例类型',
        cell: (item: SpaceSummary) => item.instance_type,
      },
      {
        id: 'status',
        header: '状态',
        cell: (item: SpaceSummary) => (
          <SpaceStatusBadge status={item.status} />
        ),
      },
      {
        id: 'created_at',
        header: '创建时间',
        cell: (item: SpaceSummary) => formatDateTime(item.created_at),
        sortingField: 'created_at',
      },
      {
        id: 'actions',
        header: '操作',
        cell: (item: SpaceSummary) => (
          <SpaceBetween direction="horizontal" size="xs">
            {item.status === 'stopped' && (
              <Button
                variant="link"
                onClick={() => handleStartSpace(item.id)}
                loading={startMutation.isPending}
              >
                启动
              </Button>
            )}
            {item.status === 'running' && (
              <Button
                variant="link"
                onClick={() => handleStopSpace(item.id)}
                loading={stopMutation.isPending}
              >
                停止
              </Button>
            )}
            {(item.status === 'stopped' || item.status === 'failed') && (
              <Button
                variant="link"
                onClick={() => handleDeleteClick(item)}
              >
                删除
              </Button>
            )}
          </SpaceBetween>
        ),
      },
    ],
    [
      navigate,
      handleStartSpace,
      handleStopSpace,
      handleDeleteClick,
      startMutation.isPending,
      stopMutation.isPending,
    ]
  );

  return (
    <PageLayout
      title="在线开发环境"
      description="管理交互式开发空间（在线 IDE / Notebook）"
      counter={data ? `(${data.total})` : undefined}
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button variant="primary" iconName="add-plus" onClick={handleCreateClick}>
            创建开发空间
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
        </SpaceBetween>
      </Container>

      {/* 空间列表表格 */}
      <Table
        loading={isLoading}
        loadingText="加载中..."
        items={data?.items ?? []}
        columnDefinitions={columnDefinitions}
        empty={
          <Box textAlign="center" padding="xl" color="text-body-secondary">
            <SpaceBetween size="m">
              <Box>暂无开发空间</Box>
              <Button onClick={handleCreateClick}>创建开发空间</Button>
            </SpaceBetween>
          </Box>
        }
        pagination={
          <Pagination
            currentPageIndex={filters.page || 1}
            pagesCount={data?.total_pages || 1}
            onChange={handlePageChange}
          />
        }
      />

      {/* 删除确认弹窗 */}
      <Modal
        visible={deleteModalVisible}
        onDismiss={handleCancelDelete}
        header="确认删除"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={handleCancelDelete}>
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirmDelete}
                loading={deleteMutation.isPending}
              >
                确认删除
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        确定要删除开发空间 <b>{spaceToDelete?.space_name}</b> 吗？此操作不可撤销。
      </Modal>
    </SpaceBetween>
    </PageLayout>
  );
}

export default SpaceListPage;
