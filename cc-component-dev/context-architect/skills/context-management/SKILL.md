---
name: context-management
description: This skill should be used when the user asks to "设计 CLAUDE.md", "配置上下文", "优化 token", "Rules 配置", "Memory 策略", "create CLAUDE.md", "configure context", or discusses Claude Code context management, token optimization, rules patterns, or memory strategies.
---

# Context Management Skill

Claude Code 上下文管理专家知识库，帮助设计最优的项目上下文配置策略。

## 核心概念

### 上下文三层体系

Claude Code 使用三层上下文管理机制：

| 层级 | 机制 | 加载时机 | Token 预算 | 适用场景 |
|------|------|---------|-----------|---------|
| **CLAUDE.md** | 层级化 Markdown | 每次对话开始 | ~2000-5000 | 核心规范、架构约束 |
| **Rules** | Glob 模式触发 | 匹配文件时 | ~500-1000/rule | 文件类型规范、工具配置 |
| **Memory** | Serena MCP | 按需读取 | 无限制 | 项目知识、决策记录 |

### CLAUDE.md 层级继承

```
~/.claude/CLAUDE.md          # 全局配置 (个人偏好)
├── project/CLAUDE.md        # 项目根配置 (架构、约定)
│   ├── backend/CLAUDE.md    # 后端配置 (SDK、测试)
│   │   └── tests/CLAUDE.md  # 测试配置 (继承后端)
│   └── frontend/CLAUDE.md   # 前端配置 (组件、状态)
```

**继承规则**:
- 子目录 CLAUDE.md 自动继承父级配置
- 使用 `>` 引用父级：`> 详见 ../CLAUDE.md`
- 避免重复，只定义增量内容

### Rules 触发模式

Rules 配置使用 `.claude/rules/` 目录下的 Markdown 文件：

**`.claude/rules/testing.md`**:
```markdown
---
paths:
  - "**/*.test.ts"
---

# Testing Rules

- 使用 Jest 和 React Testing Library
```

**`.claude/rules/backend.md`**:
```markdown
---
paths:
  - "backend/**/*.py"
---

# Backend Rules

- 遵循 DDD 模式
- 使用 SDK-First 原则
```

### Memory 持久化

通过 Serena MCP 实现跨会话记忆：

```
write_memory("arch_decision_001", "选择 DynamoDB 而非 PostgreSQL...")
read_memory("arch_decision_001")
list_memories()
```

## 设计原则

### 1. Token 效率优先

- **高频内容** → CLAUDE.md (每次对话都需要)
- **条件内容** → Rules (按文件类型触发)
- **低频内容** → Memory (按需读取)

### 2. 渐进式详细

- 根 CLAUDE.md: 50-100 行核心规范
- 子目录 CLAUDE.md: 30-50 行增量配置
- 详细文档: 独立文件，CLAUDE.md 引用

### 3. 一致性约束

- 术语表放在根 CLAUDE.md
- 命名规范放在根或相关子目录
- 架构约束使用强制性语言 ("必须"、"禁止")

## 配置决策树

```
项目规范 →
├─ 每次都需要? → CLAUDE.md
│  ├─ 全项目通用? → 根 CLAUDE.md
│  └─ 特定模块? → 子目录 CLAUDE.md
├─ 特定文件类型? → Rules (glob 触发)
└─ 偶尔参考? → Memory (按需读取)
```

## 最佳实践

### CLAUDE.md 结构模板

```markdown
# CLAUDE.md

## 响应语言
**所有对话使用中文。**

## 项目概述
[1-2 句话描述项目核心价值]

## 核心约束
- 必须: [强制性规则]
- 禁止: [绝对禁止的做法]

## 术语标准
| 中文 | 英文 | 类名 | 数据库 |
|------|------|------|--------|

## 关键文档
| 文档 | 位置 | 用途 |
|------|------|------|

## 开发原则
[3-5 条核心原则，引用详细文档]
```

### Rules 配置示例

在 `.claude/rules/` 目录下创建规则文件：

**`.claude/rules/python.md`**:
```markdown
---
paths:
  - "**/*.py"
---

# Python Rules

- 使用 Python 3.11+ 特性
- 类型提示必需
```

**`.claude/rules/infrastructure.md`**:
```markdown
---
paths:
  - "infrastructure/**/*.ts"
---

# Infrastructure Rules

- CDK 代码遵循 infrastructure/cdk/CLAUDE.md
```

**`.claude/rules/testing.md`**:
```markdown
---
paths:
  - "**/tests/**"
---

# Testing Rules

- 测试使用 TDD 红绿重构循环
```

### Memory 使用策略

| 场景 | Memory Key 模式 | 示例 |
|------|----------------|------|
| 架构决策 | `arch_decision_{id}` | `arch_decision_db_choice` |
| 技术研究 | `research_{topic}` | `research_auth_options` |
| 会话状态 | `session_{feature}` | `session_auth_impl` |
| 检查点 | `checkpoint_{timestamp}` | `checkpoint_20240118` |

## 常见问题

### Q: CLAUDE.md 应该多长？

根 CLAUDE.md 建议 100-200 行，子目录 30-50 行。超过这个长度考虑：
- 拆分到子目录 CLAUDE.md
- 使用引用指向详细文档
- 低频内容移到 Memory

### Q: 何时用 Rules 而非 CLAUDE.md？

- 规范只适用于特定文件类型 → Rules
- 需要 glob 模式匹配 → Rules
- 规范适用于整个项目 → CLAUDE.md

### Q: Memory 会影响性能吗？

Memory 是按需读取，不影响启动性能。适合：
- 大量历史决策记录
- 详细技术研究报告
- 跨会话状态持久化

## 相关参考

- @references/claude-md-hierarchy.md - CLAUDE.md 层级详解
- @references/rules-patterns.md - Rules glob 模式
- @references/memory-strategies.md - Serena Memory 策略
- @references/token-optimization.md - Token 效率原则
