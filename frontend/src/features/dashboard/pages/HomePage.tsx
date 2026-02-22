/**
 * Home Page (首页仪表盘)
 *
 * 平台概览 - 统计卡片、快速操作
 */

import {
  Box,
  Button,
  ColumnLayout,
  Container,
  Header,
  Link,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useTrainingJobs } from '@features/training/api';
import { useDatasets } from '@features/datasets/api';

/**
 * 统计卡片组件
 */
interface StatCardProps {
  title: string;
  value: number | undefined;
  loading: boolean;
  description?: string;
}

function StatCard({ title, value, loading, description }: StatCardProps) {
  return (
    <Container>
      <SpaceBetween size="xxs">
        <Box variant="awsui-key-label">{title}</Box>
        <Box variant="h1">
          {loading ? '-' : (value ?? 0)}
        </Box>
        {description && (
          <Box color="text-body-secondary" variant="small">
            {description}
          </Box>
        )}
      </SpaceBetween>
    </Container>
  );
}

/**
 * 首页仪表盘
 */
export function HomePage() {
  const navigate = useNavigate();

  // 获取训练任务统计
  const { data: allJobs, isLoading: loadingJobs } = useTrainingJobs({ page: 1, page_size: 1 });
  const { data: runningJobs, isLoading: loadingRunning } = useTrainingJobs({
    status: 'running',
    page: 1,
    page_size: 1,
  });

  // 获取数据集统计
  const { data: datasets, isLoading: loadingDatasets } = useDatasets({ page: 1, page_size: 1 });

  return (
    <SpaceBetween size="l">
      <Header variant="h1">AI 训练平台</Header>

      {/* 统计卡片 */}
      <ColumnLayout columns={4} variant="text-grid">
        <StatCard
          title="训练任务总数"
          value={allJobs?.total}
          loading={loadingJobs}
          description="全部训练任务"
        />
        <StatCard
          title="运行中任务"
          value={runningJobs?.total}
          loading={loadingRunning}
          description="当前正在运行"
        />
        <StatCard
          title="数据集数量"
          value={datasets?.total}
          loading={loadingDatasets}
          description="已注册数据集"
        />
        <StatCard
          title="平台状态"
          value={undefined}
          loading={false}
          description="系统运行正常"
        />
      </ColumnLayout>

      {/* 快速操作 */}
      <Container header={<Header variant="h2">快速操作</Header>}>
        <SpaceBetween direction="horizontal" size="m">
          <Button variant="primary" onClick={() => navigate('/training-jobs/create')}>
            创建训练任务
          </Button>
          <Button onClick={() => navigate('/datasets/create')}>
            上传数据集
          </Button>
          <Button onClick={() => navigate('/ide')}>
            打开开发空间
          </Button>
        </SpaceBetween>
      </Container>

      {/* 快速导航 */}
      <Container header={<Header variant="h2">功能导航</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <SpaceBetween size="xs">
            <Box variant="h3">训练管理</Box>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/training-jobs'); }}>
              训练任务列表
            </Link>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/models'); }}>
              模型管理
            </Link>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/checkpoints'); }}>
              检查点管理
            </Link>
          </SpaceBetween>
          <SpaceBetween size="xs">
            <Box variant="h3">数据管理</Box>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/datasets'); }}>
              数据集管理
            </Link>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/resource-quotas'); }}>
              资源配额
            </Link>
          </SpaceBetween>
          <SpaceBetween size="xs">
            <Box variant="h3">系统工具</Box>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/reports'); }}>
              报表中心
            </Link>
            <Link onFollow={(e) => { e.preventDefault(); navigate('/job-templates'); }}>
              任务模板
            </Link>
          </SpaceBetween>
        </ColumnLayout>
      </Container>
    </SpaceBetween>
  );
}

export default HomePage;
