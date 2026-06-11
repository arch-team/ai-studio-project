/**
 * Application Entry Point
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 应用入口文件
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { applyBrandTheme } from '@shared/theme';
import { App } from './App';

// 在 React 渲染前应用品牌主题，避免首屏主题闪烁
applyBrandTheme();

// 获取根元素
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Failed to find the root element');
}

// 创建并渲染应用
createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
