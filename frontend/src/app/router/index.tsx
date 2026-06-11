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
import { ErrorPage, PageSpinner } from "@shared/components/feedback";

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
  import("@features/resource-quotas").then((m) => ({
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
const DatasetDetailPage = lazy(() =>
  import("@features/datasets/pages/DatasetDetailPage").then((m) => ({
    default: m.DatasetDetailPage,
  })),
);
const DatasetVersionsPage = lazy(() =>
  import("@features/datasets/pages/DatasetVersionsPage").then((m) => ({
    default: m.DatasetVersionsPage,
  })),
);

// Dashboard 模块页面
const HomePage = lazy(() =>
  import("@features/dashboard/pages/HomePage").then((m) => ({
    default: m.HomePage,
  })),
);

// Checkpoints 页面
const CheckpointsPage = lazy(() =>
  import("@features/training/pages/CheckpointsPage").then((m) => ({
    default: m.CheckpointsPage,
  })),
);

// Admin 模块页面
const AdminPage = lazy(() =>
  import("@features/admin/pages/AdminPage").then((m) => ({
    default: m.AdminPage,
  })),
);

// Reports 入口页面
const ReportsPage = lazy(() =>
  import("@features/reports/pages/ReportsPage").then((m) => ({
    default: m.ReportsPage,
  })),
);

// IDE 开发空间页面
const IDEPage = lazy(() =>
  import("@features/spaces/pages/IDEPage").then((m) => ({
    default: m.IDEPage,
  })),
);

// Spaces 模块页面
const SpaceListPage = lazy(() =>
  import("@features/spaces/pages/SpaceListPage").then((m) => ({
    default: m.SpaceListPage,
  })),
);
const CreateSpacePage = lazy(() =>
  import("@features/spaces/pages/CreateSpacePage").then((m) => ({
    default: m.CreateSpacePage,
  })),
);

// Monitoring 模块页面
const MonitoringDashboardPage = lazy(() =>
  import("@features/monitoring/pages/MonitoringDashboardPage").then((m) => ({
    default: m.MonitoringDashboardPage,
  })),
);

// Audit 模块页面
const AuditLogsPage = lazy(() =>
  import("@features/audit/pages/AuditLogsPage").then((m) => ({
    default: m.AuditLogsPage,
  })),
);

// Admin 用户管理页面
const UserManagementPage = lazy(() =>
  import("@features/admin/pages/UserManagementPage").then((m) => ({
    default: m.UserManagementPage,
  })),
);

// 错误页面 - 居中大字号错误码 + 行动按钮
const NotFoundPage = () => (
  <ErrorPage
    code="404"
    title="页面未找到"
    description="您访问的页面不存在或已被移动，请检查 URL 是否正确。"
  />
);

const UnauthorizedPage = () => (
  <ErrorPage
    code="403"
    title="无权访问"
    description="您没有权限访问此页面，请联系管理员获取相应权限。"
  />
);

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

      // 开发空间
      {
        path: ROUTES.SPACES,
        element: <SpaceListPage />,
      },
      {
        path: ROUTES.SPACE_CREATE,
        element: <CreateSpacePage />,
      },

      // 监控
      {
        path: ROUTES.MONITORING,
        element: <MonitoringDashboardPage />,
      },

      // 审计日志（需要 admin 或 team_lead 角色）
      {
        path: ROUTES.AUDIT_LOGS,
        element: (
          <RoleGuard allowedRoles={["admin", "team_lead"]}>
            <AuditLogsPage />
          </RoleGuard>
        ),
      },

      // 管理员路由（需要 admin 角色）
      {
        path: ROUTES.ADMIN,
        element: (
          <RoleGuard allowedRoles={["admin"]}>
            <AdminPage />
          </RoleGuard>
        ),
      },
      {
        path: ROUTES.USER_MANAGEMENT,
        element: (
          <RoleGuard allowedRoles={["admin"]}>
            <UserManagementPage />
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
