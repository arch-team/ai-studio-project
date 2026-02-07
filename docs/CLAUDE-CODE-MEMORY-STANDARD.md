# Claude Code Memory 管理规范

> **版本**: 1.0 | **日期**: 2026-01-18 | **状态**: 生效

本文档是 ai-studio-project 项目 Claude Code 记忆管理的**单一真实源**。

---

## 1. 总体原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **单一真实源** | 每个领域有且仅有一个权威文档 | 架构规范只在 `.claude/rules/architecture.md` |
| **300行黄金法则** | CLAUDE.md 保持 100-300 行 | 超过则拆分或引用 |
| **层级继承** | 子文档只包含差异性内容 | 继承声明 + 增量规范 |
| **就近放置** | 规范与代码距离最小化 | `backend/tests/CLAUDE.md` |
| **按需加载** | 使用 `paths` 限制规则范围 | 仅编辑测试文件时加载测试规则 |

---

## 2. 文件层级规范

### 2.1 记忆层级（优先级从低到高）

```
1️⃣ ~/.claude/CLAUDE.md          # 用户全局记忆
2️⃣ ~/.claude/rules/*.md         # 用户全局规则
3️⃣ ./CLAUDE.md                  # 项目共享记忆
4️⃣ ./.claude/rules/*.md         # 项目规则
5️⃣ ./CLAUDE.local.md            # 本地个人记忆（最高，不提交）
```

### 2.2 项目目录结构

```
ai-studio-project/
├── CLAUDE.md                    # 根：项目概览、TDD 原则、术语标准
├── CLAUDE.local.md              # 本地覆盖（.gitignore）
├── .claude/
│   ├── commands/                # 自定义命令（speckit.*）
│   └── rules/                   # 模块化规则（本规范核心）
│       ├── general.md           # 全局术语、提交规范
│       ├── testing/
│       │   ├── tdd-workflow.md  # TDD 工作流（全局）
│       │   └── backend-tests.md # 后端测试规范（paths 限定）
│       ├── backend/
│       │   ├── ddd-patterns.md  # DDD 架构规范（paths 限定）
│       │   └── sdk-first.md     # SDK-First 原则（paths 限定）
│       ├── frontend/
│       │   └── cloudscape-rules.md  # Cloudscape 规范（paths 限定）
│       └── infrastructure/
│           └── cdk-patterns.md  # CDK 规范（paths 限定）
├── backend/
│   ├── CLAUDE.md                # 后端开发指南
│   └── tests/CLAUDE.md          # 测试规范单一真实源
├── frontend/CLAUDE.md           # 前端开发指南
└── infrastructure/cdk/CLAUDE.md # CDK 部署指南
```

### 2.3 职责分配

| 文件 | 职责 | 行数上限 |
|------|------|---------|
| 根 `CLAUDE.md` | 项目概览、TDD 原则、术语标准、文档索引 | 150 |
| `backend/CLAUDE.md` | 技术栈、命令、架构概览、代码风格 | 300 |
| `backend/tests/CLAUDE.md` | 测试规范单一真实源 | 200 |
| `frontend/CLAUDE.md` | 技术栈、命令、组件规范、状态管理 | 350 |
| `infrastructure/cdk/CLAUDE.md` | Stack 分层、部署流程、环境配置 | 150 |
| `.claude/rules/*.md` | 按需加载的专项规则 | 100/文件 |

---

## 3. CLAUDE.md 内容模板

### 3.1 根 CLAUDE.md 模板

```markdown
# CLAUDE.md

## Response Language
**所有对话和文档必须使用中文。**

## Project Overview
[1-2 段项目简介]

## Architecture
> 详细规范请参见 `backend/.claude/rules/architecture.md`
[关键架构图或概述]

## Key Development Principles
### TDD 工作流
[核心循环 + 测试分层表格]

## Terminology Standards
[核心术语表格，详细参见 spec.md]

## Key Documentation
[文档索引表格]

## Memory Rules Index
> 项目使用 `.claude/rules/` 管理模块化规则，详见 `docs/CLAUDE-CODE-MEMORY-STANDARD.md`
```

### 3.2 子模块 CLAUDE.md 模板

```markdown
# CLAUDE.md

> **继承**: `../CLAUDE.md` (TDD 原则、术语标准)
> **回复语言要求参见根目录 `CLAUDE.md`**

## Project Overview
[模块简介]

## Tech Stack
[技术栈表格]

## Common Commands
[常用命令代码块]

## Architecture
> **核心规范请参见**: [`.claude/rules/architecture.md`](.claude/rules/architecture.md)

[架构概览]

## [模块特有内容]
...
```

---

## 4. Rules 规范

### 4.1 Rule 文件结构

```markdown
---
paths:
  - "backend/tests/**/*.py"
---

# 规则标题

## AI 指令
[明确的 AI 行为指导]

## 规范内容
[具体规则、模板、示例]

## 禁止事项
[反模式列表]
```

### 4.2 paths 字段规范

| 情况 | 行为 | 适用场景 |
|------|------|---------|
| **有 paths 字段** | 仅当处理匹配文件时加载 | 模块专属规则 |
| **无 paths 字段** | 始终加载（全局规则） | 术语、TDD 原则 |

**Glob 模式示例**：

| 模式 | 匹配范围 |
|------|---------|
| `**/*.py` | 所有 Python 文件 |
| `backend/tests/**/*.py` | 后端测试文件 |
| `frontend/**/*.{ts,tsx}` | 前端 TypeScript 文件 |
| `infrastructure/cdk/**/*.py` | CDK Python 文件 |

### 4.3 Rule 命名规范

| 规则类型 | 命名格式 | 示例 |
|---------|---------|------|
| 全局规则 | `{topic}.md` | `general.md` |
| 测试规则 | `testing/{scope}-tests.md` | `testing/backend-tests.md` |
| 架构规则 | `{module}/{pattern}.md` | `backend/ddd-patterns.md` |
| 工作流规则 | `{module}/{workflow}.md` | `testing/tdd-workflow.md` |

### 4.4 加载时机

| 时机 | 说明 |
|------|------|
| 会话启动 | 新会话、恢复会话 (`--resume`) |
| 会话清空 | `/clear` 命令后 |
| 自动压缩 | `compact` 后重新加载 |

**注意**: 文件修改后需要**新会话**才能生效。

---

## 5. Serena Memory 规范

### 5.1 命名前缀

| 前缀 | 用途 | 生命周期 | 示例 |
|------|------|---------|------|
| `project-` | 项目级约束/架构决策 | 长期 | `project-architecture-decisions` |
| `task-` | 任务进度追踪 | 任务完成后清理 | `task-auth-module-progress` |
| `decision-` | 技术决策记录 | 长期 | `decision-orm-selection` |
| `validation-` | 验证结果 | 验证后清理 | `validation-api-contracts` |
| `session-` | 会话摘要 | 会话结束后清理 | `session-2026-01-18-summary` |
| `checkpoint-` | 检查点状态 | 临时 | `checkpoint-implementation` |
| `blockers-` | 阻塞问题 | 解决后清理 | `blockers-current` |

### 5.2 使用模式

#### 会话开始
```
1. list_memories() → 显示现有记忆
2. read_memory("project-*") → 读取项目约束
3. think_about_collected_information() → 理解上下文
```

#### 执行中
```
1. write_memory("task-X", "in_progress: description")
2. think_about_task_adherence() → 验证进度
3. write_memory("checkpoint-*", current_state) # 每30分钟
```

#### 会话结束
```
1. think_about_whether_you_are_done() → 评估完成度
2. write_memory("session-summary", outcomes)
3. delete_memory() # 清理临时记忆
```

### 5.3 记忆内容模板

```markdown
# task-{module}-{feature}

## 状态
- 当前阶段: [设计/实现/测试/完成]
- 最后更新: [时间戳]

## 已完成
- [x] 任务1
- [x] 任务2

## 进行中
- [ ] 当前任务

## 阻塞
- [问题描述]

## 决策
- [关键决策及原因]
```

---

## 6. 继承与引用模式

### 6.1 继承声明

子模块 CLAUDE.md **必须**在首行声明继承：

```markdown
> **继承**: `../CLAUDE.md` (TDD 原则、术语标准)
```

或更详细：

```markdown
> **继承链**: 根 `CLAUDE.md` → `backend/CLAUDE.md` (本文件)
> **继承内容**: TDD 工作流、术语标准、测试诚信原则
```

### 6.2 引用方式

| 方式 | 语法 | 适用场景 |
|------|------|---------|
| 链接引用 | `> 详见 [文档名](路径)` | 详细文档 |
| @ 引用 | `@.claude/rules/architecture.md` | 关键规范内嵌 |
| 行内指向 | `(详见 backend/CLAUDE.md)` | 简短提示 |

### 6.3 去重原则

| 原则 | 说明 |
|------|------|
| **不重复父级内容** | 子模块不复制父级已有的规范 |
| **只写差异** | 只包含本模块特有的内容 |
| **引用代替复制** | 使用引用指向权威文档 |

---

## 7. 版本控制与同步

### 7.1 提交规范

| 文件类型 | 提交消息格式 |
|---------|-------------|
| CLAUDE.md | `docs(claude): {描述}` |
| Rules | `docs(rules): {规则名} - {描述}` |
| 规范文档 | `docs: {文档名} - {描述}` |

### 7.2 变更同步

当修改以下内容时，需同步更新：

| 变更 | 需同步更新 |
|------|-----------|
| 根 CLAUDE.md 术语 | 检查 spec.md 一致性 |
| 架构规范 | 检查架构合规测试 |
| Rules paths | 验证路径匹配正确 |
| 继承链 | 检查子模块声明 |

### 7.3 验证命令

```bash
# 启动新会话后验证规则加载
/memory

# 编辑特定文件后验证规则匹配
# (应显示 paths 匹配的规则)
```

---

## 8. 反模式警告

### 8.1 CLAUDE.md 反模式

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 超过 300 行 | 加载慢，难维护 | 拆分到 rules/ 或引用外部文档 |
| 重复父级内容 | 同步困难，易过时 | 使用继承声明 |
| 包含代码实现 | 职责不清 | 只包含规范和模板 |
| 频繁变更 | 缓存失效 | 稳定核心，变动放 rules |

### 8.2 Rules 反模式

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 无 paths 的大规则 | 污染全局 | 添加精确的 paths |
| paths 过于宽泛 | 无关场景加载 | 精确匹配目标目录 |
| 规则间重复 | 冲突风险 | 单一真实源原则 |
| 嵌套过深 | 难以发现 | 最多 2 层目录 |

### 8.3 Serena Memory 反模式

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 无前缀命名 | 难以分类 | 使用标准前缀 |
| 不清理临时记忆 | 积累垃圾 | 任务完成后清理 |
| 存储代码 | 浪费空间 | 只存元数据和状态 |
| 过长内容 | 读取慢 | 精简，引用文件 |

---

## 9. 快速参考

### 9.1 文件创建检查清单

- [ ] CLAUDE.md < 300 行？
- [ ] 首行有继承声明？
- [ ] 无重复父级内容？
- [ ] 有明确的 AI 指令？
- [ ] Rules 有 paths 字段？

### 9.2 Rules 路径速查

| 场景 | paths 配置 |
|------|-----------|
| 后端测试 | `backend/tests/**/*.py` |
| 后端源码 | `backend/src/**/*.py` |
| 前端代码 | `frontend/src/**/*.{ts,tsx}` |
| CDK 代码 | `infrastructure/cdk/**/*.py` |
| 全局规则 | (不设 paths) |

### 9.3 Memory 命名速查

| 场景 | 命名模式 |
|------|---------|
| 项目架构 | `project-architecture-*` |
| 模块任务 | `task-{module}-{feature}` |
| 技术决策 | `decision-{topic}` |
| 会话摘要 | `session-{date}-summary` |

---

## 10. 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 研究报告 | `cc-doc/plans/2026-01-17-claude-code-记忆管理与-rule-机制研究.md` | 机制详解 |
| 项目宪法 | `.specify/memory/constitution.md` | 核心原则 |
| 架构规范 | `backend/.claude/rules/architecture.md` | 后端架构 |
| 测试规范 | `backend/tests/CLAUDE.md` | 测试单一真实源 |
