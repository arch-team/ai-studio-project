/**
 * Model Versions Page
 *
 * 模型版本管理页面 - 显示版本历史、对比和回滚
 */

import {
  Box,
  BreadcrumbGroup,
  Button,
  Container,
  Header,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useModel, useModelVersions } from '../api';
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

  // 获取模型详情
  const { data: model, isLoading: modelLoading } = useModel(modelId);

  // 获取版本列表（包括对比数据）
  const { data: versionsData, isLoading: versionsLoading, refetch } = useModelVersions(
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

  // 加载状态
  if (modelLoading || versionsLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态
  if (!model) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          模型不存在
        </Box>
      </Container>
    );
  }

  return (
    <SpaceBetween size="l">
      {/* 面包屑导航 */}
      <BreadcrumbGroup
        items={[
          { text: '模型管理', href: '/models' },
          { text: model.model_name, href: `/models/${modelId}` },
          { text: '版本历史', href: '#' },
        ]}
        onFollow={(e) => {
          e.preventDefault();
          if (e.detail.href !== '#') {
            navigate(e.detail.href);
          }
        }}
      />

      {/* 页面标题 */}
      <Header
        variant="h1"
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
        {model.model_name} - 版本历史
      </Header>

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
        />
      </Container>
    </SpaceBetween>
  );
}

export default ModelVersionsPage;
