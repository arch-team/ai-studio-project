# 前端 Claude Code 上下文管理规范迁移计划

## Context

**目标**: 将 `ai-agents-platform/frontend` 的 Claude Code 上下文管理规范体系迁移到 `ai-studio-project/frontend`，补齐后者在安全、性能、无障碍、检查清单等专题规范上的缺失，同时保留后者在 DDD 对齐、Cloudscape-First、EventBus 等方面的独有优势。

**策略**: 选择性引入 + 适配改造。以源项目规范为骨架，融入目标项目已有文档的独有内容，最终输出统一放在 `frontend/.claude/rules/` 目录下。

**关键差异**:

| 维度 | 源项目 (ai-agents-platform) | 目标项目 (ai-studio-project) |
|------|---------------------------|---------------------------|
| 架构 | 标准 FSD 6 层 (app→pages→widgets→features→entities→shared) | 简化 FSD + Clean Architecture (模块内 types→api→hooks→components→pages) |
| CSS | TailwindCSS | AWS Cloudscape (禁止自定义 CSS) |
| 包管理器 | pnpm | npm |
| DDD 对齐 | 无 | 有 (前后端模块名对应) |
| 模块通信 | Context/Events | EventBus (`shared/events/`) + Query Invalidation |
| 设计系统 | 无约束 | Cloudscape-First (🔴 强制) |

---

## 迁移方案

### 最终目录结构

```
frontend/
├── CLAUDE.md                        # 保留现有入口 (更新导航链接)
├── DESIGN.md                        # 保留现有 Cloudscape 设计规范 (不变)
├── .claude/
│   ├── settings.local.json          # 保留现有 (不变)
│   └── rules/                       # 新建规范目录
│       ├── architecture.md          # 基于源项目骨架 + 融合目标项目 ARCHITECTURE.md
│       ├── testing.md               # 基于源项目骨架 + 融合目标项目 TESTING.md
│       ├── state-management.md      # 基于源项目骨架 + 融合目标项目状态管理章节
│       ├── code-style.md            # 从源项目引入 (适配)
│       ├── component-design.md      # 基于源项目骨架 + 适配 Cloudscape
│       ├── security.md              # 从源项目引入 (微调)
│       ├── performance.md           # 从源项目引入 (微调)
│       ├── accessibility.md         # 从源项目引入 (补充 Cloudscape)
│       └── checklist.md             # 从源项目引入 (适配)
└── docs/                            # 删除 (内容已融入 .claude/rules/)
    ├── ARCHITECTURE.md              # → .claude/rules/architecture.md
    └── TESTING.md                   # → .claude/rules/testing.md
```

---

### 文件级实施方案 (共 11 项操作)

#### 操作 1: 创建 `frontend/.claude/rules/` 目录

#### 操作 2: 创建 `rules/architecture.md`

**策略**: 以**源项目 `architecture.md` 的 §0 速查卡片 + 结构化风格**为骨架，填入**目标项目 `docs/ARCHITECTURE.md` 的全部 10 章实质内容**。

**融合要点**:
- **新增 §0 速查卡片** (源项目特色，目标项目缺失):
  - 模块内分层依赖图 (types → api → hooks → components → pages)
  - Feature Module 依赖速查表 (现在在 ARCHITECTURE.md 附录 §10.1)
  - 与后端对齐对照表 (现在在 ARCHITECTURE.md §10.2)
- **保留目标项目全部章节** (这是核心，不可丢失):
  - §1 架构概述 (FSD + Clean Architecture + DDD 对齐)
  - §2 分层规则 (模块内 5 层，非标准 FSD 6 层)
  - §3 模块间依赖规范 (R1-R4 黄金法则 + ESLint 检查)
  - §4 模块间通信方式 (EventBus + Query Invalidation 联动)
  - §5 模块结构规范 (features/{module}/ 目录模板)
  - §6 共享内核规范 (shared/ 结构 + 错误类型体系)
  - §7 状态管理规范 → **移至独立 `state-management.md`**
  - §8 错误处理规范 (4 层错误层级 + 错误码映射)
  - §9 架构合规检查 (ESLint `no-restricted-imports` 规则)
  - §10 附录 → **提升为 §0 速查卡片**
  - §11 测试架构引用 → 指向 `testing.md`
- **不引入源项目的 6 层 FSD** (不适用):
  - widgets 层、entities 层的相关内容跳过
  - FSD 6 层依赖矩阵替换为目标项目的 4 层矩阵

**来源文件**:
- 骨架: `/ai-agents-platform/frontend/.claude/rules/architecture.md` (§0 速查卡片格式)
- 内容: `/ai-studio-project/frontend/docs/ARCHITECTURE.md` (全部 10 章)

#### 操作 3: 创建 `rules/testing.md`

**策略**: 以**源项目 `testing.md` 的 §0 速查卡片 + 代码模板风格**为骨架，融入**目标项目 `docs/TESTING.md` 的独有内容**。

**融合要点**:
- **新增 §0 速查卡片** (源项目特色):
  - 命名速查表、分层速查表、陷阱提醒
- **保留/融入源项目内容** (目标项目缺失):
  - §2 组件测试模板 (查询优先级、异步测试)
  - §3 Hook 测试模板 (renderHook + useFakeTimers)
  - §4 API Mock MSW (server 配置、动态覆盖)
  - §5 E2E 测试 + Page Object 模式
  - §7 覆盖率要求 (按层级细分: Hooks 90%, Components 80%, Utils 95%)
- **保留目标项目独有内容** (源项目缺失):
  - 目录结构 (tests/unit/ 镜像模式，非组件同目录)
  - 渲染包装器 (`render`, `renderWithQuery` from `@tests/__utils__/test-utils`)
  - Mock Store 工具 (`createMockAuthStore`, `mockUsers`)
  - 路径别名 (`@tests/` → `tests/`)
  - 命令参考 (npm 而非 pnpm)
  - 覆盖率目标 (Statements ≥80%, Branches ≥75%, Functions ≥80%, Lines ≥80%, 关键模块 ≥90%)
- **适配调整**:
  - 测试文件位置: 源项目是组件同目录 `Button.test.tsx`，目标项目是 `tests/unit/` 镜像模式 → 使用目标项目方案
  - 命令: `pnpm test` → `npm test`
  - 覆盖率: 取两者较完整的版本（目标项目有 4 维度指标）

**来源文件**:
- 骨架 + 代码模板: `/ai-agents-platform/frontend/.claude/rules/testing.md`
- 目录/工具/命令: `/ai-studio-project/frontend/docs/TESTING.md`

#### 操作 4: 创建 `rules/state-management.md`

**策略**: 以**源项目的 §0 决策流程图 + Zustand 模板**为骨架，融入**目标项目 ARCHITECTURE.md §7 的 Query Keys 集中管理**和**§4 的通信矩阵**。

**融合要点**:
- **新增 §0 速查卡片** (源项目):
  - 状态类型决策表
  - 决策流程图 (API→React Query, 跨组件→Zustand, 复杂→useReducer)
  - 文件位置速查
- **保留源项目内容**:
  - §1 React Query 基本配置、Query Keys 规范、Query/Mutation 模板、乐观更新
  - §2 Zustand Store 模板、Selector Hooks
  - §3 React Hook Form + Zod 验证
  - §4 最佳实践 (❌/✅ 示例)
- **融入目标项目内容**:
  - Query Keys 集中管理: 使用 `@lib/query/queryKeys.ts` 工厂，而非分散在各 feature
  - 通信矩阵: EventBus (异步通知) + Query Invalidation 联动 (缓存失效)
  - Zustand Store 位置: `store/slices/*.ts` (全局) + `features/auth/store/` (Auth 例外)
- **适配调整**:
  - Query Keys: 源项目分散各 feature (`agentKeys`)，目标项目集中 (`queryKeys.trainingJobs.list()`) → 使用目标项目方案
  - 文件位置速查表: 使用目标项目的路径约定
  - 移除源项目表单示例中的 TailwindCSS 类名

**来源文件**:
- 骨架: `/ai-agents-platform/frontend/.claude/rules/state-management.md`
- 补充: `/ai-studio-project/frontend/docs/ARCHITECTURE.md` §4 (通信), §7 (状态管理)

#### 操作 5: 创建 `rules/code-style.md`

**策略**: 从源项目**直接引入**，微调适配。

**适配调整**:
- §0 导入排序: 移除 `@/entities/` 层级引用，改为目标项目路径别名 (`@features/`, `@shared/`, `@lib/`, `@store/`, `@layouts/`)
- §2 类型定义位置: 源项目 `entities/{entity}/model/types.ts` → 目标项目 `features/{module}/types/index.ts`
- 移除 TailwindCSS CSS 类命名（`kebab-case`）→ 补充 Cloudscape 组件导入约定

**来源文件**: `/ai-agents-platform/frontend/.claude/rules/code-style.md`

#### 操作 6: 创建 `rules/component-design.md`

**策略**: 以**源项目的设计原则和结构**为骨架，但将所有 TailwindCSS 示例替换为 Cloudscape 组件示例，并融入目标项目 `DESIGN.md` 的组件选择指南。

**融合要点**:
- **保留源项目设计原则** (目标项目缺失):
  - §0 速查卡片: 组件类型速查、决策流程、Props 设计速查
  - §1 组件类型详解: 展示型 (forwardRef + displayName)、容器型 (三态处理)、复合型 (Context + Object.assign)
  - §2 Props 高级模式: 继承原生属性、泛型组件
  - §3 自定义 Hooks 返回值规范
- **适配 Cloudscape**:
  - 组件决策流程: 移除 `widgets/`, `entities/` 层，改为 `features/{module}/components/` 和 `shared/components/`
  - 所有示例从原生 HTML + TailwindCSS 改为 Cloudscape 组件
  - 容器型组件三态: `<Spinner>` → `<StatusIndicator type="loading">`
  - 展示型组件: 注明 Cloudscape 已提供大部分基础组件，自定义展示组件仅在 Cloudscape 不满足时才创建
- **引用 DESIGN.md**: 在 §0 添加指引 "Cloudscape 组件选择指南详见 `DESIGN.md` §二"

**来源文件**:
- 骨架: `/ai-agents-platform/frontend/.claude/rules/component-design.md`
- Cloudscape 规范: `/ai-studio-project/frontend/DESIGN.md`

#### 操作 7: 创建 `rules/security.md`

**策略**: 从源项目**直接引入**，几乎不需要修改。

**微调**:
- §0 检测命令: `pnpm audit` → `npm audit`
- §4 环境变量: `VITE_APP_TITLE=AI Agents Platform` → `VITE_APP_TITLE=AI Training Platform`
- §5 输入验证: Zod + React Hook Form 引用改为 `state-management.md §3`

**来源文件**: `/ai-agents-platform/frontend/.claude/rules/security.md`

#### 操作 8: 创建 `rules/performance.md`

**策略**: 从源项目**直接引入**，移除 TailwindCSS 相关内容。

**微调**:
- §1 路由分割: 导入路径从 `@/pages/` 改为 `@features/{module}/pages/`
- §3 列表优化: 补充 Cloudscape `<Table>` 组件自带的分页优化说明
- §5 图片优化: 保留原生 `<img>` 示例（Cloudscape 无专用图片组件）
- §7 Bundle 优化: 保持不变（`lodash-es` + Tree Shaking 通用）

**来源文件**: `/ai-agents-platform/frontend/.claude/rules/performance.md`

#### 操作 9: 创建 `rules/accessibility.md`

**策略**: 从源项目**直接引入**，补充 Cloudscape 内置无障碍说明。

**微调**:
- §0 补充说明: "Cloudscape 组件已内置大部分 ARIA 属性和键盘导航支持，以下规范主要针对**自定义组件**和**组合场景**"
- §1 语义化规则: 补充 Cloudscape 对应 (`<Button>` → Cloudscape `<Button>`, `<nav>` → Cloudscape `<SideNavigation>`)
- §2 表单无障碍: 示例改为 Cloudscape `<FormField>` + `<Input>` 组合
- §3 ARIA 模式: 自定义组件表保留（Cloudscape 不覆盖的场景）
- §4 键盘导航: 焦点管理保留（Modal trap 等通用规范）
- §5 视觉无障碍: 移除 TailwindCSS 类名，改为 Cloudscape 色彩变量

**来源文件**: `/ai-agents-platform/frontend/.claude/rules/accessibility.md`

#### 操作 10: 创建 `rules/checklist.md`

**策略**: 以源项目为骨架，适配目标项目实际约束。

**适配调整**:
- §分层与架构: "正确的 FSD 层级" → "正确的模块内分层 (types/api/hooks/components/pages)"
- §组件设计: 补充 "全部使用 Cloudscape 组件" 检查项
- §测试: "测试文件与组件同目录" → "测试文件在 tests/unit/ 镜像目录"
- §性能: 保持不变
- §无障碍: 保持不变
- §项目结构: 补充 "无自定义 CSS" 检查项
- 新增 §Cloudscape 合规:
  - [ ] 无自定义 CSS 或内联样式
  - [ ] 无原生 HTML 表单元素
  - [ ] 暗色模式下无显示异常
- 预提交命令: `npm run lint && npx tsc --noEmit && npm run test:coverage`

**来源文件**: `/ai-agents-platform/frontend/.claude/rules/checklist.md`

#### 操作 11: 更新 `frontend/CLAUDE.md`

更新导航链接，指向新的 `.claude/rules/` 目录:

```markdown
## 规范导航

| 规范 | 位置 | 内容 |
|------|------|------|
| 架构规范 | `.claude/rules/architecture.md` | 分层规则、模块依赖、DDD 对齐、EventBus、错误处理 |
| 测试规范 | `.claude/rules/testing.md` | TDD 工作流、测试分层、MSW、覆盖率 |
| 状态管理 | `.claude/rules/state-management.md` | React Query + Zustand + 表单 |
| 代码风格 | `.claude/rules/code-style.md` | 命名、TypeScript、导入排序 |
| 组件设计 | `.claude/rules/component-design.md` | 组件类型、Props 设计 |
| 设计规范 | `DESIGN.md` | Cloudscape 组件选择、禁止事项 |
| 安全规范 | `.claude/rules/security.md` | XSS、Token 存储、输入验证 |
| 性能优化 | `.claude/rules/performance.md` | 代码分割、Memoization、列表优化 |
| 无障碍 | `.claude/rules/accessibility.md` | WCAG 2.1 AA、ARIA、键盘导航 |
| PR 检查清单 | `.claude/rules/checklist.md` | 预提交验证 |
```

同时保留现有 CLAUDE.md 中的技术栈、命令速查、架构速览、核心约束、路径别名、API 集成等内容不变。

#### 清理操作: 删除 `frontend/docs/` 目录

`docs/ARCHITECTURE.md` 和 `docs/TESTING.md` 的内容已完整融入 `.claude/rules/` 对应文件，删除旧文件避免内容重复和维护负担。

---

## 实施顺序

1. 创建 `frontend/.claude/rules/` 目录
2. 创建 9 个规范文件 (architecture → testing → state-management → code-style → component-design → security → performance → accessibility → checklist)
3. 更新 `frontend/CLAUDE.md` 导航链接
4. 删除 `frontend/docs/ARCHITECTURE.md` 和 `frontend/docs/TESTING.md`
5. 验证所有文件间的交叉引用链接正确

---

## 验证方案

1. **链接完整性**: 检查所有规范文件中的交叉引用路径是否正确
2. **内容完整性**: 确认目标项目 `docs/ARCHITECTURE.md` 的 10 章和 `docs/TESTING.md` 的全部内容均已在新文件中体现
3. **一致性**: 确认所有文件中的命令使用 `npm`（非 `pnpm`）、路径使用目标项目别名、示例使用 Cloudscape 组件
4. **Git diff**: 对比旧 docs/ 文件和新 rules/ 文件，确认无内容遗漏
