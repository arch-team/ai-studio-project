# Rules 配置详解

## Rules 概述

Rules 是 Claude Code 的条件性上下文注入机制，通过文件系统自动发现。

**配置位置**: `.claude/rules/` 目录

## 目录结构

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # 主项目指令文件
│   └── rules/
│       ├── code-style.md       # 代码风格规则
│       ├── testing.md          # 测试规约
│       ├── security.md         # 安全要求
│       └── frontend/
│           ├── react.md        # React 规则
│           └── styles.md       # 样式规则
```

**注意**：
- `.claude/rules/` 中的所有 `.md` 文件自动加载
- 支持子目录组织
- 用户级规则在 `~/.claude/rules/`

## Rule 文件格式

### 无条件规则（应用到所有文件）

```markdown
# General Coding Standards

- 所有代码必须包含类型注解
- 使用 2 空格缩进
- 函数长度不超过 50 行
```

### 路径特定规则（使用 paths frontmatter）

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/services/**/*.ts"
---

# API Development Rules

- 所有 API 端点必须包含输入验证
- 使用标准的错误响应格式
- 包含 OpenAPI 文档注释
```

### 多模式规则

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---

# TypeScript Rules

- 函数参数必须显式类型
- 优先使用 type 而非 interface
```

## Glob 模式速查

| 模式 | 匹配 | 示例 |
|------|------|------|
| `**/*.ts` | 任何目录的 .ts 文件 | `src/utils/helper.ts` |
| `src/**/*` | src 下所有文件 | `src/api/users.ts` |
| `*.md` | 根目录的 .md 文件 | `README.md` |
| `src/**/*.{ts,tsx}` | src 下的 ts 和 tsx | `src/App.tsx` |
| `{src,lib}/**/*.ts` | src 或 lib 下的 ts | `lib/core.ts` |

## 常用规则示例

### 按文件类型

**`.claude/rules/python.md`**:
```markdown
---
paths:
  - "**/*.py"
---

# Python Rules

- 使用类型提示 (type hints)
- 遵循 PEP 8 规范
- docstring 使用 Google 风格
- 使用 dataclass 或 Pydantic 模型
```

**`.claude/rules/typescript.md`**:
```markdown
---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript Rules

- 严格模式，显式返回类型
- 避免使用 any
- 优先使用 type 而非 interface
```

### 按目录结构

**`.claude/rules/backend/domain.md`**:
```markdown
---
paths:
  - "src/domain/**/*.py"
---

# Domain Layer Rules

- 纯业务逻辑，禁止外部依赖
- 使用值对象和实体
- 禁止直接访问数据库
```

**`.claude/rules/backend/infrastructure.md`**:
```markdown
---
paths:
  - "src/infrastructure/**/*.py"
---

# Infrastructure Layer Rules

- 实现仓库接口
- 使用 SDK-First 原则
- 处理外部服务异常
```

### 测试规则

**`.claude/rules/testing.md`**:
```markdown
---
paths:
  - "**/tests/**"
  - "**/*.test.ts"
  - "**/*_test.py"
---

# Testing Rules

- 使用 AAA 模式 (Arrange-Act-Assert)
- 测试函数命名: test_{action}_{scenario}_{expected}
- Mock 外部依赖
- 每个测试只验证一个行为
```

## 加载优先级

1. **Managed 规则** (最高) - 系统级别
2. **用户级规则** - `~/.claude/rules/`
3. **项目规则** - `.claude/rules/`
4. **项目主文件** - `CLAUDE.md` (最低)

## 规则文件命名建议

| 类型 | 建议命名 | 说明 |
|------|---------|------|
| 语言规范 | `python.md`, `typescript.md` | 按语言分类 |
| 架构层 | `domain.md`, `api.md` | 按架构层分类 |
| 功能域 | `testing.md`, `security.md` | 按功能分类 |
| 框架特定 | `react.md`, `fastapi.md` | 按框架分类 |

## 最佳实践

### DO ✅

- **保持规则专注**: 每个文件覆盖一个主题
- **使用描述性文件名**: 反映规则内容
- **有选择地使用 paths**: 仅当规则特定于某些文件时
- **用子目录组织**: `frontend/`, `backend/`, `infra/`

### DON'T ❌

- **避免单一大文件**: 不要把所有规则放在 `all-rules.md`
- **避免过度使用 paths**: 通用规则不需要 paths
- **避免规则重复**: 合并相关的规则

## 与 CLAUDE.md 配合

### 分工原则

| 内容类型 | 放置位置 |
|---------|---------|
| 项目概述、架构 | `CLAUDE.md` |
| 术语标准 | `CLAUDE.md` |
| 文件类型规范 | `.claude/rules/*.md` |
| 测试策略 | `.claude/rules/testing.md` |

### 示例配合

**`CLAUDE.md`**:
```markdown
## 测试策略

使用 TDD 红绿重构循环。

> 具体测试规则见 `.claude/rules/testing.md`
```

**`.claude/rules/testing.md`**:
```markdown
---
paths:
  - "**/tests/**/*.py"
---

# Test Rules

- pytest: fixture 优先
- assert 语句清晰明确
- 覆盖率 > 80%
```

## Token 效率

Rules 按需加载，仅当操作匹配 paths 的文件时才注入上下文：

| 场景 | 加载的 Rules |
|------|-------------|
| 编辑 `src/api/users.py` | `python.md`, `backend/api.md` |
| 编辑 `tests/test_users.py` | `python.md`, `testing.md` |
| 编辑 `src/App.tsx` | `typescript.md`, `frontend/react.md` |

## 迁移旧格式

如果你有旧的 settings.json 格式：

```json
// ❌ 旧格式 (不再支持)
{
  "rules": [
    {"glob": "**/*.py", "rule": "Python 规则"}
  ]
}
```

迁移到新格式：

```markdown
// ✅ 新格式: .claude/rules/python.md
---
paths:
  - "**/*.py"
---

# Python Rules

Python 规则内容...
```
