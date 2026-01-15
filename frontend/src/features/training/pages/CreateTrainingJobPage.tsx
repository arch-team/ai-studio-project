/**
 * Create Training Job Page
 *
 * 创建训练任务页面
 */

import {
  Box,
  BreadcrumbGroup,
  Container,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateTrainingJob } from '../api';
import { TrainingJobForm } from '../components/TrainingJobForm';
import type { CreateTrainingJobRequest } from '../types';

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
    <SpaceBetween size="l">
      {/* 面包屑导航 */}
      <BreadcrumbGroup
        items={[
          { text: '训练任务', href: '/training-jobs' },
          { text: '创建训练任务', href: '#' },
        ]}
        onFollow={(e) => {
          e.preventDefault();
          if (e.detail.href !== '#') {
            navigate(e.detail.href);
          }
        }}
      />

      {/* 页面标题 */}
      <Header variant="h1">创建训练任务</Header>

      {/* 创建表单 */}
      <TrainingJobForm
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isSubmitting={createMutation.isPending}
      />

      {/* 错误提示 */}
      {createMutation.isError && (
        <Container>
          <Box color="text-status-error">
            创建失败: {createMutation.error?.message || '未知错误'}
          </Box>
        </Container>
      )}
    </SpaceBetween>
  );
}

export default CreateTrainingJobPage;
