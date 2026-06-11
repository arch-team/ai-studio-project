/**
 * Home Page (首页仪表盘)
 *
 * 平台概览 - 关键指标、训练任务状态分布、快速入口
 */

import {
  Badge,
  Box,
  Button,
  Cards,
  ColumnLayout,
  Container,
  Header,
  Link,
  PieChart,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrainingJobs } from '@features/training/api';
import { useDatasets } from '@features/datasets/api';
import { useModels } from '@features/models/api';
import { PageLayout } from '@shared/components';

/**
 * 关键指标卡片
 */
interface MetricCardProps {
  label: string;
  value: number | undefined;
  loading: boolean;
  description?: string;
  href: string;
  onNavigate: (href: string) => void;
}

function MetricCard({ label, value, loading, description, href, onNavigate }: MetricCardProps) {
  return (
    <Container>
      <SpaceBetween size="xxs">
        <Box variant="awsui-key-label">{label}</Box>
        <Box variant="h1">{loading ? '—' : (value ?? 0)}</Box>
        {description && (
          <Link
            variant="primary"
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
  primary?: boolean;
}

const QUICK_ACTIONS: QuickAction[] = [
  { name: '创建训练任务', description: '提交分布式训练任务（DDP / FSDP / DeepSpeed）', href: '/training-jobs/create', primary: true },
  { name: '上传数据集', description: '注册并管理训练数据集与版本', href: '/datasets/create' },
  { name: '打开开发空间', description: '启动在线 IDE 进行交互式开发', href: '/spaces' },
  { name: '查看资源监控', description: '实时查看 GPU / 节点资源使用情况', href: '/monitoring' },
];

/**
 * 首页仪表盘
 */
export function HomePage() {
  const navigate = useNavigate();
  const goTo = (href: string) => navigate(href);

  // 各类统计（仅取 total，page_size=1 降低负载）
  const { data: allJobs, isLoading: loadingAll } = useTrainingJobs({ page: 1, page_size: 1 });
  const { data: runningJobs, isLoading: loadingRunning } = useTrainingJobs({ status: 'running', page: 1, page_size: 1 });
  const { data: completedJobs, isLoading: loadingCompleted } = useTrainingJobs({ status: 'completed', page: 1, page_size: 1 });
  const { data: failedJobs } = useTrainingJobs({ status: 'failed', page: 1, page_size: 1 });
  const { data: pausedJobs } = useTrainingJobs({ status: 'paused', page: 1, page_size: 1 });
  const { data: datasets, isLoading: loadingDatasets } = useDatasets({ page: 1, page_size: 1 });
  const { data: models, isLoading: loadingModels } = useModels({ page: 1, page_size: 1 });

  // 任务状态分布（饼图）
  const statusData = useMemo(() => {
    const data = [
      { title: '运行中', value: runningJobs?.total ?? 0, color: '#0972d3' },
      { title: '已完成', value: completedJobs?.total ?? 0, color: '#037f0c' },
      { title: '已失败', value: failedJobs?.total ?? 0, color: '#d91515' },
      { title: '已暂停', value: pausedJobs?.total ?? 0, color: '#8d6c9f' },
    ];
    return data.filter((d) => d.value > 0);
  }, [runningJobs, completedJobs, failedJobs, pausedJobs]);

  const totalJobs = allJobs?.total ?? 0;
  const chartLoading = loadingRunning || loadingCompleted;

  return (
    <PageLayout
      title="平台概览"
      description="AI 训练平台运行状态与关键指标一览"
      actions={
        <Button variant="primary" iconName="add-plus" onClick={() => goTo('/training-jobs/create')}>
          创建训练任务
        </Button>
      }
    >
      <SpaceBetween size="l">
        {/* 关键指标 */}
        <ColumnLayout columns={4} variant="text-grid">
          <MetricCard
            label="训练任务总数"
            value={allJobs?.total}
            loading={loadingAll}
            description="查看全部任务"
            href="/training-jobs"
            onNavigate={goTo}
          />
          <MetricCard
            label="运行中任务"
            value={runningJobs?.total}
            loading={loadingRunning}
            description="查看运行中"
            href="/training-jobs"
            onNavigate={goTo}
          />
          <MetricCard
            label="数据集数量"
            value={datasets?.total}
            loading={loadingDatasets}
            description="管理数据集"
            href="/datasets"
            onNavigate={goTo}
          />
          <MetricCard
            label="已注册模型"
            value={models?.total}
            loading={loadingModels}
            description="查看模型库"
            href="/models"
            onNavigate={goTo}
          />
        </ColumnLayout>

        {/* 状态分布 + 系统状态 */}
        <ColumnLayout columns={2}>
          <Container
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

          <Container header={<Header variant="h2">系统状态</Header>}>
            <SpaceBetween size="m">
              <ColumnLayout columns={2} variant="text-grid">
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">平台服务</Box>
                  <StatusIndicator type="success">运行正常</StatusIndicator>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">调度器</Box>
                  <StatusIndicator type="success">就绪</StatusIndicator>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">失败任务</Box>
                  <Box>
                    {(failedJobs?.total ?? 0) > 0 ? (
                      <Badge color="red">{failedJobs?.total}</Badge>
                    ) : (
                      <StatusIndicator type="success">无</StatusIndicator>
                    )}
                  </Box>
                </SpaceBetween>
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">暂停任务</Box>
                  <Box>
                    {(pausedJobs?.total ?? 0) > 0 ? (
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
        <Container header={<Header variant="h2">快速操作</Header>}>
          <Cards
            cardDefinition={{
              header: (item) => (
                <Link
                  fontSize="heading-m"
                  onFollow={(e) => {
                    e.preventDefault();
                    goTo(item.href);
                  }}
                >
                  {item.name}
                </Link>
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
