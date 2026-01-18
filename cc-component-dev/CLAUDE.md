# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Claude Code 组件开发工作区 - 用于开发和测试 Claude Code 插件（plugins）、命令（commands）、技能（skills）和代理（agents）。

## 本地测试命令

```bash
# 测试插件加载
claude --plugin-dir ./context-architect

# 测试特定命令
/context-architect:architect
/context-architect:analyze
/context-architect:optimize
```

## Claude Code Plugin 开发规范

### plugin.json 格式

**必须遵循简洁格式**，避免使用可能导致加载失败的额外字段：

```json
{
  "name": "plugin-name",
  "description": "Plugin description in English",
  "author": {
    "name": "Author Name"
  }
}
```

**已知会导致插件无法加载的字段**：
- `keywords` 数组（特别是包含特殊字符如 `CLAUDE.md`）
- `repository` 对象格式
- `version` 字段（可选但不推荐）

### Command Frontmatter 规范

**合法字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | String | 命令描述（推荐 < 60 字符） |
| `allowed-tools` | String | 允许的工具，逗号分隔 |
| `model` | String | sonnet/opus/haiku |
| `argument-hint` | String | 参数提示 |
| `disable-model-invocation` | Boolean | 禁止自动调用 |

**非法字段**（会导致命令无法加载）：
- `name` - 命令名称由文件名决定，不能在 frontmatter 中指定

**正确示例**：
```yaml
---
description: Design optimal context configuration
allowed-tools: AskUserQuestion, Write, Read, Glob
---
```

### Agent Frontmatter 规范

```yaml
---
name: agent-name
description: Agent description
---
```

### Skill SKILL.md 规范

```yaml
---
name: skill-name
description: Trigger conditions description
---
```

## 目录结构

```
cc-component-dev/
├── context-architect/     # 主插件：上下文管理专家
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/          # 斜杠命令
│   ├── agents/            # 代理定义
│   └── skills/            # 技能定义
├── test-plugin/           # 测试用最小插件
├── ctx-test/              # 测试用临时插件
└── prompt-history/        # 其他插件
```

## claude-code-guide 集成

context-architect 插件通过 Task 工具调用 `claude-code-guide` agent 获取最新规范：

```
Task(
  subagent_type="claude-code-guide",
  prompt="查询 [具体问题]",
  description="获取 Claude Code 规范"
)
```

**注意**：`claude-code-guide` 是 Task Agent，不是 MCP Server。

## 调试技巧

当命令显示 "Unknown skill" 错误时：
1. 检查 `plugin.json` 是否使用简洁格式
2. 检查命令 frontmatter 是否使用了非法字段（如 `name`）
3. 使用 `--verbose` 标志查看加载日志
4. 创建最小测试插件逐步排查
