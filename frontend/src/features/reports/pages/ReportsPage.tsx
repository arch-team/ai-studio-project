/**
 * Reports Page
 *
 * 报表中心入口页面 - 资源使用摘要和快速导航
 */

import {
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  Link,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useResourceUsage } from '../api';

/**
 * 报表中心页面
 */
export function ReportsPage() {
  const navigate = useNavigate();

  // 获取资源使用摘要
  const { data, isLoading, error } = useResourceUsage();

  const summary = data?.summary;

  return (
    <SpaceBetween size="l">
      <Header variant="h1">报表中心</Header>

      {/* 资源使用摘要 */}
      <Container header={<Header variant="h2">资源使用概览</Header>}>
        {error ? (
          <Box textAlign="center" color="text-status-error" padding="l">
            加载失败: {error.message}
          </Box>
        ) : isLoading ? (
          <Box textAlign="center" padding="l">
            <StatusIndicator type="loading">加载中...</StatusIndicator>
          </Box>
        ) : (
          <ColumnLayout columns={4} variant="text-grid">
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">GPU 使用时长</Box>
              <Box variant="h3">{summary?.total_gpu_hours?.toFixed(1) ?? '-'} 小时</Box>
            </SpaceBetween>
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">CPU 使用时长</Box>
              <Box variant="h3">{summary?.total_cpu_hours?.toFixed(1) ?? '-'} 小时</Box>
            </SpaceBetween>
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">训练任务总数</Box>
              <Box variant="h3">{summary?.total_jobs_count ?? summary?.total_job_count ?? '-'}</Box>
            </SpaceBetween>
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">运行中任务</Box>
              <Box variant="h3">{summary?.active_jobs_count ?? '-'}</Box>
            </SpaceBetween>
          </ColumnLayout>
        )}
      </Container>

      {/* 任务统计 */}
      {summary && (
        <Container header={<Header variant="h2">任务统计</Header>}>
          <ColumnLayout columns={3} variant="text-grid">
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">已完成任务</Box>
              <Box variant="h3">
                <StatusIndicator type="success">
                  {summary.completed_jobs_count ?? '-'}
                </StatusIndicator>
              </Box>
            </SpaceBetween>
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">失败任务</Box>
              <Box variant="h3">
                <StatusIndicator type="error">
                  {summary.failed_jobs_count ?? '-'}
                </StatusIndicator>
              </Box>
            </SpaceBetween>
            <SpaceBetween size="xxs">
              <Box variant="awsui-key-label">存储使用量</Box>
              <Box variant="h3">
                {summary.total_storage_gb_hours?.toFixed(1) ?? '-'} GB*h
              </Box>
            </SpaceBetween>
          </ColumnLayout>
        </Container>
      )}

      {/* 详细报表导航 */}
      <Container header={<Header variant="h2">详细报表</Header>}>
        <ColumnLayout columns={2} variant="text-grid">
          <SpaceBetween size="m">
            <SpaceBetween size="xxs">
              <Box variant="h3">资源使用报表</Box>
              <Box color="text-body-secondary">
                按用户、项目、时间维度查看 GPU/CPU 使用详情
              </Box>
            </SpaceBetween>
            <Button
              variant="primary"
              onClick={() => navigate('/reports/resource-usage')}
            >
              查看资源使用报表
            </Button>
          </SpaceBetween>
          <SpaceBetween size="m">
            <SpaceBetween size="xxs">
              <Box variant="h3">成本分析报表</Box>
              <Box color="text-body-secondary">
                按类别分析计算、存储、网络等成本分布
              </Box>
            </SpaceBetween>
            <Button onClick={() => navigate('/reports/cost-analysis')}>
              查看成本分析报表
            </Button>
          </SpaceBetween>
        </ColumnLayout>
      </Container>

      {/* 快速链接 */}
      <Container header={<Header variant="h2">相关功能</Header>}>
        <SpaceBetween direction="horizontal" size="l">
          <Link onFollow={(e) => { e.preventDefault(); navigate('/resource-quotas'); }}>
            资源配额管理
          </Link>
          <Link onFollow={(e) => { e.preventDefault(); navigate('/training-jobs'); }}>
            训练任务列表
          </Link>
          <Link onFollow={(e) => { e.preventDefault(); navigate('/admin'); }}>
            管理后台
          </Link>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}

export default ReportsPage;
