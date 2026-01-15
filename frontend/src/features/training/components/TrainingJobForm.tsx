/**
 * Training Job Form Component
 *
 * 训练任务创建/编辑表单组件
 */

import {
  Box,
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  Select,
  SpaceBetween,
  Textarea,
  Tiles,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import type {
  CreateTrainingJobRequest,
  JobPriority,
  DistributionStrategy,
} from '../types';
import {
  JOB_PRIORITY_LABELS,
  DISTRIBUTION_STRATEGY_LABELS,
  INSTANCE_TYPES,
} from '../types';

interface TrainingJobFormProps {
  initialValues?: Partial<CreateTrainingJobRequest>;
  onSubmit: (data: CreateTrainingJobRequest) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

// 优先级选项
const priorityOptions = Object.entries(JOB_PRIORITY_LABELS).map(([value, label]) => ({
  label,
  value,
}));

// 分布式策略选项
const strategyTiles = Object.entries(DISTRIBUTION_STRATEGY_LABELS).map(
  ([value, label]) => ({
    value,
    label,
    description: getStrategyDescription(value as DistributionStrategy),
  })
);

// 实例类型选项
const instanceTypeOptions = INSTANCE_TYPES.map((type) => ({
  label: type,
  value: type,
}));

/**
 * 获取分布式策略描述
 */
function getStrategyDescription(strategy: DistributionStrategy): string {
  const descriptions: Record<DistributionStrategy, string> = {
    ddp: 'PyTorch 原生分布式数据并行，适合中小规模训练',
    fsdp: '完全分片数据并行，支持大模型训练',
    deepspeed: '微软 DeepSpeed，支持 ZeRO 优化和大规模分布式训练',
    horovod: 'Uber Horovod，跨框架分布式训练',
  };
  return descriptions[strategy];
}

/**
 * 表单验证
 */
function validateForm(values: Partial<CreateTrainingJobRequest>): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!values.job_name?.trim()) {
    errors.job_name = '请输入任务名称';
  } else if (values.job_name.length > 100) {
    errors.job_name = '任务名称不能超过 100 个字符';
  }

  if (!values.image_uri?.trim()) {
    errors.image_uri = '请输入容器镜像 URI';
  }

  if (!values.entry_point?.trim()) {
    errors.entry_point = '请输入训练脚本路径';
  }

  if (values.node_count != null && (values.node_count < 1 || values.node_count > 64)) {
    errors.node_count = '节点数量必须在 1-64 之间';
  }

  if (values.gpu_per_node != null && (values.gpu_per_node < 0 || values.gpu_per_node > 8)) {
    errors.gpu_per_node = '每节点 GPU 数量必须在 0-8 之间';
  }

  return errors;
}

/**
 * 训练任务表单组件
 */
export function TrainingJobForm({
  initialValues = {},
  onSubmit,
  onCancel,
  isSubmitting = false,
}: TrainingJobFormProps) {
  // 表单状态
  const [jobName, setJobName] = useState(initialValues.job_name || '');
  const [description, setDescription] = useState(initialValues.description || '');
  const [imageUri, setImageUri] = useState(initialValues.image_uri || '');
  const [entryPoint, setEntryPoint] = useState(initialValues.entry_point || '');
  const [priority, setPriority] = useState<JobPriority>(initialValues.priority || 'medium');
  const [strategy, setStrategy] = useState<DistributionStrategy>(
    initialValues.distribution_strategy || 'ddp'
  );
  const [instanceType, setInstanceType] = useState(
    initialValues.instance_type || 'ml.p4d.24xlarge'
  );
  const [nodeCount, setNodeCount] = useState(String(initialValues.node_count || 1));
  const [gpuPerNode, setGpuPerNode] = useState(String(initialValues.gpu_per_node || 8));
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 构建表单数据
  const buildFormData = useCallback((): Partial<CreateTrainingJobRequest> => {
    return {
      job_name: jobName,
      description: description || undefined,
      image_uri: imageUri,
      entry_point: entryPoint,
      priority,
      distribution_strategy: strategy,
      instance_type: instanceType,
      node_count: parseInt(nodeCount, 10) || 1,
      gpu_per_node: parseInt(gpuPerNode, 10) || 8,
    };
  }, [
    jobName,
    description,
    imageUri,
    entryPoint,
    priority,
    strategy,
    instanceType,
    nodeCount,
    gpuPerNode,
  ]);

  // 提交表单
  const handleSubmit = useCallback(() => {
    const formData = buildFormData();
    const validationErrors = validateForm(formData);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    onSubmit(formData as CreateTrainingJobRequest);
  }, [buildFormData, onSubmit]);

  return (
    <Form
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button variant="link" onClick={onCancel} disabled={isSubmitting}>
            取消
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            loading={isSubmitting}
          >
            创建任务
          </Button>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {/* 基础配置 */}
        <Container header={<Header variant="h2">基础配置</Header>}>
          <SpaceBetween size="m">
            <FormField
              label="任务名称"
              errorText={errors.job_name}
              constraintText="必填，最多 100 个字符"
            >
              <Input
                value={jobName}
                onChange={({ detail }) => setJobName(detail.value)}
                placeholder="my-training-job"
              />
            </FormField>

            <FormField label="描述" constraintText="可选">
              <Textarea
                value={description}
                onChange={({ detail }) => setDescription(detail.value)}
                placeholder="训练任务描述..."
                rows={3}
              />
            </FormField>

            <FormField
              label="优先级"
              constraintText="高优先级任务将优先获得资源"
            >
              <Select
                selectedOption={
                  priorityOptions.find((opt) => opt.value === priority) ||
                  priorityOptions[1]
                }
                onChange={({ detail }) =>
                  setPriority(detail.selectedOption.value as JobPriority)
                }
                options={priorityOptions}
              />
            </FormField>
          </SpaceBetween>
        </Container>

        {/* 容器配置 */}
        <Container header={<Header variant="h2">容器配置</Header>}>
          <SpaceBetween size="m">
            <FormField
              label="容器镜像 URI"
              errorText={errors.image_uri}
              constraintText="必填，ECR 镜像地址"
            >
              <Input
                value={imageUri}
                onChange={({ detail }) => setImageUri(detail.value)}
                placeholder="123456789012.dkr.ecr.us-west-2.amazonaws.com/my-training:latest"
              />
            </FormField>

            <FormField
              label="训练脚本路径"
              errorText={errors.entry_point}
              constraintText="必填，容器内脚本路径"
            >
              <Input
                value={entryPoint}
                onChange={({ detail }) => setEntryPoint(detail.value)}
                placeholder="/opt/ml/code/train.py"
              />
            </FormField>
          </SpaceBetween>
        </Container>

        {/* 分布式配置 */}
        <Container header={<Header variant="h2">分布式配置</Header>}>
          <SpaceBetween size="m">
            <FormField label="分布式策略">
              <Tiles
                value={strategy}
                onChange={({ detail }) =>
                  setStrategy(detail.value as DistributionStrategy)
                }
                items={strategyTiles}
              />
            </FormField>

            <FormField label="实例类型">
              <Select
                selectedOption={
                  instanceTypeOptions.find((opt) => opt.value === instanceType) ||
                  instanceTypeOptions[0]
                }
                onChange={({ detail }) =>
                  setInstanceType(detail.selectedOption.value || '')
                }
                options={instanceTypeOptions}
              />
            </FormField>

            <SpaceBetween direction="horizontal" size="m">
              <FormField
                label="节点数量"
                errorText={errors.node_count}
                constraintText="1-64"
              >
                <Input
                  type="number"
                  value={nodeCount}
                  onChange={({ detail }) => setNodeCount(detail.value)}
                />
              </FormField>

              <FormField
                label="每节点 GPU 数量"
                errorText={errors.gpu_per_node}
                constraintText="0-8"
              >
                <Input
                  type="number"
                  value={gpuPerNode}
                  onChange={({ detail }) => setGpuPerNode(detail.value)}
                />
              </FormField>
            </SpaceBetween>

            <Box color="text-body-secondary">
              <b>总资源:</b> {parseInt(nodeCount, 10) || 1} 节点 ×{' '}
              {parseInt(gpuPerNode, 10) || 8} GPU ={' '}
              {(parseInt(nodeCount, 10) || 1) * (parseInt(gpuPerNode, 10) || 8)} GPU
            </Box>
          </SpaceBetween>
        </Container>
      </SpaceBetween>
    </Form>
  );
}

export default TrainingJobForm;
