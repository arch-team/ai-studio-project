/**
 * Navigation Component
 *
 * 侧边导航栏组件，使用 Cloudscape SideNavigation
 *
 * 特性:
 * - 覆盖全部业务模块 (训练/数据/资源/开发/监控/系统管理)
 * - 按用户角色动态过滤管理类入口
 * - 基于当前路由自动高亮 active 项
 */

import { SideNavigation, SideNavigationProps } from '@cloudscape-design/components';
import { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@features/auth';
import type { UserRole } from '@/types/common';
import { ROUTES } from '@app/router/routes';

/**
 * 顶部 Header（平台标识）
 */
const navHeader: SideNavigationProps['header'] = {
  href: ROUTES.HOME,
  text: 'AI 训练平台',
};

/**
 * 基础导航项（所有登录用户可见）
 */
const baseItems: SideNavigationProps.Item[] = [
  {
    type: 'link',
    text: '首页',
    href: ROUTES.HOME,
  },
  { type: 'divider' },
  {
    type: 'section-group',
    title: '训练管理',
    items: [
      { type: 'link', text: '训练任务', href: ROUTES.TRAINING_JOBS },
      { type: 'link', text: '任务模板', href: ROUTES.JOB_TEMPLATES },
      { type: 'link', text: '模型管理', href: ROUTES.MODELS },
      { type: 'link', text: '检查点', href: ROUTES.CHECKPOINTS },
    ],
  },
  {
    type: 'section-group',
    title: '数据管理',
    items: [{ type: 'link', text: '数据集', href: ROUTES.DATASETS }],
  },
  {
    type: 'section-group',
    title: '开发空间',
    items: [
      { type: 'link', text: '我的空间', href: ROUTES.SPACES },
      { type: 'link', text: '在线 IDE', href: ROUTES.IDE },
    ],
  },
  {
    type: 'section-group',
    title: '资源管理',
    items: [
      { type: 'link', text: '配额管理', href: ROUTES.RESOURCE_QUOTAS },
      { type: 'link', text: '资源监控', href: ROUTES.MONITORING },
    ],
  },
];

/**
 * 报表入口（admin / team_lead 可见）
 */
const reportItems: SideNavigationProps.Item[] = [
  {
    type: 'section-group',
    title: '报表中心',
    items: [
      { type: 'link', text: '报表概览', href: ROUTES.REPORTS },
      { type: 'link', text: '资源使用报表', href: ROUTES.REPORTS_RESOURCE_USAGE },
      { type: 'link', text: '成本分析', href: ROUTES.REPORTS_COST_ANALYSIS },
      { type: 'link', text: '审计日志', href: ROUTES.AUDIT_LOGS },
    ],
  },
];

/**
 * 系统管理入口（admin 可见）
 */
const adminItems: SideNavigationProps.Item[] = [
  {
    type: 'section-group',
    title: '系统管理',
    items: [
      { type: 'link', text: '管理后台', href: ROUTES.ADMIN },
      { type: 'link', text: '用户管理', href: ROUTES.USER_MANAGEMENT },
    ],
  },
];

const EXTERNAL_LINKS: SideNavigationProps.Item[] = [
  { type: 'divider' },
  {
    type: 'link',
    text: '使用文档',
    href: 'https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html',
    external: true,
  },
];

/**
 * 根据角色构建导航项
 */
function buildItems(role: UserRole | undefined): SideNavigationProps.Item[] {
  const items = [...baseItems];

  if (role === 'admin' || role === 'team_lead') {
    items.push(...reportItems);
  }
  if (role === 'admin') {
    items.push(...adminItems);
  }

  items.push(...EXTERNAL_LINKS);
  return items;
}

/**
 * 计算当前激活的导航 href
 *
 * 对子路径（如 /training-jobs/123）匹配其顶层入口（/training-jobs），
 * 确保进入详情页时父级导航仍保持高亮。
 */
function resolveActiveHref(pathname: string): string {
  if (pathname === ROUTES.HOME) return ROUTES.HOME;

  const candidates = [
    ROUTES.TRAINING_JOBS,
    ROUTES.JOB_TEMPLATES,
    ROUTES.MODELS,
    ROUTES.CHECKPOINTS,
    ROUTES.DATASETS,
    ROUTES.SPACES,
    ROUTES.IDE,
    ROUTES.RESOURCE_QUOTAS,
    ROUTES.MONITORING,
    ROUTES.REPORTS_RESOURCE_USAGE,
    ROUTES.REPORTS_COST_ANALYSIS,
    ROUTES.REPORTS,
    ROUTES.AUDIT_LOGS,
    ROUTES.USER_MANAGEMENT,
    ROUTES.ADMIN,
  ];

  // 优先匹配最长前缀，避免 /reports 抢占 /reports/resource-usage
  const match = candidates
    .filter((href) => pathname === href || pathname.startsWith(`${href}/`))
    .sort((a, b) => b.length - a.length)[0];

  return match ?? pathname;
}

/**
 * Navigation 组件
 *
 * 侧边导航栏，覆盖全部业务模块，并按用户角色过滤管理类入口。
 */
export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const role = useAuthStore((s) => s.user?.role);

  const items = useMemo(() => buildItems(role), [role]);
  const activeHref = useMemo(
    () => resolveActiveHref(location.pathname),
    [location.pathname]
  );

  const handleFollow: SideNavigationProps['onFollow'] = (event) => {
    // 外部链接保持默认行为（新标签打开）
    if (event.detail.external) {
      return;
    }
    event.preventDefault();
    navigate(event.detail.href);
  };

  return (
    <SideNavigation
      header={navHeader}
      activeHref={activeHref}
      items={items}
      onFollow={handleFollow}
    />
  );
}
