/**
 * Create Space Page
 *
 * 创建开发空间页面
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useCreateSpace } from '../api';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '开发空间', href: '/spaces' },
  { text: '创建开发空间', href: '#' },
];
import type { SpaceType, SpaceInstanceType, SpaceBackend, CreateSpaceRequest } from '../types';
import { SPACE_TYPE_LABELS, INSTANCE_TYPE_LABELS, SPACE_BACKEND_LABELS } from '../types';

// 环境类型选项（SageMaker Studio / HyperPod 集群）
const backendOptions = Object.entries(SPACE_BACKEND_LABELS).map(
  ([value, label]) => ({ label, value })
);

// IDE 类型选项（与后端 SpaceTypeEnum 一致）
const spaceTypeOptions = Object.entries(SPACE_TYPE_LABELS).map(
  ([value, label]) => ({ label, value })
);

// 实例类型选项（与后端 SpaceInstanceTypeEnum 一致，越界值会被 422 拒绝）
const instanceTypeOptions = Object.entries(INSTANCE_TYPE_LABELS).map(
  ([value, label]) => ({ label, value })
);

/**
 * 表单验证（约束与后端 CreateSpaceRequest 对齐: 名称 3-63 字符）
 */
function validateForm(values: {
  name: string;
  backend: string;
  spaceType: string;
  instanceType: string;
  storageGb: string;
}): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!values.name.trim()) {
    errors.name = '请输入空间名称';
  } else if (values.name.length < 3) {
    errors.name = '空间名称至少 3 个字符';
  } else if (values.name.length > 63) {
    errors.name = '空间名称不能超过 63 个字符';
  } else if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/.test(values.name)) {
    errors.name = '空间名称只能包含小写字母、数字和连字符，且必须以字母或数字开头和结尾';
  }

  if (!values.backend) {
    errors.backend = '请选择环境类型';
  }

  if (!values.spaceType) {
    errors.spaceType = '请选择 IDE 类型';
  }

  if (!values.instanceType) {
    errors.instanceType = '请选择实例类型';
  }

  const storageNum = parseInt(values.storageGb, 10);
  if (isNaN(storageNum) || storageNum < 5 || storageNum > 500) {
    errors.storageGb = '存储大小必须在 5-500 GB 之间';
  }

  return errors;
}

/**
 * 创建开发空间页面
 */
export function CreateSpacePage() {
  const navigate = useNavigate();
  const createMutation = useCreateSpace();

  // 表单状态
  const [name, setName] = useState('');
  const [backend, setBackend] = useState<SpaceBackend>('studio');
  const [spaceType, setSpaceType] = useState<string>('jupyter');
  const [instanceType, setInstanceType] = useState<string>('ml.g5.xlarge');
  const [storageGb, setStorageGb] = useState('10');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 取消创建
  const handleCancel = useCallback(() => {
    navigate('/spaces');
  }, [navigate]);

  // 提交表单
  const handleSubmit = useCallback(async () => {
    const validationErrors = validateForm({
      name,
      backend,
      spaceType,
      instanceType,
      storageGb,
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});

    const request: CreateSpaceRequest = {
      space_name: name,
      backend: backend,
      space_type: spaceType as SpaceType,
      instance_type: instanceType as SpaceInstanceType,
      storage_size_gb: parseInt(storageGb, 10),
    };

    try {
      await createMutation.mutateAsync(request);
      navigate('/spaces');
    } catch (error) {
      // 错误处理由 mutation 的 onError 处理
      console.error('创建开发空间失败:', error);
    }
  }, [name, backend, spaceType, instanceType, storageGb, createMutation, navigate]);

  return (
    <PageLayout
      title="创建开发空间"
      description="启动交互式在线 IDE，支持 JupyterLab / Code Editor"
      breadcrumbs={BREADCRUMBS}
    >
    <SpaceBetween size="l">
      {/* 创建表单 */}
      <Form
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button
              variant="link"
              onClick={handleCancel}
              disabled={createMutation.isPending}
            >
              取消
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              loading={createMutation.isPending}
            >
              创建空间
            </Button>
          </SpaceBetween>
        }
      >
        <Container header={<Header variant="h2">基础配置</Header>}>
          <SpaceBetween size="m">
            <FormField
              label="环境类型"
              errorText={errors.backend}
              constraintText="选择运行环境（SageMaker Studio 或 HyperPod 集群）"
            >
              <Select
                selectedOption={
                  backendOptions.find((opt) => opt.value === backend) ||
                  backendOptions[0]
                }
                onChange={({ detail }) =>
                  setBackend(detail.selectedOption.value as SpaceBackend || 'studio')
                }
                options={backendOptions}
              />
            </FormField>

            {backend === 'hyperpod' && (
              <Alert type="info">
                HyperPod 集群空间将占用团队的 ClusterQueue 配额，空闲资源会被集群自动回收。
              </Alert>
            )}

            <FormField
              label="空间名称"
              errorText={errors.name}
              constraintText="必填，3-63 个字符，小写字母、数字和连字符"
            >
              <Input
                value={name}
                onChange={({ detail }) => setName(detail.value)}
                placeholder="my-dev-space"
              />
            </FormField>

            <FormField
              label="IDE 类型"
              errorText={errors.spaceType}
              constraintText="选择开发环境类型"
            >
              <Select
                selectedOption={
                  spaceTypeOptions.find((opt) => opt.value === spaceType) ||
                  spaceTypeOptions[0]
                }
                onChange={({ detail }) =>
                  setSpaceType(detail.selectedOption.value || 'jupyter')
                }
                options={spaceTypeOptions}
              />
            </FormField>

            <FormField
              label="实例类型"
              errorText={errors.instanceType}
              constraintText="选择计算实例规格"
            >
              <Select
                selectedOption={
                  instanceTypeOptions.find(
                    (opt) => opt.value === instanceType
                  ) || instanceTypeOptions[0]
                }
                onChange={({ detail }) =>
                  setInstanceType(detail.selectedOption.value || 'ml.g5.xlarge')
                }
                options={instanceTypeOptions}
              />
            </FormField>

            <FormField
              label="存储大小 (GB)"
              errorText={errors.storageGb}
              constraintText="5-500 GB，默认 10 GB"
            >
              <Input
                type="number"
                value={storageGb}
                onChange={({ detail }) => setStorageGb(detail.value)}
              />
            </FormField>
          </SpaceBetween>
        </Container>
      </Form>

      {/* 错误提示 */}
      {createMutation.isError && (
        <Container>
          <Box color="text-status-error">
            创建失败: {createMutation.error?.message || '未知错误'}
          </Box>
        </Container>
      )}
    </SpaceBetween>
    </PageLayout>
  );
}

export default CreateSpacePage;
