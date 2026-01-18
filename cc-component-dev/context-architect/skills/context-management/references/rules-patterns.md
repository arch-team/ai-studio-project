# Rules Glob 模式详解

## Rules 概述

Rules 是 Claude Code 的条件性上下文注入机制，通过 glob 模式匹配触发。

**配置位置**: `.claude/settings.json` 或 `.claude/settings.local.json`

## 基本语法

```json
{
  "rules": [
    {
      "glob": "pattern",
      "rule": "当匹配到该模式的文件时，应用此规则"
    }
  ]
}
```

## Glob 模式速查

| 模式 | 匹配 | 不匹配 |
|------|------|--------|
| `*.ts` | `app.ts` | `src/app.ts` |
| `**/*.ts` | `src/app.ts`, `app.ts` | `app.tsx` |
| `src/**` | `src/` 下所有文件 | `lib/app.ts` |
| `**/*.{ts,tsx}` | `.ts` 和 `.tsx` 文件 | `.js` 文件 |
| `**/tests/**` | `tests/` 目录下所有 | `src/test.ts` |
| `!**/*.test.ts` | 排除测试文件 | - |

## 常用配置示例

### 按文件类型

```json
{
  "rules": [
    {
      "glob": "**/*.py",
      "rule": "Python 代码: 使用类型提示，遵循 PEP 8，docstring 使用 Google 风格"
    },
    {
      "glob": "**/*.ts",
      "rule": "TypeScript: 严格模式，显式返回类型，避免 any"
    },
    {
      "glob": "**/*.tsx",
      "rule": "React 组件: 函数组件优先，使用 hooks，props 需要类型定义"
    },
    {
      "glob": "**/*.sql",
      "rule": "SQL: 使用大写关键字，表名小写下划线，添加注释说明"
    }
  ]
}
```

### 按目录结构

```json
{
  "rules": [
    {
      "glob": "src/domain/**/*.py",
      "rule": "领域层: 纯业务逻辑，禁止外部依赖，使用值对象和实体"
    },
    {
      "glob": "src/infrastructure/**/*.py",
      "rule": "基础设施层: 实现仓库接口，使用 SDK-First 原则"
    },
    {
      "glob": "src/api/**/*.py",
      "rule": "API 层: FastAPI 路由，Pydantic 验证，异常处理"
    }
  ]
}
```

### 按测试类型

```json
{
  "rules": [
    {
      "glob": "**/tests/unit/**",
      "rule": "单元测试: 隔离测试，mock 外部依赖，快速执行"
    },
    {
      "glob": "**/tests/integration/**",
      "rule": "集成测试: 使用 testcontainers，真实数据库"
    },
    {
      "glob": "**/tests/e2e/**",
      "rule": "E2E 测试: localstack 模拟 AWS，完整流程"
    },
    {
      "glob": "**/*.test.ts",
      "rule": "Jest 测试: describe/it 结构，expect 断言"
    }
  ]
}
```

### 配置文件

```json
{
  "rules": [
    {
      "glob": "**/Dockerfile*",
      "rule": "Docker: 多阶段构建，非 root 用户，最小化镜像"
    },
    {
      "glob": "**/*.tf",
      "rule": "Terraform: 模块化设计，变量验证，输出文档化"
    },
    {
      "glob": "**/cdk.ts",
      "rule": "CDK: TypeScript，Construct 模式，标签策略"
    },
    {
      "glob": "**/.github/workflows/*.yml",
      "rule": "GitHub Actions: 复用 actions，secrets 管理，缓存优化"
    }
  ]
}
```

## 高级模式

### 组合模式

```json
{
  "glob": "**/*.{ts,tsx,js,jsx}",
  "rule": "JavaScript/TypeScript 文件通用规则"
}
```

### 排除模式

```json
{
  "glob": "src/**/*.ts",
  "rule": "源码规则 (排除 node_modules 已默认)"
}
```

### 特定文件

```json
{
  "glob": "**/package.json",
  "rule": "package.json: 保持依赖排序，使用精确版本"
}
```

## 规则编写指南

### 好的规则

```json
{
  "glob": "**/*.py",
  "rule": "Python: 类型提示必需，使用 dataclass 或 Pydantic，docstring Google 风格"
}
```

特点:
- 具体可执行
- 明确技术选择
- 简洁但完整

### 差的规则

```json
{
  "glob": "**/*.py",
  "rule": "写好的 Python 代码"
}
```

问题:
- 太模糊
- 没有可执行标准
- 浪费 token

## 优先级与冲突

### 加载顺序

1. 全局 settings (`~/.claude/settings.json`)
2. 项目 settings (`.claude/settings.json`)
3. 本地 settings (`.claude/settings.local.json`)

**后加载覆盖先加载**

### 多规则匹配

当文件匹配多个规则时，**所有规则累加应用**：

```json
{
  "rules": [
    {"glob": "**/*.py", "rule": "Python 规则"},
    {"glob": "src/**", "rule": "源码规则"},
    {"glob": "**/tests/**", "rule": "测试规则"}
  ]
}
```

编辑 `src/tests/test_app.py` 时，三条规则全部应用。

## Token 效率

### 规则 Token 预算

| 类型 | 建议长度 | Token |
|------|---------|-------|
| 简单规则 | 1-2 句 | 50-100 |
| 复杂规则 | 3-5 句 | 100-200 |
| 最大单规则 | - | <500 |

### 优化策略

```json
// 低效 ❌
{
  "glob": "**/*.ts",
  "rule": "TypeScript 代码应该使用严格模式，并且要有显式的返回类型声明，同时应该避免使用 any 类型，代码应该遵循项目的 ESLint 配置..."
}

// 高效 ✓
{
  "glob": "**/*.ts",
  "rule": "TS: strict mode, explicit returns, no any"
}
```

## 与 CLAUDE.md 配合

### 分工原则

- **CLAUDE.md**: 全局/模块级规范
- **Rules**: 文件类型特定规范

### 示例配合

```markdown
# backend/CLAUDE.md
## 测试策略
使用 TDD 红绿重构循环
> 具体测试规则见 .claude/settings.json rules
```

```json
// .claude/settings.json
{
  "rules": [
    {"glob": "**/tests/**/*.py", "rule": "pytest: fixture 优先，assert 清晰"}
  ]
}
```
