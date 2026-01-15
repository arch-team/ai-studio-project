/**
 * TopNavigation Component
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 2: Green - 实现代码
 *
 * 顶部导航栏组件，使用 Cloudscape TopNavigation
 */

import { Input, TopNavigation, TopNavigationProps } from '@cloudscape-design/components';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * TopNav 组件
 *
 * 顶部导航栏，包含：
 * - 平台标题/Logo
 * - 搜索框
 * - 通知按钮
 * - 帮助链接
 * - 用户菜单
 */
export function TopNav() {
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: 'button',
      text: '通知',
      iconName: 'notification',
      ariaLabel: '通知',
      badge: false,
      disableUtilityCollapse: false,
    },
    {
      type: 'button',
      text: '帮助',
      iconName: 'status-info',
      ariaLabel: '帮助',
      disableUtilityCollapse: false,
    },
    {
      type: 'menu-dropdown',
      text: '用户',
      iconName: 'user-profile',
      onItemClick: ({ detail }) => {
        switch (detail.id) {
          case 'signout':
            navigate('/login');
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
    },
  ];

  return (
    <TopNavigation
      identity={{
        href: '/',
        title: 'AI 训练平台',
        onFollow: (event) => {
          event.preventDefault();
          navigate('/');
        },
      }}
      search={
        <Input
          type="search"
          placeholder="搜索..."
          ariaLabel="搜索"
          value={searchValue}
          onChange={({ detail }) => setSearchValue(detail.value)}
        />
      }
      utilities={utilities}
    />
  );
}
