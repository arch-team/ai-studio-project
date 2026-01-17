# Claude Code 记忆管理与 Rule 机制深度研究报告

**日期**: 2026-01-18
**研究范围**: CLAUDE.md 工作原理、Rules 机制、Serena MCP Memory 功能、社区最佳实践

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [CLAUDE.md 文件工作原理](#2-claudemd-文件工作原理)
3. [Rules 机制详解](#3-rules-机制详解)
4. [Serena MCP Memory 功能](#4-serena-mcp-memory-功能)
5. [社区最佳实践](#5-社区最佳实践)
6. [当前项目分析](#6-当前项目分析)
7. [优化建议](#7-优化建议)
8. [参考资源](#8-参考资源)

---

## 1. 执行摘要

### 核心发现

| 机制 | 用途 | 持久性 | 优先级 |
|------|------|--------|--------|
| **CLAUDE.md** | 项目/用户级持久记忆 | 跨会话持久 | 高（自动加载） |
| **Rules (.claude/rules/)** | 模块化规则配置 | 跨会话持久 | 与 CLAUDE.md 同级 |
| **Serena Memory** | 项目特定知识存储 | 跨会话持久 | 按需加载 |
| **Session Persistence** | 会话状态恢复 | 会话内持久 | 临时 |

### 关键洞察

1. **CLAUDE.md 是 Claude Code 的"宪法"** - 始终被加载，规则具有最高遵从度
2. **层级覆盖机制** - 更具体的配置覆盖更通用的配置
3. **300 行黄金法则** - 社区共识：CLAUDE.md 应控制在 100-300 行内
4. **渐进式披露** - 使用 `@import` 语法按需加载详细文档

---

## 2. CLAUDE.md 文件工作原理

### 2.1 加载层级与优先级

Claude Code 采用层级式记忆加载机制，从高到低优先级如下：

```
优先级 1 (最高): Enterprise Policy
  └─ macOS: /Library/Application Support/ClaudeCode/CLAUDE.md
  └─ Linux: /etc/claude-code/CLAUDE.md
  └─ Windows: C:\Program Files\ClaudeCode\CLAUDE.md

优先级 2: Project Memory (项目目录)
  └─ ./CLAUDE.md 或 ./.claude/CLAUDE.md (版本控制共享)

优先级 3: Project Local Memory
  └─ ./CLAUDE.local.md (个人本地，被 .gitignore)

优先级 4: User Memory (全局用户)
  └─ ~/.claude/CLAUDE.md (跨所有项目生效)
```

### 2.2 目录递归加载机制

Claude Code 会从当前工作目录向上递归查找 CLAUDE.md 文件：

```
/project-root/
├── CLAUDE.md                    # 项目根级别 (始终加载)
├── src/
│   └── api/
│       └── CLAUDE.md            # 按需加载 (仅编辑该目录文件时)
├── frontend/
│   └── CLAUDE.md                # 按需加载
└── backend/
    └── CLAUDE.md                # 按需加载
```

**加载时机**：
- **根级 CLAUDE.md**: 会话启动时立即加载
- **子目录 CLAUDE.md**: 仅当 Claude 在该子目录中工作时按需加载

### 2.3 Import 语法

CLAUDE.md 支持通过 `@path/to/file` 语法导入其他文件：

```markdown
# 项目概述
本项目使用 DDD 架构...

# 详细文档引用
@docs/architecture.md
@docs/api-contracts.yaml
@specs/001-ai-training-platform/spec.md
```

**导入行为**：
- 导入的文件内容会被合并到上下文中
- 支持相对路径和绝对路径
- 建议使用"指针而非副本"策略，避免文档过时

### 2.4 文件大小限制与性能影响

| 文件大小 | 性能影响 | 建议 |
|----------|----------|------|
| < 100 行 | 最优 | 推荐：核心规则 |
| 100-300 行 | 良好 | 可接受：包含结构化内容 |
| 300-500 行 | 警告 | 考虑拆分或使用 @import |
| > 500 行 | 性能下降 | 必须拆分，上下文窗口占用过大 |

**性能警告**：
- CLAUDE.md 内容在每个会话中被完整加载到上下文窗口
- 过大的文件会减少可用于实际工作的上下文空间
- 导致 token 成本增加、响应质量下降

---

## 3. Rules 机制详解

### 3.1 .claude/rules/ 目录结构

从 v2.0.64 版本开始，Claude Code 支持模块化规则目录：

```
your-project/
├── .claude/
│   ├── CLAUDE.md              # 主项目指令
│   └── rules/
│       ├── code-style.md      # 代码风格规则
│       ├── testing.md         # 测试约定
│       ├── security.md        # 安全要求
│       ├── frontend/          # 子目录分组
│       │   ├── components.md
│       │   └── styling.md
│       └── backend/
│           ├── api.md
│           └── database.md
```

### 3.2 Rules vs CLAUDE.md 对比

| 特性 | CLAUDE.md | .claude/rules/ |
|------|-----------|----------------|
| 结构 | 单一文件 | 多文件 |
| 组织方式 | 全部在一起 | 按主题分类 |
| 最适合 | 小型项目 | 大型项目、团队协作 |
| 可维护性 | 可能变得臃肿 | 易于管理 |
| 加载优先级 | 自动加载 | 与 CLAUDE.md 同级 |

### 3.3 路径特定规则 (Path-Specific Rules)

使用 YAML frontmatter 限定规则作用范围：

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/services/**/*.ts"
---

# API 开发规则

- 所有 API 端点必须包含输入验证
- 使用标准错误响应格式
- 包含 OpenAPI 文档注释
```

**Glob 模式支持**：
- `*` - 匹配任意字符（不含路径分隔符）
- `**` - 匹配任意目录深度
- `{a,b}` - 匹配 a 或 b

### 3.4 用户级规则

个人规则存放在 `~/.claude/rules/`，适用于所有项目：

```
~/.claude/rules/
├── preferences.md      # 个人编码偏好
└── workflows.md        # 工作流程偏好
```

**优先级**：用户级规则先于项目规则加载，项目规则具有更高优先级（可覆盖）

### 3.5 符号链接共享

跨项目共享规则：

```bash
# 链接共享目录
ln -s ~/shared-claude-rules .claude/rules/shared

# 链接单个文件
ln -s ~/company-standards/security.md .claude/rules/security.md
```

---

## 4. Serena MCP Memory 功能

### 4.1 Memory 系统概述

Serena MCP 提供了一个独立于 CLAUDE.md 的项目级知识存储系统：

```
.serena/
├── project.yml          # 项目配置
├── memories/            # Memory 存储目录
│   ├── architecture.md
│   ├── coding-conventions.md
│   └── task-progress.md
└── cache/               # LSP 缓存
```

### 4.2 Memory 工具集

| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `write_memory` | 写入命名记忆 | 保存项目知识、决策记录 |
| `read_memory` | 读取记忆内容 | 获取相关上下文 |
| `list_memories` | 列出所有记忆 | 发现可用知识 |
| `delete_memory` | 删除记忆 | 清理过时信息 |
| `edit_memory` | 编辑记忆内容 | 更新现有知识 |

### 4.3 与 CLAUDE.md 的关键区别

| 特性 | CLAUDE.md | Serena Memory |
|------|-----------|---------------|
| 加载时机 | 会话启动自动加载 | 按需加载（LLM 决策） |
| 存储位置 | 项目根目录 | `.serena/memories/` |
| 更新方式 | 手动编辑或 `#` 快捷键 | 通过 MCP 工具调用 |
| 内容类型 | 规则、约定、结构 | 任务进度、发现、决策 |
| 跨会话 | 是 | 是 |

### 4.4 Memory 使用模式

**会话开始**：
```python
# Serena 自动执行
list_memories()  # 显示可用 memories
# LLM 根据当前任务决定是否 read_memory()
```

**任务执行中**：
```python
# 发现重要信息时
write_memory("architecture-decision-001", """
# 认证架构决策

## 决策
使用 JWT + Refresh Token 双令牌模式

## 原因
- 无状态服务支持
- 安全性与体验平衡
""")
```

**会话结束**：
```python
# 保存会话学习成果
write_memory("session-2026-01-18", """
# 会话摘要

## 完成的工作
- 实现了用户认证模块
- 修复了 #123 bug

## 待续任务
- 完成单元测试
""")
```

### 4.5 当前项目的 Serena Memory 状态

从项目文件分析，当前项目已配置 Serena：

**根项目** (`/ai-studio-project/.serena/`):
- `project.yml` - 项目配置（bash 语言服务器）
- `memories/project-constraints.md` - 记录禁止使用 Fargate 等约束
- `memories/migration_analysis_report.md` - 迁移分析报告

**CDK 子项目** (`/infrastructure/cdk/.serena/`):
- 独立的项目配置
- 包含验证发现、关键问题、HyperPod 插件验证等 memories

---

## 5. 社区最佳实践

### 5.1 CLAUDE.md 内容组织

**推荐结构** (来自 Anthropic 官方和社区共识):

```markdown
# 项目名称

## 快速命令
- `npm run dev` - 启动开发服务器
- `npm test` - 运行测试
- `npm run lint` - 代码检查

## 架构概述
简要说明技术栈和目录结构...

## 编码规范
- 使用 2 空格缩进
- 函数命名使用 camelCase
- ...

## 禁止事项
- 不要删除 .env 文件
- 不要直接修改 migrations 目录
- ...

## 详细文档
@docs/architecture.md
@docs/api-design.md
```

### 5.2 分层记忆策略

```
Layer 1: Global (~/.claude/CLAUDE.md)
├── 通用偏好（语言、格式）
├── 安全规则（密钥处理）
└── 工作流偏好

Layer 2: Project (./CLAUDE.md)
├── 项目架构
├── 命令速查
└── 团队规范

Layer 3: Module (.claude/rules/ 或子目录 CLAUDE.md)
├── 模块特定规则
├── API 设计约定
└── 测试策略

Layer 4: Session (Serena Memory / 会话内记忆)
├── 当前任务进度
├── 临时发现
└── 决策记录
```

### 5.3 常见反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|----------|
| CLAUDE.md 过长 | 上下文污染，token 浪费 | 拆分到 rules/ 或使用 @import |
| 复制代码片段 | 容易过时 | 使用 `file:line` 引用 |
| 通用建议 | Claude 已知，无需重复 | 只写项目特定内容 |
| MCP 工具说明 | 冗余，Claude 已有工具描述 | 删除工具说明 |
| 未版本控制 | 团队无法共享 | 提交 CLAUDE.md，.gitignore CLAUDE.local.md |

### 5.4 /compact vs /clear 使用策略

| 命令 | 效果 | 使用时机 |
|------|------|----------|
| `/clear` | 完全清除会话历史 | 开始新任务（推荐） |
| `/compact` | 智能压缩历史 | 需要保留部分上下文时 |

**社区建议**：
- 优先使用 `/clear` 开始新任务
- 保持会话简短聚焦
- 重要学习成果写入 CLAUDE.md 或 Serena Memory

### 5.5 记忆更新策略

```markdown
## 记忆更新时机

1. **实现大功能后**: "将本会话学到的内容保存到记忆中"
2. **修复非显而易见的 bug 后**: 记录问题和解决方案
3. **发现项目约束时**: 立即更新 CLAUDE.md
4. **会话结束前**: 检查是否有值得持久化的知识
```

---

## 6. 当前项目分析

### 6.1 现有 CLAUDE.md 结构

当前项目已建立完善的 CLAUDE.md 层级：

```
ai-studio-project/
├── CLAUDE.md                    # 项目根 (主入口)
├── backend/
│   ├── CLAUDE.md               # 后端开发指南
│   └── tests/
│       └── CLAUDE.md           # 测试规范
├── frontend/
│   └── CLAUDE.md               # 前端开发指南
└── infrastructure/cdk/
    └── CLAUDE.md               # CDK 部署指南
```

### 6.2 现有配置优势

1. **清晰的模块分离** - 每个主要组件有独立的 CLAUDE.md
2. **术语标准化** - 定义了训练任务、数据集等核心实体命名
3. **Spec-Kit 集成** - 使用规范驱动开发工作流
4. **Serena 集成** - 项目约束通过 Serena Memory 管理

### 6.3 潜在改进空间

| 现状 | 建议 |
|------|------|
| 未使用 `.claude/rules/` | 考虑将大型规范拆分到 rules 目录 |
| 部分导入未使用 @语法 | 统一使用 @import 语法 |
| 缺少路径特定规则 | 为 API 和测试添加 path-specific rules |

---

## 7. 优化建议

### 7.1 短期优化

1. **创建 `.claude/rules/` 结构**：
   ```
   .claude/rules/
   ├── tdd-workflow.md        # TDD 工作流详细说明
   ├── api-design.md          # API 设计规范
   ├── testing-standards.md   # 测试标准（带 paths 限定）
   └── ddd-patterns.md        # DDD 模式指南
   ```

2. **为测试文件添加路径特定规则**：
   ```markdown
   ---
   paths:
     - "backend/tests/**/*.py"
   ---
   # 测试规则
   - 测试诚信原则：永不伪造测试结果
   - 使用 pytest fixtures
   - ...
   ```

### 7.2 中期优化

1. **建立 Serena Memory 使用规范**：
   - 架构决策记录 (ADR) → `memories/adr-*.md`
   - 任务进度追踪 → `memories/task-progress.md`
   - 技术债务记录 → `memories/tech-debt.md`

2. **实现记忆审计流程**：
   - 每周 review CLAUDE.md 和 memories
   - 删除过时信息
   - 更新变更的约定

### 7.3 长期优化

1. **团队级记忆共享**：
   - 将验证过的规则提取到公司级共享目录
   - 使用符号链接在项目间共享

2. **自动化记忆管理**：
   - Hook 实现：在特定事件后提示更新记忆
   - CI 集成：验证 CLAUDE.md 格式和大小

---

## 8. 参考资源

### 官方文档
- [Claude Code Memory Management](https://code.claude.com/docs/en/memory)
- [Claude Code Settings](https://code.claude.com/docs/en/settings)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### 社区资源
- [The Complete Guide to CLAUDE.md - Builder.io](https://www.builder.io/blog/claude-md-guide)
- [Writing a Good CLAUDE.md - HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Claude Code Memory Optimization - ClaudeFast](https://claudefa.st/blog/guide/mechanics/memory-optimization)

### MCP 相关
- [Serena MCP Server](https://mcpservers.org/servers/oraios/serena)
- [Serena GitHub](https://github.com/oraios/serena)

---

## 附录 A: 配置速查表

### CLAUDE.md 位置速查

| 类型 | 位置 | 优先级 | 版本控制 |
|------|------|--------|----------|
| Enterprise | `/Library/Application Support/ClaudeCode/CLAUDE.md` | 最高 | N/A |
| Project | `./CLAUDE.md` | 高 | 应提交 |
| Project Local | `./CLAUDE.local.md` | 高 | 不提交 |
| User Global | `~/.claude/CLAUDE.md` | 低 | 个人 |

### Serena Memory 命令速查

```python
# 列出所有记忆
list_memories()

# 读取记忆
read_memory("memory-name")

# 写入记忆
write_memory("memory-name", "content in markdown")

# 删除记忆
delete_memory("memory-name")

# 编辑记忆
edit_memory("memory-name", "old_pattern", "new_content")
```

### Claude Code 会话命令

```bash
# 继续最近会话
claude --continue

# 恢复指定会话
claude --resume abc123

# 交互式选择会话
claude --resume

# 指定会话 ID
claude --session-id my-custom-id
```

---

**报告生成时间**: 2026-01-18
**研究置信度**: 高 (基于官方文档和广泛社区验证)
