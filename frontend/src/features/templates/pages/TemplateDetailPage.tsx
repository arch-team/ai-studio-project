/**
 * Template Detail Page
 *
 * 模板详情页面
 */

import {
  Badge,
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  KeyValuePairs,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { InlineErrorState, PageLayout } from '@shared/components';
import { useDeleteJobTemplate, useJobTemplate } from '../api';
import {
  DISTRIBUTION_STRATEGY_LABELS,
  VISIBILITY_COLORS,
  VISIBILITY_LABELS,
} from '../types';

/**
 * 模板详情页面
 */
export function TemplateDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const templateId = id ? parseInt(id, 10) : undefined;

  const { data: template, isLoading, error, refetch } = useJobTemplate(templateId);

  // 面包屑（模板名加载后更新）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '任务模板', href: '/job-templates' },
      { text: template?.name ?? '模板详情', href: '#' },
    ],
    [template?.name],
  );
  const deleteTemplate = useDeleteJobTemplate();

  const handleUseTemplate = useCallback(() => {
    if (templateId) {
      navigate(`/training-jobs/create?template=${templateId}`);
    }
  }, [navigate, templateId]);

  const handleEditTemplate = useCallback(() => {
    if (templateId) {
      navigate(`/job-templates/${templateId}/edit`);
    }
  }, [navigate, templateId]);

  const handleDeleteTemplate = useCallback(async () => {
    if (templateId && window.confirm('确定要删除此模板吗？')) {
      try {
        await deleteTemplate.mutateAsync(templateId);
        navigate('/job-templates');
      } catch (err) {
        console.error('删除模板失败:', err);
      }
    }
  }, [deleteTemplate, navigate, templateId]);

  const handleBack = useCallback(() => {
    navigate('/job-templates');
  }, [navigate]);

  // 加载态：保留稳定居中 Spinner + 文案，避免整页塌缩
  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误 或 !template 态：保留 PageLayout 骨架（标题/面包屑），内放 InlineErrorState
  if (error || !template) {
    return (
      <PageLayout title="模板详情" breadcrumbs={breadcrumbs}>
        <InlineErrorState
          title={error ? '加载失败' : '模板不存在'}
          message={error?.message ?? '未找到该模板，它可能已被删除。'}
          onRetry={error ? () => refetch() : undefined}
        />
      </PageLayout>
    );
  }

  const config = template.training_config;

  return (
    <PageLayout
      title={template.name}
      description={template.description || '训练任务配置模板详情'}
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button onClick={handleBack}>返回</Button>
          <Button onClick={handleEditTemplate}>编辑</Button>
          <Button
            onClick={handleDeleteTemplate}
            loading={deleteTemplate.isPending}
          >
            删除
          </Button>
          <Button variant="primary" onClick={handleUseTemplate}>
            使用此模板
          </Button>
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l">
      {/* 基本信息 */}
      <Container header={<Header variant="h2">基本信息</Header>}>
        <ColumnLayout columns={2} variant="text-grid">
          <KeyValuePairs
            items={[
              {
                label: '模板名称',
                value: template.name,
              },
              {
                label: '可见性',
                value: (
                  <Badge color={VISIBILITY_COLORS[template.visibility]}>
                    {VISIBILITY_LABELS[template.visibility]}
                  </Badge>
                ),
              },
              {
                label: '使用次数',
                value: template.usage_count,
              },
              {
                label: '创建时间',
                value: new Date(template.created_at).toLocaleString('zh-CN'),
              },
            ]}
          />
          <KeyValuePairs
            items={[
              {
                label: '描述',
                value: template.description || '-',
              },
              {
                label: '最后使用时间',
                value: template.last_used_at
                  ? new Date(template.last_used_at).toLocaleString('zh-CN')
                  : '-',
              },
              {
                label: '更新时间',
                value: new Date(template.updated_at).toLocaleString('zh-CN'),
              },
            ]}
          />
        </ColumnLayout>
      </Container>

      {/* 训练配置 */}
      <Container header={<Header variant="h2">训练配置</Header>}>
        <ColumnLayout columns={2} variant="text-grid">
          <KeyValuePairs
            items={[
              {
                label: '镜像',
                value: config.image,
              },
              {
                label: '实例类型',
                value: config.instance_type,
              },
              {
                label: '实例数量',
                value: config.instance_count,
              },
              {
                label: '分布式策略',
                value:
                  DISTRIBUTION_STRATEGY_LABELS[config.distribution_strategy] ||
                  config.distribution_strategy,
              },
            ]}
          />
          <KeyValuePairs
            items={[
              {
                label: '脚本路径',
                value: config.script_path || '-',
              },
              {
                label: '环境变量',
                value: config.environment
                  ? Object.keys(config.environment).length + ' 个变量'
                  : '-',
              },
              {
                label: '超参数',
                value: config.hyperparameters
                  ? Object.keys(config.hyperparameters).length + ' 个参数'
                  : '-',
              },
            ]}
          />
        </ColumnLayout>
      </Container>

      {/* 环境变量详情 */}
      {config.environment && Object.keys(config.environment).length > 0 && (
        <Container header={<Header variant="h2">环境变量</Header>}>
          <KeyValuePairs
            items={Object.entries(config.environment).map(([key, value]) => ({
              label: key,
              value: value,
            }))}
          />
        </Container>
      )}

      {/* 超参数详情 */}
      {config.hyperparameters &&
        Object.keys(config.hyperparameters).length > 0 && (
          <Container header={<Header variant="h2">超参数</Header>}>
            <KeyValuePairs
              items={Object.entries(config.hyperparameters).map(
                ([key, value]) => ({
                  label: key,
                  value: String(value),
                })
              )}
            />
          </Container>
        )}
    </SpaceBetween>
    </PageLayout>
  );
}

export default TemplateDetailPage;
