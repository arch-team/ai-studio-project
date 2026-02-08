# 前端 Claude Code 上下文管理规范迁移计划

## Context

**目标**: 将 `ai-agents-platform/frontend` 的 Claude Code 上下文管理规范体系迁移到 `ai-studio-project/frontend`，补齐后者在安全、性能、无障碍、检查清单等专题规范上的缺失，同时保留后者在 DDD 对齐、Cloudscape-First、EventBus 等方面的独有优势。

**策略**: 选择性引入 + 适配改造。以源项目规范为骨架，融入目标项目已有文档的独有内容，最终输出统一放在 `frontend/.claude/rules/` 目录下。

### 架构决策 (已确认)

**保留当前简化架构**，不引入源项目的标准 FSD 6 层。理由：
1. Cloudscape 使得 widgets 层冗余（`<AppLayout>` 等已承担组合职责）
2. entities 层会打破已建立的前后端 DDD 对齐映射
3. 顶级 pages/ 不利于 13 模块场景下的模块自治
4. 目标项目的模块内分层 (types/api/hooks/components/pages/) 语义更清晰

仅引入源项目的**规范呈现方式**（§0 速查卡片、依赖矩阵格式、决策流程图、陷阱提示）。

### 关键路径

- 源项目: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-agents-platform/frontend/.claude/rules/`
- 目标项目: `/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/frontend/`
- 输出目录: `frontend/.claude/rules/`

---

## 执行计划: 逐文件创建

### File 1: `rules/architecture.md` ✅ 已确认

- **策略**: 源项目文档框架（§0 速查卡片格式、节结构、✅❌ 呈现）+ 目标项目 ARCHITECTURE.md 全部实质内容
- **源文件**: `ai-agents-platform: rules/architecture.md` (框架) + `ai-studio-project: docs/ARCHITECTURE.md` (内容)
- **最终结构**: §0 速查卡片 → §1 架构概览 → §2 层级规则 → §3 模块依赖 → §4 模块通信(EventBus) → §5 模块导出规则 → §6 共享内核 → §7 错误处理 → §8 架构合规(ESLint)
- **关键差异**: 6 层 FSD → 简化 FSD; widgets/entities 路径移除; 状态管理拆分至独立文件

### File 2: `rules/testing.md` ✅ 已确认

- **策略**: 源项目速查卡片+代码模板 + 目标项目 TESTING.md 独有内容
- **源文件**: `ai-agents-platform: rules/testing.md` (框架+模板) + `ai-studio-project: docs/TESTING.md` (内容)
- **最终结构**: §0 速查卡片 → §1 测试文件位置(tests/镜像) → §2 组件测试(查询优先级) → §3 Hook 测试 → §4 API Mock(MSW+动态覆盖+Mock Store) → §5 E2E(Page Object+三模式命令) → §6 测试配置(别名+渲染包装器) → §7 覆盖率(双维度)
- **关键差异**: 同目录测试 → tests/独立目录; pnpm → npm; 覆盖率双维度呈现

### File 3: `rules/state-management.md` ✅ 已确认

- **策略**: 源项目决策流程+模板 + 目标项目 Query Keys 集中管理 + EventBus 联动
- **源文件**: `ai-agents-platform: rules/state-management.md` (框架) + `ai-studio-project: docs/ARCHITECTURE.md §7+§4.3` (内容)
- **最终结构**: §0 速查卡片(决策表+流程图+文件位置) → §1 React Query(queryKeys集中工厂+乐观更新) → §2 Zustand(Auth安全+Selector+store/slices/) → §3 表单(RHF+Zod) → §4 EventBus联动 → §5 最佳实践(❌/✅)
- **关键差异**: 各feature自定义Keys → 全局queryKeys工厂; features/model/store → store/slices/; 新增EventBus章节; 4种状态类型(+URL)

### File 4: `rules/code-style.md` ✅ 已确认

- **策略**: 源项目直接引入，仅做路径别名适配
- **源文件**: `ai-agents-platform: rules/code-style.md`
- **最终结构**: §0 速查卡片 → §1 命名规范补充 → §2 TypeScript 规范 → §3 导入规范
- **适配点(3处)**: 路径别名 `@/` → `@shared/`/`@features/`等; 移除CSS类命名行; 类型位置 entities/ → features/{module}/types/

### File 5: `rules/component-design.md` ✅ 已确认

- **策略**: 源项目设计原则 + Cloudscape 组件示例替换 + DESIGN.md 独有内容融入
- **源文件**: `ai-agents-platform: rules/component-design.md` (理论框架) + `ai-studio-project: DESIGN.md` (Cloudscape内容)
- **最终结构**: §0 速查卡片 → §1 组件类型(Cloudscape示例) → §2 Cloudscape组件选择(场景映射+禁止事项) → §3 Props高级模式 → §4 状态反馈与交互(Flashbar+危险操作Modal) → §5 组件文件结构 → §6 暗色模式
- **关键差异**: 自定义UI示例 → Cloudscape组件; 移除widgets/entities决策路径; features/*/ui/ → features/*/components/

### File 6: `rules/security.md` ✅ 已确认

- **策略**: 源项目几乎直接引入
- **源文件**: `ai-agents-platform: rules/security.md`
- **最终结构**: §0 速查卡片 → §2 XSS防护 → §3 敏感数据存储 → §4 环境变量安全 → §5 输入验证 → §6 API安全 → §7 第三方依赖安全
- **适配点(1处)**: `pnpm audit` → `npm audit`

### File 7: `rules/performance.md` ✅ 已确认

- **策略**: 源项目直接引入，路径适配
- **源文件**: `ai-agents-platform: rules/performance.md`
- **最终结构**: §0 速查卡片 → §1 代码分割 → §2 Memoization → §3 列表优化 → §4 状态优化 → §5 图片优化 → §6 性能指标目标 → §7 Bundle优化
- **适配点(2处)**: 路径别名适配; 图片章节精简+Cloudscape说明

### File 8: `rules/accessibility.md` ✅ 已确认

- **策略**: 源项目直接引入，补充 Cloudscape 无障碍说明
- **源文件**: `ai-agents-platform: rules/accessibility.md`
- **最终结构**: §0 速查卡片 → §1 语义化规则 → §2 表单无障碍 → §3 ARIA模式 → §4 键盘导航 → §5 视觉无障碍
- **适配点(3处)**: 补充Cloudscape内置ARIA说明; 焦点陷阱 @headlessui → Cloudscape Modal; CSS示例 → StatusIndicator

### File 9: `rules/checklist.md` ✅ 已确认

- **策略**: 源项目骨架 + 新增 Cloudscape 合规检查维度
- **源文件**: `ai-agents-platform: rules/checklist.md` (骨架) + `ai-studio-project: DESIGN.md §七` (Cloudscape检查项)
- **最终结构**: 分层与架构 → 组件设计 → **Cloudscape合规**(页面/表单/表格/代码质量) → 代码风格 → 状态管理 → 安全 → 测试 → 性能 → 无障碍 → 项目结构
- **关键差异**: 适配简化FSD检查项; 测试位置适配tests/; queryKeys工厂; 新增Cloudscape合规维度

### File 10: 更新 `frontend/CLAUDE.md` ✅ 已确认

- **变更**: 更新"文档导航"表指向 `.claude/rules/` 下的 9 个规范文件
- **变更**: 更新"架构速览"节引用 `docs/ARCHITECTURE.md` → `.claude/rules/architecture.md`
- **变更**: 更新"测试"节引用 `docs/TESTING.md` → `.claude/rules/testing.md`
- **变更**: 移除 `DESIGN.md` 引用，替换为 `rules/component-design.md` + `rules/checklist.md`

### File 11: 删除旧文件 ✅ 已确认

在所有 rules/ 文件创建完成且 CLAUDE.md 更新后：
- 删除 `frontend/docs/ARCHITECTURE.md`
- 删除 `frontend/docs/TESTING.md`
- 删除 `frontend/DESIGN.md`
- 如果 `frontend/docs/` 目录为空则删除该目录

---

## 执行顺序

1. 创建 `frontend/.claude/rules/` 目录
2. 按 File 1-9 顺序创建 9 个规范文件
3. File 10: 更新 `frontend/CLAUDE.md`
4. File 11: 删除旧文件
5. `git status` 确认变更正确

## 验证方式

- 确认 9 个 rules/ 文件均已创建且内容完整
- 确认 CLAUDE.md 所有引用链接指向正确路径
- 确认旧文件已删除
- 确认无残留的 docs/ 空目录
- `git diff` 审查所有变更
