/**
 * TopNavigation Tests
 *
 * Task: T018 - 创建 Cloudscape Layout
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TopNav } from '@layouts/MainLayout/TopNavigation';

describe('TopNavigation', () => {
  describe('渲染', () => {
    it('should render platform title', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      // Cloudscape TopNavigation 可能渲染多个标题实例
      const titles = screen.getAllByText('AI 训练平台');
      expect(titles.length).toBeGreaterThan(0);
    });

    it('should render search input', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      // Cloudscape TopNavigation 可能渲染多个搜索框实例
      const searchInputs = screen.getAllByPlaceholderText('搜索...');
      expect(searchInputs.length).toBeGreaterThan(0);
    });
  });

  describe('用户菜单', () => {
    it('should render user dropdown trigger', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      // Cloudscape TopNavigation 用户菜单
      const userMenus = screen.getAllByText('用户');
      expect(userMenus.length).toBeGreaterThan(0);
    });
  });

  describe('辅助功能', () => {
    it('should render help link', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      const helpItems = screen.getAllByText('帮助');
      expect(helpItems.length).toBeGreaterThan(0);
    });

    it('should render notifications button', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      const notificationItems = screen.getAllByText('通知');
      expect(notificationItems.length).toBeGreaterThan(0);
    });
  });

  describe('交互', () => {
    it('should have clickable logo/title for home navigation', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      const titles = screen.getAllByText('AI 训练平台');
      expect(titles.length).toBeGreaterThan(0);
      // 至少一个标题应该包含在可点击元素中
      const hasClickable = titles.some(
        (title) => title.closest('a') || title.closest('button')
      );
      expect(hasClickable).toBe(true);
    });
  });
});
