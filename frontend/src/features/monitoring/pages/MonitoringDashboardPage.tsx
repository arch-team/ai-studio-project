/**
 * Monitoring Dashboard Page
 *
 * Task: T066 - 集群监控仪表盘
 * 功能:
 * - 集群状态概览
 * - 资源利用率展示
 * - Grafana 仪表盘嵌入 (iframe)
 * - 实时指标图表
 * - 时间范围选择
 * - 告警信息展示
 */

import { useState, useMemo } from "react";
import {
  Alert,
  Box,
  ColumnLayout,
  Container,
  DateRangePicker,
  Header,
  Link,
  ProgressBar,
  SegmentedControl,
  SpaceBetween,
  StatusIndicator,
  Table,
  Tabs,
  Toggle,
} from "@cloudscape-design/components";
import type { DateRangePickerProps } from "@cloudscape-design/components";
import {
  useClusters,
  useResourceUtilization,
  useAlerts,
  useMetricSeries,
} from "../api";
import { PageLayout, InlineErrorState } from "@shared/components";
import { MetricsCharts } from "../components";

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: "首页", href: "/" },
  { text: "资源监控", href: "/monitoring" },
];
import {
  formatDateTimeShort,
  calculateTimeRange,
  DATE_RANGE_PICKER_I18N,
} from "@shared/utils";
import type {
  Alert as AlertData,
  ClusterSummary,
  ResourceUtilization,
  MetricFilters,
} from "../types";
import {
  CLUSTER_STATUS_LABELS,
  CLUSTER_STATUS_COLORS,
  CLUSTER_HEALTH_LABELS,
  CLUSTER_HEALTH_COLORS,
  ALERT_SEVERITY_LABELS,
  ALERT_SEVERITY_COLORS,
} from "../types";

// === 常量配置 ===

// 时间范围预设选项
const TIME_RANGE_OPTIONS: DateRangePickerProps.RelativeOption[] = [
  { key: "15m", amount: 15, unit: "minute", type: "relative" },
  { key: "1h", amount: 1, unit: "hour", type: "relative" },
  { key: "6h", amount: 6, unit: "hour", type: "relative" },
  { key: "24h", amount: 24, unit: "hour", type: "relative" },
  { key: "7d", amount: 7, unit: "day", type: "relative" },
];

// 自动刷新间隔选项
const REFRESH_INTERVAL_OPTIONS = [
  { id: "off", text: "关闭" },
  { id: "30s", text: "30秒" },
  { id: "1m", text: "1分钟" },
  { id: "5m", text: "5分钟" },
];

// Grafana 静态配置 (baseUrl 在组件内动态读取环境变量，以支持运行时降级判断)
const GRAFANA_CONFIG = {
  dashboardId: "cluster-overview",
  orgId: 1,
};

// 默认监控指标
const DEFAULT_METRICS = [
  "cpu_utilization",
  "memory_utilization",
  "gpu_utilization",
];

// === 工具函数 ===

/**
 * 获取刷新间隔毫秒数
 */
function getRefreshIntervalMs(intervalId: string): number | undefined {
  switch (intervalId) {
    case "30s":
      return 30000;
    case "1m":
      return 60000;
    case "5m":
      return 300000;
    default:
      return undefined;
  }
}

// === 子组件 ===

/**
 * 时间范围选择器组件
 */
function TimeRangeSelector({
  value,
  onChange,
  refreshInterval,
  onRefreshIntervalChange,
}: {
  value: DateRangePickerProps.Value | null;
  onChange: (value: DateRangePickerProps.Value | null) => void;
  refreshInterval: string;
  onRefreshIntervalChange: (interval: string) => void;
}) {
  return (
    <SpaceBetween direction="horizontal" size="m">
      <div style={{ minWidth: 280 }}>
        <DateRangePicker
          value={value}
          onChange={({ detail }) => onChange(detail.value)}
          relativeOptions={TIME_RANGE_OPTIONS}
          isValidRange={(range) => {
            if (range?.type === "absolute") {
              const start = new Date(range.startDate);
              const end = new Date(range.endDate);
              if (start > end) {
                return {
                  valid: false,
                  errorMessage: "开始时间不能晚于结束时间",
                };
              }
              // 限制最大范围为 30 天
              const maxRange = 30 * 24 * 60 * 60 * 1000;
              if (end.getTime() - start.getTime() > maxRange) {
                return {
                  valid: false,
                  errorMessage: "时间范围不能超过 30 天",
                };
              }
            }
            return { valid: true };
          }}
          i18nStrings={DATE_RANGE_PICKER_I18N}
          placeholder="选择时间范围"
        />
      </div>

      <SegmentedControl
        selectedId={refreshInterval}
        onChange={({ detail }) => onRefreshIntervalChange(detail.selectedId)}
        label="自动刷新"
        options={REFRESH_INTERVAL_OPTIONS}
      />
    </SpaceBetween>
  );
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
            <StatusIndicator
              type={CLUSTER_HEALTH_COLORS[cluster.health_status]}
            >
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
function ResourceUtilizationCards({
  utilization,
}: {
  utilization: ResourceUtilization[];
}) {
  if (utilization.length === 0) {
    return null;
  }

  const resourceLabels: Record<string, string> = {
    cpu: "CPU",
    memory: "内存",
    gpu: "GPU",
    storage: "存储",
  };

  // 根据利用率获取进度条颜色
  const getProgressStatus = (
    percentage: number,
  ): "success" | "in-progress" | "error" => {
    if (percentage < 60) return "success";
    if (percentage < 85) return "in-progress";
    return "error";
  };

  return (
    <Container header={<Header variant="h2">资源利用率</Header>}>
      <ColumnLayout columns={utilization.length} variant="text-grid">
        {utilization.map((item) => (
          <div key={item.resource_type}>
            <Box variant="awsui-key-label">
              {resourceLabels[item.resource_type] || item.resource_type}
            </Box>
            <Box variant="awsui-value-large">
              {item.utilization_percentage}%
            </Box>
            <ProgressBar
              value={item.utilization_percentage}
              status={getProgressStatus(item.utilization_percentage)}
              additionalInfo={`${item.used} / ${item.total} ${item.unit}`}
            />
          </div>
        ))}
      </ColumnLayout>
    </Container>
  );
}

/**
 * Grafana 仪表盘嵌入组件
 */
function GrafanaDashboard({
  startTime,
  endTime,
  refreshInterval,
  visible,
}: {
  startTime: string;
  endTime: string;
  refreshInterval?: number;
  visible: boolean;
}) {
  // 动态读取环境变量，判断 Grafana 是否真正配置
  // 注意: fallback "/grafana" 在 dev 环境是死链，不视为"已配置"
  const grafanaBaseUrl = import.meta.env.VITE_GRAFANA_URL;
  const isGrafanaConfigured = Boolean(grafanaBaseUrl);

  // 构建 Grafana URL (必须在条件返回之前调用 Hook)
  const grafanaUrl = useMemo(() => {
    if (!grafanaBaseUrl) {
      return "";
    }

    const params = new URLSearchParams({
      orgId: String(GRAFANA_CONFIG.orgId),
      from: new Date(startTime).getTime().toString(),
      to: new Date(endTime).getTime().toString(),
      theme: "light",
      kiosk: "tv", // 隐藏 Grafana 导航栏
    });

    if (refreshInterval) {
      params.append("refresh", `${Math.floor(refreshInterval / 1000)}s`);
    }

    return `${grafanaBaseUrl}/d/${GRAFANA_CONFIG.dashboardId}?${params.toString()}`;
  }, [grafanaBaseUrl, startTime, endTime, refreshInterval]);

  if (!visible) {
    return null;
  }

  // 未配置 Grafana: 优雅降级，展示引导文案而非死链 iframe
  // 文案分层: 对终端用户说"还能去哪看数据"，运维提示不暴露 env 变量名
  if (!isGrafanaConfigured) {
    return (
      <Container header={<Header variant="h2">Grafana 仪表盘</Header>}>
        <Alert type="info" header="Grafana 监控大盘未启用">
          <SpaceBetween size="xs">
            <Box variant="p">
              实时监控大盘尚未启用。您仍可在「概览」与「指标趋势」标签页查看集群状态、资源利用率和指标趋势。
            </Box>
            <Box variant="small" color="text-body-secondary">
              管理员可配置监控大盘地址以启用此功能。
            </Box>
          </SpaceBetween>
        </Alert>
      </Container>
    );
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="实时集群监控仪表盘"
          actions={
            <Link href={grafanaUrl} target="_blank" external>
              在 Grafana 中打开
            </Link>
          }
        >
          Grafana 仪表盘
        </Header>
      }
    >
      <Box padding={{ vertical: "xxs" }}>
        <iframe
          src={grafanaUrl}
          width="100%"
          height="500"
          title="Grafana 监控仪表盘"
          sandbox="allow-scripts allow-same-origin"
          style={{ border: "none", borderRadius: "4px" }}
          loading="lazy"
        />
      </Box>
    </Container>
  );
}

/**
 * 告警面板
 */
function AlertsPanel({ alerts }: { alerts: AlertData[] }) {
  const columnDefinitions = [
    {
      id: "severity",
      header: "级别",
      cell: (item: AlertData) => (
        <StatusIndicator type={ALERT_SEVERITY_COLORS[item.severity]}>
          {ALERT_SEVERITY_LABELS[item.severity]}
        </StatusIndicator>
      ),
      width: 100,
    },
    {
      id: "title",
      header: "告警",
      cell: (item: AlertData) => item.title,
    },
    {
      id: "resource",
      header: "资源",
      cell: (item: AlertData) => item.resource_type,
      width: 100,
    },
    {
      id: "fired_at",
      header: "触发时间",
      cell: (item: AlertData) => formatDateTimeShort(item.fired_at),
      width: 150,
    },
    {
      id: "status",
      header: "状态",
      cell: (item: AlertData) => (
        // F-036：触发中/已确认的图标颜色随告警级别联动（critical 红 / warning 黄 / info 蓝），
        // 与"级别"列语义呼应，不再对所有未解决告警一律黄色 warning 图标
        <StatusIndicator
          type={
            item.status === "resolved"
              ? "success"
              : ALERT_SEVERITY_COLORS[item.severity]
          }
        >
          {item.status === "firing"
            ? "触发中"
            : item.status === "acknowledged"
              ? "已确认"
              : "已解决"}
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
        <Header
          variant="h2"
          counter={alerts.length > 0 ? `(${alerts.length})` : undefined}
        >
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

// === 主组件 ===

/**
 * 监控仪表盘页面
 */
export function MonitoringDashboardPage() {
  // === 状态管理 ===

  // 时间范围状态 (默认最近 1 小时)
  const [dateRange, setDateRange] = useState<DateRangePickerProps.Value | null>(
    {
      type: "relative",
      amount: 1,
      unit: "hour",
    } as DateRangePickerProps.RelativeValue,
  );

  // 自动刷新间隔
  const [refreshInterval, setRefreshInterval] = useState("1m");

  // Grafana 仪表盘显示开关
  const [showGrafana, setShowGrafana] = useState(true);

  // 活动标签页
  const [activeTabId, setActiveTabId] = useState("overview");

  // === 计算时间范围 ===
  const { startTime, endTime } = useMemo(
    () => calculateTimeRange(dateRange),
    [dateRange],
  );

  const refreshIntervalMs = useMemo(
    () => getRefreshIntervalMs(refreshInterval),
    [refreshInterval],
  );

  // === 数据查询 ===

  // 集群状态
  const {
    data: clustersData,
    isLoading: clustersLoading,
    error: clustersError,
    refetch,
  } = useClusters();

  // 资源利用率
  const { data: utilizationData, isLoading: utilizationLoading } =
    useResourceUtilization();

  // 告警
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({
    status: "firing",
  });

  // 时间序列指标
  const metricFilters: MetricFilters = useMemo(
    () => ({
      metric_names: DEFAULT_METRICS,
      start_time: startTime,
      end_time: endTime,
      step: 60, // 60 秒间隔
    }),
    [startTime, endTime],
  );

  const { data: metricsData, isLoading: metricsLoading } = useMetricSeries(
    metricFilters,
    refreshIntervalMs,
  );

  // === 数据处理 ===
  const clusters = clustersData?.items || [];
  const utilization = utilizationData || [];
  const alerts = alertsData?.items || [];

  // === 错误处理 ===
  // 错误态保留 PageLayout 骨架（标题/面包屑），在内部渲染 InlineErrorState + 重试，
  // 不再塌缩为裸 Container（F-008）。
  if (clustersError) {
    return (
      <PageLayout title="资源监控" breadcrumbs={BREADCRUMBS}>
        <InlineErrorState
          message={clustersError.message}
          onRetry={() => refetch()}
        />
      </PageLayout>
    );
  }

  // === 加载状态 ===
  const isLoading =
    clustersLoading || utilizationLoading || alertsLoading || metricsLoading;

  // === 渲染 ===
  return (
    <PageLayout
      title="资源监控"
      description="实时监控集群状态、资源利用率和告警信息"
      breadcrumbs={BREADCRUMBS}
      actions={
        <TimeRangeSelector
          value={dateRange}
          onChange={setDateRange}
          refreshInterval={refreshInterval}
          onRefreshIntervalChange={setRefreshInterval}
        />
      }
    >
    <SpaceBetween size="l" data-testid="monitoring-dashboard">
      {isLoading ? (
        // 分区骨架占位：保留各 Container 标题外壳（概览/资源利用率），
        // 内部局部 Spinner，避免整页塌缩为单一居中 Spinner 致加载完成时布局跳变（F-050）。
        <SpaceBetween size="l">
          <Container header={<Header variant="h2">集群概览</Header>}>
            <Box textAlign="center" padding="l">
              <StatusIndicator type="loading">加载中...</StatusIndicator>
            </Box>
          </Container>
          <Container header={<Header variant="h2">资源利用率</Header>}>
            <Box textAlign="center" padding="l">
              <StatusIndicator type="loading">加载中...</StatusIndicator>
            </Box>
          </Container>
          <Container header={<Header variant="h2">当前告警</Header>}>
            <Box textAlign="center" padding="l">
              <StatusIndicator type="loading">加载中...</StatusIndicator>
            </Box>
          </Container>
        </SpaceBetween>
      ) : (
        <Tabs
          activeTabId={activeTabId}
          onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
          tabs={[
            {
              id: "overview",
              label: "概览",
              content: (
                <SpaceBetween size="l">
                  {/* 集群摘要 */}
                  <ClusterSummaryCards clusters={clusters} />

                  {/* 资源利用率 */}
                  <ResourceUtilizationCards utilization={utilization} />

                  {/* 利用率图表（统一 0-100% 量纲，F-009/F-010）。
                      两图同源数据，避免冗余：概览仅保留一张资源利用率对比柱状图。 */}
                  {utilization.length > 0 && (
                    <MetricsCharts
                      type="bar"
                      title="资源利用率对比"
                      utilizationData={utilization}
                      height={280}
                    />
                  )}

                  {/* 告警面板 */}
                  <AlertsPanel alerts={alerts} />
                </SpaceBetween>
              ),
            },
            {
              id: "metrics",
              label: "指标趋势",
              content: (
                <SpaceBetween size="l">
                  {/* 时间序列图表 */}
                  <MetricsCharts
                    type="line"
                    title="资源利用率趋势"
                    data={metricsData || []}
                    height={350}
                    loading={metricsLoading}
                  />

                  {/* 当前资源利用率快照（0-100% 量纲，与趋势图互补） */}
                  {utilization.length > 0 && (
                    <MetricsCharts
                      type="bar"
                      title="当前资源利用率"
                      utilizationData={utilization}
                      height={280}
                    />
                  )}
                </SpaceBetween>
              ),
            },
            {
              id: "grafana",
              label: "Grafana",
              content: (
                <SpaceBetween size="l">
                  {/* Grafana 显示开关 */}
                  <Container>
                    <Toggle
                      checked={showGrafana}
                      onChange={({ detail }) => setShowGrafana(detail.checked)}
                    >
                      显示 Grafana 仪表盘
                    </Toggle>
                  </Container>

                  {/* Grafana 嵌入 */}
                  <GrafanaDashboard
                    startTime={startTime}
                    endTime={endTime}
                    refreshInterval={refreshIntervalMs}
                    visible={showGrafana}
                  />

                  {!showGrafana && (
                    <Container>
                      <Box
                        textAlign="center"
                        color="text-body-secondary"
                        padding="xl"
                      >
                        Grafana 仪表盘已隐藏，点击上方开关显示
                      </Box>
                    </Container>
                  )}
                </SpaceBetween>
              ),
            },
            {
              id: "alerts",
              label: `告警${alerts.length > 0 ? ` (${alerts.length})` : ""}`,
              content: (
                <SpaceBetween size="l">
                  <AlertsPanel alerts={alerts} />

                  {/* 告警统计 */}
                  {alerts.length > 0 && (
                    <Container header={<Header variant="h2">告警统计</Header>}>
                      <ColumnLayout columns={3} variant="text-grid">
                        <div>
                          <Box variant="awsui-key-label">严重</Box>
                          <Box
                            variant="awsui-value-large"
                            color="text-status-error"
                          >
                            {
                              alerts.filter((a) => a.severity === "critical")
                                .length
                            }
                          </Box>
                        </div>
                        <div>
                          <Box variant="awsui-key-label">警告</Box>
                          <Box
                            variant="awsui-value-large"
                            color="text-status-warning"
                          >
                            {
                              alerts.filter((a) => a.severity === "warning")
                                .length
                            }
                          </Box>
                        </div>
                        <div>
                          <Box variant="awsui-key-label">信息</Box>
                          <Box
                            variant="awsui-value-large"
                            color="text-status-info"
                          >
                            {alerts.filter((a) => a.severity === "info").length}
                          </Box>
                        </div>
                      </ColumnLayout>
                    </Container>
                  )}
                </SpaceBetween>
              ),
            },
          ]}
        />
      )}
    </SpaceBetween>
    </PageLayout>
  );
}

export default MonitoringDashboardPage;
