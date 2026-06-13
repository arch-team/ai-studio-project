/**
 * Model Versions Page
 *
 * 模型版本管理页面 - 显示版本历史、对比和回滚
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Header,
  Modal,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { useMemo, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageLayout, InlineErrorState } from '@shared/components';
import { useModel, useModelVersions, useRollbackModelVersion } from '../api';
import { ModelVersionTable, ModelMetricsCompare } from '../components';

/**
 * 模型版本管理页面
 */
export function ModelVersionsPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const modelId = id ? parseInt(id, 10) : undefined;

  // 版本选择状态
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [showRollbackModal, setShowRollbackModal] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null);

  // 获取模型详情
  const { data: model, isLoading: modelLoading } = useModel(modelId);

  // 面包屑（模型名加载后更新）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '模型管理', href: '/models' },
      { text: model?.model_name ?? '模型', href: `/models/${modelId}` },
      { text: '版本历史', href: '#' },
    ],
    [model?.model_name, modelId],
  );

  // 回滚 mutation
  const rollbackMutation = useRollbackModelVersion();

  // 获取版本列表（包括对比数据）
  const {
    data: versionsData,
    isLoading: versionsLoading,
    isError: versionsError,
    refetch,
  } = useModelVersions(
    modelId,
    showComparison && selectedVersions.length === 2
      ? { compare_v1: selectedVersions[0], compare_v2: selectedVersions[1] }
      : undefined
  );

  // 处理版本选择变化
  const handleSelectionChange = useCallback((versions: string[]) => {
    setSelectedVersions(versions);
    setShowComparison(false);
  }, []);

  // 处理对比
  const handleCompare = useCallback(() => {
    if (selectedVersions.length === 2) {
      setShowComparison(true);
      refetch();
    }
  }, [selectedVersions, refetch]);

  // 清除对比
  const handleClearComparison = useCallback(() => {
    setShowComparison(false);
    setSelectedVersions([]);
  }, []);

  // 打开回滚确认弹窗
  const handleOpenRollback = useCallback((version: string) => {
    setRollbackTarget(version);
    setShowRollbackModal(true);
  }, []);

  // 执行回滚
  const handleRollback = useCallback(async () => {
    if (!modelId || !rollbackTarget) return;
    await rollbackMutation.mutateAsync({ id: modelId, targetVersion: rollbackTarget });
    setShowRollbackModal(false);
    setRollbackTarget(null);
    refetch();
  }, [modelId, rollbackTarget, rollbackMutation, refetch]);

  // 加载状态
  if (modelLoading || versionsLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态：保留页面骨架（固定标题/面包屑），不裸 Container 塌缩
  if (!model) {
    return (
      <PageLayout title="模型版本历史" breadcrumbs={breadcrumbs}>
        <InlineErrorState
          title="模型不存在"
          message="未找到该模型，无法查看版本历史。"
        />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={`${model.model_name} - 版本历史`}
      description="模型版本对比与回滚管理"
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>
            刷新
          </Button>
          <Button onClick={() => navigate(`/models/${modelId}`)}>
            返回详情
          </Button>
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l">
      {/* 对比结果 */}
      {showComparison && versionsData?.comparison && (
        <SpaceBetween size="m">
          <Box float="right">
            <Button onClick={handleClearComparison}>清除对比</Button>
          </Box>
          <ModelMetricsCompare
            comparison={versionsData.comparison}
            version1={selectedVersions[0]}
            version2={selectedVersions[1]}
          />
        </SpaceBetween>
      )}

      {/* 版本列表加载失败：显式报错，不静默降级为空表（F-006） */}
      {versionsError && (
        <InlineErrorState
          message="版本列表加载失败。"
          onRetry={() => refetch()}
        />
      )}

      {/* 版本列表 */}
      <Container
        header={
          <Header
            variant="h2"
            counter={`(${versionsData?.versions?.length || 0})`}
          >
            版本列表
          </Header>
        }
      >
        <ModelVersionTable
          versions={versionsData?.versions || []}
          loading={versionsLoading}
          selectedVersions={selectedVersions}
          onSelectionChange={handleSelectionChange}
          onCompare={handleCompare}
          onRollback={handleOpenRollback}
          currentVersion={model.version}
        />
      </Container>

      {/* 回滚确认弹窗 */}
      <Modal
        visible={showRollbackModal}
        onDismiss={() => setShowRollbackModal(false)}
        header="确认回滚"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => setShowRollbackModal(false)}
              >
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleRollback}
                loading={rollbackMutation.isPending}
              >
                确认回滚
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box>
            确定要将模型 <b>{model.model_name}</b> 回滚到版本 <b>{rollbackTarget}</b> 吗？
          </Box>
          <Alert type="warning">
            回滚操作会创建一个新的模型版本，原有版本不会被删除。
          </Alert>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
    </PageLayout>
  );
}

export default ModelVersionsPage;
