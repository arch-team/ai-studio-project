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

export type AuditState = 'default' | 'empty' | 'loading' | 'error';
export type PageType = 'list' | 'detail' | 'form' | 'dashboard' | 'special';

export interface ApiMock {
  /** 主数据 API 匹配（注意排除子路径，参考 e2e/utils/mockApi.ts 的正则写法） */
  pattern: RegExp;
  /** default 状态返回体 */
  defaultBody: unknown;
  /** empty 状态返回体（缺省用标准空列表） */
  emptyBody?: unknown;
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
  { module: 'dashboard', pageName: 'home', route: '/', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === auth ===
  { module: 'auth', pageName: 'login', route: '/login', pageType: 'special', states: ['default'], requiresAuth: false },

  // === training ===
  { module: 'training', pageName: 'training-list', route: '/training-jobs', pageType: 'list', states: LIST_STATES },
  { module: 'training', pageName: 'training-create', route: '/training-jobs/create', pageType: 'form', states: ['default'] },
  { module: 'training', pageName: 'training-detail', route: '/training-jobs/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'training', pageName: 'checkpoints', route: '/checkpoints', pageType: 'list', states: LIST_STATES },

  // === templates ===
  { module: 'templates', pageName: 'template-list', route: '/job-templates', pageType: 'list', states: LIST_STATES },
  { module: 'templates', pageName: 'template-detail', route: '/job-templates/1', pageType: 'detail', states: DETAIL_STATES },

  // === models ===
  { module: 'models', pageName: 'model-list', route: '/models', pageType: 'list', states: LIST_STATES },
  { module: 'models', pageName: 'model-detail', route: '/models/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'models', pageName: 'model-versions', route: '/models/1/versions', pageType: 'list', states: LIST_STATES },

  // === datasets ===
  { module: 'datasets', pageName: 'dataset-list', route: '/datasets', pageType: 'list', states: LIST_STATES },
  { module: 'datasets', pageName: 'dataset-create', route: '/datasets/create', pageType: 'form', states: ['default'] },
  { module: 'datasets', pageName: 'dataset-detail', route: '/datasets/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'datasets', pageName: 'dataset-versions', route: '/datasets/1/versions', pageType: 'list', states: LIST_STATES },

  // === resource-quotas ===
  { module: 'resource-quotas', pageName: 'resource-quotas', route: '/resource-quotas', pageType: 'list', states: LIST_STATES },

  // === spaces ===
  { module: 'spaces', pageName: 'space-list', route: '/spaces', pageType: 'list', states: LIST_STATES },
  { module: 'spaces', pageName: 'space-create', route: '/spaces/create', pageType: 'form', states: ['default'] },
  { module: 'spaces', pageName: 'space-detail', route: '/spaces/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'spaces', pageName: 'ide', route: '/ide', pageType: 'special', states: ['default'] },

  // === monitoring ===
  { module: 'monitoring', pageName: 'monitoring', route: '/monitoring', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === audit ===
  { module: 'audit', pageName: 'audit-logs', route: '/audit-logs', pageType: 'list', states: LIST_STATES },

  // === admin ===
  { module: 'admin', pageName: 'admin-home', route: '/admin', pageType: 'dashboard', states: ['default'] },
  { module: 'admin', pageName: 'user-management', route: '/admin/users', pageType: 'list', states: LIST_STATES },

  // === reports ===
  { module: 'reports', pageName: 'reports-home', route: '/reports', pageType: 'dashboard', states: ['default'] },
  { module: 'reports', pageName: 'resource-usage', route: '/reports/resource-usage', pageType: 'dashboard', states: DASHBOARD_STATES },
  { module: 'reports', pageName: 'cost-analysis', route: '/reports/cost-analysis', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === 错误页 ===
  { module: 'shared', pageName: 'not-found', route: '/404', pageType: 'special', states: ['default'], requiresAuth: false },
  { module: 'shared', pageName: 'unauthorized', route: '/unauthorized', pageType: 'special', states: ['default'], requiresAuth: false },
];

/** 预期截图总数 = Σ(states) × 2 主题 */
export const EXPECTED_SCREENSHOT_COUNT = AUDIT_PAGES.reduce((sum, p) => sum + p.states.length, 0) * 2;
