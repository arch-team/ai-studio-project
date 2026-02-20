## EVAL: frontend-core
Created: 2026-02-20
Module: frontend/src/app/ + frontend/src/layouts/ + frontend/src/lib/ + frontend/src/store/
Phase: 2 (Foundational)
Tasks: T017-T020

### Capability Evals

#### 路由配置 (T017)
- [ ] React Router 正确配置所有主要路由 (/training-jobs, /datasets, /models, /admin, /reports, /spaces, /monitoring)
- [ ] AuthGuard 正确拦截未认证用户并重定向到登录页
- [ ] RoleGuard 根据用户角色限制路由访问 (admin 页面仅 admin 可访问)
- [ ] 404 页面正确渲染

#### Cloudscape Layout (T018)
- [ ] MainLayout 使用 AppLayout 组件正确渲染
- [ ] 侧边导航 (Navigation) 包含所有功能模块入口
- [ ] 顶部导航 (TopNavigation) 显示用户信息和操作菜单
- [ ] 导航高亮当前活动路由
- [ ] 响应式布局适配不同屏幕尺寸

#### 状态管理 (T019)
- [ ] Zustand store 正确初始化
- [ ] uiSlice 管理侧边栏折叠/展开状态
- [ ] notificationSlice 管理通知消息队列
- [ ] 状态持久化正确执行

#### TanStack Query (T020)
- [ ] QueryClient 配置全局重试策略 (3 次)
- [ ] QueryClient 配置缓存策略 (staleTime)
- [ ] Query Key 工厂模式正确实现
- [ ] 查询错误时自动重试
- [ ] 查询数据正确缓存和失效

#### 所有 Feature 模块前端
- [ ] 所有 Cloudscape UI 组件来自 @cloudscape-design/components (无 MUI/Ant Design)
- [ ] 所有页面遵循 Feature-Sliced Design (pages -> components -> hooks -> api -> types)
- [ ] 所有 API 调用使用 TanStack Query hooks
- [ ] TypeScript 类型定义完整，无 any 类型

### Regression Evals
- [ ] 路由守卫测试 (AuthGuard, RoleGuard) 全部通过
- [ ] Layout 组件测试 (MainLayout, Navigation, TopNavigation) 全部通过
- [ ] Store 切片测试 (uiSlice, notificationSlice) 全部通过
- [ ] QueryClient 配置测试全部通过
- [ ] 无 ESLint 错误
- [ ] TypeScript 编译无错误

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 前端单元测试覆盖率 >= 70%
- 首屏加载 <3 秒
- WCAG 2.1 AA 级别合规
- 所有 UI 组件来自 Cloudscape Design System
