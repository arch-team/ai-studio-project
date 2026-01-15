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
import { App } from './App';

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
