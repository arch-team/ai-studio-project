/**
 * Space Detail Page
 *
 * 开发空间详情页面 - 展示空间配置信息并提供启动/停止/删除操作
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Header,
  KeyValuePairs,
  Modal,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { formatDateTime } from '@shared/utils';
import { useSpace, useStartSpace, useStopSpace, useDeleteSpace } from '../api';
import { SpaceStatusBadge } from '../components/SpaceStatusBadge';
import { SPACE_TYPE_LABELS, INSTANCE_TYPE_LABELS } from '../types';

/**
 * 开发空间详情页面
 */
export function SpaceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: space, isLoading, error, refetch } = useSpace(id);

  const startMutation = useStartSpace();
  const stopMutation = useStopSpace();
  const deleteMutation = useDeleteSpace();

  const [deleteModalVisible, setDeleteModalVisible] = useState(false);

  // 面包屑（空间名加载后更新）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '开发空间', href: '/spaces' },
      { text: space?.space_name ?? '空间详情', href: '#' },
    ],
    [space?.space_name],
  );

  const handleStart = useCallback(() => {
    if (id) startMutation.mutate(id);
  }, [id, startMutation]);

  const handleStop = useCallback(() => {
    if (id) stopMutation.mutate(id);
  }, [id, stopMutation]);

  const handleConfirmDelete = useCallback(() => {
    if (!id) return;
    deleteMutation.mutate(id, {
      onSuccess: () => {
        setDeleteModalVisible(false);
        navigate('/spaces');
      },
    });
  }, [id, deleteMutation, navigate]);

  const canStart = space?.status === 'stopped';
  const canStop = space?.status === 'running';
  const canDelete = space?.status === 'stopped' || space?.status === 'failed';

  return (
    <PageLayout
      title={space?.space_name ?? '空间详情'}
      description="开发空间配置详情与生命周期管理"
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          {canStart && (
            <Button
              variant="primary"
              onClick={handleStart}
              loading={startMutation.isPending}
            >
              启动
            </Button>
          )}
          {canStop && (
            <Button onClick={handleStop} loading={stopMutation.isPending}>
              停止
            </Button>
          )}
          {canDelete && (
            <Button onClick={() => setDeleteModalVisible(true)}>删除</Button>
          )}
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {/* 错误提示 */}
        {error && (
          <Alert
            type="error"
            header="加载失败"
            action={<Button onClick={() => refetch()}>重试</Button>}
          >
            {error.message}
          </Alert>
        )}

        {/* 加载中 */}
        {isLoading && (
          <Box textAlign="center" padding="xl">
            <Spinner size="large" />
          </Box>
        )}

        {/* 详情内容 */}
        {space && (
          <Container header={<Header variant="h2">基本信息</Header>}>
            <KeyValuePairs
              columns={3}
              items={[
                { label: '空间名称', value: space.space_name },
                {
                  label: '状态',
                  value: <SpaceStatusBadge status={space.status} />,
                },
                {
                  label: 'IDE 类型',
                  value:
                    SPACE_TYPE_LABELS[space.space_type] || space.space_type,
                },
                {
                  label: '实例类型',
                  value:
                    INSTANCE_TYPE_LABELS[space.instance_type] ||
                    space.instance_type,
                },
                {
                  label: '存储大小',
                  value: `${space.storage_size_gb} GB`,
                },
                { label: '所有者 ID', value: String(space.owner_id) },
                { label: '创建时间', value: formatDateTime(space.created_at) },
                { label: '更新时间', value: formatDateTime(space.updated_at) },
                {
                  label: 'SageMaker ARN',
                  value: space.sagemaker_space_arn ?? '-',
                },
              ]}
            />
          </Container>
        )}

        {/* 删除确认弹窗 */}
        <Modal
          visible={deleteModalVisible}
          onDismiss={() => setDeleteModalVisible(false)}
          header="确认删除"
          footer={
            <Box float="right">
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  variant="link"
                  onClick={() => setDeleteModalVisible(false)}
                >
                  取消
                </Button>
                <Button
                  variant="primary"
                  onClick={handleConfirmDelete}
                  loading={deleteMutation.isPending}
                >
                  确认删除
                </Button>
              </SpaceBetween>
            </Box>
          }
        >
          确定要删除开发空间 <b>{space?.space_name}</b> 吗？此操作不可撤销。
        </Modal>
      </SpaceBetween>
    </PageLayout>
  );
}

export default SpaceDetailPage;
