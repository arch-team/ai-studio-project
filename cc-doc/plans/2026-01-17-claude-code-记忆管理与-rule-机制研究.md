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
| 项目记忆 | `./CLAUDE.md` | 当前项目（当前所在目录下有效） |
| 项目规则 | `./.claude/rules/*.md` | 当前项目（当前所在目录下有效） |
| 本地覆盖 | `./CLAUDE.local.md` | 个人（当前所在目录下有效）（不提交） |

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

### Rules vs CLAUDE.md 完整对比

| 特性 | CLAUDE.md | Rules |
|------|-----------|-------|
| **文件位置** | 任意目录（递归向上查找） | 仅 `.claude/rules/` 位置固定|
| **文件数量** | 每目录 1 个 | 多个专题文件 |
| **路径特定** | 隐式（放置位置决定） | 显式（`paths` 字段） |
| **组织方式** | 分散在各目录 | 集中管理 |
| **适用范围** | 当前目录及子目录 | 通过 glob（一种文件路径匹配的通配符语法）模式指定 |
| **版本控制** | 与代码一起提交 | 与代码一起提交 |

### 两种方式的适用场景

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 统一管理所有规范 | `.claude/rules/` | 集中维护，易于审查 |
| 规范与代码紧密关联 | 目录下的 `CLAUDE.md` | 就近原则，便于发现 |
| 需要跨多个目录应用 | Rules + `paths` | 一处定义，多处生效 |
| 模块独立性强 | 目录下的 `CLAUDE.md` | 模块自包含 |

### 只用一种方式的缺点对比

| 方面 | 只用 CLAUDE.md | 只用 Rules |
|------|---------------|------------|
| **集中管理** | ❌ 分散 | ✅ 集中 |
| **就近原则** | ✅ 与代码一起 | ❌ 分离 |
| **跨目录复用** | ❌ 需重复 | ✅ paths 指定 |
| **模块自包含** | ✅ 随模块走 | ❌ 可能遗留 |
| **发现性** | ✅ 目录下可见 | ❌ 需要知道去哪找 |
| **维护成本** | 高（多处修改） | 低（一处修改） |

**推荐**: 混合使用，全局规范放 Rules，模块说明放 CLAUDE.md。

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
| `src/**/*.{ts,tsx}` | TypeScript 和 TSX 文件 |
| `{src,tests}/**/*` | 多个目录 |

### Rule 加载机制

#### 加载时机

| 时机 | 说明 |
|------|------|
| 会话启动 | 新会话、恢复会话 (`--resume`) |
| 会话清空 | `/clear` 命令后 |
| 自动压缩 | `compact` 后重新加载 |

**注意**: 文件修改后需要**新会话**才能生效，运行时修改不会立即应用。

#### 加载顺序（优先级从低到高）

```
1️⃣ ~/.claude/CLAUDE.md          # 用户全局记忆
2️⃣ ~/.claude/rules/*.md         # 用户全局规则
3️⃣ ./CLAUDE.md                  # 项目共享记忆
4️⃣ ./.claude/rules/*.md         # 项目规则
5️⃣ ./CLAUDE.local.md            # 本地个人记忆（最高）
```

**规则**: 高优先级配置**覆盖**低优先级配置。

#### paths 匹配机制

| 情况 | 行为 |
|------|------|
| **有 paths 字段** | 仅当处理匹配文件时加载 |
| **无 paths 字段** | 始终加载，适用于所有文件 |
| **匹配基准** | 当前正在处理的**文件路径**（非工作目录） |

```
处理文件: backend/tests/unit/test_entity.py
↓
匹配 paths: "backend/tests/**/*.py" ✅ 加载
匹配 paths: "frontend/**/*.tsx" ❌ 不加载
无 paths 字段 ✅ 始终加载
```

#### 冲突处理

| 场景 | 处理方式 |
|------|----------|
| 不同内容 | **合并**（累积生效） |
| 相同指令 | **高优先级覆盖**低优先级 |

```
用户 Rule: "Use formatter X"
项目 Rule: "Use formatter Y"
结果: 使用 formatter Y（项目 Rule 优先）
```

#### 性能与缓存

- Rules 在会话启动时**快照加载**
- 支持按子目录组织，按需匹配
- 使用 `paths` 字段限制范围可减少无关规则加载

---

## 3. 为特定目录添加规范的两种方式

### 方式 A: Rules（集中管理）

**位置**: `.claude/rules/testing/backend-tests.md`

**特点**: 规范集中存放，通过 `paths` 字段指定适用范围

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

### 方式 B: CLAUDE.md（就近放置）

**位置**: `backend/tests/CLAUDE.md`

**特点**: 规范与代码放在一起，无需 `paths` 字段，自动应用于当前目录及子目录

```markdown
# 后端测试规范

## TDD 工作流
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 最小实现使测试通过
3. 🔄 Refactor: 保持测试绿色，优化代码

## 测试分层
- **Unit**: `unit/` - 实体、值对象、域逻辑
- **Integration**: `integration/` - API、仓库
- **E2E**: `e2e/` - HyperPod/S3 集成

## 命名规范
- 文件: `test_<功能>.py`
- 函数: `test_<功能>_<场景>_<预期结果>()`
```

### 方式选择建议

| 项目情况 | 推荐方式 |
|----------|----------|
| 测试规范需要全团队统一 | **方式 A** (Rules) |
| 测试模块相对独立 | **方式 B** (CLAUDE.md) |
| 本项目（DDD + Modular） | **方式 A** (统一管理) |

### 验证方式

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
