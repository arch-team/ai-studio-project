/**
 * Monitoring Dashboard Page
 *
 * Task: T066 - 集群监控仪表盘
 * 显示集群状态、资源利用率、告警信息
 */

import {
  Box,
  ColumnLayout,
  Container,
  Grid,
  Header,
  ProgressBar,
  SpaceBetween,
  StatusIndicator,
  Table,
} from '@cloudscape-design/components';
import { useClusters, useResourceUtilization, useAlerts } from '../api';
import { MetricsCharts } from '../components/MetricsCharts';
import type { Alert, ClusterSummary, ResourceUtilization } from '../types';
import {
  CLUSTER_STATUS_LABELS,
  CLUSTER_STATUS_COLORS,
  CLUSTER_HEALTH_LABELS,
  CLUSTER_HEALTH_COLORS,
  ALERT_SEVERITY_LABELS,
  ALERT_SEVERITY_COLORS,
} from '../types';

// 日期格式化
function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 集群摘要卡片
 */
function ClusterSummaryCards({ clusters }: { clusters: ClusterSummary[] }) {
  if (clusters.length === 0) {
    return (
      <Container header={<Header variant="h2">集群概览</Header>}>
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无集群
        </Box>
      </Container>
    );
  }

  const cluster = clusters[0]; // 显示第一个集群

  return (
    <Container header={<Header variant="h2">集群概览</Header>}>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">集群名称</Box>
          <Box variant="awsui-value-large">{cluster.cluster_name}</Box>
        </div>
        <div>
          <Box variant="awsui-key-label">状态</Box>
          <StatusIndicator type={CLUSTER_STATUS_COLORS[cluster.status]}>
            {CLUSTER_STATUS_LABELS[cluster.status]}
          </StatusIndicator>
        </div>
        <div>
          <Box variant="awsui-key-label">健康状态</Box>
          {cluster.health_status ? (
            <StatusIndicator type={CLUSTER_HEALTH_COLORS[cluster.health_status]}>
              {CLUSTER_HEALTH_LABELS[cluster.health_status]}
            </StatusIndicator>
          ) : (
            <Box color="text-body-secondary">-</Box>
          )}
        </div>
        <div>
          <Box variant="awsui-key-label">节点数</Box>
          <Box variant="awsui-value-large">
            {cluster.available_nodes} / {cluster.total_nodes}
          </Box>
        </div>
      </ColumnLayout>
    </Container>
  );
}

/**
 * 资源利用率卡片
 */
function ResourceUtilizationCards({ utilization }: { utilization: ResourceUtilization[] }) {
  if (utilization.length === 0) {
    return null;
  }

  const resourceLabels: Record<string, string> = {
    cpu: 'CPU',
    memory: '内存',
    gpu: 'GPU',
    storage: '存储',
  };

  return (
    <Container header={<Header variant="h2">资源利用率</Header>}>
      <ColumnLayout columns={utilization.length} variant="text-grid">
        {utilization.map((item) => (
          <div key={item.resource_type}>
            <Box variant="awsui-key-label">
              {resourceLabels[item.resource_type] || item.resource_type}
            </Box>
            <Box variant="awsui-value-large">{item.utilization_percentage}%</Box>
            <ProgressBar
              value={item.utilization_percentage}
              additionalInfo={`${item.used} / ${item.total} ${item.unit}`}
            />
          </div>
        ))}
      </ColumnLayout>
    </Container>
  );
}

/**
 * 告警面板
 */
function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  const columnDefinitions = [
    {
      id: 'severity',
      header: '级别',
      cell: (item: Alert) => (
        <StatusIndicator type={ALERT_SEVERITY_COLORS[item.severity]}>
          {ALERT_SEVERITY_LABELS[item.severity]}
        </StatusIndicator>
      ),
      width: 100,
    },
    {
      id: 'title',
      header: '告警',
      cell: (item: Alert) => item.title,
    },
    {
      id: 'resource',
      header: '资源',
      cell: (item: Alert) => item.resource_type,
      width: 100,
    },
    {
      id: 'fired_at',
      header: '触发时间',
      cell: (item: Alert) => formatDateTime(item.fired_at),
      width: 150,
    },
    {
      id: 'status',
      header: '状态',
      cell: (item: Alert) => (
        <StatusIndicator type={item.status === 'resolved' ? 'success' : 'warning'}>
          {item.status === 'firing' ? '触发中' : item.status === 'acknowledged' ? '已确认' : '已解决'}
        </StatusIndicator>
      ),
      width: 100,
    },
  ];

  return (
    <Table
      columnDefinitions={columnDefinitions}
      items={alerts}
      sortingDisabled
      variant="container"
      header={
        <Header variant="h2" counter={alerts.length > 0 ? `(${alerts.length})` : undefined}>
          当前告警
        </Header>
      }
      empty={
        <Box textAlign="center" color="inherit" padding="l">
          <Box color="text-status-success">
            <StatusIndicator type="success">暂无告警</StatusIndicator>
          </Box>
        </Box>
      }
    />
  );
}

/**
 * 监控仪表盘页面
 */
export function MonitoringDashboardPage() {
  // 数据查询
  const { data: clustersData, isLoading: clustersLoading, error: clustersError } = useClusters();
  const { data: utilizationData, isLoading: utilizationLoading } = useResourceUtilization();
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({ status: 'firing' });

  const clusters = clustersData?.items || [];
  const utilization = utilizationData || [];
  const alerts = alertsData?.items || [];

  // 错误处理
  if (clustersError) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          加载失败: {clustersError.message}
        </Box>
      </Container>
    );
  }

  // 加载状态
  const isLoading = clustersLoading || utilizationLoading || alertsLoading;

  return (
    <SpaceBetween size="l" data-testid="monitoring-dashboard">
      <Header variant="h1">集群监控</Header>

      {isLoading ? (
        <Container>
          <Box textAlign="center" padding="l">
            <StatusIndicator type="loading">加载中...</StatusIndicator>
          </Box>
        </Container>
      ) : (
        <SpaceBetween size="l">
          {/* 集群摘要 */}
          <ClusterSummaryCards clusters={clusters} />

          {/* 资源利用率 */}
          <ResourceUtilizationCards utilization={utilization} />

          {/* 利用率图表 */}
          {utilization.length > 0 && (
            <Grid
              gridDefinition={[
                { colspan: 6 },
                { colspan: 6 },
              ]}
            >
              <MetricsCharts
                type="bar"
                title="资源使用对比"
                utilizationData={utilization}
                height={250}
              />
              <MetricsCharts
                type="pie"
                title="资源分布"
                utilizationData={utilization}
                height={250}
              />
            </Grid>
          )}

          {/* 告警面板 */}
          <AlertsPanel alerts={alerts} />
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}

export default MonitoringDashboardPage;
