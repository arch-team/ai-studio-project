/**
 * MainLayout Tests
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MainLayout } from '@layouts/MainLayout';

// Mock useUIStore
vi.mock('@store/slices/uiSlice', () => ({
  useUIStore: vi.fn(() => ({
    sidebarOpen: true,
    toggleSidebar: vi.fn(),
    breadcrumbs: [],
  })),
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('MainLayout', () => {
  describe('渲染', () => {
    it('should render children content', () => {
      renderWithRouter(
        <MainLayout>
          <div data-testid="test-content">测试内容</div>
        </MainLayout>
      );
      expect(screen.getByTestId('test-content')).toBeInTheDocument();
    });

    it('should render platform title in header', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      // Cloudscape TopNavigation 可能渲染多个标题实例
      const titles = screen.getAllByText('AI 训练平台');
      expect(titles.length).toBeGreaterThan(0);
    });

    it('should render navigation component', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      // 检查导航菜单是否存在（Cloudscape 渲染为 link 列表）
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
    });
  });

  describe('导航菜单', () => {
    it('should render navigation sections', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      // 检查主要导航项
      expect(screen.getByText('首页')).toBeInTheDocument();
    });

    it('should render training management section', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      expect(screen.getByText('训练管理')).toBeInTheDocument();
    });

    it('should render data management section', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      expect(screen.getByText('数据管理')).toBeInTheDocument();
    });

    it('should render resource management section', () => {
      renderWithRouter(
        <MainLayout>
          <div>内容</div>
        </MainLayout>
      );
      expect(screen.getByText('资源管理')).toBeInTheDocument();
    });
  });

  describe('内容区域', () => {
    it('should render main content area', () => {
      renderWithRouter(
        <MainLayout>
          <main data-testid="main-content">主内容</main>
        </MainLayout>
      );
      expect(screen.getByTestId('main-content')).toBeInTheDocument();
    });

    it('should render multiple children correctly', () => {
      renderWithRouter(
        <MainLayout>
          <div data-testid="child-1">子组件1</div>
          <div data-testid="child-2">子组件2</div>
        </MainLayout>
      );
      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });
  });
});
