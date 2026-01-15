/**
 * MainLayout Component
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 2: Green - 实现代码
 *
 * 主布局组件，使用 Cloudscape AppLayout
 */

import { AppLayout, BreadcrumbGroup } from '@cloudscape-design/components';
import { useUIStore } from '@store/slices/uiSlice';
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
  const { sidebarOpen, toggleSidebar, breadcrumbs } = useUIStore();

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
        onNavigationChange={() => toggleSidebar()}
        breadcrumbs={
          breadcrumbItems.length > 0 ? (
            <BreadcrumbGroup items={breadcrumbItems} />
          ) : undefined
        }
        content={children}
        toolsHide={true}
        headerSelector="#top-navigation"
      />
    </>
  );
}
