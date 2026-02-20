## EVAL: frontend-core
Created: 2026-02-20
Last Check: 2026-02-20
Module: frontend/src/app/ + frontend/src/layouts/ + frontend/src/lib/ + frontend/src/store/
Phase: 2 (Foundational)
Tasks: T017-T020

### Capability Evals

#### 路由配置 (T017)
- [x] React Router 正确配置所有主要路由 (/training-jobs, /datasets, /models, /admin, /reports, /spaces, /monitoring)
- [x] AuthGuard 正确拦截未认证用户并重定向到登录页
- [x] RoleGuard 根据用户角色限制路由访问 (admin 页面仅 admin 可访问)
- [x] 404 页面正确渲染

#### Cloudscape Layout (T018)
- [x] MainLayout 使用 AppLayout 组件正确渲染
- [x] 侧边导航 (Navigation) 包含所有功能模块入口
- [x] 顶部导航 (TopNavigation) 显示用户信息和操作菜单
- [x] 导航高亮当前活动路由
- [x] 响应式布局适配不同屏幕尺寸

#### 状态管理 (T019)
- [x] Zustand store 正确初始化
- [x] uiSlice 管理侧边栏折叠/展开状态
- [x] notificationSlice 管理通知消息队列
- [x] 状态持久化正确执行

#### TanStack Query (T020)
- [x] QueryClient 配置全局重试策略 (3 次)
- [x] QueryClient 配置缓存策略 (staleTime 5分钟)
- [x] Query Key 工厂模式正确实现
- [x] 查询错误时自动重试
- [x] 查询数据正确缓存和失效

#### 所有 Feature 模块前端
- [x] 所有 Cloudscape UI 组件来自 @cloudscape-design/components (无 MUI/Ant Design)
- [x] 所有页面遵循 Feature-Sliced Design (pages -> components -> hooks -> api -> types)
- [x] 所有 API 调用使用 TanStack Query hooks
- [x] TypeScript 类型定义完整，无 any 类型 (tsc --noEmit 零错误)

### Regression Evals
- [x] 路由守卫测试 (AuthGuard, RoleGuard) 全部通过
- [x] Layout 组件测试 (MainLayout, Navigation, TopNavigation) 全部通过
- [x] Store 切片测试 (uiSlice, notificationSlice) 全部通过
- [x] QueryClient 配置测试全部通过
- [x] 无 ESLint 错误
- [x] TypeScript 编译无错误

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 前端单元测试覆盖率 >= 70%
- 首屏加载 <3 秒
- 所有 UI 组件来自 Cloudscape Design System
