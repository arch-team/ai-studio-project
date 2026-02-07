# 删除 docs/ARCHITECTURE.md 并整合至 rules/architecture.md

## Context

迁移完成后项目中存在两份架构文档：
- `docs/ARCHITECTURE.md`（~700 行）— 原始完整架构文档，通过 `@` 指令每次会话强制加载
- `.claude/rules/architecture.md`（295 行）— 迁移时创建的速查索引

两者内容大量重叠，且 `docs/ARCHITECTURE.md` §6 异常体系仍为旧版继承式（与实际 `@problem` 代码不一致）。删除 `docs/ARCHITECTURE.md` 可以：
1. 消除 SSOT 冲突（两份架构文档长期分裂风险）
2. 节省每次会话 ~700 行 token 预算（去掉 `@` 强制加载）
3. 修复已知的异常文档过时问题

## 内容差异分析

`docs/ARCHITECTURE.md` 中 `rules/architecture.md` 尚未覆盖的内容：

| 内容 | docs/ 章节 | 处理方式 |
|------|-----------|---------|
| 架构核心原则（5 条） | §1.3 | **补入** rules/architecture.md §1 |
| 文件命名规范表 | §5.2 | **补入** rules/architecture.md §7 |
| DI 标准模板代码 | §7.2 | **补入** rules/architecture.md §6 |
| DDD 完整代码示例 | §3.4 | **不补**，rules 已有规范摘要，Claude 可读实际源码 |
| 事件通信完整示例 | §4.2 | **不补**，rules 已有精简示例 |
| 共享接口完整示例 | §4.3 | **不补**，rules 已有接口位置区分说明 |
| 旧版异常继承体系 | §6 | **丢弃**，rules §5 已用 @problem 替代（修复已知不一致） |
| 跨模块依赖 ASCII 图 | §2.2 | **不补**，rules 速查矩阵更高效 |

预计 `rules/architecture.md` 从 295 行增长至 ~350 行。

## 执行步骤

### Step 1: 扩充 rules/architecture.md

**文件**: `backend/.claude/rules/architecture.md`

改动：
1. §1 分层规则前增加核心原则表（模块自治、显式依赖、最小知识、单向依赖、高内聚低耦合）
2. §6 依赖注入增加标准模板代码（`get_xxx_repository` → `get_xxx_service` 模式）
3. §7 模块结构模板后增加文件命名规范表
4. 删除所有 6 处 `> 详见 docs/ARCHITECTURE.md` 引用
5. 头部 blockquote 从"速查索引"改为"架构规范单一真实源"

### Step 2: 删除 docs/ARCHITECTURE.md

**文件**: `backend/docs/ARCHITECTURE.md` → 删除

### Step 3: 更新 backend/CLAUDE.md

**文件**: `backend/CLAUDE.md`

改动：
1. 删除 `@docs/ARCHITECTURE.md` 指令（第 81 行）
2. 核心架构部分改为指向 `rules/architecture.md`
3. 规范文档索引表中删除"完整架构文档"行，architecture 条目说明改为"架构规范单一真实源"

### Step 4: 更新 rules/project-structure.md

**文件**: `backend/.claude/rules/project-structure.md`

改动：目录树中 `docs/` 下的 `ARCHITECTURE.md` 条目删除或更新

### Step 5: 更新项目根级引用

**文件** (共 4 个):
- `CLAUDE.md`（根目录，第 38 行）— 改为指向 `backend/.claude/rules/architecture.md`
- `README.md`（第 92、271 行）— 改为指向 `backend/.claude/rules/architecture.md`
- `frontend/CLAUDE.md`（第 48、90 行）— 改为指向 `backend/.claude/rules/architecture.md`
- `docs/CLAUDE-CODE-MEMORY-STANDARD.md`（多处）— 更新引用路径

### Step 6: 历史文档处理

以下文件为历史记录/计划/prompts，**不做修改**（引用在历史语境中是正确的）：
- `backend/my-prompts.md`
- `cc-doc/plans/*.md`
- `prompt.md`
- `codemaps/architecture.md`
- `cc-component-dev/` 下各文件
- `specs/001-ai-training-platform/checklists/ddd-modular-clean-architecture.md`

## 验证

1. `grep -r "docs/ARCHITECTURE.md" backend/CLAUDE.md backend/.claude/` — 应返回空
2. `grep -r "@docs/ARCHITECTURE.md" backend/` — 应返回空
3. 检查 `rules/architecture.md` 新增内容的格式正确性
4. 确认 `backend/docs/ARCHITECTURE.md` 已删除
