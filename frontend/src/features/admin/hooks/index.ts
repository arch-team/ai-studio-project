/**
 * Admin module hooks
 *
 * 用户管理 React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import {
  fetchUsers,
  fetchUser,
  createUser,
  updateUser,
} from '../api/userApi';
import type {
  UserFilters,
  CreateUserRequest,
  UpdateUserRequest,
} from '../types';

/**
 * 获取用户列表
 */
export function useUsers(filters: UserFilters = {}) {
  return useQuery({
    queryKey: queryKeys.users.list(filters as Record<string, unknown>),
    queryFn: () => fetchUsers(filters),
  });
}

/**
 * 获取单个用户
 */
export function useUser(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.users.detail(String(id!)),
    queryFn: () => fetchUser(id!),
    enabled: id !== undefined,
  });
}

/**
 * 创建用户
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserRequest) => createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.lists(),
      });
    },
  });
}

/**
 * 更新用户
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) =>
      updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.lists(),
      });
    },
  });
}
