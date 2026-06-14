/**
 * Monitoring Dashboard Page Tests
 *
 * Task: T066 - 集群监控仪表盘
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { MonitoringDashboardPage } from '@features/monitoring';
import type {
  ClusterSummary,
  ClusterListResponse,
  ResourceUtilization,
  Alert,
  AlertListResponse,
} from '@features/monitoring';

// Mock 集群数据
const mockCluster: ClusterSummary = {
  id: 1,
  cluster_name: 'ai-training-cluster',
  cluster_arn: 'arn:aws:sagemaker:us-east-1:123456789:cluster/ai-training-cluster',
  region: 'us-east-1',
  status: 'active',
  health_status: 'healthy',
  total_nodes: 10,
  available_nodes: 8,
  total_gpu_count: 80,
  available_gpu_count: 64,
  total_cpu_cores: 320,
  available_cpu_cores: 256,
  last_sync_at: '2024-01-15T10:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
};

const mockClustersResponse: ClusterListResponse = {
  items: [mockCluster],
  total: 1,
};

// Mock 资源利用率数据
const mockUtilization: ResourceUtilization[] = [
  {
    resource_type: 'cpu',
    total: 320,
    used: 200,
    available: 120,
    utilization_percentage: 62.5,
    unit: 'cores',
  },
  {
    resource_type: 'memory',
    total: 2560,
    used: 1920,
    available: 640,
    utilization_percentage: 75,
    unit: 'GB',
  },
  {
    resource_type: 'gpu',
    total: 80,
    used: 60,
    available: 20,
    utilization_percentage: 75,
    unit: 'cards',
  },
];

// Mock 告警数据
const mockAlerts: Alert[] = [
  {
    id: '1',
    severity: 'warning',
    title: 'GPU 使用率过高',
    message: 'GPU 使用率超过 90%',
    source: 'prometheus',
    resource_type: 'cluster',
    resource_id: '1',
    fired_at: '2024-01-15T09:30:00Z',
    resolved_at: null,
    status: 'firing',
  },
];

const mockAlertsResponse: AlertListResponse = {
  items: mockAlerts,
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

// Mock hooks
const mockUseClusters = vi.fn();
const mockUseResourceUtilization = vi.fn();
const mockUseAlerts = vi.fn();
const mockUseMetricSeries = vi.fn();

vi.mock('@features/monitoring/api', () => ({
  useClusters: () => mockUseClusters(),
  useResourceUtilization: () => mockUseResourceUtilization(),
  useAlerts: () => mockUseAlerts(),
  useMetricSeries: (...args: unknown[]) => mockUseMetricSeries(...args),
}));

describe('MonitoringDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseClusters.mockReturnValue({
      data: mockClustersResponse,
      isLoading: false,
      error: null,
    });

    mockUseResourceUtilization.mockReturnValue({
      data: mockUtilization,
      isLoading: false,
      error: null,
    });

    mockUseAlerts.mockReturnValue({
      data: mockAlertsResponse,
      isLoading: false,
      error: null,
    });

    mockUseMetricSeries.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
  });

  describe('基本渲染', () => {
    it('should render page header with title', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      // 命名统一：侧栏/面包屑/标题均用「资源监控」（消除同页「集群监控」vs「资源监控」冲突）
      expect(screen.getByRole('heading', { name: /资源监控/i })).toBeInTheDocument();
    });

    it('should render dashboard container', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByTestId('monitoring-dashboard')).toBeInTheDocument();
    });
  });

  describe('集群摘要卡片', () => {
    it('should display cluster summary section', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText(/集群概览/i)).toBeInTheDocument();
    });

    it('should display cluster name', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText('ai-training-cluster')).toBeInTheDocument();
    });

    it('should display cluster status', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/活跃/i).length).toBeGreaterThan(0);
    });

    it('should display node count', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      // 8/10 节点可用
      expect(screen.getByText(/8.*\/.*10/)).toBeInTheDocument();
    });
  });

  describe('资源利用率卡片', () => {
    it('should display resource utilization section', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/资源利用率/i).length).toBeGreaterThan(0);
    });

    it('should display CPU utilization', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/CPU/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/62.5%/).length).toBeGreaterThan(0);
    });

    it('should display Memory utilization', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/内存/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/75%/).length).toBeGreaterThan(0);
    });

    it('should display GPU utilization', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/GPU/i).length).toBeGreaterThan(0);
    });
  });

  describe('告警面板', () => {
    it('should display alerts section', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText(/当前告警/i)).toBeInTheDocument();
    });

    it('should display alert title', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText('GPU 使用率过高')).toBeInTheDocument();
    });

    it('should display alert severity', () => {
      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/警告/i).length).toBeGreaterThan(0);
    });
  });

  describe('加载状态', () => {
    it('should display loading state', () => {
      mockUseClusters.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });
      mockUseResourceUtilization.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });
      mockUseAlerts.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getAllByText(/加载中/i).length).toBeGreaterThan(0);
    });

    // F-050 残留：loading 态须保留页面骨架（标题/dashboard 结构），
    // 不整页塌缩为孤立 Spinner，避免加载完成时布局跳变；与 error 态骨架范围一致。
    it('loading 态保留 PageLayout 骨架（标题与 dashboard 结构不塌缩）', () => {
      mockUseClusters.mockReturnValue({ data: undefined, isLoading: true, error: null });
      mockUseResourceUtilization.mockReturnValue({ data: undefined, isLoading: true, error: null });
      mockUseAlerts.mockReturnValue({ data: undefined, isLoading: true, error: null });
      mockUseMetricSeries.mockReturnValue({ data: undefined, isLoading: true, error: null });

      renderWithProviders(<MonitoringDashboardPage />);
      // 骨架保留：标题「资源监控」与 dashboard 容器在 loading 态仍渲染
      expect(screen.getByRole('heading', { name: /资源监控/i })).toBeInTheDocument();
      expect(screen.getByTestId('monitoring-dashboard')).toBeInTheDocument();
      // 分区骨架：概览/资源利用率等区块标题保留（不是单一居中 Spinner）
      expect(screen.getByText('集群概览')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('should display error message when clusters fail to load', () => {
      mockUseClusters.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load clusters'),
        refetch: vi.fn(),
      });

      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
    });

    it('应在错误态保留页面骨架并展示 InlineErrorState 与重试按钮（F-008）', async () => {
      const refetch = vi.fn();
      mockUseClusters.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: '服务器内部错误' },
        refetch,
      });

      renderWithProviders(<MonitoringDashboardPage />);

      // InlineErrorState：标题"加载失败" + 错误消息
      expect(await screen.findByText('加载失败')).toBeInTheDocument();
      expect(screen.getByText('服务器内部错误')).toBeInTheDocument();

      // 重试按钮存在且点击触发 refetch
      const retryButton = screen.getByRole('button', { name: '重试' });
      expect(retryButton).toBeInTheDocument();
      await userEvent.click(retryButton);
      expect(refetch).toHaveBeenCalledTimes(1);

      // 骨架保留：PageLayout Header 渲染"资源监控"标题
      expect(
        screen.getByRole('heading', { name: /资源监控/i }),
      ).toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('should display empty state when no clusters', () => {
      mockUseClusters.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<MonitoringDashboardPage />);
      expect(screen.getByText(/暂无集群/i)).toBeInTheDocument();
    });
  });

  describe('Grafana 未配置降级', () => {
    afterEach(() => {
      vi.unstubAllEnvs();
    });

    it('未配置 VITE_GRAFANA_URL 时应显示引导文案而非死链 iframe', async () => {
      // 显式置空 VITE_GRAFANA_URL，模拟 dev 环境未部署 Grafana
      vi.stubEnv('VITE_GRAFANA_URL', '');
      const user = userEvent.setup();

      renderWithProviders(<MonitoringDashboardPage />);

      // 切换到 Grafana 标签页
      await user.click(screen.getByRole('tab', { name: /Grafana/i }));

      // 引导文案对终端用户友好：标题提示未启用，正文告知仍可在概览/指标趋势查看数据
      expect(screen.getByText('Grafana 监控大盘未启用')).toBeInTheDocument();
      expect(
        screen.getByText(/您仍可在「概览」与「指标趋势」标签页查看/),
      ).toBeInTheDocument();

      // 文案不暴露 env 变量名等运维信息
      expect(screen.queryByText(/VITE_GRAFANA_URL/)).not.toBeInTheDocument();

      // 不渲染指向 /grafana 死链的 iframe
      expect(screen.queryByTitle('Grafana 监控仪表盘')).not.toBeInTheDocument();
    });

    it('已配置 VITE_GRAFANA_URL 时应渲染 iframe 且 src 指向配置的 URL', async () => {
      vi.stubEnv('VITE_GRAFANA_URL', 'https://grafana.example.com');
      const user = userEvent.setup();

      renderWithProviders(<MonitoringDashboardPage />);

      // 切换到 Grafana 标签页
      await user.click(screen.getByRole('tab', { name: /Grafana/i }));

      // iframe 渲染，且 src 指向配置的 Grafana URL
      const iframe = screen.getByTitle('Grafana 监控仪表盘');
      expect(iframe).toBeInTheDocument();
      expect(iframe).toHaveAttribute(
        'src',
        expect.stringContaining('https://grafana.example.com'),
      );
    });
  });
});
