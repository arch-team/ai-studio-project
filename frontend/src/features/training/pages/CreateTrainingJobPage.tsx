/**
 * Create Training Job Page
 *
 * 创建训练任务页面
 */

import { Alert, SpaceBetween } from '@cloudscape-design/components';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useCreateTrainingJob } from '../api';
import { TrainingJobForm } from '../components/TrainingJobForm';
import type { CreateTrainingJobRequest } from '../types';

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '训练任务', href: '/training-jobs' },
  { text: '创建训练任务', href: '#' },
];

/**
 * 创建训练任务页面
 */
export function CreateTrainingJobPage() {
  const navigate = useNavigate();
  const createMutation = useCreateTrainingJob();

  // 取消创建
  const handleCancel = useCallback(() => {
    navigate('/training-jobs');
  }, [navigate]);

  // 提交创建
  const handleSubmit = useCallback(
    async (data: CreateTrainingJobRequest) => {
      try {
        const result = await createMutation.mutateAsync(data);
        // 创建成功后跳转到详情页
        navigate(`/training-jobs/${result.id}`);
      } catch (error) {
        // 错误处理由 mutation 的 onError 处理
        console.error('创建训练任务失败:', error);
      }
    },
    [createMutation, navigate]
  );

  return (
    <PageLayout
      title="创建训练任务"
      description="配置并提交 DDP / FSDP / DeepSpeed 分布式训练任务"
      breadcrumbs={BREADCRUMBS}
    >
      <SpaceBetween size="l">
        {/* 错误提示 */}
        {createMutation.isError && (
          <Alert type="error" header="创建失败">
            {createMutation.error?.message || '未知错误'}
          </Alert>
        )}

        {/* 创建表单 */}
        <TrainingJobForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isSubmitting={createMutation.isPending}
        />
      </SpaceBetween>
    </PageLayout>
  );
}

export default CreateTrainingJobPage;
