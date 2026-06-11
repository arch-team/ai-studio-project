/**
 * TopNavigation Component
 *
 * 顶部导航栏组件，使用 Cloudscape TopNavigation
 *
 * 特性:
 * - 平台标识 + 全局搜索
 * - 主题切换（明 / 暗 / 跟随系统）
 * - 密度切换（舒适 / 紧凑）
 * - 用户菜单（显示当前用户名与角色）
 */

import { Input, TopNavigation, TopNavigationProps } from '@cloudscape-design/components';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@features/auth';
import { useNotification } from '@shared/events';
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
        onFollow: (event) => {
          event.preventDefault();
          navigate(ROUTES.HOME);
        },
      }}
      search={
        <Input
          type="search"
          placeholder="搜索任务、数据集、模型..."
          ariaLabel="全局搜索"
          value={searchValue}
          onChange={({ detail }) => setSearchValue(detail.value)}
        />
      }
      utilities={utilities}
    />
  );
}
