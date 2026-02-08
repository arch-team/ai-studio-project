# 前端 Claude Code 上下文管理规范 - 冗余分析与优化计划

## Context

前端 `.claude/` 目录下 13 个规范文件（CLAUDE.md + project-config.md + 11 个 rules/）存在信息冗余、职责重叠问题。总计 ~2,554 行 / ~79KB，每次会话估计消耗 40-60K tokens。目标：消除冗余，压缩代码示例，保持单一职责。

## 执行方式

**逐问题处理**: 每个问题先说明优化依据 → 获得用户确认 → 执行修改

## 问题清单与状态

### 🔴 高优先级

| # | 问题 | 涉及文件 | 状态 |
|---|------|---------|------|
| 1 | CLAUDE.md 技术栈表 vs tech-stack.md 50% 重叠 + 导航表缺 2 条目 | `CLAUDE.md` | ⏳ 部分完成（表已替换为引用，导航表待补） |
| 2 | architecture.md §1.3 模块列表 vs project-config.md 90% 重叠 | `architecture.md`, `project-config.md` | ⏳ 待处理 |

### 🟡 中优先级

| # | 问题 | 涉及文件 | 状态 |
|---|------|---------|------|
| 3 | architecture.md §2.1-§2.2 ASCII 图与 §0 重复 | `architecture.md` | ⏳ 待处理 |
| 4 | project-config.md ApiClient 代码与 architecture.md §7.2 重复 | `project-config.md` | ⏳ 待处理 |
| 5 | testing.md §1 目录树与 project-structure.md 重叠 | `testing.md` | ⏳ 待处理 |
| 6 | state-management.md 3 个完整 Store 实现 (~60 行可压缩) | `state-management.md` | ⏳ 待处理 |
| 7 | component-design.md 3 个完整组件实现 (~50 行可压缩) | `component-design.md` | ⏳ 待处理 |
| 8 | testing.md 完整 MSW 配置 + 测试模板 (~70 行可压缩) | `testing.md` | ⏳ 待处理 |

### 🟢 低优先级

| # | 问题 | 涉及文件 | 状态 |
|---|------|---------|------|
| 9 | (已合并到问题 1) CLAUDE.md 导航表缺 tech-stack.md 和 project-structure.md | `CLAUDE.md` | ⏳ 待处理 |
| 10 | architecture.md §5-§6 代码示例过于冗长 | `architecture.md` | ⏳ 待处理 |

## 验证方式

每个问题修改后：
1. 确认修改文件的信息完整性未受损
2. 确认交叉引用路径正确
3. 全部完成后提交 git
