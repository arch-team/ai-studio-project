/**
 * Quota Form Modal
 *
 * 资源配额表单弹窗 - 用于创建/编辑配额配置
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
  ResourceLimitConfig,
  CreateResourceLimitConfigRequest,
  UpdateResourceLimitConfigRequest,
  UserRole,
  Priority,
} from '../types';
import { ROLE_LABELS, PRIORITY_LABELS } from '../types';

interface QuotaFormModalProps {
  visible: boolean;
  onDismiss: () => void;
  onSubmit: (data: CreateResourceLimitConfigRequest | UpdateResourceLimitConfigRequest) => void;
  editingQuota?: ResourceLimitConfig | null;
  isLoading?: boolean;
}

interface FormState {
  config_name: string;
  role: UserRole | null;
  max_gpu_per_job: string;
  max_cpu_per_job: string;
  max_memory_gb_per_job: string;
  max_storage_gb_per_job: string;
  max_nodes_per_job: string;
  priority_default: Priority | null;
}

interface FormErrors {
  config_name?: string;
  role?: string;
  max_gpu_per_job?: string;
  max_cpu_per_job?: string;
  max_memory_gb_per_job?: string;
  max_storage_gb_per_job?: string;
  max_nodes_per_job?: string;
  priority_default?: string;
}

const initialFormState: FormState = {
  config_name: '',
  role: null,
  max_gpu_per_job: '4',
  max_cpu_per_job: '16',
  max_memory_gb_per_job: '64',
  max_storage_gb_per_job: '200',
  max_nodes_per_job: '2',
  priority_default: null,
};

const roleOptions = Object.entries(ROLE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const priorityOptions = Object.entries(PRIORITY_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function QuotaFormModal({
  visible,
  onDismiss,
  onSubmit,
  editingQuota,
  isLoading = false,
}: QuotaFormModalProps) {
  const [formState, setFormState] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FormErrors>({});

  const isEditing = !!editingQuota;

  // 编辑时加载现有数据
  useEffect(() => {
    if (editingQuota) {
      setFormState({
        config_name: editingQuota.config_name,
        role: editingQuota.role,
        max_gpu_per_job: String(editingQuota.max_gpu_per_job),
        max_cpu_per_job: String(editingQuota.max_cpu_per_job),
        max_memory_gb_per_job: String(editingQuota.max_memory_gb_per_job),
        max_storage_gb_per_job: String(editingQuota.max_storage_gb_per_job),
        max_nodes_per_job: String(editingQuota.max_nodes_per_job),
        priority_default: editingQuota.priority_default,
      });
    } else {
      setFormState(initialFormState);
    }
    setErrors({});
  }, [editingQuota, visible]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formState.config_name.trim()) {
      newErrors.config_name = '配置名称不能为空';
    }

    if (!formState.role) {
      newErrors.role = '请选择适用角色';
    }

    if (!formState.priority_default) {
      newErrors.priority_default = '请选择默认优先级';
    }

    // 数值验证
    const numericFields = [
      { key: 'max_gpu_per_job', label: '最大 GPU', min: 0, max: 1000 },
      { key: 'max_cpu_per_job', label: '最大 CPU', min: 0, max: 10000 },
      { key: 'max_memory_gb_per_job', label: '最大内存', min: 0, max: 10000 },
      { key: 'max_storage_gb_per_job', label: '最大存储', min: 0, max: 100000 },
      { key: 'max_nodes_per_job', label: '最大节点', min: 1, max: 1000 },
    ] as const;

    for (const field of numericFields) {
      const value = parseInt(formState[field.key], 10);
      if (isNaN(value) || value < field.min || value > field.max) {
        newErrors[field.key] = `${field.label}必须是 ${field.min}-${field.max} 之间的整数`;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    const data: CreateResourceLimitConfigRequest = {
      config_name: formState.config_name.trim(),
      role: formState.role!,
      max_gpu_per_job: parseInt(formState.max_gpu_per_job, 10),
      max_cpu_per_job: parseInt(formState.max_cpu_per_job, 10),
      max_memory_gb_per_job: parseInt(formState.max_memory_gb_per_job, 10),
      max_storage_gb_per_job: parseInt(formState.max_storage_gb_per_job, 10),
      max_nodes_per_job: parseInt(formState.max_nodes_per_job, 10),
      priority_default: formState.priority_default!,
    };

    onSubmit(data);
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
      header={isEditing ? '编辑资源配额' : '新建资源配额'}
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
            label="配置名称"
            errorText={errors.config_name}
            constraintText="为此配额配置指定一个唯一的名称"
          >
            <Input
              value={formState.config_name}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, config_name: detail.value }))
              }
              placeholder="例如：高级工程师配额"
              ariaLabel="配置名称"
            />
          </FormField>

          <FormField label="适用角色" errorText={errors.role}>
            <Select
              selectedOption={
                formState.role
                  ? { value: formState.role, label: ROLE_LABELS[formState.role] }
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
              ariaLabel="适用角色"
            />
          </FormField>

          <FormField
            label="最大 GPU/任务"
            errorText={errors.max_gpu_per_job}
            constraintText="单个训练任务可使用的最大 GPU 数量"
          >
            <Input
              type="number"
              value={formState.max_gpu_per_job}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, max_gpu_per_job: detail.value }))
              }
              ariaLabel="最大 GPU"
            />
          </FormField>

          <FormField
            label="最大 CPU/任务"
            errorText={errors.max_cpu_per_job}
            constraintText="单个训练任务可使用的最大 CPU 核数"
          >
            <Input
              type="number"
              value={formState.max_cpu_per_job}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, max_cpu_per_job: detail.value }))
              }
              ariaLabel="最大 CPU"
            />
          </FormField>

          <FormField
            label="最大内存/任务 (GB)"
            errorText={errors.max_memory_gb_per_job}
            constraintText="单个训练任务可使用的最大内存 (GB)"
          >
            <Input
              type="number"
              value={formState.max_memory_gb_per_job}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, max_memory_gb_per_job: detail.value }))
              }
              ariaLabel="最大内存"
            />
          </FormField>

          <FormField
            label="最大存储/任务 (GB)"
            errorText={errors.max_storage_gb_per_job}
            constraintText="单个训练任务可使用的最大存储 (GB)"
          >
            <Input
              type="number"
              value={formState.max_storage_gb_per_job}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, max_storage_gb_per_job: detail.value }))
              }
              ariaLabel="最大存储"
            />
          </FormField>

          <FormField
            label="最大节点/任务"
            errorText={errors.max_nodes_per_job}
            constraintText="单个训练任务可使用的最大计算节点数"
          >
            <Input
              type="number"
              value={formState.max_nodes_per_job}
              onChange={({ detail }) =>
                setFormState((prev) => ({ ...prev, max_nodes_per_job: detail.value }))
              }
              ariaLabel="最大节点"
            />
          </FormField>

          <FormField label="默认优先级" errorText={errors.priority_default}>
            <Select
              selectedOption={
                formState.priority_default
                  ? {
                      value: formState.priority_default,
                      label: PRIORITY_LABELS[formState.priority_default],
                    }
                  : null
              }
              onChange={({ detail }) =>
                setFormState((prev) => ({
                  ...prev,
                  priority_default: detail.selectedOption.value as Priority,
                }))
              }
              options={priorityOptions}
              placeholder="选择优先级"
              ariaLabel="默认优先级"
            />
          </FormField>
        </SpaceBetween>
      </Form>
    </Modal>
  );
}

export default QuotaFormModal;
