/**
 * User Management Page
 *
 * 用户管理页面 - 支持用户 CRUD、角色管理
 */

import { useState, useMemo } from 'react';
import {
  Box,
  Button,
  Container,
  Header,
  Pagination,
  Select,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import { useUsers, useCreateUser, useUpdateUser } from '../hooks';
import { UserFormModal } from '../components/UserFormModal';
import type {
  UserDetail,
  UserFilters,
  UserRole,
  UserStatus,
  CreateUserRequest,
  UpdateUserRequest,
} from '../types';
import {
  USER_ROLE_LABELS,
  USER_ROLE_COLORS,
  USER_STATUS_LABELS,
  USER_STATUS_COLORS,
} from '../types';

// 日期格式化
function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// 构建 Select 选项
const roleFilterOptions = [
  { value: '', label: '全部角色' },
  ...Object.entries(USER_ROLE_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

const statusFilterOptions = [
  { value: '', label: '全部状态' },
  ...Object.entries(USER_STATUS_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

export function UserManagementPage() {
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // 过滤器状态
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Modal 状态
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<UserDetail | null>(null);

  // 构建过滤器参数
  const filters: UserFilters = useMemo(() => {
    const params: UserFilters = {
      page: currentPage,
      page_size: pageSize,
    };

    if (roleFilter) {
      params.role = roleFilter as UserRole;
    }

    if (statusFilter) {
      params.status = statusFilter as UserStatus;
    }

    return params;
  }, [currentPage, roleFilter, statusFilter]);

  // 数据查询
  const { data, isLoading, error } = useUsers(filters);

  // 创建/更新 mutations
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();

  // 打开创建 Modal
  const handleCreate = () => {
    setEditingUser(null);
    setIsModalVisible(true);
  };

  // 打开编辑 Modal
  const handleEdit = (user: UserDetail) => {
    setEditingUser(user);
    setIsModalVisible(true);
  };

  // 关闭 Modal
  const handleModalDismiss = () => {
    setIsModalVisible(false);
    setEditingUser(null);
  };

  // 提交表单
  const handleSubmit = (formData: CreateUserRequest | UpdateUserRequest) => {
    if (editingUser) {
      updateMutation.mutate(
        { id: editingUser.id, data: formData as UpdateUserRequest },
        {
          onSuccess: () => {
            handleModalDismiss();
          },
        }
      );
    } else {
      createMutation.mutate(formData as CreateUserRequest, {
        onSuccess: () => {
          handleModalDismiss();
        },
      });
    }
  };

  // 表格列定义
  const columnDefinitions = [
    {
      id: 'username',
      header: '用户名',
      cell: (item: UserDetail) => item.username,
      sortingField: 'username',
      width: 150,
    },
    {
      id: 'email',
      header: '邮箱',
      cell: (item: UserDetail) => item.email,
      width: 220,
    },
    {
      id: 'role',
      header: '角色',
      cell: (item: UserDetail) => (
        <StatusIndicator type={USER_ROLE_COLORS[item.role]}>
          {USER_ROLE_LABELS[item.role]}
        </StatusIndicator>
      ),
      width: 120,
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: UserDetail) => (
        <StatusIndicator type={USER_STATUS_COLORS[item.status]}>
          {USER_STATUS_LABELS[item.status]}
        </StatusIndicator>
      ),
      width: 100,
    },
    {
      id: 'created_at',
      header: '创建时间',
      cell: (item: UserDetail) => formatDateTime(item.created_at),
      width: 160,
    },
    {
      id: 'actions',
      header: '操作',
      cell: (item: UserDetail) => (
        <Button variant="inline-link" onClick={() => handleEdit(item)}>
          编辑
        </Button>
      ),
      width: 80,
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
            新建用户
          </Button>
        }
      >
        用户管理
      </Header>

      {/* 过滤器区域 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                roleFilter
                  ? roleFilterOptions.find((o) => o.value === roleFilter) || null
                  : roleFilterOptions[0]
              }
              onChange={({ detail }) => {
                setRoleFilter(detail.selectedOption.value || '');
                setCurrentPage(1);
              }}
              options={roleFilterOptions}
              ariaLabel="角色筛选"
            />
          </div>

          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                statusFilter
                  ? statusFilterOptions.find((o) => o.value === statusFilter) || null
                  : statusFilterOptions[0]
              }
              onChange={({ detail }) => {
                setStatusFilter(detail.selectedOption.value || '');
                setCurrentPage(1);
              }}
              options={statusFilterOptions}
              ariaLabel="状态筛选"
            />
          </div>
        </SpaceBetween>
      </Container>

      {/* 用户表格 */}
      <Table
        columnDefinitions={columnDefinitions}
        items={data?.items || []}
        loading={isLoading}
        loadingText="加载中..."
        sortingDisabled
        variant="container"
        header={
          <Header variant="h2" counter={data ? `(${data.total})` : undefined}>
            用户列表
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无用户</b>
              <Box color="text-body-secondary">尚未创建任何用户</Box>
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

      <UserFormModal
        visible={isModalVisible}
        onDismiss={handleModalDismiss}
        onSubmit={handleSubmit}
        editingUser={editingUser}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </SpaceBetween>
  );
}

export default UserManagementPage;
