/**
 * Resource Quotas Page
 *
 * 资源配额管理页面 - 显示资源限制配置列表，支持创建/编辑
 */

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Header,
  Modal,
  Pagination,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import {
  useResourceLimitConfigs,
  useCreateResourceLimitConfig,
  useUpdateResourceLimitConfig,
  useDeleteResourceLimitConfig,
} from './api';
import { PageLayout } from '@shared/components';
import { QuotaFormModal } from './components/QuotaFormModal';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '配额管理', href: '/resource-quotas' },
];
import type {
  ResourceLimitConfig,
  CreateResourceLimitConfigRequest,
  UpdateResourceLimitConfigRequest,
} from './types';
import { ROLE_LABELS, PRIORITY_LABELS, PRIORITY_STATUS } from './types';

export function ResourceQuotasPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Modal 状态
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingQuota, setEditingQuota] = useState<ResourceLimitConfig | null>(null);

  // 删除确认弹窗状态
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [configToDelete, setConfigToDelete] = useState<ResourceLimitConfig | null>(null);

  // 数据查询
  const { data, isLoading, error, refetch } = useResourceLimitConfigs({
    page: currentPage,
    page_size: pageSize,
  });

  // 创建/更新/删除 mutations
  const createMutation = useCreateResourceLimitConfig();
  const updateMutation = useUpdateResourceLimitConfig();
  const deleteMutation = useDeleteResourceLimitConfig();

  // 打开创建 Modal
  const handleCreate = () => {
    setEditingQuota(null);
    setIsModalVisible(true);
  };

  // 打开编辑 Modal
  const handleEdit = (quota: ResourceLimitConfig) => {
    setEditingQuota(quota);
    setIsModalVisible(true);
  };

  // 关闭 Modal
  const handleModalDismiss = () => {
    setIsModalVisible(false);
    setEditingQuota(null);
  };

  // 提交表单
  const handleSubmit = (
    formData: CreateResourceLimitConfigRequest | UpdateResourceLimitConfigRequest
  ) => {
    if (editingQuota) {
      updateMutation.mutate(
        { id: editingQuota.id, data: formData as UpdateResourceLimitConfigRequest },
        {
          onSuccess: () => {
            handleModalDismiss();
          },
        }
      );
    } else {
      createMutation.mutate(formData as CreateResourceLimitConfigRequest, {
        onSuccess: () => {
          handleModalDismiss();
        },
      });
    }
  };

  // 打开删除确认弹窗
  const handleDeleteClick = (config: ResourceLimitConfig) => {
    setConfigToDelete(config);
    setDeleteModalVisible(true);
  };

  // 取消删除
  const handleCancelDelete = () => {
    setDeleteModalVisible(false);
    setConfigToDelete(null);
  };

  // 确认删除
  const handleConfirmDelete = () => {
    if (configToDelete) {
      deleteMutation.mutate(configToDelete.id, {
        onSuccess: () => {
          // 删除成功：关闭弹窗（列表由 hook 自动 invalidate 刷新）
          setDeleteModalVisible(false);
          setConfigToDelete(null);
        },
      });
    }
  };

  const columnDefinitions = [
    {
      id: 'config_name',
      header: '配置名称',
      cell: (item: ResourceLimitConfig) => item.config_name,
      sortingField: 'config_name',
    },
    {
      id: 'role',
      header: '适用角色',
      cell: (item: ResourceLimitConfig) => ROLE_LABELS[item.role] || item.role,
    },
    {
      id: 'max_gpu_per_job',
      header: '最大 GPU/任务',
      cell: (item: ResourceLimitConfig) => item.max_gpu_per_job,
    },
    {
      id: 'max_cpu_per_job',
      header: '最大 CPU/任务',
      cell: (item: ResourceLimitConfig) => item.max_cpu_per_job,
    },
    {
      id: 'max_memory_gb_per_job',
      header: '最大内存/任务 (GB)',
      cell: (item: ResourceLimitConfig) => item.max_memory_gb_per_job,
    },
    {
      id: 'max_nodes_per_job',
      header: '最大节点/任务',
      cell: (item: ResourceLimitConfig) => item.max_nodes_per_job,
    },
    {
      id: 'priority_default',
      header: '默认优先级',
      cell: (item: ResourceLimitConfig) => (
        <StatusIndicator type={PRIORITY_STATUS[item.priority_default]}>
          {PRIORITY_LABELS[item.priority_default] || item.priority_default}
        </StatusIndicator>
      ),
    },
    {
      id: 'actions',
      header: '操作',
      cell: (item: ResourceLimitConfig) => (
        <SpaceBetween direction="horizontal" size="xs">
          <Button variant="inline-link" onClick={() => handleEdit(item)}>
            编辑
          </Button>
          <Button variant="inline-link" onClick={() => handleDeleteClick(item)}>
            删除
          </Button>
        </SpaceBetween>
      ),
    },
  ];

  return (
    <PageLayout
      title="资源配额管理"
      description="按团队与角色配置 GPU / 节点资源上限"
      breadcrumbs={BREADCRUMBS}
      actions={
        <Button variant="primary" iconName="add-plus" onClick={handleCreate}>
          新建配置
        </Button>
      }
    >
    <SpaceBetween size="l">
      {error && (
        <Alert
          type="error"
          header="加载失败"
          action={<Button onClick={() => refetch()}>重试</Button>}
        >
          {error.message}
        </Alert>
      )}

      <Table
        columnDefinitions={columnDefinitions}
        items={data?.items || []}
        loading={isLoading}
        loadingText="加载中..."
        sortingDisabled
        variant="container"
        header={
          <Header variant="h2" counter={data ? `(${data.total})` : undefined}>
            资源限制配置
          </Header>
        }
        empty={
          // error 态抑制 empty 正向语义：失败时只显示中性占位（顶部 Alert 已说明并提供重试），
          // 不渲染"暂无配置/尚未创建"误导用户（interaction-states.md §1 R3 / F-028）
          error ? (
            <Box textAlign="center" color="text-body-secondary" padding="xl">
              无法显示配置列表
            </Box>
          ) : (
            <Box textAlign="center" color="inherit" padding="xl">
              <SpaceBetween size="m">
                <b>暂无配置</b>
                <Box color="text-body-secondary">尚未创建任何资源限制配置</Box>
              </SpaceBetween>
            </Box>
          )
        }
        pagination={
          data && data.total_pages > 1 ? (
            <Pagination
              currentPageIndex={currentPage}
              pagesCount={data.total_pages}
              onChange={({ detail }) => setCurrentPage(detail.currentPageIndex)}
            />
          ) : undefined
        }
      />

      <QuotaFormModal
        visible={isModalVisible}
        onDismiss={handleModalDismiss}
        onSubmit={handleSubmit}
        editingQuota={editingQuota}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* 删除确认弹窗（仅在打开时挂载，避免与表单弹窗的 dialog 角色共存） */}
      {deleteModalVisible && (
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
          <SpaceBetween size="m">
            <Alert type="warning">此操作不可撤销</Alert>
            <Box>
              确定删除配置「<b>{configToDelete?.config_name}</b>」吗？
            </Box>
          </SpaceBetween>
        </Modal>
      )}
    </SpaceBetween>
    </PageLayout>
  );
}

export default ResourceQuotasPage;
