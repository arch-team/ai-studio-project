/* eslint-disable react-refresh/only-export-components */
/**
 * Router Configuration
 *
 * Task: T017 - 配置 React Router
 * Task: T103 - 前端性能优化 (路由级懒加载)
 *
 * 应用路由配置 - 使用 React.lazy() 实现路由级代码分割
 */

import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { MainLayout } from "@layouts/MainLayout";
import { AuthGuard } from "./guards/AuthGuard";
import { RoleGuard } from "./guards/RoleGuard";
import { ROUTES } from "./routes";
import { PageSpinner } from "@shared/components/feedback";

// === 懒加载页面组件 ===

// Auth 模块 (登录页不懒加载，保证首屏体验)
import { LoginPage } from "@features/auth";
import { AuthLayout } from "@layouts/AuthLayout";

// Training 模块页面
const TrainingJobListPage = lazy(() =>
  import("@features/training/pages/TrainingJobListPage").then((m) => ({
    default: m.TrainingJobListPage,
  })),
);
const CreateTrainingJobPage = lazy(() =>
  import("@features/training/pages/CreateTrainingJobPage").then((m) => ({
    default: m.CreateTrainingJobPage,
  })),
);
const TrainingJobDetailPage = lazy(() =>
  import("@features/training/pages/TrainingJobDetailPage").then((m) => ({
    default: m.TrainingJobDetailPage,
  })),
);

// Templates 模块页面
const TemplateListPage = lazy(() =>
  import("@features/templates/pages/TemplateListPage").then((m) => ({
    default: m.TemplateListPage,
  })),
);
const TemplateDetailPage = lazy(() =>
  import("@features/templates/pages/TemplateDetailPage").then((m) => ({
    default: m.TemplateDetailPage,
  })),
);

// Models 模块页面
const ModelListPage = lazy(() =>
  import("@features/models/pages/ModelListPage").then((m) => ({
    default: m.ModelListPage,
  })),
);
const ModelDetailPage = lazy(() =>
  import("@features/models/pages/ModelDetailPage").then((m) => ({
    default: m.ModelDetailPage,
  })),
);
const ModelVersionsPage = lazy(() =>
  import("@features/models/pages/ModelVersionsPage").then((m) => ({
    default: m.ModelVersionsPage,
  })),
);

// Resource Quotas 模块页面
const ResourceQuotasPage = lazy(() =>
  import("@features/resource-quotas/ResourceQuotasPage").then((m) => ({
    default: m.ResourceQuotasPage,
  })),
);

// Reports 模块页面
const CostAnalysisPage = lazy(() =>
  import("@features/reports/pages/CostAnalysisPage").then((m) => ({
    default: m.CostAnalysisPage,
  })),
);
const ResourceUsageReportPage = lazy(() =>
  import("@features/reports/pages/ResourceUsageReportPage").then((m) => ({
    default: m.ResourceUsageReportPage,
  })),
);

// Datasets 模块页面
const DatasetListPage = lazy(() =>
  import("@features/datasets/pages/DatasetListPage").then((m) => ({
    default: m.DatasetListPage,
  })),
);
const CreateDatasetPage = lazy(() =>
  import("@features/datasets/pages/CreateDatasetPage").then((m) => ({
    default: m.CreateDatasetPage,
  })),
);
const DatasetVersionsPage = lazy(() =>
  import("@features/datasets/pages/DatasetVersionsPage").then((m) => ({
    default: m.DatasetVersionsPage,
  })),
);

// 占位页面组件 (待实现)
const HomePage = () => <div>首页</div>;
const DatasetDetailPage = () => <div>数据集详情</div>;
const CheckpointsPage = () => <div>检查点列表</div>;
const AdminPage = () => <div>管理后台</div>;
const ReportsPage = () => <div>报表</div>;
const IDEPage = () => <div>开发环境</div>;
const NotFoundPage = () => <div>404 - 页面未找到</div>;
const UnauthorizedPage = () => <div>无权访问</div>;

/**
 * 受保护的布局容器
 * 包含 AuthGuard、MainLayout 和 Suspense
 */
function ProtectedLayout() {
  return (
    <AuthGuard>
      <MainLayout>
        <Suspense fallback={<PageSpinner />}>
          <Outlet />
        </Suspense>
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
    element: (
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    ),
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

      // 任务模板
      {
        path: ROUTES.JOB_TEMPLATES,
        element: <TemplateListPage />,
      },
      {
        path: ROUTES.JOB_TEMPLATE_DETAIL,
        element: <TemplateDetailPage />,
      },

      // 数据管理
      {
        path: ROUTES.DATASETS,
        element: <DatasetListPage />,
      },
      {
        path: ROUTES.DATASET_CREATE,
        element: <CreateDatasetPage />,
      },
      {
        path: ROUTES.DATASET_DETAIL,
        element: <DatasetDetailPage />,
      },
      {
        path: ROUTES.DATASET_VERSIONS,
        element: <DatasetVersionsPage />,
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
          <RoleGuard allowedRoles={["admin"]}>
            <AdminPage />
          </RoleGuard>
        ),
      },
      {
        path: ROUTES.REPORTS,
        element: (
          <RoleGuard allowedRoles={["admin", "team_lead"]}>
            <ReportsPage />
          </RoleGuard>
        ),
      },
      {
        path: ROUTES.REPORTS_RESOURCE_USAGE,
        element: (
          <RoleGuard allowedRoles={["admin", "team_lead"]}>
            <ResourceUsageReportPage />
          </RoleGuard>
        ),
      },
      {
        path: ROUTES.REPORTS_COST_ANALYSIS,
        element: (
          <RoleGuard allowedRoles={["admin", "team_lead"]}>
            <CostAnalysisPage />
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
    path: "*",
    element: <Navigate to={ROUTES.NOT_FOUND} replace />,
  },
]);
