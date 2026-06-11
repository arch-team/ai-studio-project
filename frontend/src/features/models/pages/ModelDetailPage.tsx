/**
 * Model Detail Page
 *
 * 模型详情页面 - 显示模型元数据、指标、超参数和关联训练任务
 */

import {
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  KeyValuePairs,
  Link,
  SpaceBetween,
  Spinner,
  Tabs,
} from '@cloudscape-design/components';
import { useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useModel, useArchiveModel, useRestoreModel } from '../api';
import { ModelStatusBadge, RegistrySyncStatus } from '../components';
import { MODEL_FRAMEWORK_LABELS } from '../types';

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 格式化 JSON 对象为可读文本
 */
function formatJson(obj: Record<string, unknown> | null | undefined): string {
  if (!obj || Object.keys(obj).length === 0) return '-';
  return JSON.stringify(obj, null, 2);
}

/**
 * 模型详情页面
 */
export function ModelDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const modelId = id ? parseInt(id, 10) : undefined;

  // 获取模型详情
  const { data: model, isLoading, error, refetch } = useModel(modelId);

  // 面包屑（模型名加载后更新）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '模型管理', href: '/models' },
      { text: model?.model_name ?? '模型详情', href: '#' },
    ],
    [model?.model_name],
  );

  // Mutations
  const archiveMutation = useArchiveModel();
  const restoreMutation = useRestoreModel();

  // 判断是否可以归档
  const canArchive = model?.status !== 'archived' && model?.status !== 'training';
  // 判断是否可以恢复
  const canRestore = model?.status === 'archived';

  // 归档模型
  const handleArchive = useCallback(async () => {
    if (!modelId) return;
    await archiveMutation.mutateAsync(modelId);
    refetch();
  }, [modelId, archiveMutation, refetch]);

  // 恢复模型
  const handleRestore = useCallback(async () => {
    if (!modelId) return;
    await restoreMutation.mutateAsync(modelId);
    refetch();
  }, [modelId, restoreMutation, refetch]);

  // 加载状态
  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态
  if (error || !model) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          {error?.message || '模型不存在'}
        </Box>
      </Container>
    );
  }

  return (
    <PageLayout
      title={model.model_name}
      description={model.description || '模型详情、指标与版本信息'}
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button onClick={() => navigate(`/models/${modelId}/versions`)}>
            版本历史
          </Button>
          {canArchive && (
            <Button onClick={handleArchive} loading={archiveMutation.isPending}>
              归档
            </Button>
          )}
          {canRestore && (
            <Button
              variant="primary"
              onClick={handleRestore}
              loading={restoreMutation.isPending}
            >
              恢复
            </Button>
          )}
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l">
      {/* 概览信息 */}
      <Container header={<Header variant="h2">概览</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">状态</Box>
            <ModelStatusBadge status={model.status} />
          </div>
          <div>
            <Box variant="awsui-key-label">版本</Box>
            <Box>{model.version || '-'}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">框架</Box>
            <Box>
              {model.framework ? MODEL_FRAMEWORK_LABELS[model.framework] : '-'}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Registry 同步</Box>
            <RegistrySyncStatus model={model} />
          </div>
        </ColumnLayout>
      </Container>

      {/* 关联训练任务 */}
      {model.training_job_id && (
        <Container header={<Header variant="h2">关联训练任务</Header>}>
          <SpaceBetween size="s">
            <Box>
              <Box variant="awsui-key-label">训练任务 ID</Box>
              <Link href={`/training-jobs/${model.training_job_id}`}>
                #{model.training_job_id}
              </Link>
            </Box>
            {model.checkpoint_id && (
              <Box>
                <Box variant="awsui-key-label">检查点 ID</Box>
                <Box>#{model.checkpoint_id}</Box>
              </Box>
            )}
          </SpaceBetween>
        </Container>
      )}

      {/* 详细信息标签页 */}
      <Tabs
        tabs={[
          {
            id: 'info',
            label: '基本信息',
            content: (
              <Container>
                <KeyValuePairs
                  columns={2}
                  items={[
                    { label: '模型 ID', value: String(model.id) },
                    { label: '模型名称', value: model.model_name },
                    { label: '版本', value: model.version || '-' },
                    { label: '描述', value: model.description || '-' },
                    {
                      label: '框架',
                      value: model.framework
                        ? MODEL_FRAMEWORK_LABELS[model.framework]
                        : '-',
                    },
                    { label: '模型路径', value: model.model_path || '-' },
                    { label: 'Registry ARN', value: model.registry_arn || '-' },
                    { label: '创建时间', value: formatDateTime(model.created_at) },
                    { label: '更新时间', value: formatDateTime(model.updated_at) },
                  ]}
                />
              </Container>
            ),
          },
          {
            id: 'metrics',
            label: '训练指标',
            content: (
              <Container>
                {model.metrics && Object.keys(model.metrics).length > 0 ? (
                  <KeyValuePairs
                    columns={3}
                    items={Object.entries(model.metrics).map(([key, value]) => ({
                      label: key,
                      value:
                        typeof value === 'number' ? value.toFixed(6) : String(value),
                    }))}
                  />
                ) : (
                  <Box textAlign="center" color="text-body-secondary" padding="l">
                    暂无训练指标数据
                  </Box>
                )}
              </Container>
            ),
          },
          {
            id: 'hyperparameters',
            label: '超参数',
            content: (
              <Container>
                {model.hyperparameters &&
                Object.keys(model.hyperparameters).length > 0 ? (
                  <Box fontSize="body-s">
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                      {formatJson(model.hyperparameters)}
                    </pre>
                  </Box>
                ) : (
                  <Box textAlign="center" color="text-body-secondary" padding="l">
                    暂无超参数数据
                  </Box>
                )}
              </Container>
            ),
          },
        ]}
      />
    </SpaceBetween>
    </PageLayout>
  );
}

export default ModelDetailPage;
