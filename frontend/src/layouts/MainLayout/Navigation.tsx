/**
 * Navigation Component
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 2: Green - 实现代码
 *
 * 侧边导航栏组件，使用 Cloudscape SideNavigation
 */

import { SideNavigation, SideNavigationProps } from '@cloudscape-design/components';
import { useLocation, useNavigate } from 'react-router-dom';

/**
 * 导航项配置
 */
const navigationItems: SideNavigationProps.Item[] = [
  {
    type: 'link',
    text: '首页',
    href: '/',
  },
  {
    type: 'section',
    text: '训练管理',
    items: [
      {
        type: 'link',
        text: '训练任务',
        href: '/training-jobs',
      },
      {
        type: 'link',
        text: '模型管理',
        href: '/models',
      },
    ],
  },
  {
    type: 'section',
    text: '数据管理',
    items: [
      {
        type: 'link',
        text: '数据集',
        href: '/datasets',
      },
      {
        type: 'link',
        text: '检查点',
        href: '/checkpoints',
      },
    ],
  },
  {
    type: 'section',
    text: '资源管理',
    items: [
      {
        type: 'link',
        text: '配额管理',
        href: '/resource-quotas',
      },
    ],
  },
];

/**
 * Navigation 组件
 *
 * 侧边导航栏，包含：
 * - 首页链接
 * - 训练管理分组
 * - 数据管理分组
 * - 资源管理分组
 */
export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleFollow: SideNavigationProps['onFollow'] = (event) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  return (
    <SideNavigation
      activeHref={location.pathname}
      items={navigationItems}
      onFollow={handleFollow}
    />
  );
}
