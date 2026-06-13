# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **回复语言要求参见根目录 `CLAUDE.md`**

## 项目概述

AI Training Platform 前端 - React + AWS Cloudscape Design System 企业级 UI。

## 技术栈

> 版本要求 → `.claude/rules/tech-stack.md` (单一真实源)

React + TypeScript + Vite | Cloudscape | TanStack Query + Zustand

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

> 详细规范 → `.claude/rules/architecture.md`

## 核心约束

| 规则 | 说明 |
|------|------|
| **Cloudscape-First** | 禁止自定义 CSS、内联样式、原生 HTML 元素 |
| **模块隔离** | 模块间通过 `index.ts` 导入，禁止导入内部文件 |
| **状态分层** | 服务器状态 → TanStack Query，客户端状态 → Zustand |
| **Query Keys** | 使用 `@lib/query` 的 `queryKeys` 工厂管理缓存键 |
| **模块通信** | 异步通知通过 `@shared/events` EventBus |

> 组件选择与设计规范 → `.claude/rules/component-design.md`

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

> 完整测试规范 → `.claude/rules/testing.md`

## 文档导航

| 文档 | 内容 |
|------|------|
| `.claude/rules/tech-stack.md` | 技术栈版本 (单一真实源)、禁止使用清单、升级策略 |
| `.claude/rules/project-structure.md` | 目录结构、配置文件速查、初始化检查清单 |
| `.claude/rules/architecture.md` | 分层规则、模块依赖、模块通信、共享内核、错误处理 |
| `.claude/rules/testing.md` | 测试分层、目录结构、命名规范、工具使用、命令参考 |
| `.claude/rules/state-management.md` | React Query、Zustand、表单状态、EventBus 联动 |
| `.claude/rules/code-style.md` | 命名规范、TypeScript 规范、导入排序 |
| `.claude/rules/component-design.md` | Cloudscape 组件选择、Props 设计、交互模式、暗色模式 |
| `.claude/rules/security.md` | XSS 防护、敏感数据存储、输入验证、API 安全 |
| `.claude/rules/performance.md` | 代码分割、Memoization、列表优化、Bundle 优化 |
| `.claude/rules/accessibility.md` | WCAG 2.1 AA、ARIA 使用、键盘导航 |
| `.claude/rules/checklist.md` | PR Review 检查清单 (架构、Cloudscape、安全、测试、设计规范) |
| `.claude/rules/design-tokens.md` | 深空离子青品牌主题：色板、字体栈、图表色、Hero、Logo (色值单一真实源) |
| `.claude/rules/page-templates.md` | 列表/详情/表单/Dashboard 四大页面模式骨架 + 图表严谨性 |
| `.claude/rules/interaction-states.md` | 错误/加载/空/成功四态完整性 + error 态铁律 |
| `.claude/rules/ux-writing.md` | 术语映射、状态标签、文案模式、中文排版 |
