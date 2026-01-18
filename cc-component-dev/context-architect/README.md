# Context Architect Plugin

Claude Code 上下文管理专家插件，帮助设计最优的 CLAUDE.md、Rules、Memory 配置。

## 功能概述

Context Architect 提供以下能力：

1. **引导式配置设计** - 通过多轮对话收集项目信息，生成最优配置
2. **现有配置分析** - 扫描项目结构，评估配置状态
3. **Token 效率优化** - 识别冗余内容，提供精简建议
4. **主动配置检测** - 自动发现配置缺失，提供建议

## 安装

将此插件目录放入 Claude Code 插件路径：

```bash
# 全局安装
cp -r context-architect ~/.claude/plugins/

# 或项目级安装
cp -r context-architect .claude/plugins/
```

## 使用方法

### 命令

#### `/context-architect:architect`

引导式配置向导，帮助从零开始设计项目的上下文配置。

```
/context-architect:architect
```

**流程**:
1. Phase 1: 收集项目画像 (类型、技术栈、规模)
2. Phase 2: 盘点规范需求 (术语、架构、编码风格)
3. Phase 3: 规划 Token 预算，生成配置

**输出**:
- 项目 CLAUDE.md 模板
- 子目录 CLAUDE.md 模板
- Rules 配置 JSON
- Memory 使用建议

#### `/context-architect:analyze`

分析现有项目的上下文配置状态。

```
/context-architect:analyze
```

**输出**:
- 项目概况
- 配置状态评估
- 问题检测与建议
- Token 预算分析

#### `/context-architect:optimize`

专项分析 CLAUDE.md 的 Token 效率。

```
/context-architect:optimize
```

**输出**:
- Token 占用分析
- 冗余内容检测
- 精简建议
- 优化后预览

### Skill

插件包含 `context-management` skill，在以下场景自动激活：

- "设计 CLAUDE.md"
- "配置上下文"
- "优化 token"
- "Rules 配置"
- "Memory 策略"

### Agent

`context-analyzer` agent 在以下情况主动触发：

- 检测到项目根目录没有 CLAUDE.md
- 检测到 `.claude/` 目录配置不完整
- 用户请求分析上下文配置

## 知识体系

### 混合知识策略

插件采用 **静态知识 + 动态查询** 的混合策略：

1. **静态知识 (Skill references)** - 核心稳定知识，离线可用
2. **动态查询 (claude-code-guide agent)** - 最新规范，实时获取

### claude-code-guide 集成

命令执行时可调用 `claude-code-guide` agent 获取最新的 Claude Code 规范：

```
Task(
  subagent_type="claude-code-guide",
  prompt="查询 CLAUDE.md 的最新层级规范",
  description="获取 Claude Code 规范"
)
```

**适用场景**：
- 确认 CLAUDE.md 最新支持的特性
- 验证 Rules glob 模式语法
- 了解 Hooks 事件类型
- 确认 MCP server 配置格式

### Skill 知识结构

```
skills/context-management/
├── SKILL.md                    # 核心知识 (上下文三层体系、设计原则)
└── references/
    ├── claude-md-hierarchy.md  # CLAUDE.md 层级详解
    ├── rules-patterns.md       # Rules glob 模式
    ├── memory-strategies.md    # Serena Memory 策略
    └── token-optimization.md   # Token 效率原则
```

### 核心概念

| 机制 | 加载时机 | Token 预算 | 适用场景 |
|------|---------|-----------|---------|
| CLAUDE.md | 每次对话 | ~2000-5000 | 核心规范 |
| Rules | 文件匹配时 | ~500-1000/rule | 文件类型规范 |
| Memory | 按需读取 | 无限制 | 项目知识 |

## 最佳实践

### CLAUDE.md 层级

```
~/.claude/CLAUDE.md          # 全局 (个人偏好)
└── project/CLAUDE.md        # 项目根 (架构、术语)
    ├── backend/CLAUDE.md    # 后端 (SDK、测试)
    └── frontend/CLAUDE.md   # 前端 (组件、状态)
```

### Token 预算分配

| 层级 | 建议行数 | Token |
|------|---------|-------|
| 全局 | 50-100 | 500-1000 |
| 项目根 | 100-200 | 1000-2000 |
| 子目录 | 30-50 | 300-500 |

### 内容分类

- **高频内容** → CLAUDE.md
- **条件触发** → Rules
- **低频参考** → Memory

## 示例

### 创建新项目配置

```
用户: /context-architect:architect

Claude: 我将帮助你设计项目的上下文配置。首先，请告诉我这是什么类型的软件项目？

[选项: Web应用, CLI工具, 库/SDK, 微服务, 基础设施, 其他]

用户: Web应用

Claude: 了解了。请问使用什么技术栈？
...

[完成向导后生成配置文件]
```

### 分析现有配置

```
用户: /context-architect:analyze

Claude:
# 上下文配置分析报告

## 项目概况
| 属性 | 值 |
|------|-----|
| 技术栈 | Python (FastAPI) |
| CLAUDE.md 数量 | 2 |

## 问题与建议

🔴 backend/CLAUDE.md 重复了根目录的术语表
🟡 根 CLAUDE.md 的架构说明过长

## 推荐操作
1. 删除 backend/CLAUDE.md 第 45-65 行的重复内容
2. 将详细架构说明移到 docs/ARCHITECTURE.md
```

## 文件结构

```
context-architect/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── architect.md
│   ├── analyze.md
│   └── optimize.md
├── agents/
│   └── context-analyzer.md
├── skills/
│   └── context-management/
│       ├── SKILL.md
│       └── references/
│           ├── claude-md-hierarchy.md
│           ├── rules-patterns.md
│           ├── memory-strategies.md
│           └── token-optimization.md
└── README.md
```

## 开发

### 本地测试

```bash
# 在测试项目中运行
claude /context-architect:analyze
```

### 验证插件

使用 plugin-validator 验证结构：

```
/plugin-dev:validate context-architect
```

## 许可证

MIT License

## 作者

AI Studio Project
