/**
 * TopNavigation Component
 *
 * 顶部导航栏组件，使用 Cloudscape TopNavigation
 *
 * 特性:
 * - 品牌 Logo + 平台标识
 * - 全局快捷导航搜索（Autosuggest，支持按名称/拼音前缀过滤并直达页面）
 * - 主题切换（明 / 暗 / 跟随系统）
 * - 密度切换（舒适 / 紧凑）
 * - 用户菜单（显示当前用户名与角色）
 */

import {
  Autosuggest,
  TopNavigation,
  TopNavigationProps,
} from '@cloudscape-design/components';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@features/auth';
import { useNotification } from '@shared/events';
import { BRAND_LOGO_ALT, BRAND_LOGO_SRC } from '@shared/theme';
import { useUIStore } from '@store/slices/uiSlice';
import { ROUTES } from '@app/router/routes';
import type { ThemeMode, UserRole } from '@/types/common';
import type { DensityMode } from '@store/slices/uiSlice';

/** 角色中文标签 */
const ROLE_LABELS: Record<UserRole, string> = {
  admin: '系统管理员',
  team_lead: '团队负责人',
  project_manager: '项目经理',
  engineer: '工程师',
  viewer: '访客',
};

/** 全局搜索的可达目的地（按业务域分组，filteringTags 提供英文别名） */
interface SearchDestination {
  value: string;
  label: string;
  description: string;
  tags: string[];
  roles?: UserRole[];
}

const SEARCH_DESTINATIONS: SearchDestination[] = [
  { value: ROUTES.HOME, label: '平台概览', description: '关键指标与系统状态', tags: ['home', 'dashboard'] },
  { value: ROUTES.TRAINING_JOBS, label: '训练任务', description: '分布式训练任务管理', tags: ['training', 'job'] },
  { value: ROUTES.TRAINING_JOB_CREATE, label: '创建训练任务', description: '提交 DDP / FSDP / DeepSpeed 任务', tags: ['create', 'submit'] },
  { value: ROUTES.JOB_TEMPLATES, label: '任务模板', description: '复用训练配置模板', tags: ['template'] },
  { value: ROUTES.MODELS, label: '模型管理', description: '模型注册与版本', tags: ['model'] },
  { value: ROUTES.CHECKPOINTS, label: '检查点', description: '训练检查点管理', tags: ['checkpoint'] },
  { value: ROUTES.DATASETS, label: '数据集', description: '数据集与版本管理', tags: ['dataset', 'data'] },
  { value: ROUTES.SPACES, label: '开发空间', description: '在线 IDE 与交互式开发', tags: ['space', 'ide'] },
  { value: ROUTES.RESOURCE_QUOTAS, label: '配额管理', description: '团队资源配额', tags: ['quota'] },
  { value: ROUTES.MONITORING, label: '资源监控', description: 'GPU / 节点实时监控', tags: ['monitor', 'gpu'] },
  { value: ROUTES.REPORTS, label: '报表概览', description: '使用与成本报表', tags: ['report'], roles: ['admin', 'team_lead'] },
  { value: ROUTES.AUDIT_LOGS, label: '审计日志', description: '操作审计追踪', tags: ['audit', 'log'], roles: ['admin', 'team_lead'] },
  { value: ROUTES.ADMIN, label: '管理后台', description: '系统管理入口', tags: ['admin'], roles: ['admin'] },
  { value: ROUTES.USER_MANAGEMENT, label: '用户管理', description: '用户与角色管理', tags: ['user'], roles: ['admin'] },
];

/**
 * TopNav 组件
 */
export function TopNav() {
  const navigate = useNavigate();
  const notify = useNotification();
  const [searchValue, setSearchValue] = useState('');

  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const density = useUIStore((s) => s.density);
  const setDensity = useUIStore((s) => s.setDensity);

  // 按角色过滤可见的搜索目的地
  const searchOptions = useMemo(() => {
    const role = user?.role;
    return SEARCH_DESTINATIONS.filter(
      (d) => !d.roles || (role && d.roles.includes(role))
    ).map((d) => ({
      value: d.value,
      label: d.label,
      description: d.description,
      filteringTags: d.tags,
    }));
  }, [user?.role]);

  // 偏好设置下拉：主题 + 密度，当前选项显示勾选
  const preferencesUtility: TopNavigationProps.Utility = {
    type: 'menu-dropdown',
    iconName: 'settings',
    ariaLabel: '外观设置',
    title: '外观设置',
    items: [
      {
        id: 'theme',
        text: '主题',
        items: [
          { id: 'theme:light', text: '明亮', disabled: theme === 'light' },
          { id: 'theme:dark', text: '暗黑', disabled: theme === 'dark' },
          { id: 'theme:system', text: '跟随系统', disabled: theme === 'system' },
        ],
      },
      {
        id: 'density',
        text: '密度',
        items: [
          { id: 'density:comfortable', text: '舒适', disabled: density === 'comfortable' },
          { id: 'density:compact', text: '紧凑', disabled: density === 'compact' },
        ],
      },
    ],
    onItemClick: ({ detail }) => {
      const [group, value] = detail.id.split(':');
      if (group === 'theme') {
        setTheme(value as ThemeMode);
        notify.info(`已切换主题：${value === 'system' ? '跟随系统' : value === 'dark' ? '暗黑' : '明亮'}`);
      } else if (group === 'density') {
        setDensity(value as DensityMode);
        notify.info(`已切换密度：${value === 'compact' ? '紧凑' : '舒适'}`);
      }
    },
  };

  const userName = user?.name ?? '未登录';
  const userRoleLabel = user ? ROLE_LABELS[user.role] : undefined;

  const userUtility: TopNavigationProps.Utility = {
    type: 'menu-dropdown',
    text: userName,
    description: userRoleLabel,
    iconName: 'user-profile',
    ariaLabel: '用户菜单',
    onItemClick: ({ detail }) => {
      switch (detail.id) {
        case 'signout':
          logout();
          notify.success('已退出登录');
          navigate(ROUTES.LOGIN);
          break;
        case 'profile':
          navigate('/profile');
          break;
        case 'settings':
          navigate('/settings');
          break;
      }
    },
    items: [
      { id: 'profile', text: '个人资料' },
      { id: 'settings', text: '设置' },
      { id: 'signout', text: '退出登录' },
    ],
  };

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: 'button',
      iconName: 'notification',
      ariaLabel: '通知',
      title: '通知',
      onClick: () => navigate(ROUTES.MONITORING),
    },
    {
      type: 'button',
      iconName: 'status-info',
      ariaLabel: '帮助文档',
      title: '帮助',
      href: 'https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html',
      external: true,
    },
    preferencesUtility,
    userUtility,
  ];

  return (
    <TopNavigation
      identity={{
        href: ROUTES.HOME,
        title: 'AI 训练平台',
        logo: { src: BRAND_LOGO_SRC, alt: BRAND_LOGO_ALT },
        onFollow: (event) => {
          event.preventDefault();
          navigate(ROUTES.HOME);
        },
      }}
      search={
        <Autosuggest
          value={searchValue}
          options={searchOptions}
          placeholder="搜索页面：任务、数据集、模型..."
          ariaLabel="全局搜索"
          enteredTextLabel={(value) => `搜索 "${value}"`}
          empty="未找到匹配的页面"
          onChange={({ detail }) => setSearchValue(detail.value)}
          onSelect={({ detail }) => {
            // 仅当选择了具体目的地（非自由文本）时跳转
            if (detail.selectedOption?.value) {
              navigate(detail.selectedOption.value);
              setSearchValue('');
            }
          }}
        />
      }
      utilities={utilities}
    />
  );
}
