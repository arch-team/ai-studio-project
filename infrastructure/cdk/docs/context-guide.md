# Claude Code 上下文管理

> **职责**: 说明 `.claude/` 目录结构、文件用途和引用关系，帮助开发者快速定位所需规范文档。

> 本文档位于 `docs/` 目录，用于说明 CDK 基础设施项目的 Claude Code 上下文配置，不直接参与规范加载。

---

## 目录结构

```
.claude/
├── CLAUDE.md                              # 项目主规范 (入口)
├── project-config.md                      # 项目特定配置
└── rules/                                 # 专题规范文档
    ├── architecture.md                    # CDK 架构规范 ★始终加载
    ├── stack-design.md                    # Stack 设计规范
    ├── construct-design.md                # Construct 设计规范
    ├── configuration.md                   # 配置管理规范
    ├── code-style.md                      # 代码风格规范 ★始终加载
    ├── testing.md                         # 测试规范
    ├── security.md                        # 安全规范
    ├── hyperpod.md                        # HyperPod 部署规范
    ├── checklist.md                       # PR Review 检查清单 ★单一真实源
    ├── deployment.md                      # 部署规范
    ├── cost-optimization.md               # 成本优化规范
    └── tech-stack.md                      # 技术栈规范 ★单一真实源
```

---

## 快速开始

### 开发者入门

1. **阅读入口**: 从 `CLAUDE.md` 开始，了解项目概况和核心原则
2. **查阅配置**: 参考 `project-config.md` 了解 Stack 划分
3. **深入专题**: 按需阅读 `rules/` 下的专题规范

### 常用查阅场景

| 场景 | 推荐文档 |
|------|----------|
| PR Review | `rules/checklist.md` |
| Stack 分层和依赖 | `rules/architecture.md` |
| Construct 设计模式 | `rules/construct-design.md` |
| 环境配置 | `rules/configuration.md` |
| 安全最佳实践 | `rules/security.md` |
| HyperPod 部署 | `rules/hyperpod.md` |
| 多环境部署流程 | `rules/deployment.md` |
| 成本优化策略 | `rules/cost-optimization.md` |
| 版本要求 | `rules/tech-stack.md` |
| CDK 命令速查 | `CLAUDE.md` §常用命令 |

---

## 加载策略

### 始终加载

这些规范在所有 CDK 开发场景中始终可用:
- `architecture.md` — Stack 依赖规则
- `code-style.md` — 代码风格

### 按需加载 (frontmatter paths 触发)

| 规范 | 触发路径 |
|------|----------|
| `stack-design` | `stacks/**/*.py`, `app.py` |
| `construct-design` | `cdk_constructs/**/*.py`, `aspects/**/*.py` |
| `configuration` | `config/**/*.py`, `cdk.json` |
| `testing` | `tests/**/*.py`, `conftest.py` |
| `security` | `stacks/**/*.py`, `utils/nag_suppressions.py` |
| `hyperpod` | `*hyperpod*.py`, `helm_charts/**` |
| `deployment` | `app.py`, `cdk.json` |
| `cost-optimization` | `stacks/**/*.py`, `config/environments.py` |

### 手动引用

没有 frontmatter paths 的规范需手动引用:
- `checklist.md` — PR Review 时手动引用
- `tech-stack.md` — 版本检查时手动引用

---

## 引用关系

| 文档 | 主要引用 | 说明 |
|------|---------|------|
| **CLAUDE.md** (入口) | 所有 rules/*.md | 项目入口，引用所有专题文档 |
| checklist.md | 所有 rules/*.md | PR Review 检查清单，引用各专题详细说明 |
| deployment.md | architecture, configuration, security, hyperpod, cost-optimization | 部署规范，与 configuration 有职责边界 |
| cost-optimization.md | configuration, hyperpod, deployment | 成本优化，引用部署和配置 |
| architecture.md | - | 核心架构，被大多数文档引用 |
| construct-design.md | architecture | Construct 设计，引用架构规范 |
| security.md | - | 安全规范，被 checklist 和 deployment 引用 |

**引用原则**:
- **单向为主**: CLAUDE.md 是入口，rules/ 是专题文档
- **单一真实源 (SSOT)**: checklist 是 PR Review 唯一来源，tech-stack 是版本唯一来源，deployment 是删除策略唯一来源
- **职责边界**: 相关文档通过边界说明明确各自职责

---

## 设计特点

### 速查卡片 (Section 0)

规范文档提供速查区域，包含:
- 常用模式速查表
- 关键命令
- 环境差异矩阵

### 单一真实源 (SSOT)

关键信息只在一个地方定义:
- **PR Review 检查清单**: `checklist.md`
- **技术栈版本**: `tech-stack.md`
- **删除策略**: `deployment.md`
- **TDD 工作流**: `testing.md`
- **覆盖率要求**: `testing.md`

其他文档通过链接引用，避免重复。

### 职责边界

相关文档通过边界说明明确职责分工:
- `configuration.md` ↔ `deployment.md`: 配置代码架构 vs 部署执行
- `configuration.md` ↔ `cost-optimization.md`: 代码层配置 vs 资源规格成本
- `security.md` ↔ `checklist.md`: 安全详细说明 vs 检查项汇总

---

## 维护指南

### 新增规范

1. 按需加载的规范添加 frontmatter `paths`
2. 更新本文件的目录结构和引用关系
3. 更新 `CLAUDE.md` 的规范导航表

### 更新规范

1. 修改规范后，确保更新对应的速查区域
2. 新增引用时，检查是否形成循环依赖
3. 保持 `CLAUDE.md` 的规范导航表同步
