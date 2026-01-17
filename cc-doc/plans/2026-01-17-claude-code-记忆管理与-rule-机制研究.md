# Plan: Claude Code 记忆管理与 Rule 机制研究

## 研究摘要

Claude Code 提供两种配置机制来管理项目规范：
1. **CLAUDE.md** - 项目级指导文档
2. **Rules** - 模块化、路径特定的规范文件

---

## 1. 记忆管理机制

### 记忆层级（优先级从低到高）

| 层级 | 位置 | 作用域 |
|------|------|--------|
| 用户记忆 | `~/.claude/CLAUDE.md` | 所有项目 |
| 项目记忆 | `./CLAUDE.md` | 当前项目 |
| 项目规则 | `./.claude/rules/*.md` | 当前项目 |
| 本地覆盖 | `./CLAUDE.local.md` | 个人（不提交） |

### 加载机制

Claude Code **自动递归向上查找**记忆文件：
```
当前目录: backend/tests/unit/
↓ 查找 backend/tests/unit/CLAUDE.md
↓ 查找 backend/tests/CLAUDE.md
↓ 查找 backend/CLAUDE.md ✅
↓ 查找 CLAUDE.md ✅
```

---

## 2. Rule 机制详解

### Rule vs CLAUDE.md

| 特性 | CLAUDE.md | Rules |
|------|-----------|-------|
| 文件位置 | 项目根 | `.claude/rules/` |
| 文件数量 | 1个 | 多个专题文件 |
| 路径特定 | ❌ | ✅ 支持 |
| 组织方式 | 单一 | 支持子目录 |

### Rule 文件结构

```
.claude/rules/
├── general.md              # 全局规范
├── testing/
│   ├── pytest-patterns.md  # pytest 最佳实践
│   └── tdd-principles.md   # TDD 工作流
├── backend/
│   ├── ddd-patterns.md     # DDD 架构规范
│   └── modules/
│       ├── training.md     # 训练模块专用
│       └── datasets.md     # 数据集模块专用
└── infrastructure/
    └── cdk-patterns.md     # CDK 规范
```

### 路径特定 Rule（关键功能）

使用 YAML frontmatter 的 `paths` 字段指定规则适用范围：

```markdown
---
paths:
  - "backend/tests/**/*.py"
---

# 后端测试规范

这些规则仅在编辑 backend/tests/ 下的文件时生效。
```

### Glob 模式支持

| 模式 | 匹配 |
|------|------|
| `**/*.py` | 所有 Python 文件 |
| `backend/tests/**/*.py` | 后端测试文件 |
| `{src,tests}/**/*` | 多个目录 |

---

## 3. 为 backend/tests 添加 Rule 的方案

### 方案：创建测试专用 Rule 文件

**文件**: `.claude/rules/testing/backend-tests.md`

```markdown
---
paths:
  - "backend/tests/**/*.py"
---

# 后端测试规范

## TDD 工作流
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 最小实现使测试通过
3. 🔄 Refactor: 保持测试绿色，优化代码

## 测试分层
- **Unit**: `tests/unit/` - 实体、值对象、域逻辑
- **Integration**: `tests/integration/` - API、仓库
- **E2E**: `tests/e2e/` - HyperPod/S3 集成

## 命名规范
- 文件: `test_<功能>.py`
- 函数: `test_<功能>_<场景>_<预期结果>()`

## Fixture 位置
- 共享: `tests/conftest.py`
- 模块级: `tests/modules/<module>/conftest.py`
```

### 执行验证

使用 `/memory` 命令查看加载的规则：
```bash
> /memory
已加载: .claude/rules/testing/backend-tests.md
  (因为 paths 匹配当前文件)
```

---

## 4. 推荐的 Rules 目录结构

```
.claude/rules/
├── general.md                    # 全局术语、提交规范
├── testing/
│   ├── backend-tests.md          # 后端测试规范
│   │   paths: backend/tests/**/*.py
│   ├── frontend-tests.md         # 前端测试规范
│   │   paths: frontend/src/**/*.test.tsx
│   └── tdd-principles.md         # TDD 原则（无 paths = 全局）
├── backend/
│   ├── ddd-architecture.md       # DDD 架构
│   │   paths: backend/src/**/*.py
│   └── sdk-first.md              # SDK-First 原则
└── infrastructure/
    └── cdk-patterns.md           # CDK 规范
        paths: infrastructure/cdk/**/*.ts
```

---

## 5. 实施计划

### 要创建的文件

| 文件 | 用途 | paths 匹配 |
|------|------|------------|
| `.claude/rules/testing/backend-tests.md` | 后端测试规范 | `backend/tests/**/*.py` |
| `.claude/rules/testing/tdd-principles.md` | TDD 工作流 | 全局 |
| `.claude/rules/backend/ddd-architecture.md` | DDD 架构规范 | `backend/src/**/*.py` |
| `.claude/rules/general.md` | 术语标准 | 全局 |

### 实施步骤

1. 创建 `.claude/rules/` 目录结构
2. 创建测试专用 Rule (`testing/backend-tests.md`)
3. 创建 TDD 原则 Rule (`testing/tdd-principles.md`)
4. 创建 DDD 架构 Rule (`backend/ddd-architecture.md`)
5. 创建全局术语 Rule (`general.md`)

### 关键文件路径

```
.claude/rules/
├── general.md
├── testing/
│   ├── backend-tests.md
│   └── tdd-principles.md
└── backend/
    └── ddd-architecture.md
```

---

## 验证方式

1. 创建后使用 `/memory` 命令验证加载
2. 在 `backend/tests/` 下编辑文件，验证规则生效
3. 检查 Claude 响应是否遵循规则规范
