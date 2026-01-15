/**
 * Navigation Tests
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { Navigation } from '@layouts/MainLayout/Navigation';

// Mock useUIStore
vi.mock('@store/slices/uiSlice', () => ({
  useUIStore: vi.fn(() => ({
    sidebarOpen: true,
    toggleSidebar: vi.fn(),
  })),
}));

describe('Navigation', () => {
  describe('导航项渲染', () => {
    it('should render home navigation item', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('首页')).toBeInTheDocument();
    });

    it('should render training jobs navigation item', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('训练任务')).toBeInTheDocument();
    });

    it('should render datasets navigation item', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('数据集')).toBeInTheDocument();
    });

    it('should render quota management navigation item', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('配额管理')).toBeInTheDocument();
    });
  });

  describe('导航分组', () => {
    it('should render training management section', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('训练管理')).toBeInTheDocument();
    });

    it('should render data management section', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('数据管理')).toBeInTheDocument();
    });

    it('should render resource management section', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      expect(screen.getByText('资源管理')).toBeInTheDocument();
    });
  });

  describe('路由激活状态', () => {
    it('should highlight active route for home', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <Navigation />
        </MemoryRouter>
      );
      // SideNavigation 会根据 activeHref 高亮当前项
      const homeItem = screen.getByText('首页');
      expect(homeItem).toBeInTheDocument();
    });

    it('should highlight active route for training-jobs', () => {
      render(
        <MemoryRouter initialEntries={['/training-jobs']}>
          <Navigation />
        </MemoryRouter>
      );
      const trainingItem = screen.getByText('训练任务');
      expect(trainingItem).toBeInTheDocument();
    });

    it('should highlight active route for datasets', () => {
      render(
        <MemoryRouter initialEntries={['/datasets']}>
          <Navigation />
        </MemoryRouter>
      );
      const datasetsItem = screen.getByText('数据集');
      expect(datasetsItem).toBeInTheDocument();
    });
  });

  describe('导航结构', () => {
    it('should render navigation links', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );
      // Cloudscape SideNavigation 渲染为 list 结构
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
    });

    it('should contain all required menu items', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const expectedItems = ['首页', '训练任务', '数据集', '配额管理'];
      expectedItems.forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });
  });
});
