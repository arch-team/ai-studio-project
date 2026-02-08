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

---

## 处理方式: 逐文件确认后执行

### 文件 1: `rules/architecture.md`
- **策略**: 源项目 §0 速查卡片格式 + 目标项目 ARCHITECTURE.md 全部内容
- **状态**: 待确认

### 文件 2: `rules/testing.md`
- **策略**: 源项目速查卡片+代码模板 + 目标项目 TESTING.md 独有内容
- **状态**: 待确认

### 文件 3: `rules/state-management.md`
- **策略**: 源项目决策流程 + 目标项目 Query Keys 集中管理 + EventBus 联动
- **状态**: 待确认

### 文件 4: `rules/code-style.md`
- **策略**: 源项目直接引入，路径别名适配
- **状态**: 待确认

### 文件 5: `rules/component-design.md`
- **策略**: 源项目设计原则 + Cloudscape 组件示例替换
- **状态**: 待确认

### 文件 6: `rules/security.md`
- **策略**: 源项目直接引入，几乎不改
- **状态**: 待确认

### 文件 7: `rules/performance.md`
- **策略**: 源项目直接引入，移除 TailwindCSS
- **状态**: 待确认

### 文件 8: `rules/accessibility.md`
- **策略**: 源项目直接引入，补充 Cloudscape 说明
- **状态**: 待确认

### 文件 9: `rules/checklist.md`
- **策略**: 源项目骨架 + 新增 Cloudscape 合规检查项
- **状态**: 待确认

### 文件 10: 更新 `frontend/CLAUDE.md`
- **策略**: 更新导航链接指向 .claude/rules/
- **状态**: 待确认

### 文件 11: 删除 `frontend/docs/`
- **策略**: 内容已融入 rules/，删除旧文件
- **状态**: 待确认
