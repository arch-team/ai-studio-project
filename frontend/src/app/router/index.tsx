/* eslint-disable react-refresh/only-export-components */
/**
 * Router Configuration
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 应用路由配置
 */

import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { MainLayout } from '@layouts/MainLayout';
import { AuthGuard } from './guards/AuthGuard';
import { RoleGuard } from './guards/RoleGuard';
import { ROUTES } from './routes';

// Training 模块页面
import {
  TrainingJobListPage,
  CreateTrainingJobPage,
  TrainingJobDetailPage,
} from '@features/training';

// Models 模块页面
import {
  ModelListPage,
  ModelDetailPage,
  ModelVersionsPage,
} from '@features/models';

// Resource Quotas 模块页面
import { ResourceQuotasPage } from '@features/resource-quotas';

// 占位页面组件 (待实现)
const HomePage = () => <div>首页</div>;
const LoginPage = () => <div>登录页</div>;
const DatasetsPage = () => <div>数据集列表</div>;
const DatasetDetailPage = () => <div>数据集详情</div>;
const CheckpointsPage = () => <div>检查点列表</div>;
const AdminPage = () => <div>管理后台</div>;
const ReportsPage = () => <div>报表</div>;
const IDEPage = () => <div>开发环境</div>;
const NotFoundPage = () => <div>404 - 页面未找到</div>;
const UnauthorizedPage = () => <div>无权访问</div>;

/**
 * 受保护的布局容器
 * 包含 AuthGuard 和 MainLayout
 */
function ProtectedLayout() {
  return (
    <AuthGuard>
      <MainLayout>
        <Outlet />
      </MainLayout>
    </AuthGuard>
  );
}

/**
 * 应用路由配置
 */
export const router = createBrowserRouter([
  // 公共路由
  {
    path: ROUTES.LOGIN,
    element: <LoginPage />,
  },

  // 受保护路由
  {
    element: <ProtectedLayout />,
    children: [
      // 首页
      {
        path: ROUTES.HOME,
        element: <HomePage />,
      },

      // 训练管理
      {
        path: ROUTES.TRAINING_JOBS,
        element: <TrainingJobListPage />,
      },
      {
        path: ROUTES.TRAINING_JOB_CREATE,
        element: <CreateTrainingJobPage />,
      },
      {
        path: ROUTES.TRAINING_JOB_DETAIL,
        element: <TrainingJobDetailPage />,
      },
      {
        path: ROUTES.MODELS,
        element: <ModelListPage />,
      },
      {
        path: ROUTES.MODEL_DETAIL,
        element: <ModelDetailPage />,
      },
      {
        path: ROUTES.MODEL_VERSIONS,
        element: <ModelVersionsPage />,
      },

      // 数据管理
      {
        path: ROUTES.DATASETS,
        element: <DatasetsPage />,
      },
      {
        path: ROUTES.DATASET_DETAIL,
        element: <DatasetDetailPage />,
      },
      {
        path: ROUTES.CHECKPOINTS,
        element: <CheckpointsPage />,
      },

      // 资源管理
      {
        path: ROUTES.RESOURCE_QUOTAS,
        element: <ResourceQuotasPage />,
      },

      // 管理员路由（需要 admin 或 team_lead 角色）
      {
        path: ROUTES.ADMIN,
        element: (
          <RoleGuard allowedRoles={['admin']}>
            <AdminPage />
          </RoleGuard>
        ),
      },
      {
        path: ROUTES.REPORTS,
        element: (
          <RoleGuard allowedRoles={['admin', 'team_lead']}>
            <ReportsPage />
          </RoleGuard>
        ),
      },

      // 开发工具
      {
        path: ROUTES.IDE,
        element: <IDEPage />,
      },
    ],
  },

  // 错误页面
  {
    path: ROUTES.NOT_FOUND,
    element: <NotFoundPage />,
  },
  {
    path: ROUTES.UNAUTHORIZED,
    element: <UnauthorizedPage />,
  },

  // 未匹配路由重定向到 404
  {
    path: '*',
    element: <Navigate to={ROUTES.NOT_FOUND} replace />,
  },
]);

