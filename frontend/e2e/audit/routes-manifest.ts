/**
 * UI/UX 审计页面清单
 *
 * 数据源：frontend/src/app/router/routes.ts（29 个可审计页面）
 * 状态豁免规则见 spec §3.1/§5.4：
 * - 列表页: default/empty/loading/error 四态
 * - 详情页: default/loading/error 三态（error 用 404）
 * - 表单页: 仅 default（提交类错误属交互级，静态截图不适用）
 * - dashboard 类: default/loading/error
 * - 特殊页（登录/404/IDE）: 仅 default
 *
 * 注意：billing 模块无独立页面（src/features/billing/pages/ 为空），不在清单内。
 */

import {
  mockTrainingJobs,
  getMockTrainingJobDetail,
  createPaginatedResponse,
} from '../fixtures/trainingJobs';
import {
  datasetListResponse,
  datasetDetailResponse,
  datasetVersionListResponse,
  emptyDatasetVersionListResponse,
} from './fixtures/datasets';
import {
  modelListResponse,
  modelDetailResponse,
  modelVersionsResponse,
  emptyModelVersionsResponse,
} from './fixtures/models';
import {
  templateListResponse,
  templateDetailResponse,
  popularTemplatesResponse,
} from './fixtures/templates';
import { auditLogListResponse } from './fixtures/auditLogs';
import { userListResponse } from './fixtures/users';
import { checkpointListResponse } from './fixtures/checkpoints';
import { mockSpaces, createSpaceListResponse } from '../fixtures/spaces';
import { createResourceLimitConfigResponse } from '../fixtures/resourceQuotas';
import {
  dashboardJobStats,
  resolveDashboardJobStats,
  clusterListResponse,
  resourceUtilization,
  alertListResponse,
  metricSeriesResponse,
  resourceUsageResponse,
  costAnalysisResponse,
} from './fixtures/metrics';

export type AuditState = 'default' | 'empty' | 'loading' | 'error';
export type PageType = 'list' | 'detail' | 'form' | 'dashboard' | 'special';

export interface ApiMock {
  /** 主数据 API 匹配（注意排除子路径，参考 e2e/utils/mockApi.ts 的正则写法） */
  pattern: RegExp;
  /** default 状态返回体 */
  defaultBody: unknown;
  /** empty 状态返回体（缺省用标准空列表） */
  emptyBody?: unknown;
  /**
   * 可选：按请求 URL 动态解析 default 返回体（优先于 defaultBody）。
   * 用于同一端点按查询参数返回不同数据的页面（如首页按 status 统计任务数）。
   */
  resolveBody?: (url: string) => unknown;
}

export interface PageSpec {
  module: string;
  pageName: string;
  route: string;
  pageType: PageType;
  states: AuditState[];
  /** 默认 true；登录页/错误页为 false */
  requiresAuth?: boolean;
  /** 状态切换作用于此 API；undefined 表示页面无主数据 API（纯静态页） */
  primary?: ApiMock;
  /** 页面依赖的其他 API，始终返回 defaultBody */
  extras?: ApiMock[];
}

const LIST_STATES: AuditState[] = ['default', 'empty', 'loading', 'error'];
const DETAIL_STATES: AuditState[] = ['default', 'loading', 'error'];
const DASHBOARD_STATES: AuditState[] = ['default', 'loading', 'error'];

export const AUDIT_PAGES: PageSpec[] = [
  // === dashboard ===
  // 首页对同一端点发 5 个统计查询（全量 + 4 状态，page_size=1 仅取 total），
  // 用 resolveBody 按 status 参数分流；loading/error 作用于全部统计查询。
  {
    module: 'dashboard',
    pageName: 'home',
    route: '/',
    pageType: 'dashboard',
    states: DASHBOARD_STATES,
    primary: {
      pattern: /\/api\/v1\/training-jobs(\?.*)?$/,
      defaultBody: dashboardJobStats.all,
      resolveBody: resolveDashboardJobStats,
    },
    extras: [
      {
        pattern: /\/api\/v1\/datasets(\?.*)?$/,
        defaultBody: datasetListResponse,
      },
      {
        pattern: /\/api\/v1\/models(\?.*)?$/,
        defaultBody: modelListResponse,
      },
    ],
  },

  // === auth ===
  { module: 'auth', pageName: 'login', route: '/login', pageType: 'special', states: ['default'], requiresAuth: false },

  // === training ===
  {
    module: 'training',
    pageName: 'training-list',
    route: '/training-jobs',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/training-jobs(\?.*)?$/,
      defaultBody: createPaginatedResponse(mockTrainingJobs, 1, 20),
    },
  },
  { module: 'training', pageName: 'training-create', route: '/training-jobs/create', pageType: 'form', states: ['default'] },
  {
    module: 'training',
    pageName: 'training-detail',
    route: '/training-jobs/1',
    pageType: 'detail',
    states: DETAIL_STATES,
    primary: {
      pattern: /\/api\/v1\/training-jobs\/(\d+)$/,
      defaultBody: getMockTrainingJobDetail(1),
    },
  },
  // 注意：CheckpointsPage 初始渲染不发 checkpoints 请求（需先选任务，enabled 守卫），
  // 静态截图呈现"请选择训练任务"初始态；primary 仍按页面主数据语义指向 checkpoints 端点，
  // 任务下拉数据由 extras 提供。
  {
    module: 'training',
    pageName: 'checkpoints',
    route: '/checkpoints',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/training-jobs\/(\d+)\/checkpoints$/,
      defaultBody: checkpointListResponse,
    },
    extras: [
      {
        pattern: /\/api\/v1\/training-jobs(\?.*)?$/,
        defaultBody: createPaginatedResponse(mockTrainingJobs, 1, 100),
      },
    ],
  },

  // === templates ===
  {
    module: 'templates',
    pageName: 'template-list',
    route: '/job-templates',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/job-templates(\?.*)?$/,
      defaultBody: templateListResponse,
    },
    extras: [
      {
        // 热门模板卡片（返回裸数组，非分页对象）
        pattern: /\/api\/v1\/job-templates\/popular(\?.*)?$/,
        defaultBody: popularTemplatesResponse,
      },
    ],
  },
  {
    module: 'templates',
    pageName: 'template-detail',
    route: '/job-templates/1',
    pageType: 'detail',
    states: DETAIL_STATES,
    primary: {
      pattern: /\/api\/v1\/job-templates\/(\d+)$/,
      defaultBody: templateDetailResponse,
    },
  },

  // === models ===
  {
    module: 'models',
    pageName: 'model-list',
    route: '/models',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/models(\?.*)?$/,
      defaultBody: modelListResponse,
    },
  },
  {
    module: 'models',
    pageName: 'model-detail',
    route: '/models/1',
    pageType: 'detail',
    states: DETAIL_STATES,
    primary: {
      pattern: /\/api\/v1\/models\/(\d+)$/,
      defaultBody: modelDetailResponse,
    },
  },
  {
    module: 'models',
    pageName: 'model-versions',
    route: '/models/1/versions',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      // 响应形状为 { model_name, versions, comparison }，empty 态需显式声明
      pattern: /\/api\/v1\/models\/(\d+)\/versions(\?.*)?$/,
      defaultBody: modelVersionsResponse,
      emptyBody: emptyModelVersionsResponse,
    },
    extras: [
      {
        pattern: /\/api\/v1\/models\/(\d+)$/,
        defaultBody: modelDetailResponse,
      },
    ],
  },

  // === datasets ===
  {
    module: 'datasets',
    pageName: 'dataset-list',
    route: '/datasets',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/datasets(\?.*)?$/,
      defaultBody: datasetListResponse,
    },
  },
  { module: 'datasets', pageName: 'dataset-create', route: '/datasets/create', pageType: 'form', states: ['default'] },
  {
    module: 'datasets',
    pageName: 'dataset-detail',
    route: '/datasets/1',
    pageType: 'detail',
    states: DETAIL_STATES,
    primary: {
      pattern: /\/api\/v1\/datasets\/(\d+)$/,
      defaultBody: datasetDetailResponse,
    },
    extras: [
      {
        // 详情页版本 Tab 请求，显式声明保证 default 截图信息完整
        pattern: /\/api\/v1\/datasets\/(\d+)\/versions$/,
        defaultBody: datasetVersionListResponse,
      },
    ],
  },
  {
    module: 'datasets',
    pageName: 'dataset-versions',
    route: '/datasets/1/versions',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      // 响应形状为 { items, total }（无分页字段）
      pattern: /\/api\/v1\/datasets\/(\d+)\/versions$/,
      defaultBody: datasetVersionListResponse,
      emptyBody: emptyDatasetVersionListResponse,
    },
    extras: [
      {
        pattern: /\/api\/v1\/datasets\/(\d+)$/,
        defaultBody: datasetDetailResponse,
      },
    ],
  },

  // === resource-quotas ===
  {
    module: 'resource-quotas',
    pageName: 'resource-quotas',
    route: '/resource-quotas',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/resource-limit-configs(\?.*)?$/,
      defaultBody: createResourceLimitConfigResponse(),
    },
  },

  // === spaces ===
  // 注意：空间 ID 为 UUID 字符串，detail 路由用真实 mock 的首个 UUID。
  {
    module: 'spaces',
    pageName: 'space-list',
    route: '/spaces',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/spaces(\?.*)?$/,
      defaultBody: createSpaceListResponse(mockSpaces),
    },
  },
  { module: 'spaces', pageName: 'space-create', route: '/spaces/create', pageType: 'form', states: ['default'] },
  {
    module: 'spaces',
    pageName: 'space-detail',
    route: `/spaces/${mockSpaces[0].id}`,
    pageType: 'detail',
    states: DETAIL_STATES,
    primary: {
      pattern: /\/api\/v1\/spaces\/[0-9a-f-]+$/,
      defaultBody: mockSpaces[0],
    },
  },
  // IDE 页直接复用 SpaceListPage 组件，数据依赖与 space-list 相同（仅 default 态）
  {
    module: 'spaces',
    pageName: 'ide',
    route: '/ide',
    pageType: 'special',
    states: ['default'],
    primary: {
      pattern: /\/api\/v1\/spaces(\?.*)?$/,
      defaultBody: createSpaceListResponse(mockSpaces),
    },
  },

  // === monitoring ===
  // /monitoring/utilization 与 /monitoring/metrics 返回裸数组（MetricSeries[]/ResourceUtilization[]），
  // 不可落入 catch-all 的 {items} 兜底，必须显式声明。
  // 页面把 clusters/utilization/alerts/metrics 四个查询的 loading 合并渲染，
  // primary 指向 clusters（错误态也由它驱动）。
  {
    module: 'monitoring',
    pageName: 'monitoring',
    route: '/monitoring',
    pageType: 'dashboard',
    states: DASHBOARD_STATES,
    primary: {
      pattern: /\/api\/v1\/clusters(\?.*)?$/,
      defaultBody: clusterListResponse,
    },
    extras: [
      {
        pattern: /\/api\/v1\/monitoring\/utilization(\?.*)?$/,
        defaultBody: resourceUtilization,
      },
      {
        pattern: /\/api\/v1\/monitoring\/alerts(\?.*)?$/,
        defaultBody: alertListResponse,
      },
      {
        pattern: /\/api\/v1\/monitoring\/metrics(\?.*)?$/,
        defaultBody: metricSeriesResponse,
      },
    ],
  },

  // === audit ===
  {
    module: 'audit',
    pageName: 'audit-logs',
    route: '/audit-logs',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/audit-logs(\?.*)?$/,
      defaultBody: auditLogListResponse,
    },
  },

  // === admin ===
  { module: 'admin', pageName: 'admin-home', route: '/admin', pageType: 'dashboard', states: ['default'] },
  {
    module: 'admin',
    pageName: 'user-management',
    route: '/admin/users',
    pageType: 'list',
    states: LIST_STATES,
    primary: {
      pattern: /\/api\/v1\/users(\?.*)?$/,
      defaultBody: userListResponse,
    },
  },

  // === reports ===
  // /reports/* 返回 { summary, breakdown, daily_* } 复合对象（非列表形状），
  // 落入 catch-all 会让摘要卡/图表全部空白，必须显式声明。
  {
    module: 'reports',
    pageName: 'reports-home',
    route: '/reports',
    pageType: 'dashboard',
    states: ['default'],
    primary: {
      pattern: /\/api\/v1\/reports\/resource-usage(\?.*)?$/,
      defaultBody: resourceUsageResponse,
    },
  },
  {
    module: 'reports',
    pageName: 'resource-usage',
    route: '/reports/resource-usage',
    pageType: 'dashboard',
    states: DASHBOARD_STATES,
    primary: {
      pattern: /\/api\/v1\/reports\/resource-usage(\?.*)?$/,
      defaultBody: resourceUsageResponse,
    },
  },
  {
    module: 'reports',
    pageName: 'cost-analysis',
    route: '/reports/cost-analysis',
    pageType: 'dashboard',
    states: DASHBOARD_STATES,
    primary: {
      pattern: /\/api\/v1\/reports\/cost-analysis(\?.*)?$/,
      defaultBody: costAnalysisResponse,
    },
  },

  // === 错误页 ===
  { module: 'shared', pageName: 'not-found', route: '/404', pageType: 'special', states: ['default'], requiresAuth: false },
  { module: 'shared', pageName: 'unauthorized', route: '/unauthorized', pageType: 'special', states: ['default'], requiresAuth: false },
];

/** 预期截图总数 = Σ(states) × 2 主题 */
export const EXPECTED_SCREENSHOT_COUNT = AUDIT_PAGES.reduce((sum, p) => sum + p.states.length, 0) * 2;
