/**
 * Routes Configuration
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 定义应用的所有路由路径常量
 */

/**
 * 路由路径常量
 *
 * 按功能分组：
 * - 公共路由：首页、登录
 * - 训练管理：训练任务、模型
 * - 数据管理：数据集、检查点
 * - 资源管理：资源配额
 * - 管理员：管理后台、报表
 * - 开发工具：IDE
 * - 错误页面：404、未授权
 */
export const ROUTES = {
  // 公共路由
  HOME: '/',
  LOGIN: '/login',

  // 训练管理
  TRAINING_JOBS: '/training-jobs',
  TRAINING_JOB_DETAIL: '/training-jobs/:id',
  TRAINING_JOB_CREATE: '/training-jobs/create',
  MODELS: '/models',
  MODEL_DETAIL: '/models/:id',
  MODEL_VERSIONS: '/models/:id/versions',

  // 数据管理
  DATASETS: '/datasets',
  DATASET_DETAIL: '/datasets/:id',
  CHECKPOINTS: '/checkpoints',

  // 资源管理
  RESOURCE_QUOTAS: '/resource-quotas',

  // 管理员
  ADMIN: '/admin',
  REPORTS: '/reports',

  // 开发工具
  IDE: '/ide',

  // 错误页面
  NOT_FOUND: '/404',
  UNAUTHORIZED: '/unauthorized',
} as const;

/**
 * 路由路径类型
 */
export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES];

/**
 * 生成带参数的路由路径
 */
export function generatePath(
  route: string,
  params: Record<string, string>
): string {
  let path = route;
  for (const [key, value] of Object.entries(params)) {
    path = path.replace(`:${key}`, value);
  }
  return path;
}
