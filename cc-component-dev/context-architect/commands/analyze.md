---
description: Analyze existing context configuration and provide suggestions
allowed-tools: Read, Glob, Grep, Task
---

# Context Analyze 命令

分析当前项目的上下文配置状态，并提供优化建议。

## 获取最新规范

当需要验证配置是否符合 Claude Code 最新规范时，使用 Task 工具调用 claude-code-guide agent：

```
Task(
  subagent_type="claude-code-guide",
  prompt="查询 [具体问题]",
  description="验证配置规范"
)
```

**适用场景**：
- 验证 CLAUDE.md 结构是否符合最新推荐
- 检查 Rules glob 模式是否正确
- 确认 settings.json 字段是否有效
- 了解最新的最佳实践

## 执行流程

### Step 1: 扫描项目结构

使用 Glob 工具扫描以下内容：

```
# 扫描 CLAUDE.md 文件
**/CLAUDE.md

# 扫描 Claude 配置
.claude/**

# 扫描技术栈标识文件
package.json
pyproject.toml
Cargo.toml
go.mod
pom.xml
build.gradle
*.csproj
```

### Step 2: 检测技术栈

根据配置文件判断技术栈：

| 文件 | 技术栈 |
|------|--------|
| `package.json` | Node.js/JavaScript |
| `pyproject.toml` / `requirements.txt` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `pom.xml` / `build.gradle` | Java |
| `*.csproj` | .NET |

### Step 3: 读取现有配置

读取以下文件（如果存在）：

1. **CLAUDE.md 文件**
   - 项目根 CLAUDE.md
   - 子目录 CLAUDE.md

2. **Claude 设置**
   - `.claude/settings.json`
   - `.claude/settings.local.json`

3. **项目配置**
   - 技术栈配置文件
   - README.md (了解项目背景)

### Step 4: 验证规范合规性

对发现的配置进行规范验证。如果存在以下情况，调用 claude-code-guide 获取最新规范：

- 发现未知的配置字段
- Rules 使用了复杂的 glob 模式
- 存在 Hooks 或 MCP 配置

```
Task(
  subagent_type="claude-code-guide",
  prompt="验证以下 Claude Code 配置是否符合最新规范: [配置内容]",
  description="验证配置合规性"
)
```

### Step 5: 分析与评估

对每个发现的配置进行评估：

#### CLAUDE.md 分析

```markdown
## CLAUDE.md 分析报告

### 文件: {path}

**行数**: {lines}
**估算 Token**: {tokens}

**内容评估**:
- [ ] 包含响应语言设置
- [ ] 包含项目概述
- [ ] 包含核心约束
- [ ] 包含术语标准
- [ ] 包含关键文档索引

**问题检测**:
- [ ] 内容过长 (>200行)
- [ ] 与父级重复内容
- [ ] 缺少必要章节
- [ ] 详细信息应移到 Rules/Memory
```

#### Rules 分析

```markdown
## Rules 配置分析

**规则数量**: {count}
**涉及模式**: {patterns}

**评估**:
- [ ] glob 模式合理
- [ ] 规则描述清晰
- [ ] 无重叠规则
- [ ] Token 效率良好
```

### Step 6: 生成建议报告

输出完整的分析报告：

```markdown
# 上下文配置分析报告

## 项目概况

| 项目属性 | 值 |
|---------|-----|
| 技术栈 | {stack} |
| 目录深度 | {depth} |
| CLAUDE.md 数量 | {count} |
| Rules 数量 | {rules} |

## 当前配置状态

### CLAUDE.md 层级

```
project/CLAUDE.md ({lines}行, ~{tokens} tokens)
├── backend/CLAUDE.md ({lines}行)
└── frontend/CLAUDE.md ({lines}行)
```

### Rules 配置

{rules 列表或"未配置"}

### Memory 使用

{检测到的 memory 使用情况或"未检测到"}

## 规范合规性检查

{基于 claude-code-guide 查询结果的合规性评估}

## 问题与建议

### 🔴 需要修复

{严重问题列表}

### 🟡 建议优化

{优化建议列表}

### 🟢 良好实践

{做得好的地方}

## 推荐操作

1. {具体操作建议 1}
2. {具体操作建议 2}
3. {具体操作建议 3}

## Token 预算分析

| 配置项 | 当前 Token | 建议 Token | 状态 |
|--------|-----------|-----------|------|
| 根 CLAUDE.md | {current} | <2000 | {status} |
| 子目录合计 | {current} | <2000 | {status} |
| Rules 合计 | {current} | <1500 | {status} |
| **总计** | {total} | <5500 | {status} |
```

## 输出格式

分析结果使用以下格式输出：

1. **概览表格**: 快速了解配置状态
2. **详细分析**: 每个文件的具体评估
3. **规范合规性**: 基于最新规范的验证结果
4. **问题列表**: 按优先级排列
5. **建议操作**: 具体可执行的改进步骤
6. **Token 分析**: 预算使用情况

## 开始执行

现在开始分析当前项目的上下文配置。首先扫描项目结构。
