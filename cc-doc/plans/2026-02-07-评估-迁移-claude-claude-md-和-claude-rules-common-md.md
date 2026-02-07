# 评估：迁移 .claude/CLAUDE.md 和 .claude/rules/common.md

## Context

ai-studio-project 的 `.claude/` 目录当前只有 `settings.local.json`、`commands/`、`evals/`、`skills/`，缺少入口文件和通用规则。评估是否将 ai-agents-platform 的 `.claude/CLAUDE.md` 和 `.claude/rules/common.md` 迁移过来。

---

## 源文件分析

### `.claude/CLAUDE.md`（agents-platform）

内容：响应语言要求（中文强制）、项目概述、Monorepo 结构表、子项目导航链接。

**评估**：
- ai-studio-project 的根目录 `CLAUDE.md` 已包含响应语言要求、项目概述、术语标准等内容
- `.claude/CLAUDE.md` 的作用是作为 `.claude/` 目录内的导航入口
- **当前差距**：ai-studio-project 的 `.claude/` 目录下没有入口文件，进入该目录后缺少规范导航
- **迁移价值**：中等。提供 `.claude/` 目录的入口导航，指向 `rules/common.md` 和各子项目规范

### `.claude/rules/common.md`（agents-platform）

内容：Git 提交规范（类型+范围格式）、代码审查通用检查项、文档命名规范、Monorepo 结构概览。

**评估**：
- ai-studio-project 根目录 `CLAUDE.md` 未定义 Git 提交规范和文档命名规范
- 当前项目的 Git 提交已在事实上遵循类似格式（从 git log 可见：`docs(backend):`, `chore(backend):`, `refactor(docs):` 等），但未成文
- **当前差距**：跨项目通用规则（Git 规范、审查标准、文档命名）没有统一的成文定义
- **迁移价值**：高。将隐性约定显性化，确保 Claude 遵循一致的提交规范和文档组织

---

## 结论：建议迁移，需适配

两个文件都值得迁移，但需要适配内容：

### 1. 新建 `.claude/rules/common.md`

基于 agents-platform 的 `common.md` 模板，需调整：
- **Git 范围**: `infra` → `cdk`（因为 ai-studio-project 用 `infrastructure/cdk/` 而非 `infra/`）
- **Monorepo 结构**: 替换为 ai-studio-project 的目录树（backend/, frontend/, infrastructure/cdk/, specs/, .specify/）
- **增加 Spec-Kit 说明**: 在 Monorepo 结构概览中标注 Spec-Kit 工作流体系的位置和职责
- **文档命名规范**: 保持一致（CLAUDE.md / rules/{topic}.md / project-config.md）

### 2. 新建 `.claude/CLAUDE.md`

基于 agents-platform 的 `.claude/CLAUDE.md` 模板，需调整：
- **响应语言**: 引用根目录 `CLAUDE.md`，不重复定义
- **项目概述**: 改为 AI Training Platform（非 AI Agents Platform）
- **子项目导航**: 指向 `backend/CLAUDE.md`、`frontend/CLAUDE.md`、`infrastructure/cdk/CLAUDE.md`
- **通用规则链接**: 指向 `.claude/rules/common.md`

---

## 实施步骤

1. 创建 `.claude/rules/` 目录
2. 创建 `.claude/rules/common.md`（适配 ai-studio-project 的内容）
3. 创建 `.claude/CLAUDE.md`（精简入口导航）
4. 在根目录 `CLAUDE.md` 的 Key Documentation 表中增加对 `.claude/rules/common.md` 的引用

### 关键文件

| 操作 | 文件路径 |
|------|---------|
| 新建 | `.claude/CLAUDE.md` |
| 新建 | `.claude/rules/common.md` |
| 修改 | `CLAUDE.md`（根目录，增加一行引用） |

### 参考文件

| 文件 | 用途 |
|------|------|
| `ai-agents-platform/.claude/CLAUDE.md` | CLAUDE.md 模板 |
| `ai-agents-platform/.claude/rules/common.md` | common.md 模板 |

---

## 验证方法

1. 检查 `.claude/CLAUDE.md` 中的导航链接是否都指向存在的文件
2. 让 Claude 生成一个 Git 提交，检查是否遵循 `common.md` 定义的格式
3. 确认根目录 `CLAUDE.md` 的 Key Documentation 表中新增引用正确
