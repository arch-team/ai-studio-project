# Claude Code 工具生态指导手册 — 编写计划

## Context

AI Training Platform 项目已配置了丰富的 Claude Code 工具生态（8 个 MCP Server、5 个已启用 Plugin、SuperClaude 框架、Spec-Kit 工作流），但缺少一份系统性的指导手册来帮助日常开发中高效选择和组合这些工具。

**目标**: 编写一份实用操作手册 `cc-doc/claude-code-工具生态指导手册.md`，以场景驱动的方式指导工具选择与组合，成为团队日常查阅的参考文档。

**定位**: 聚焦"什么场景用什么工具"，不含配置操作细节。

---

## 输出文件

`cc-doc/claude-code-工具生态指导手册.md` — 单文件，预计 400-600 行

---

## 文档结构 (7 个章节)

### §0 速查卡片
- 工具选择决策树 (文字流程图)
- 开发场景 → 推荐工具映射表 (一页速查)

### §1 工具生态现状盘点
| 类别 | 内容 |
|------|------|
| MCP Servers | aws-cdk, aws-knowledge, sagemaker-hyperpod-cli, serena, context7, sequential-thinking, tavily, pencil |
| 已启用 Plugins | python-development, error-debugging, code-simplifier, aws-cdk, claude-md-management |
| 全局框架 | SuperClaude (7 模式 + 26 命令 + 17 Agent) |
| 项目级资产 | 2 Skills (hyperpod-scheduling, decorator-exception) + 9 /speckit 命令 + 10 evals |

### §2 场景化工具推荐矩阵

按 **6 大开发场景** 给出具体工具组合推荐：

| 场景 | 推荐工具组合 | 示例触发 |
|------|-------------|---------|
| 后端 DDD 开发 | serena (符号导航) + context7 (FastAPI/SQLAlchemy 文档) + python-development plugin | 新增 training module endpoint |
| 前端 Cloudscape 开发 | context7 (Cloudscape 文档) + serena (组件模式查找) | 新增数据集管理页面 |
| CDK Stack 开发 | aws-cdk MCP + aws-knowledge MCP + sequential-thinking | 新增 Stack 或修改资源 |
| HyperPod 集成 | sagemaker-hyperpod-cli + aws-knowledge + hyperpod-scheduling skill | 训练任务提交/调度 |
| 调试与根因分析 | error-debugging plugin + sequential-thinking + serena | 生产问题排查 |
| 深度研究 | tavily + sequential-thinking + /sc:research | 技术选型、SDK 调研 |

每个场景包含：
- 推荐工具链（按执行顺序）
- 具体命令/flag 示例
- 反模式提醒（不该用什么）

### §3 MCP Server 实战指南

针对本项目最常用的 **5 个 MCP Server** 给出实战用法：

1. **aws-cdk** — CDK 开发必备
   - CDKGeneralGuidance: Stack 设计前咨询
   - ExplainCDKNagRule: Nag 检查失败时查规则
   - GetAwsSolutionsConstructPattern: 查找最佳实践 Construct
   - 适用场景 + 不适用场景

2. **aws-knowledge + sagemaker-hyperpod-cli** — AWS 文档查询
   - search_documentation: 查 API/SDK 用法
   - recommend: 获取服务选型建议
   - fetch_sagemaker_docs: HyperPod 专属文档
   - 与 context7 的区分（AWS 服务 → aws-knowledge，开源库 → context7）

3. **serena** — 代码导航与记忆
   - find_symbol / get_symbols_overview: 大型代码库符号导航
   - write_memory / read_memory: 跨会话上下文持久化
   - 后端 9 模块 DDD 架构中的高效导航模式

4. **context7** — 库文档查询
   - resolve-library-id + query-docs: 查 FastAPI/React/Cloudscape 官方文档
   - 优于 WebSearch 的场景（版本特定、API 签名）

5. **sequential-thinking** — 复杂推理
   - 适用：架构决策、多步调试、系统设计
   - 配合 --think / --think-hard / --ultrathink flag

### §4 Plugin 启用建议

基于项目需求的插件优先级评估：

| 优先级 | Plugin | 理由 |
|--------|--------|------|
| 🔴 必须 | tdd-workflows | 项目核心工作流，TDD 强制要求 |
| 🔴 必须 | kubernetes-operations | K8s manifest 管理（HyperPod 基于 EKS） |
| 🟡 推荐 | backend-development | 后端 DDD 架构 + TDD 编排 |
| 🟡 推荐 | cicd-automation | GitHub Actions 工作流管理 |
| 🟢 按需 | machine-learning-ops | ML 实验管理（当前阶段非核心） |
| 🟢 按需 | cloud-infrastructure | 多云场景（当前仅 AWS） |
| ❌ 不推荐 | api-scaffolding | 与 Spec-Kit 工作流重叠 |
| ❌ 不推荐 | business-analytics | 与项目业务领域不匹配 |
| ❌ 不推荐 | full-stack-orchestration | SuperClaude /sc:task 已覆盖 |

### §5 Agent Team 协作配方

针对本项目 **4 种常见复杂任务** 推荐团队组合：

1. **新功能全栈开发** (如新增"模型注册"模块)
   - Leader: system-architect
   - Members: backend-architect (DDD 建模) + frontend-architect (Cloudscape 页面) + quality-engineer (测试)
   - 工作流: spec → plan → parallel(backend, frontend) → integration test

2. **CDK 基础设施变更** (如新增 Stack)
   - Leader: devops-architect
   - Members: security-engineer (Nag 审查) + quality-engineer (Stack 测试)
   - 工具: aws-cdk MCP + aws-knowledge MCP

3. **生产问题根因分析**
   - Leader: root-cause-analyst
   - Members: error-debugging plugin + performance-engineer
   - 工具: sequential-thinking + serena (记忆)

4. **跨模块重构**
   - Leader: refactoring-expert
   - Members: backend-architect (架构守护) + quality-engineer (回归测试)
   - 工具: serena (符号重命名) + code-simplifier

### §6 Skill 提取机会

从现有代码模式中可提取的 **5 个高价值 Skill**：

| Skill 名称 | 来源 | 价值 |
|------------|------|------|
| `cdk-stack-scaffold` | infrastructure/cdk/ Stack 模式 | 新 Stack 快速生成（6 层架构遵从） |
| `ddd-module-scaffold` | backend/src/modules/ 模块模式 | 新业务模块脚手架（domain/app/infra/api 四层） |
| `cloudscape-page-scaffold` | frontend/src/features/ 页面模式 | Feature-Sliced 页面快速生成 |
| `training-job-lifecycle` | 训练任务状态机模式 | 状态转换与事件处理模板 |
| `async-aws-integration` | aioboto3 集成模式 | 异步 AWS SDK 调用最佳实践 |

### §7 反模式与注意事项

- **Magic MCP 冲突**: 项目强制 Cloudscape，禁止使用 Magic MCP 生成 UI
- **工具过载**: 不要同时启用所有 Plugin，按当前任务阶段选择
- **Agent Team 滥用**: 3 步以内的任务不需要 Team，直接执行
- **MCP 误用**: AWS 服务文档用 aws-knowledge，开源库用 context7，不要混用

---

## 信息来源

| 信息 | 来源文件 |
|------|---------|
| 项目架构与技术栈 | 根目录 `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `infrastructure/cdk/CLAUDE.md` |
| 当前插件/MCP 配置 | `~/.claude/settings.json`, `~/.claude/.mcp.json` |
| 可用 MCP 工具列表 | 当前会话 ToolSearch 可查询的 deferred tools |
| SuperClaude 框架 | `~/.claude/FLAGS.md`, `~/.claude/MODE_*.md`, `~/.claude/MCP_*.md` |
| 可用插件列表 | `~/.claude/settings.json` enabledPlugins 字段 |
| Agent 列表 | `~/.claude/agents/*.md` (17 个) |
| 项目级 Skills | `.claude/skills/` (hyperpod-scheduling, decorator-exception) |
| Spec-Kit 工作流 | `.claude/commands/speckit.*.md` (9 个) |
| Skill 提取模式 | `backend/src/modules/`, `frontend/src/features/`, `infrastructure/cdk/stacks/` |

---

## 验证方法

1. 检查文档中所有 MCP Server 名称与当前会话实际可用工具一致
2. 检查 Plugin 名称与 `settings.json` 中的 key 完全匹配
3. 确认场景推荐不包含 Magic MCP (Cloudscape 约束)
4. 确认文档引用的文件路径实际存在
5. 文档结构遵循 cc-doc/ 现有风格（中文、速查卡片优先、实用导向）
