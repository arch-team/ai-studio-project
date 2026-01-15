/**
 * Resource Quotas Page
 *
 * 资源配额管理页面 - 显示资源限制配置列表
 */

import {
  Box,
  Button,
  Container,
  Header,
  Pagination,
  SpaceBetween,
  Spinner,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import { useState } from 'react';
import { useResourceLimitConfigs } from './hooks';
import type { ResourceLimitConfig, Priority, UserRole } from './types';

// 角色显示映射
const roleLabels: Record<UserRole, string> = {
  admin: '管理员',
  project_manager: '项目经理',
  engineer: '工程师',
  viewer: '查看者',
};

// 优先级显示映射
const priorityLabels: Record<Priority, string> = {
  high: '高',
  medium: '中',
  low: '低',
};

// 优先级状态颜色
const priorityStatus: Record<Priority, 'success' | 'warning' | 'info'> = {
  high: 'success',
  medium: 'warning',
  low: 'info',
};

export function ResourceQuotasPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useResourceLimitConfigs({
    page: currentPage,
    page_size: pageSize,
  });

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
      cell: (item: ResourceLimitConfig) => roleLabels[item.role] || item.role,
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
        <StatusIndicator type={priorityStatus[item.priority_default]}>
          {priorityLabels[item.priority_default] || item.priority_default}
        </StatusIndicator>
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
          <Button variant="primary" disabled>
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
          <Header
            variant="h2"
            counter={data ? `(${data.total})` : undefined}
          >
            资源限制配置
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无配置</b>
              <Box color="text-body-secondary">
                尚未创建任何资源限制配置
              </Box>
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
    </SpaceBetween>
  );
}

export default ResourceQuotasPage;
