# CLAUDE.md 层级详解

## 层级结构

Claude Code 支持多层级 CLAUDE.md 配置，形成继承链：

```
~/.claude/CLAUDE.md                    # Level 0: 全局用户配置
└── project/CLAUDE.md                  # Level 1: 项目根配置
    ├── backend/CLAUDE.md              # Level 2: 模块配置
    │   ├── src/domain/CLAUDE.md       # Level 3: 子模块配置
    │   └── tests/CLAUDE.md            # Level 3: 测试配置
    ├── frontend/CLAUDE.md             # Level 2: 前端配置
    └── infrastructure/cdk/CLAUDE.md   # Level 2: 基础设施配置
```

## 加载顺序

1. **全局配置** (`~/.claude/CLAUDE.md`) - 始终加载
2. **项目配置** (`project/CLAUDE.md`) - 进入项目时加载
3. **子目录配置** - 操作该目录文件时加载

**示例**: 编辑 `backend/tests/test_user.py` 时加载：
```
~/.claude/CLAUDE.md
→ project/CLAUDE.md
→ project/backend/CLAUDE.md
→ project/backend/tests/CLAUDE.md
```

## 各层级职责

### Level 0: 全局用户配置

**位置**: `~/.claude/CLAUDE.md`

**适合内容**:
- 个人偏好 (响应语言、代码风格)
- 常用框架/工具配置
- MCP Server 使用指南
- 通用行为模式

**示例**:
```markdown
# 全局配置

## 响应语言
所有对话使用中文。

## 通用原则
- 代码注释使用英文
- 优先使用 TypeScript
- 测试覆盖率 > 80%

## MCP 配置
@MCP_Serena.md
@MCP_Sequential.md
```

### Level 1: 项目根配置

**位置**: `project/CLAUDE.md`

**适合内容**:
- 项目概述和核心价值
- 架构约束和设计原则
- 术语标准表
- 关键文档索引
- TDD/开发流程

**示例**:
```markdown
# CLAUDE.md

## 项目概述
AI Training Platform - 企业级分布式训练平台

## 核心约束
- DDD + Clean Architecture
- SDK-First 原则
- TDD 红绿重构

## 术语标准
| 中文 | 类名 | 数据库表 |
|------|------|---------|
| 训练任务 | TrainingJob | training_jobs |

## 关键文档
> 详见 `docs/ARCHITECTURE.md`
```

### Level 2: 模块配置

**位置**: `backend/CLAUDE.md`, `frontend/CLAUDE.md`

**适合内容**:
- 模块特定技术栈
- 测试策略
- 代码组织规范
- 依赖管理

**示例** (`backend/CLAUDE.md`):
```markdown
# Backend CLAUDE.md

> 继承 ../CLAUDE.md 的核心约束

## 技术栈
- Python 3.11+, FastAPI, SQLAlchemy
- boto3 SDK 优先于直接 API

## 目录结构
src/
├── domain/      # 领域模型
├── application/ # 应用服务
├── infrastructure/ # 基础设施
└── api/         # API 端点

## 测试命令
pytest tests/ -v --cov=src
```

### Level 3: 子模块配置

**位置**: `backend/tests/CLAUDE.md`

**适合内容**:
- 子模块特定规范
- 覆盖父级配置
- 细粒度工具配置

**示例** (`backend/tests/CLAUDE.md`):
```markdown
# Tests CLAUDE.md

> 继承 ../CLAUDE.md

## 测试规范
- Unit: pytest + pytest-mock
- Integration: testcontainers
- E2E: localstack

## 命名约定
- 文件: test_{module}.py
- 函数: test_{action}_{scenario}_{expected}
```

## 继承与覆盖

### 继承模式

子目录 CLAUDE.md **累加**父级配置，不覆盖：

```
project/CLAUDE.md:     "使用 TDD"
backend/CLAUDE.md:     "使用 pytest" + 继承 TDD
backend/tests/CLAUDE.md: "覆盖率 > 90%" + 继承上述所有
```

### 覆盖模式

需要覆盖时，明确声明：

```markdown
# backend/tests/CLAUDE.md

## 覆盖配置
- 测试文件无需文档字符串 (覆盖父级要求)
```

## 设计原则

### 1. 避免重复

```markdown
# 错误 ❌
backend/CLAUDE.md: "本项目使用 DDD..."
frontend/CLAUDE.md: "本项目使用 DDD..."

# 正确 ✓
project/CLAUDE.md: "本项目使用 DDD..."
backend/CLAUDE.md: "> 继承 ../CLAUDE.md"
```

### 2. 增量定义

子目录只定义新增内容：

```markdown
# backend/CLAUDE.md
> 架构规范见 ../CLAUDE.md

## 后端特有配置
- Python 版本: 3.11+
- ORM: SQLAlchemy 2.0
```

### 3. 引用而非复制

```markdown
# 错误 ❌
## 详细架构
[复制 100 行架构说明]

# 正确 ✓
## 架构
> 详见 docs/ARCHITECTURE.md
```

## Token 预算指南

| 层级 | 建议行数 | Token 估算 |
|------|---------|-----------|
| 全局 | 50-100 | 500-1000 |
| 项目根 | 100-200 | 1000-2000 |
| 模块 | 30-50 | 300-500 |
| 子模块 | 20-30 | 200-300 |

**总预算**: 单次对话不超过 ~5000 tokens 用于 CLAUDE.md
