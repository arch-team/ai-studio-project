/**
 * Create Dataset Page
 *
 * 注册数据集页面 - 填写数据集信息并提交注册
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
  StatusIndicator,
  Textarea,
  TokenGroup,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useCreateDataset } from '../api';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '数据集', href: '/datasets' },
  { text: '注册数据集', href: '#' },
];
import type {
  CreateDatasetRequest,
  StorageType,
  DatasetType,
  DatasetVisibility,
} from '../types';
import {
  STORAGE_TYPE_LABELS,
  DATASET_TYPE_LABELS,
  VISIBILITY_LABELS,
} from '../types';

// 存储类型选项
const storageTypeOptions = Object.entries(STORAGE_TYPE_LABELS).map(
  ([value, label]) => ({
    label,
    value,
  })
);

// 数据类型选项
const datasetTypeOptions = Object.entries(DATASET_TYPE_LABELS).map(
  ([value, label]) => ({
    label,
    value,
  })
);

// 可见性选项
const visibilityOptions = Object.entries(VISIBILITY_LABELS).map(
  ([value, label]) => ({
    label,
    value,
  })
);

/**
 * 表单验证
 */
function validateForm(values: {
  name: string;
  storageType: string;
  storageUri: string;
  datasetType: string;
}): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!values.name.trim()) {
    errors.name = '请输入数据集名称';
  } else if (values.name.trim().length < 3) {
    errors.name = '数据集名称至少 3 个字符';
  } else if (values.name.trim().length > 128) {
    errors.name = '数据集名称不能超过 128 个字符';
  }

  if (!values.storageType) {
    errors.storageType = '请选择存储类型';
  }

  if (!values.storageUri.trim()) {
    errors.storageUri = '请输入存储路径';
  }

  if (!values.datasetType) {
    errors.datasetType = '请选择数据类型';
  }

  return errors;
}

/**
 * 注册数据集页面
 */
export function CreateDatasetPage() {
  const navigate = useNavigate();
  const createMutation = useCreateDataset();

  // 表单状态
  const [name, setName] = useState('');
  const [version, setVersion] = useState('v1');
  const [description, setDescription] = useState('');
  const [storageType, setStorageType] = useState<string>('');
  const [storageUri, setStorageUri] = useState('');
  const [datasetType, setDatasetType] = useState<string>('');
  const [dataFormat, setDataFormat] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [visibility, setVisibility] = useState<string>('private');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 取消创建
  const handleCancel = useCallback(() => {
    navigate('/datasets');
  }, [navigate]);

  // 添加标签
  const handleAddTag = useCallback(() => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags((prev) => [...prev, trimmed]);
      setTagInput('');
    }
  }, [tagInput, tags]);

  // 标签输入回车处理
  const handleTagKeyDown = useCallback(
    (event: CustomEvent<{ keyCode: number }>) => {
      if (event.detail.keyCode === 13) {
        handleAddTag();
      }
    },
    [handleAddTag]
  );

  // 移除标签
  const handleRemoveTag = useCallback(
    (itemIndex: number) => {
      setTags((prev) => prev.filter((_, index) => index !== itemIndex));
    },
    []
  );

  // 提交表单
  const handleSubmit = useCallback(async () => {
    // 表单验证
    const validationErrors = validateForm({
      name,
      storageType,
      storageUri,
      datasetType,
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});

    // 构建请求数据
    const requestData: CreateDatasetRequest = {
      name: name.trim(),
      version: version.trim() || 'v1',
      description: description.trim() || undefined,
      storage_type: storageType as StorageType,
      storage_uri: storageUri.trim(),
      dataset_type: datasetType as DatasetType,
      data_format: dataFormat.trim() || undefined,
      tags: tags.length > 0 ? tags : undefined,
      visibility: visibility as DatasetVisibility,
    };

    try {
      const result = await createMutation.mutateAsync(requestData);
      // 创建成功后跳转到详情页
      navigate(`/datasets/${result.id}`);
    } catch (error) {
      // 错误处理由 mutation 的 onError 处理
      console.error('注册数据集失败:', error);
    }
  }, [
    name,
    version,
    description,
    storageType,
    storageUri,
    datasetType,
    dataFormat,
    tags,
    visibility,
    createMutation,
    navigate,
  ]);

  return (
    <PageLayout
      title="注册数据集"
      description="注册数据集元数据并指定存储位置与可见范围"
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
              注册数据集
            </Button>
          </SpaceBetween>
        }
      >
        <SpaceBetween size="l">
          {/* 基本信息 */}
          <Container header={<Header variant="h2">基本信息</Header>}>
            <SpaceBetween size="m">
              <FormField
                label="数据集名称"
                errorText={errors.name}
                constraintText="必填，3-128 个字符"
              >
                <Input
                  value={name}
                  onChange={({ detail }) => setName(detail.value)}
                  placeholder="my-dataset"
                />
              </FormField>

              <FormField
                label="版本"
                constraintText="默认 v1"
              >
                <Input
                  value={version}
                  onChange={({ detail }) => setVersion(detail.value)}
                  placeholder="v1"
                />
              </FormField>

              <FormField label="描述" constraintText="可选">
                <Textarea
                  value={description}
                  onChange={({ detail }) => setDescription(detail.value)}
                  placeholder="数据集描述..."
                  rows={3}
                />
              </FormField>
            </SpaceBetween>
          </Container>

          {/* 存储配置 */}
          <Container header={<Header variant="h2">存储配置</Header>}>
            <SpaceBetween size="m">
              <FormField
                label="存储类型"
                errorText={errors.storageType}
                constraintText="必填"
              >
                <Select
                  selectedOption={
                    storageTypeOptions.find(
                      (opt) => opt.value === storageType
                    ) || null
                  }
                  onChange={({ detail }) =>
                    setStorageType(detail.selectedOption.value || '')
                  }
                  options={storageTypeOptions}
                  placeholder="选择存储类型"
                />
              </FormField>

              <FormField
                label="存储路径"
                errorText={errors.storageUri}
                constraintText="必填"
              >
                <Input
                  value={storageUri}
                  onChange={({ detail }) => setStorageUri(detail.value)}
                  placeholder="s3://my-bucket/datasets/"
                />
              </FormField>
            </SpaceBetween>
          </Container>

          {/* 数据配置 */}
          <Container header={<Header variant="h2">数据配置</Header>}>
            <SpaceBetween size="m">
              <FormField
                label="数据类型"
                errorText={errors.datasetType}
                constraintText="必填"
              >
                <Select
                  selectedOption={
                    datasetTypeOptions.find(
                      (opt) => opt.value === datasetType
                    ) || null
                  }
                  onChange={({ detail }) =>
                    setDatasetType(detail.selectedOption.value || '')
                  }
                  options={datasetTypeOptions}
                  placeholder="选择数据类型"
                />
              </FormField>

              <FormField
                label="数据格式"
                constraintText="可选"
              >
                <Input
                  value={dataFormat}
                  onChange={({ detail }) => setDataFormat(detail.value)}
                  placeholder="imagenet, csv, jsonl..."
                />
              </FormField>
            </SpaceBetween>
          </Container>

          {/* 标签和可见性 */}
          <Container header={<Header variant="h2">标签和可见性</Header>}>
            <SpaceBetween size="m">
              <FormField
                label="标签"
                constraintText="可选，输入后按回车添加"
              >
                <SpaceBetween size="xs">
                  <SpaceBetween direction="horizontal" size="xs">
                    <Input
                      value={tagInput}
                      onChange={({ detail }) => setTagInput(detail.value)}
                      onKeyDown={handleTagKeyDown}
                      placeholder="输入标签..."
                    />
                    <Button onClick={handleAddTag}>添加</Button>
                  </SpaceBetween>
                  {tags.length > 0 && (
                    <TokenGroup
                      items={tags.map((tag) => ({ label: tag }))}
                      onDismiss={({ detail }) =>
                        handleRemoveTag(detail.itemIndex)
                      }
                    />
                  )}
                </SpaceBetween>
              </FormField>

              <FormField
                label="可见性"
                constraintText="默认私有"
              >
                <Select
                  selectedOption={
                    visibilityOptions.find(
                      (opt) => opt.value === visibility
                    ) || visibilityOptions[1]
                  }
                  onChange={({ detail }) =>
                    setVisibility(detail.selectedOption.value || 'private')
                  }
                  options={visibilityOptions}
                />
              </FormField>
            </SpaceBetween>
          </Container>

          {/* 文件上传（可选） */}
          <Container header={<Header variant="h2">文件上传（可选）</Header>}>
            <Box padding="m">
              <StatusIndicator type="info">
                数据集创建成功后，可在详情页上传数据文件
              </StatusIndicator>
            </Box>
          </Container>
        </SpaceBetween>
      </Form>

      {/* 错误提示 */}
      {createMutation.isError && (
        <Alert type="error" header="注册失败">
          {createMutation.error?.message || '未知错误，请稍后重试'}
        </Alert>
      )}
    </SpaceBetween>
    </PageLayout>
  );
}

export default CreateDatasetPage;
