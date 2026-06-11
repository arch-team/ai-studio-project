/**
 * PageLayout Tests
 *
 * 验证统一页面模板：渲染标题/描述/操作区，并将面包屑同步到 UI Store。
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '@cloudscape-design/components';
import { PageLayout } from '@shared/components';
import { useUIStore } from '@store/slices/uiSlice';

describe('PageLayout', () => {
  beforeEach(() => {
    useUIStore.getState().setBreadcrumbs([]);
  });

  it('应渲染标题与内容', () => {
    render(
      <PageLayout title="训练任务">
        <div>页面内容</div>
      </PageLayout>
    );
    expect(screen.getByText('训练任务')).toBeInTheDocument();
    expect(screen.getByText('页面内容')).toBeInTheDocument();
  });

  it('应渲染描述与操作区', () => {
    render(
      <PageLayout
        title="数据集"
        description="管理训练数据集"
        actions={<Button>创建</Button>}
      >
        <div>内容</div>
      </PageLayout>
    );
    expect(screen.getByText('管理训练数据集')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument();
  });

  it('应将面包屑同步到 UI Store', () => {
    const breadcrumbs = [
      { text: '首页', href: '/' },
      { text: '模型', href: '/models' },
    ];
    render(
      <PageLayout title="模型" breadcrumbs={breadcrumbs}>
        <div>内容</div>
      </PageLayout>
    );
    expect(useUIStore.getState().breadcrumbs).toEqual(breadcrumbs);
  });

  it('卸载时应清空面包屑', () => {
    const breadcrumbs = [{ text: '首页', href: '/' }];
    const { unmount } = render(
      <PageLayout title="测试" breadcrumbs={breadcrumbs}>
        <div>内容</div>
      </PageLayout>
    );
    expect(useUIStore.getState().breadcrumbs).toEqual(breadcrumbs);

    unmount();
    expect(useUIStore.getState().breadcrumbs).toEqual([]);
  });
});
