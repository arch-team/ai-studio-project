/**
 * Home Page (首页仪表盘)
 *
 * 平台门户 - 品牌 Hero 页头、关键指标、训练任务状态分布、快速入口。
 *
 * 设计要点:
 * - Hero 页头：深空渐变 + 时段问候，建立平台品牌氛围
 * - 指标卡：图标 + 大数字（display-l），一眼读取关键数据
 * - 状态饼图：使用品牌语义色，与全局主题一致
 */

import {
  Badge,
  Box,
  Button,
  Cards,
  ColumnLayout,
  Container,
  Header,
  Icon,
  Link,
  PieChart,
  SpaceBetween,
  StatusIndicator,
  type IconProps,
} from '@cloudscape-design/components';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@features/auth';
import { useTrainingJobs } from '@features/training/api';
import { useDatasets } from '@features/datasets/api';
import { useModels } from '@features/models/api';
import { PageLayout, InlineErrorState } from '@shared/components';
import { JOB_STATUS_CHART_COLORS } from '@shared/theme';

/**
 * 根据当前时段生成问候语
 */
function greetingByHour(hour: number): string {
  if (hour < 6) return '夜深了';
  if (hour < 12) return '早上好';
  if (hour < 14) return '中午好';
  if (hour < 18) return '下午好';
  return '晚上好';
}

/**
 * 关键指标卡片
 */
interface MetricCardProps {
  label: string;
  value: number | undefined;
  loading: boolean;
  iconName: IconProps.Name;
  description?: string;
  href: string;
  onNavigate: (href: string) => void;
}

function MetricCard({ label, value, loading, iconName, description, href, onNavigate }: MetricCardProps) {
  return (
    <Container fitHeight>
      <SpaceBetween size="xs">
        <SpaceBetween size="xs" direction="horizontal" alignItems="center">
          <Icon name={iconName} size="medium" variant="link" />
          <Box variant="awsui-key-label">{label}</Box>
        </SpaceBetween>
        <Box fontSize="display-l" fontWeight="bold" variant="span">
          {loading ? '—' : (value ?? 0)}
        </Box>
        {description && (
          <Link
            variant="primary"
            fontSize="body-s"
            onFollow={(e) => {
              e.preventDefault();
              onNavigate(href);
            }}
          >
            {description}
          </Link>
        )}
      </SpaceBetween>
    </Container>
  );
}

/** 快速操作项 */
interface QuickAction {
  name: string;
  description: string;
  href: string;
  iconName: IconProps.Name;
  primary?: boolean;
}

const QUICK_ACTIONS: QuickAction[] = [
  { name: '创建训练任务', description: '提交分布式训练任务（DDP / FSDP / DeepSpeed）', href: '/training-jobs/create', iconName: 'gen-ai', primary: true },
  { name: '上传数据集', description: '注册并管理训练数据集与版本', href: '/datasets/create', iconName: 'upload' },
  { name: '打开开发空间', description: '启动在线 IDE 进行交互式开发', href: '/spaces', iconName: 'command-prompt' },
  { name: '查看资源监控', description: '实时查看 GPU / 节点资源使用情况', href: '/monitoring', iconName: 'multiscreen' },
];

/**
 * 首页仪表盘
 */
export function HomePage() {
  const navigate = useNavigate();
  const goTo = (href: string) => navigate(href);
  const userName = useAuthStore((s) => s.user?.name);

  // 各类统计（仅取 total，page_size=1 降低负载）
  const { data: allJobs, isLoading: loadingAll, isError: jobsError, refetch: refetchJobs } = useTrainingJobs({ page: 1, page_size: 1 });
  const { data: runningJobs, isLoading: loadingRunning } = useTrainingJobs({ status: 'running', page: 1, page_size: 1 });
  const { data: completedJobs, isLoading: loadingCompleted } = useTrainingJobs({ status: 'completed', page: 1, page_size: 1 });
  const { data: failedJobs } = useTrainingJobs({ status: 'failed', page: 1, page_size: 1 });
  const { data: pausedJobs } = useTrainingJobs({ status: 'paused', page: 1, page_size: 1 });
  const { data: datasets, isLoading: loadingDatasets } = useDatasets({ page: 1, page_size: 1 });
  const { data: models, isLoading: loadingModels } = useModels({ page: 1, page_size: 1 });

  // 任务状态分布（饼图，使用品牌语义色）
  const statusData = useMemo(() => {
    const data = [
      { title: '运行中', value: runningJobs?.total ?? 0, color: JOB_STATUS_CHART_COLORS.running },
      { title: '已完成', value: completedJobs?.total ?? 0, color: JOB_STATUS_CHART_COLORS.completed },
      { title: '已失败', value: failedJobs?.total ?? 0, color: JOB_STATUS_CHART_COLORS.failed },
      { title: '已暂停', value: pausedJobs?.total ?? 0, color: JOB_STATUS_CHART_COLORS.paused },
    ];
    return data.filter((d) => d.value > 0);
  }, [runningJobs, completedJobs, failedJobs, pausedJobs]);

  const totalJobs = allJobs?.total ?? 0;
  const chartLoading = loadingRunning || loadingCompleted;

  // 错误态：核心数据源 allJobs 加载失败时显式报错，不再静默伪装健康（F-001/F-030）
  const hasError = jobsError;

  const greeting = greetingByHour(new Date().getHours());
  const heroTitle = userName ? `${greeting}，${userName}` : '平台概览';

  return (
    <PageLayout
      hero
      title={heroTitle}
      description="AI 训练平台运行状态与关键指标一览"
      actions={
        <Button variant="primary" iconName="add-plus" onClick={() => goTo('/training-jobs/create')}>
          创建训练任务
        </Button>
      }
      heroExtra={
        <SpaceBetween size="l" direction="horizontal">
          <StatusIndicator type={hasError ? 'warning' : 'success'}>
            {hasError ? '平台状态无法获取' : '平台服务运行正常'}
          </StatusIndicator>
          <StatusIndicator type={(runningJobs?.total ?? 0) > 0 ? 'in-progress' : 'stopped'}>
            {(runningJobs?.total ?? 0) > 0
              ? `${runningJobs?.total} 个任务训练中`
              : '当前无运行任务'}
          </StatusIndicator>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {hasError && (
          <InlineErrorState
            message="部分平台数据加载失败，显示的指标可能不完整。"
            onRetry={() => refetchJobs()}
          />
        )}

        {/* 关键指标 */}
        <ColumnLayout columns={4} minColumnWidth={170}>
          <MetricCard
            label="训练任务总数"
            value={allJobs?.total}
            loading={loadingAll}
            iconName="gen-ai"
            description="查看全部任务"
            href="/training-jobs"
            onNavigate={goTo}
          />
          <MetricCard
            label="运行中任务"
            value={runningJobs?.total}
            loading={loadingRunning}
            iconName="status-in-progress"
            description="查看运行中"
            href="/training-jobs"
            onNavigate={goTo}
          />
          <MetricCard
            label="数据集数量"
            value={datasets?.total}
            loading={loadingDatasets}
            iconName="folder-open"
            description="管理数据集"
            href="/datasets"
            onNavigate={goTo}
          />
          <MetricCard
            label="已注册模型"
            value={models?.total}
            loading={loadingModels}
            iconName="share"
            description="查看模型库"
            href="/models"
            onNavigate={goTo}
          />
        </ColumnLayout>

        {/* 状态分布 + 系统状态 */}
        <ColumnLayout columns={2}>
          <Container
            fitHeight
            header={
              <Header variant="h2" description="按状态统计的训练任务分布">
                训练任务状态分布
              </Header>
            }
          >
            <PieChart
              data={statusData}
              statusType={chartLoading ? 'loading' : 'finished'}
              hideFilter
              size="medium"
              variant="donut"
              innerMetricValue={`${totalJobs}`}
              innerMetricDescription="任务总数"
              detailPopoverContent={(datum, sum) => [
                { key: '数量', value: datum.value },
                { key: '占比', value: sum > 0 ? `${((datum.value / sum) * 100).toFixed(1)}%` : '0%' },
              ]}
              ariaLabel="训练任务状态分布饼图"
              empty={
                <Box textAlign="center" color="inherit">
                  <b>暂无任务数据</b>
                  <Box variant="p" color="inherit">
                    创建训练任务后将在此展示状态分布
                  </Box>
                </Box>
              }
            />
          </Container>

          <Container fitHeight header={<Header variant="h2">系统状态</Header>}>
            <SpaceBetween size="m">
              <ColumnLayout columns={2} variant="text-grid">
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">平台服务</Box>
                  <StatusIndicator type={hasError ? 'warning' : 'success'}>
                    {hasError ? '无法获取' : '运行正常'}
                  </StatusIndicator>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">调度器</Box>
                  {/* error 时调度器状态不可信，降级为"未知"而非伪装"就绪"（F-030/R2） */}
                  <StatusIndicator type={hasError ? 'warning' : 'success'}>
                    {hasError ? '未知' : '就绪'}
                  </StatusIndicator>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">失败任务</Box>
                  <Box>
                    {/* error 时计数不可信，显示"无法获取"而非绿色"无"（F-030/R2） */}
                    {hasError ? (
                      <StatusIndicator type="warning">无法获取</StatusIndicator>
                    ) : (failedJobs?.total ?? 0) > 0 ? (
                      <Badge color="red">{failedJobs?.total}</Badge>
                    ) : (
                      <StatusIndicator type="success">无</StatusIndicator>
                    )}
                  </Box>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">暂停任务</Box>
                  <Box>
                    {hasError ? (
                      <StatusIndicator type="warning">无法获取</StatusIndicator>
                    ) : (pausedJobs?.total ?? 0) > 0 ? (
                      <Badge color="grey">{pausedJobs?.total}</Badge>
                    ) : (
                      <StatusIndicator type="success">无</StatusIndicator>
                    )}
                  </Box>
                </SpaceBetween>
              </ColumnLayout>
            </SpaceBetween>
          </Container>
        </ColumnLayout>

        {/* 快速操作 */}
        <Container header={<Header variant="h2" description="一步直达常用工作流">快速操作</Header>}>
          <Cards
            cardDefinition={{
              header: (item) => (
                <SpaceBetween size="xs" direction="horizontal" alignItems="center">
                  <Icon name={item.iconName} size="medium" variant={item.primary ? 'link' : 'normal'} />
                  <Link
                    fontSize="heading-m"
                    onFollow={(e) => {
                      e.preventDefault();
                      goTo(item.href);
                    }}
                  >
                    {item.name}
                  </Link>
                </SpaceBetween>
              ),
              sections: [
                {
                  id: 'description',
                  content: (item) => <Box color="text-body-secondary">{item.description}</Box>,
                },
                {
                  id: 'action',
                  content: (item) => (
                    <Button
                      variant={item.primary ? 'primary' : 'normal'}
                      iconName="arrow-right"
                      iconAlign="right"
                      onClick={() => goTo(item.href)}
                    >
                      前往
                    </Button>
                  ),
                },
              ],
            }}
            cardsPerRow={[{ cards: 1 }, { minWidth: 500, cards: 2 }, { minWidth: 900, cards: 4 }]}
            items={QUICK_ACTIONS}
            trackBy="name"
          />
        </Container>
      </SpaceBetween>
    </PageLayout>
  );
}

export default HomePage;
