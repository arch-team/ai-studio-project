/**
 * 应用程序入口文件
 *
 * 初始化React应用,配置全局providers和路由
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { AuthProvider } from './services/auth/AuthContext';
import AppRouter from './router';
import './index.css';

// 创建React根节点
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// 渲染应用
root.render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>
);
