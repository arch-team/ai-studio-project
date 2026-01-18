---
name: analyze
description: 分析现有项目的上下文配置，提供优化建议
allowed-tools: Read, Glob, Grep
---

# Context Analyze 命令

分析当前项目的上下文配置状态，并提供优化建议。

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

### Step 4: 分析与评估

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

### Step 5: 生成建议报告

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
3. **问题列表**: 按优先级排列
4. **建议操作**: 具体可执行的改进步骤
5. **Token 分析**: 预算使用情况

## 执行示例

```
用户: /context-architect:analyze

输出:
# 上下文配置分析报告

## 项目概况
| 项目属性 | 值 |
|---------|-----|
| 技术栈 | Python (FastAPI) |
| 目录深度 | 3 级 |
| CLAUDE.md 数量 | 2 |
| Rules 数量 | 5 |

## 问题与建议

### 🔴 需要修复
1. backend/CLAUDE.md 重复了根目录的术语表 (50行)
2. 缺少 tests/ 目录的 CLAUDE.md

### 🟡 建议优化
1. 根 CLAUDE.md 的架构说明过长，建议移到 docs/
2. Rules 中的 Python 规则可以更精简

### 🟢 良好实践
- 清晰的层级继承结构
- 术语表格式规范
```

## 开始执行

现在开始分析当前项目的上下文配置。首先扫描项目结构。
