/**
 * Resource Quotas Page
 *
 * 资源配额管理页面 - 显示资源限制配置列表，支持创建/编辑
 */

import { useState } from 'react';
import {
  Box,
  Button,
  Container,
  Header,
  Pagination,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import {
  useResourceLimitConfigs,
  useCreateResourceLimitConfig,
  useUpdateResourceLimitConfig,
} from './api';
import { QuotaFormModal } from './components/QuotaFormModal';
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

  // 数据查询
  const { data, isLoading, error } = useResourceLimitConfigs({
    page: currentPage,
    page_size: pageSize,
  });

  // 创建/更新 mutations
  const createMutation = useCreateResourceLimitConfig();
  const updateMutation = useUpdateResourceLimitConfig();

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
        <Button variant="inline-link" onClick={() => handleEdit(item)}>
          编辑
        </Button>
      ),
    },
  ];

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
      <Header
        variant="h1"
        actions={
          <Button variant="primary" onClick={handleCreate}>
            新建配置
          </Button>
        }
      >
        资源配额管理
      </Header>

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
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无配置</b>
              <Box color="text-body-secondary">尚未创建任何资源限制配置</Box>
            </SpaceBetween>
          </Box>
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
    </SpaceBetween>
  );
}

export default ResourceQuotasPage;
