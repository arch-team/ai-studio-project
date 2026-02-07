# 计划：将 ai-agents-platform 的 .claude 上下文管理规范应用到 ai-studio-project

## Context

ai-agents-platform 建立了一套成熟的三层分布式 `.claude` 规范体系（根级 → 子项目级 → rules 级），包含完整的前端/后端/基础设施规则库。ai-studio-project 的后端和 CDK 规则已很完善，但**前端完全缺失 `.claude/rules/` 规则库**，且根级缺少跨项目通用规则。本计划借鉴 agents-platform 的设计模式，补全 ai-studio-project 的规范空白。

**核心发现**：
- 后端规则 (12 份) 和 CDK 规则 (8 份) 质量高，**无需迁移**
- 前端仅有 `CLAUDE.md` 入口，无 `rules/` 目录 — **最大差距**
- 根级缺少 `.claude/CLAUDE.md` 和 `rules/common.md` — 跨项目治理缺失
- Spec-Kit 工作流、Skills、Evals 是 ai-studio-project 独有优势，保留不动

---

## 实施计划

### 第 1 轮：高优先级 — 前端核心规则 + 通用规则

直接影响 Claude 代码生成质量。以 agents-platform 对应文件为模板，适配 ai-studio-project 技术栈。

#### 1.1 `frontend/.claude/rules/tech-stack.md` — 前端版本矩阵

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/tech-stack.md`
- **内容**: §0 速查卡片（版本矩阵表）、核心依赖版本（TypeScript 5.3, React 18.2, Vite 5.0, Cloudscape 3.0, TanStack Query 5.17, Zustand 4.4, Vitest 1.2）、禁止使用列表（TailwindCSS, 自定义 CSS 框架, Redux, MobX）、npm 包管理器约束
- **关键适配**: Cloudscape 替代 TailwindCSS; npm 替代 pnpm

#### 1.2 `frontend/.claude/rules/architecture.md` — 前端架构规范

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/architecture.md`
- **内容**: §0 速查卡片（分层依赖矩阵 + 路径别名速查）、FSD + Clean Architecture 分层规则、依赖方向（pages → components → hooks → api → types）、模块隔离规则（通过 index.ts 导入）、Cloudscape-First 约束
- **关键适配**: 目录结构基于现有 `src/`（app/features/layouts/shared/lib/store/types），而非标准 FSD 的 pages/widgets/entities

#### 1.3 `frontend/.claude/rules/component-design.md` — 组件设计规范

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/component-design.md`
- **内容**: §0 速查卡片（Cloudscape 组件选择决策树）、Cloudscape-First 原则（禁止自定义 CSS/内联样式/原生 HTML 元素）、组件类型分类（容器型/展示型/复合型）、Props 设计原则、页面模板模式（Table/Form/Detail）
- **关键适配**: 全面以 Cloudscape 组件为基础（SpaceBetween, Container, Table, Form, Header 等），与 agents-platform 的原生 HTML + TailwindCSS 方案完全不同

#### 1.4 `frontend/.claude/rules/code-style.md` — 代码风格规范

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/code-style.md`
- **内容**: §0 速查卡片（命名速查表）、命名规范（PascalCase 组件/camelCase 函数/UPPER_SNAKE 常量）、TypeScript 规范（interface vs type, 禁止 any, 联合类型优先）、导入排序（React → 三方 → 别名 → 相对 → 类型）、路径别名使用规则
- **关键适配**: 路径别名 `@features/` 而非 `@/features/`

#### 1.5 `.claude/rules/common.md` — 跨项目通用规则

- **模板来源**: `ai-agents-platform/.claude/rules/common.md`
- **内容**: Git 提交规范（类型+范围格式，范围改为 backend/frontend/infra/cdk/docs）、代码审查通用检查项、文档命名规范（CLAUDE.md/rules/project-config.md）、Monorepo 结构概览（ai-studio-project 的目录树，含 Spec-Kit 体系说明）
- **关键适配**: 范围列表适配 ai-studio-project（infra → infrastructure/cdk），增加 Spec-Kit 工作流说明

### 第 2 轮：中优先级 — 前端补全 + 配置文件

#### 2.1 `frontend/.claude/rules/state-management.md`

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/state-management.md`
- **内容**: React Query 配置（staleTime/gcTime）、Query Keys 工厂模式（`@lib/query` 的 queryKeys）、Zustand Store 模板、Selector Hooks 性能优化、EventBus 模块通信（`@shared/events`）、React Hook Form + Zod 表单验证
- **关键适配**: 增加 EventBus 模式（agents-platform 无此概念）

#### 2.2 `frontend/.claude/rules/testing.md`

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/testing.md`
- **内容**: TDD 工作流、测试分层（Unit/Integration/E2E）、目录结构（tests/unit/, tests/integration/, e2e/）、MSW 配置（tests/__utils__/）、查询优先级（角色 > 标签 > 文本 > testId）、覆盖率要求
- **关键适配**: 测试目录与 agents-platform 不同（独立 tests/ 目录 vs 与组件同目录）

#### 2.3 `frontend/.claude/rules/checklist.md`

- **模板来源**: `ai-agents-platform/frontend/.claude/rules/checklist.md`
- **内容**: PR Review 检查清单，整合架构/组件设计/代码风格/状态管理/安全/测试/性能/无障碍共 9 个维度

#### 2.4 `frontend/.claude/project-config.md`

- **模板来源**: `ai-agents-platform/frontend/.claude/project-config.md`
- **内容**: 项目信息（名称/架构模式/UI框架）、功能模块列表（training/datasets/models/spaces/audit 等，与后端对应）、路由配置、API 端点、环境变量（VITE_*）

#### 2.5 `infrastructure/cdk/.claude/project-config.md`

- **内容**: Stack 列表及依赖关系、环境配置（dev/staging/prod）、命名约定（ai-platform 前缀）、CDK Nag 检测规则

#### 2.6 `.claude/CLAUDE.md` — 规范框架入口

- **模板来源**: `ai-agents-platform/.claude/CLAUDE.md`
- **内容**: 响应语言引用（→ 根目录 CLAUDE.md）、子项目规范导航表（后端/前端/CDK 各 CLAUDE.md 和 rules/）、通用规则链接（→ rules/common.md）
- **注意**: 保持简洁，避免与根目录 `CLAUDE.md` 内容重复

### 第 3 轮：低优先级 — 前端细分规则

#### 3.1 `frontend/.claude/rules/security.md`
- XSS 防护、敏感存储规则（禁止 localStorage Token）、VITE_ 环境变量安全、CSRF 防护

#### 3.2 `frontend/.claude/rules/performance.md`
- 代码分割（路由级 lazy）、Memoization 决策流程、虚拟列表阈值、状态拆分优化

#### 3.3 `frontend/.claude/rules/accessibility.md`
- POUR 原则速查、注明 Cloudscape 已内置大部分无障碍支持

#### 3.4 `frontend/.claude/rules/project-structure.md`
- 基于现有 src/ 目录结构编写、配置文件速查、禁止事项

---

## 需要修改的现有文件

| 文件 | 修改要点 |
|------|---------|
| `CLAUDE.md` (根目录) | Key Documentation 表增加 `.claude/rules/common.md` 引用 |
| `frontend/CLAUDE.md` | 增加「规范文档索引」节，链接到新建 `rules/*.md`（仿 `backend/CLAUDE.md` 格式） |
| `infrastructure/cdk/CLAUDE.md` | 增加对 `project-config.md` 的引用链接 |

## 不动的文件

| 类别 | 文件 | 理由 |
|------|------|------|
| 后端规则 | `backend/.claude/rules/*` (12份) | 质量高，已深度定制 |
| CDK 规则 | `infrastructure/cdk/.claude/rules/*` (8份) | 已适配 HyperPod，保留数字前缀命名 |
| Spec-Kit | `.claude/commands/speckit.*.md` (9个) | ai-studio-project 独有优势 |
| Skills | `.claude/skills/*` (2个) | 实战知识资产 |
| Evals | `.claude/evals/*` (10个) | 历史评估记录 |
| Settings | 各级 `settings.local.json` | 个人工作流配置，已深度积累 |

---

## 冲突处理

1. **Spec-Kit vs Rules 体系**: 不冲突。Spec-Kit 管理需求和流程 (WHAT/HOW/DO)，Rules 管理编码规范 (HOW TO CODE)，互补关系
2. **CDK 命名方式**: 保留数字前缀（00-08），后端和前端用无前缀命名。不强制统一
3. **settings.local.json**: 不迁移，保留现有配置

---

## 验证方法

实施完成后，验证步骤：
1. 在 `frontend/` 目录下让 Claude 生成一个新页面组件，检查是否遵循 Cloudscape-First 和 FSD 分层
2. 检查 Git 提交信息是否遵循 `common.md` 格式
3. 检查新建前端代码的导入排序、命名规范是否符合 `code-style.md`
4. 验证所有 CLAUDE.md 中的文档导航链接有效
