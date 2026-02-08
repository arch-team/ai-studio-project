# 跨项目通用规则 (Common Rules)

> 适用于所有子项目的通用规范

---

## Git 提交规范

### 提交信息格式

```
<类型>(<范围>): <简短描述>

<详细描述（可选）>

<关联 Issue（可选）>
```

### 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（非新功能/修复） |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖更新 |

### 范围

| 范围 | 说明 |
|------|------|
| `backend` | 后端服务 |
| `frontend` | 前端应用 |
| `cdk` | 基础设施 (CDK) |
| `docs` | 文档 |
| `specs` | 规范文件 |
| `*` | 多个子项目 |

### 示例

```bash
feat(backend): 添加训练任务提交模块
fix(frontend): 修复数据集上传进度显示
docs(*): 更新 CLAUDE.md 文档
chore(backend): 升级 FastAPI 到 0.115
refactor(cdk): 重构 HyperPod Stack 分层
```

---

## 代码审查标准

### 通用检查项

- [ ] 代码符合子项目规范
- [ ] 有充分的测试覆盖
- [ ] 无明显的安全漏洞
- [ ] 文档/注释使用中文
- [ ] 提交信息格式正确

---

## 文档规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 主规范 | `CLAUDE.md` | 各子项目入口（Claude Code 框架约定） |
| 专题规范 | `rules/{topic}.md` | `rules/testing.md`, `rules/architecture.md` |
| 项目配置 | `project-config.md` | 项目特定配置（非 Claude Code 加载） |
| 项目说明 | `README.md` | 项目根目录说明 |

**命名原则**: 除 `CLAUDE.md`（Claude Code 框架约定）和 `README.md` 外，所有文档统一使用 `kebab-case.md`

### 文档语言

- 所有文档内容使用中文
- 代码示例保持原始语言

---

## Monorepo 结构概览

> 本节是 Monorepo 结构的**单一真实源 (Single Source of Truth)**

```
ai-studio-project/                 # Monorepo 根目录
├── .claude/                       # 根级：通用规范
│   ├── CLAUDE.md                  # 全局入口（导航、项目概述）
│   ├── rules/
│   │   └── common.md              # 跨项目通用规则（本文件）
│   ├── commands/                  # Claude Code 自定义命令
│   ├── skills/                    # Claude Code 技能
│   └── evals/                     # Claude Code 评估
├── .specify/                      # Spec-Kit 项目宪法
│   └── memory/
│       └── constitution.md        # 不可违反的核心原则和技术约束
├── specs/                         # Spec-Kit 功能规范
│   └── 001-ai-training-platform/
│       ├── spec.md                # 功能规范 (WHAT/WHY)
│       ├── plan.md                # 实施计划 (HOW)
│       ├── tasks.md               # 任务清单 (DO)
│       ├── data-model.md          # 数据模型设计
│       ├── contracts/             # OpenAPI 契约
│       └── checklists/            # 质量检查清单
├── backend/                       # 后端项目 (Python + FastAPI, DDD)
├── frontend/                      # 前端项目 (React + TypeScript)
├── infrastructure/cdk/            # 基础设施项目 (AWS CDK)
├── cc-doc/                        # Claude Code 文档和计划
└── README.md                      # 项目总说明
```

各子项目的详细目录结构请参考对应的 CLAUDE.md 或 `project-structure.md` 文档。

---

## Spec-Kit 文件体系

本项目使用 Spec-Kit 进行规范驱动开发。文件结构和职责如下：

### 目录结构
```
.specify/memory/constitution.md    # 项目宪法 (全局约束)
specs/{feature}/
├── spec.md          # 功能规范 (WHAT/WHY)
├── plan.md          # 实施计划 (HOW)
├── tasks.md         # 任务清单 (DO)
├── data-model.md    # 数据模型设计
├── research.md      # 技术研究报告
├── quickstart.md    # 快速开始指南
├── checklists/      # 质量检查清单
└── contracts/       # OpenAPI 契约
```

### 文件职责速查

| 文件 | 生成命令 | 职责 |
|------|---------|------|
| `constitution.md` | `/speckit.constitution` | 不可违反的核心原则和技术约束 |
| `spec.md` | `/speckit.specify` | 用户故事、验收标准、术语定义 |
| `plan.md` | `/speckit.plan` | 技术选型、架构设计、里程碑 |
| `tasks.md` | `/speckit.tasks` | 可执行的原子任务清单 (0.5-2人日/任务) |
| `data-model.md` | (plan 附带) | 数据库表结构、持久化策略 |
| `research.md` | (plan 附带) | SDK 可行性验证、技术决策依据 |
| `contracts/*.yaml` | (plan 附带) | OpenAPI 3.0 API 接口规范 |
| `checklists/*.md` | `/speckit.checklist` | 架构/安全/UX 质量验证清单 |

### 工作流程
```
constitution → specify → [clarify] → plan → [checklist] → tasks → implement
```

### 一致性检查
运行 `/speckit.analyze` 检查 spec.md、plan.md、tasks.md 之间的一致性。
