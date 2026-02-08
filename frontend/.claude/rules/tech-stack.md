> **职责**: 技术栈版本的单一真实源

# 前端技术栈 (Tech Stack)

## 核心依赖

| 技术 | 版本 |
|------|------|
| React | 18.2+ |
| TypeScript | 5.3+ |
| Vite | 5+ |
| @cloudscape-design/components | 3.0+ |
| @cloudscape-design/global-styles | 1.0+ |
| TanStack Query | 5.17+ |
| Zustand | 4.4+ |
| react-router-dom | 6.21+ |

## 测试工具

| 技术 | 版本 |
|------|------|
| Vitest | 1.2+ |
| Testing Library | 14+ |
| MSW | 2+ |
| Playwright | 1+ |

## 开发工具

npm | ESLint

## 可选 (按需引入)

React Hook Form | Zod | react-window | web-vitals | rollup-plugin-visualizer

## 禁止使用

| 禁止 | 替代 |
|------|------|
| TailwindCSS, 自定义 CSS, 内联样式 | Cloudscape 组件 |
| Redux, MobX | Zustand |
| axios | 原生 fetch (`shared/api/client.ts`) |
| lodash (全量) | lodash-es |
| Prettier | ESLint (项目未使用 Prettier) |

## 升级策略

- **主版本** (React, TS, Vite, Cloudscape): 团队评审
- **次/补丁版本**: 自主升级 + 测试
