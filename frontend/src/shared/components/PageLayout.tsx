/**
 * PageLayout Component
 *
 * 统一页面模板组件，封装 Cloudscape ContentLayout + Header，
 * 并自动同步面包屑到全局 UI Store。
 *
 * 所有功能页面应使用此组件作为最外层容器，确保:
 * - 一致的页头（标题 + 描述 + 操作区）
 * - 统一的面包屑联动
 * - 统一的内容间距
 * - 可选的品牌 Hero 页头（深空渐变高对比背景，用于首页等门户型页面）
 */

import {
  ContentLayout,
  Header,
  SpaceBetween,
  type HeaderProps,
} from '@cloudscape-design/components';
import { useEffect } from 'react';
import { useUIStore } from '@store/slices/uiSlice';
import { heroHeaderBackground } from '@shared/theme';
import type { BreadcrumbItem } from '@/types/common';

export interface PageLayoutProps {
  /** 页面标题 */
  title: string;
  /** 标题下方的描述文本 */
  description?: React.ReactNode;
  /** 标题右侧的操作区（按钮组等） */
  actions?: React.ReactNode;
  /** 计数信息，如 "(20)"，显示在标题右侧 */
  counter?: string;
  /** 标题层级，默认 h1 */
  headerVariant?: HeaderProps['variant'];
  /**
   * 品牌 Hero 页头。开启后页头使用深空渐变背景 + 高对比文字，
   * 适用于首页 / 门户型页面，让关键页面更具品牌识别度。
   */
  hero?: boolean;
  /** Hero 模式下显示在标题区的附加内容（如欢迎语下的指标摘要） */
  heroExtra?: React.ReactNode;
  /**
   * 面包屑配置。传入后会自动同步到全局 UI Store，
   * MainLayout 会据此渲染 BreadcrumbGroup。
   * 不传则清空面包屑（仅显示页面本身）。
   */
  breadcrumbs?: BreadcrumbItem[];
  /** 页面内容 */
  children: React.ReactNode;
}

/**
 * PageLayout 组件
 *
 * @example
 * ```tsx
 * <PageLayout
 *   title="训练任务"
 *   description="管理和监控分布式训练任务"
 *   counter={`(${total})`}
 *   actions={<Button variant="primary">创建任务</Button>}
 *   breadcrumbs={[
 *     { text: '首页', href: '/' },
 *     { text: '训练任务', href: '/training-jobs' },
 *   ]}
 * >
 *   <TrainingJobTable />
 * </PageLayout>
 * ```
 */
export function PageLayout({
  title,
  description,
  actions,
  counter,
  headerVariant = 'h1',
  hero = false,
  heroExtra,
  breadcrumbs,
  children,
}: PageLayoutProps) {
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs(breadcrumbs ?? []);
    // 离开页面时清空，避免残留到下一个页面
    return () => setBreadcrumbs([]);
  }, [breadcrumbs, setBreadcrumbs]);

  return (
    <ContentLayout
      headerVariant={hero ? 'high-contrast' : 'default'}
      headerBackgroundStyle={hero ? heroHeaderBackground : undefined}
      header={
        hero && heroExtra ? (
          <SpaceBetween size="m">
            <Header
              variant={headerVariant}
              description={description}
              counter={counter}
              actions={actions}
            >
              {title}
            </Header>
            {heroExtra}
          </SpaceBetween>
        ) : (
          <Header
            variant={headerVariant}
            description={description}
            counter={counter}
            actions={actions}
          >
            {title}
          </Header>
        )
      }
    >
      {children}
    </ContentLayout>
  );
}
