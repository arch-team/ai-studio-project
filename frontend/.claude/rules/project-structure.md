> **职责**: 目录结构规范 - 物理目录结构和配置文件速查

# 项目目录结构规范 (Project Structure)

---

## 0. 速查卡片

> Monorepo 结构概览请参考 [根级 common.md](../../../.claude/rules/common.md#monorepo-结构概览)

### 前端目录结构 ← 当前位置

```
frontend/                       # 前端项目根目录
├── .claude/                    # Claude Code 上下文
│   ├── CLAUDE.md               # 前端入口
│   ├── project-config.md       # 项目特定配置 (业务模块、路由、API)
│   └── rules/                  # 11 个规范文件
├── src/
│   ├── app/                    # 入口、路由、Provider
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── providers/
│   │   └── router/
│   ├── features/               # 功能模块 (12 个)
│   │   ├── training/
│   │   ├── datasets/
│   │   ├── models/
│   │   ├── spaces/
│   │   ├── audit/
│   │   ├── billing/
│   │   ├── monitoring/
│   │   ├── templates/
│   │   ├── reports/
│   │   ├── admin/
│   │   ├── auth/
│   │   └── resource-quotas/
│   ├── layouts/                # 布局 (MainLayout, AuthLayout)
│   ├── shared/                 # 共享内核
│   │   ├── api/
│   │   ├── components/
│   │   ├── events/
│   │   ├── hooks/
│   │   └── types/
│   ├── lib/                    # 基础设施 (query)
│   ├── store/                  # Zustand (slices/)
│   └── types/                  # 全局类型
├── tests/                      # 单元 + 集成测试
│   ├── setup.ts
│   ├── unit/                   # 镜像 src 结构
│   ├── integration/            # API + 页面集成
│   └── __utils__/              # 测试工具、MSW、Mock
├── e2e/                        # E2E 测试 (Playwright)
│   ├── pages/
│   ├── tests/
│   ├── fixtures/
│   └── utils/
├── docs/                       # 元文档
├── .eslintrc.cjs               # ESLint 配置 (传统格式)
├── index.html                  # HTML 入口
├── package.json                # 项目配置
├── package-lock.json           # 依赖锁定
├── tsconfig.json               # TypeScript 配置
├── tsconfig.node.json          # Node TypeScript 配置
├── vite.config.ts              # Vite 配置
├── vitest.config.ts            # Vitest 测试配置
├── playwright.config.ts        # E2E 测试配置
└── README.md                   # 前端说明
```

### 配置文件速查

| 文件 | 用途 | 必须 |
|------|------|:----:|
| `package.json` | 项目和脚本配置 | ✅ |
| `tsconfig.json` | TypeScript 配置 | ✅ |
| `vite.config.ts` | Vite 构建配置 | ✅ |
| `.eslintrc.cjs` | ESLint 配置 (传统格式) | ✅ |
| `vitest.config.ts` | Vitest 测试配置 | ✅ |
| `index.html` | HTML 入口 | ✅ |
| `README.md` | 项目说明 | ✅ |
| `playwright.config.ts` | E2E 测试配置 | 推荐 |
| `package-lock.json` | 依赖锁定 | ✅ |

### 禁止事项

| 规则 | 说明 |
|------|------|
| ❌ 根目录放组件 | 所有组件必须在 `src/` 对应层级下 |
| ❌ 测试散落源码目录 | 单元/集成测试在 `tests/`，E2E 在 `e2e/` |
| ❌ 配置文件散落各处 | 配置统一在根目录 |
| ❌ 未声明的环境变量 | 所有变量必须在 `.env.example` 中声明 |

---

## 1. 新项目初始化检查清单

### 目录
- [ ] `src/app/` 包含 App.tsx、main.tsx、providers/、router/
- [ ] `src/shared/` 包含 api/、components/、events/、hooks/、types/
- [ ] `src/features/` 已创建功能模块
- [ ] `src/layouts/` 已创建布局组件
- [ ] `src/lib/` 已创建基础设施 (query)
- [ ] `src/store/` 已创建全局状态 (slices/)
- [ ] `.claude/CLAUDE.md` 已配置

### 配置文件
- [ ] `package.json` 包含所有必要脚本
- [ ] `tsconfig.json` 配置路径别名
- [ ] `vite.config.ts` 配置路径别名
- [ ] `.eslintrc.cjs` 配置 React + TypeScript 规则
- [ ] `vitest.config.ts` 配置测试
- [ ] `README.md` 包含项目说明
