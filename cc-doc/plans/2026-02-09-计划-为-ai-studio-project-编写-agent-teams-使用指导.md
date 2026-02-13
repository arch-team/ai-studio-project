# 计划: 为 ai-studio-project 编写 Agent Teams 使用指导

## Context

源项目 ai-agents-platform 有一份经过实战验证的 `agent-teams-guide.md`（9 章，361 行），基于 Phase 1 (M1-M3) 的 DDD 后端模块开发经验提炼。但该指南仅覆盖**后端 DDD 模块开发**场景。

ai-studio-project 是一个**全栈 Monorepo**（9 个后端 DDD 模块 + 12 个前端 Cloudscape feature + 11 个 CDK Stack），且已有 `cc-doc/claude-code-工具生态指导手册.md` 覆盖了工具选择。需要一份定制版的 Agent Teams 指导来覆盖全栈协作场景。

**目标**: 创建 `cc-doc/agent-teams-guide.md`，基于源指南框架，扩展为覆盖后端 + 前端 + CDK 三条主线的全栈 Agent Teams 操作手册。

---

## 输出文件

`cc-doc/agent-teams-guide.md` — 单文件，预计 550-700 行

---

## 文档结构（9 章）

### 第 1 章: 何时使用 Agent Teams (~40 行)
- 保留源指南的使用/不使用判断矩阵
- **扩展三条线阈值**: 后端(≥5任务+≥2层), 前端(≥3新文件+≥2层), CDK(≥2 Stack层级), 全栈(前后端同时+API契约)
- 单 Agent 条件保持: 单文件修复、scope 明确的优化、文档更新、单层实现

### 第 2 章: 经验证的团队组合模式 (~200 行，核心章节)
6 个模式，每个含: 适用场景、团队构成表、工作流、关键经验

| 模式 | 名称 | Agent 数 | 来源 | 适用场景 |
|------|------|---------|------|---------|
| A | 后端 DDD 模块开发 | 5-6 | 源指南适配 | 9 个后端模块新建/大改 |
| B | 代码优化 | 3-5 | 源指南适配 | 已有代码简化重构 |
| C | 安全/质量审查 | 3-4 | 源指南适配 | Phase 验收、PR 批量审计 |
| D | 前端 Cloudscape 页面开发 | 4-6 | **新增** | 12 个前端 feature 模块 |
| E | CDK Stack 开发 | 3-5 | **新增** | 11 个 CDK Stack 新建/修改 |
| F | 全栈功能开发 | 4-5 | **新增** | 前后端同时开发(billing/spaces等) |

### 第 3 章: 任务拆解策略 (~80 行)
- **3.1** 后端 DDD 标准 9 步模板 (保留源指南，更新产出路径)
- **3.2** 前端 Feature-Sliced 标准 7 步模板 (**新增**: types → api → hooks → components → pages → 路由注册 → 测试)
- **3.3** CDK Stack 标准 5 步模板 (**新增**: config → stack → app.py注册 → 测试 → 安全审查)
- **3.4** 依赖 DAG 构建规则 (保留源指南 + 全栈扩展: API 契约是前后端共同前置依赖)

### 第 4 章: 波次执行模型 (~70 行)
- **4.1** 波次划分原则 (保留源指南 4 条)
- **4.2** 后端标准波次 (保留源指南 4 波次，更新验证命令)
- **4.3** 前端标准波次 (**新增**: Types+API → Hooks+Components → Pages+路由 → 测试审查，共 4 波次)
- **4.4** CDK 标准波次 (**新增**: Config+Stack → 注册+测试 → 安全审查，共 3 波次)
- **4.5** 全栈模块波次 (**新增**: API契约 → Domain+Types → App/Infra+API/Hooks → API+Components/Pages → 集成测试，共 5 波次)

### 第 5 章: Agent 类型速查表 (~60 行)
- 按任务类型选择 subagent_type (扩展源指南，新增前端/CDK/需求分析/技术文档)
- 按子项目层级推荐 (后端 DDD 层级表 + 前端 FSD 层级表 + CDK 层级表)

### 第 6 章: 质量保障与验证 (~50 行)
- 每波次验证 (后端/前端/CDK 三套命令)
- 最终汇聚验证 (三个子项目各自的 Milestone 验收命令)
- 架构安全网 (后端 `test_architecture_compliance.py` + 前端 ESLint `no-restricted-imports` + CDK Nag)

### 第 7 章: Agent Prompt 模板 (~80 行)
- 后端实现类 Prompt (适配规范路径和验证命令)
- 前端实现类 Prompt (**新增**: Cloudscape 约束、TanStack Query + Zustand、Query Keys 工厂)
- CDK 实现类 Prompt (**新增**: 6 层 Stack 架构、mypy --strict、Fn.import_value 禁止)
- 审查类 Prompt (引用各子项目独立 checklist)

### 第 8 章: Phase 4-8 并行规划 (~80 行)
- Phase 总览表 (Phase 4-8 的范围、任务数、子项目、当前状态)
- 并行可行性分析
- 推荐执行方案:
  ```
  当前: Phase 4 前端 (datasets)
  第一批并行: Phase 5 后端 + Phase 5 前端
  第二批并行: Phase 6 全栈(billing) + Phase 7 全栈(spaces+CDK)
  第三批串行: Phase 8 横向功能
  ```
- 共享文件冲突管理 (`main.py`, `router.py`, `app/router/routes.ts`, `app.py`)

### 第 9 章: 常见问题与经验教训 (~40 行)
- 保留源指南 Q1-Q5 (文件冲突、上下文传递、Agent失败、团队规模、background)
- **新增 Q6**: 前后端 API 契约一致性 (OpenAPI 契约先行 + MSW mock)
- **新增 Q7**: CDK 测试依赖链 (共用 Fixture)
- **新增 Q8**: 与 Spec-Kit 工作流配合 (/speckit.tasks → TaskCreate → 波次分派)

---

## 关键适配点

### 验证命令更新
| 子项目 | 源指南命令 | 本项目实际命令 |
|--------|-----------|-------------|
| 后端波次验证 | `uv run ruff check` | `black --check src/ && ruff check src/ && mypy src/` |
| 后端最终验收 | `uv run pytest --cov-fail-under=85` | `pytest --cov=src --cov-fail-under=85` |
| 前端 | (无) | `npm run lint && npm test && npm run build` |
| CDK | (无) | `make check` (ruff + mypy strict + pytest) |

### 与工具生态指导手册的衔接
- **互补定位**: Agent Teams 指导聚焦"团队组织和执行"，工具生态手册聚焦"工具选择"
- **交叉引用**: 模式中的"工具配置"段落引用手册 §2 场景矩阵
- **不重复**: MCP Server 详细用法、Plugin 启用建议、Skill 提取建议均在工具生态手册中，此处不再赘述
- **关联更新**: 工具生态手册 §5 有 4 个简要配方，Agent Teams 指导 §2 有 6 个完整模式——后者是前者的详尽版

---

## 关键参考文件

| 文件 | 用途 |
|------|------|
| `ai-agents-platform/plan-docs/agent-teams-guide.md` | 源指南模板 (结构基础) |
| `cc-doc/claude-code-工具生态指导手册.md` | 工具选择手册 (交叉引用) |
| `backend/.claude/rules/architecture.md` | 后端 DDD 架构规范 |
| `frontend/.claude/rules/architecture.md` | 前端 FSD 架构规范 |
| `infrastructure/cdk/.claude/rules/architecture.md` | CDK 6 层 Stack 架构 |
| `specs/001-ai-training-platform/tasks.md` | 180 个任务清单 (Phase 并行规划数据) |
| 各子项目 `.claude/rules/checklist.md` | PR Review 检查清单 (审查 Prompt 引用) |
| 各子项目 `.claude/rules/testing.md` | 测试规范 (验证命令来源) |

---

## 实施步骤

1. 以源指南 `agent-teams-guide.md` 为结构骨架
2. 逐章编写，保留源指南核心内容 + 适配本项目 + 新增前端/CDK/全栈模式
3. 确保所有验证命令、规范路径、Agent 类型名称与本项目实际一致
4. 在文档头部添加与工具生态指导手册的定位区分说明
5. 最终检查: 行数 550-700、中文、速查卡片优先、无过时引用

## 验证方法

1. 检查所有 Agent `subagent_type` 名称在当前环境中可用 (plugins 已启用)
2. 检查所有验证命令可在对应子项目目录下执行
3. 检查所有规范路径引用的文件实际存在
4. 检查与工具生态指导手册的引用链接有效
5. 检查 Phase 4-8 并行规划与 `tasks.md` 数据一致
