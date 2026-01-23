# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **回复语言要求参见根目录 `CLAUDE.md`**

## 项目概述

AI Training Platform 前端 - React + AWS Cloudscape Design System 企业级 UI。

## 技术栈

| 核心 | 版本 |
|------|------|
| TypeScript / React / Vite | 5.3 / 18.2 / 5.0 |
| TanStack Query / Zustand | 5.17 / 4.4 |
| AWS Cloudscape | 3.0 |
| Vitest / Testing Library | 1.2 / - |

## 命令速查

```bash
npm run dev              # 开发服务器 localhost:5173
npm run build            # 生产构建
npm test                 # 单元测试
npm test -- path/to/test # 单个测试
npm run lint             # ESLint (--max-warnings 0)
npm run test:coverage    # 覆盖率报告
```

## 架构速览

```
src/
├── app/          # 入口、路由、Provider
├── features/     # 功能模块 (training, datasets, models, spaces, audit...)
├── layouts/      # 布局组件 (MainLayout, AuthLayout)
├── shared/       # 共享内核 (types, api, hooks, events)
├── lib/          # 基础设施 (query)
├── store/        # 全局状态 (Zustand slices)
└── types/        # 全局类型
```

**架构模式**: Feature-Sliced Design + Clean Architecture

**依赖方向**: `pages → components → hooks → api → types`

> 详细规范 → `docs/ARCHITECTURE.md`

## 核心约束

| 规则 | 说明 |
|------|------|
| **Cloudscape-First** | 禁止自定义 CSS、内联样式、原生 HTML 元素 |
| **模块隔离** | 模块间通过 `index.ts` 导入，禁止导入内部文件 |
| **状态分层** | 服务器状态 → TanStack Query，客户端状态 → Zustand |
| **Query Keys** | 使用 `@lib/query` 的 `queryKeys` 工厂管理缓存键 |
| **模块通信** | 异步通知通过 `@shared/events` EventBus |

> 设计规范 (组件选择、页面模板、禁止事项) → `DESIGN.md`

## 路径别名

| 别名 | 路径 |
|------|------|
| `@features/` | `src/features/` |
| `@shared/` | `src/shared/` |
| `@lib/` | `src/lib/` |
| `@store/` | `src/store/` |
| `@layouts/` | `src/layouts/` |

## API 集成

- **代理**: `/api` → `http://localhost:8000`
- **环境变量**: `VITE_API_BASE_URL` (必须 `VITE_` 前缀)

## 测试

- **配置**: `vitest.config.ts`, `tests/tsconfig.json`
- **位置**: `tests/unit/` (单元测试), `tests/integration/` (集成测试), `e2e/` (E2E)
- **工具**: `tests/__utils__/` (MSW, 渲染包装器, Mock)
- **别名**: `@tests/` → `tests/`

> 完整测试规范 → `docs/TESTING.md`

## 文档导航

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 分层规则、模块依赖、模块通信、状态管理、错误处理 |
| `docs/TESTING.md` | 测试分层、目录结构、命名规范、工具使用、命令参考 |
| `DESIGN.md` | 组件选择、状态反馈、禁止事项、暗色模式、Checklist |
| `../specs/frontend-design-guide.md` | 完整视觉规范、页面模板、色彩系统、间距系统、响应式、无障碍、国际化 |
