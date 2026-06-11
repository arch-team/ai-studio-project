/**
 * TopNavigation Tests
 *
 * 验证顶部导航栏渲染：平台标识、全局搜索、图标按钮（通知/帮助）、
 * 外观设置与用户菜单。
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
      // 搜索框通过 aria-label 定位（比 placeholder 更稳健）
      const searchInputs = screen.getAllByLabelText('全局搜索');
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
      // 未登录时用户菜单显示「未登录」，通过 aria-label 定位触发器
      const userMenus = screen.getAllByLabelText('用户菜单');
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
      // 帮助为图标按钮，通过 aria-label 定位
      const helpItems = screen.getAllByLabelText('帮助文档');
      expect(helpItems.length).toBeGreaterThan(0);
    });

    it('should render notifications button', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      // 通知为图标按钮，通过 aria-label 定位
      const notificationItems = screen.getAllByLabelText('通知');
      expect(notificationItems.length).toBeGreaterThan(0);
    });

    it('should render appearance settings', () => {
      render(
        <BrowserRouter>
          <TopNav />
        </BrowserRouter>
      );
      // 外观设置（主题/密度切换）入口
      const settingsItems = screen.getAllByLabelText('外观设置');
      expect(settingsItems.length).toBeGreaterThan(0);
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
