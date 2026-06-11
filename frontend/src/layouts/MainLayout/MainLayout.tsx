/**
 * MainLayout Component
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 2: Green - 实现代码
 *
 * 主布局组件，使用 Cloudscape AppLayout
 */

import { AppLayout, BreadcrumbGroup } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@store/slices/uiSlice';
import { NotificationCenter } from '@shared/components';
import { Navigation } from './Navigation';
import { TopNav } from './TopNavigation';

interface MainLayoutProps {
  children: React.ReactNode;
}

/**
 * MainLayout 组件
 *
 * 应用主布局，包含：
 * - 顶部导航栏 (TopNavigation)
 * - 侧边导航 (Navigation)
 * - 面包屑导航 (Breadcrumbs)
 * - 内容区域 (Content)
 */
export function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate();
  const { sidebarOpen, setSidebarOpen, breadcrumbs } = useUIStore();

  const breadcrumbItems = breadcrumbs.map((item) => ({
    text: item.text,
    href: item.href || '#',
  }));

  return (
    <>
      <div id="top-navigation">
        <TopNav />
      </div>
      <AppLayout
        navigation={<Navigation />}
        navigationOpen={sidebarOpen}
        onNavigationChange={({ detail }) => setSidebarOpen(detail.open)}
        breadcrumbs={
          breadcrumbItems.length > 0 ? (
            <BreadcrumbGroup
              items={breadcrumbItems}
              ariaLabel="面包屑导航"
              onFollow={(event) => {
                event.preventDefault();
                navigate(event.detail.href);
              }}
            />
          ) : undefined
        }
        notifications={<NotificationCenter />}
        stickyNotifications
        content={children}
        toolsHide={true}
        headerSelector="#top-navigation"
      />
    </>
  );
}
