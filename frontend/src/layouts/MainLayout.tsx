import { ReactNode, useState } from 'react';
import {
  AppLayout,
  SideNavigation,
  TopNavigation,
  BreadcrumbGroup,
} from '@cloudscape-design/components';

interface MainLayoutProps {
  children: ReactNode;
}

const navigationItems = [
  { type: 'link' as const, text: '首页', href: '/' },
  { type: 'divider' as const },
  {
    type: 'section' as const,
    text: '训练管理',
    items: [
      { type: 'link' as const, text: '训练任务', href: '/training/jobs' },
      { type: 'link' as const, text: '模型版本', href: '/training/models' },
    ],
  },
  {
    type: 'section' as const,
    text: '数据管理',
    items: [
      { type: 'link' as const, text: '数据集', href: '/datasets' },
    ],
  },
  {
    type: 'section' as const,
    text: '资源管理',
    items: [
      { type: 'link' as const, text: '配额管理', href: '/resources/quotas' },
      { type: 'link' as const, text: '集群监控', href: '/resources/monitoring' },
    ],
  },
  {
    type: 'section' as const,
    text: '开发环境',
    items: [
      { type: 'link' as const, text: 'Spaces', href: '/spaces' },
    ],
  },
];

function MainLayout({ children }: MainLayoutProps) {
  const [navigationOpen, setNavigationOpen] = useState(true);

  return (
    <>
      <TopNavigation
        identity={{
          href: '/',
          title: 'AI 训练平台',
        }}
        utilities={[
          {
            type: 'button',
            text: '文档',
            href: '/docs',
            external: true,
          },
          {
            type: 'menu-dropdown',
            text: '用户',
            iconName: 'user-profile',
            items: [
              { id: 'profile', text: '个人设置' },
              { id: 'logout', text: '退出登录' },
            ],
          },
        ]}
      />
      <AppLayout
        navigation={
          <SideNavigation
            header={{ text: '导航', href: '/' }}
            items={navigationItems}
          />
        }
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        breadcrumbs={
          <BreadcrumbGroup
            items={[{ text: '首页', href: '/' }]}
          />
        }
        content={children}
        toolsHide={true}
      />
    </>
  );
}

export default MainLayout;
