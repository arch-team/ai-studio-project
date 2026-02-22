/**
 * IDE Page (开发空间)
 *
 * 开发空间列表页面 - 管理在线开发环境
 * 复用已有的 SpaceListPage 组件
 */

import { SpaceListPage } from './SpaceListPage';

/**
 * IDE 开发空间页面
 *
 * 当前直接复用 SpaceListPage，因为该页面已经完整实现了
 * 开发空间的列表、筛选、启停和删除功能
 */
export function IDEPage() {
  return <SpaceListPage />;
}

export default IDEPage;
