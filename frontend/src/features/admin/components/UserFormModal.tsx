/**
 * User Form Modal
 *
 * 用户表单弹窗 - 用于创建/编辑用户
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Form,
  FormField,
  Input,
  Modal,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import type {
  UserDetail,
  CreateUserRequest,
  UpdateUserRequest,
  UserRole,
  UserStatus,
} from '../types';
import { USER_ROLE_LABELS, USER_STATUS_LABELS } from '../types';

interface UserFormModalProps {
  visible: boolean;
  onDismiss: () => void;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => void;
  editingUser?: UserDetail | null;
  isLoading?: boolean;
}

interface FormState {
  username: string;
  email: string;
  role: UserRole | null;
  status: UserStatus | null;
}

interface FormErrors {
  username?: string;
  email?: string;
  role?: string;
  status?: string;
}

const initialFormState: FormState = {
  username: '',
  email: '',
  role: null,
  status: 'active',
};

const roleOptions = Object.entries(USER_ROLE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const statusOptions = Object.entries(USER_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function UserFormModal({
  visible,
  onDismiss,
  onSubmit,
  editingUser,
  isLoading = false,
}: UserFormModalProps) {
  const [formState, setFormState] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FormErrors>({});

  const isEditing = !!editingUser;

  // 编辑时加载现有数据
  useEffect(() => {
    if (editingUser) {
      setFormState({
        username: editingUser.username,
        email: editingUser.email,
        role: editingUser.role,
        status: editingUser.status,
      });
    } else {
      setFormState(initialFormState);
    }
    setErrors({});
  }, [editingUser, visible]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formState.username.trim()) {
      newErrors.username = '用户名不能为空';
    } else if (formState.username.length < 3) {
      newErrors.username = '用户名至少 3 个字符';
    }

    if (!formState.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formState.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }

    if (!formState.role) {
      newErrors.role = '请选择角色';
    }

    if (isEditing && !formState.status) {
      newErrors.status = '请选择状态';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    if (isEditing) {
      const data: UpdateUserRequest = {
        username: formState.username.trim(),
        email: formState.email.trim(),
        role: formState.role!,
        status: formState.status!,
      };
      onSubmit(data);
    } else {
      const data: CreateUserRequest = {
        username: formState.username.trim(),
        email: formState.email.trim(),
        role: formState.role!,
      };
      onSubmit(data);
    }
  };

  const handleDismiss = () => {
    setFormState(initialFormState);
    setErrors({});
    onDismiss();
  };

  return (
    <Modal
      visible={visible}
      onDismiss={handleDismiss}
      header={isEditing ? '编辑用户' : '新建用户'}
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={handleDismiss}>
              取消
            </Button>
            <Button variant="primary" onClick={handleSubmit} loading={isLoading}>
              {isEditing ? '保存' : '创建'}
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <Form>
        <SpaceBetween size="l">
          <FormField
            label="用户名"
            errorText={errors.username}
            constraintText="用于登录和显示，至少 3 个字符"
          >
            <Input
              value={formState.username}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, username: detail.value }))
              }
              placeholder="例如：zhangsan"
              ariaLabel="用户名"
            />
          </FormField>

          <FormField
            label="邮箱"
            errorText={errors.email}
            constraintText="用于通知和找回密码"
          >
            <Input
              type="email"
              value={formState.email}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, email: detail.value }))
              }
              placeholder="例如：zhangsan@company.com"
              ariaLabel="邮箱"
            />
          </FormField>

          <FormField label="角色" errorText={errors.role}>
            <Select
              selectedOption={
                formState.role
                  ? { value: formState.role, label: USER_ROLE_LABELS[formState.role] }
                  : null
              }
              onChange={({ detail }) =>
                setFormState((prev) => ({
                  ...prev,
                  role: detail.selectedOption.value as UserRole,
                }))
              }
              options={roleOptions}
              placeholder="选择角色"
              ariaLabel="角色"
            />
          </FormField>

          {isEditing && (
            <FormField label="状态" errorText={errors.status}>
              <Select
                selectedOption={
                  formState.status
                    ? { value: formState.status, label: USER_STATUS_LABELS[formState.status] }
                    : null
                }
                onChange={({ detail }) =>
                  setFormState((prev) => ({
                    ...prev,
                    status: detail.selectedOption.value as UserStatus,
                  }))
                }
                options={statusOptions}
                placeholder="选择状态"
                ariaLabel="状态"
              />
            </FormField>
          )}
        </SpaceBetween>
      </Form>
    </Modal>
  );
}

export default UserFormModal;
