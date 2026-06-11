# CLAUDE.md

本文件为 Claude Code 提供项目级开发指导。

## 响应语言
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)
### 强制要求

- 所有对话必须使用中文
- 代码注释使用中文
- 文档内容使用中文
- Git 提交信息使用中文

### 例外情况

以下内容保持英文:
- 代码变量名、函数名、类名
- 技术术语 (如 API, SDK, TDD)
- 第三方库/框架名称
- 错误信息和日志 (可选)


## 项目概述
AI Training Platform - 基于 AWS SageMaker HyperPod 构建的企业级 AI 训练平台。

**核心功能**:
- 分布式训练管理 (PyTorch DDP, FSDP, DeepSpeed)
- 资源调度 (Gang Scheduling, 优先级抢占)
- 数据集管理 (版本控制, 大文件断点续传)
- 检查点管理 (分层存储, 自动恢复)
- 多租户支持 (RBAC, 资源配额)

## 架构概览

| 子项目 | 架构模式 | 核心依赖方向 |
|--------|---------|-------------|
| 后端 | DDD + Modular Monolith + Clean Architecture | `API → Application → Domain ← Infrastructure` |
| 前端 | Feature-Sliced Design + Clean Architecture | `pages → components → hooks → api → types` |
| 基础设施 | CDK Stack 5 层分层 | `L1 Network/IAM → L2 DB/Storage → L3 EKS/HyperPod` |

> 各子项目详细架构规范参见对应的 `.claude/rules/architecture.md`

## 核心开发原则

### TDD 工作流

本项目全面采用测试驱动开发 (TDD)。

**核心循环**: Red (先写失败测试) → Green (最少代码通过) → Refactor (重构保持通过)

**测试诚信原则**: 切勿为让测试通过而伪造结果。测试失败 = 代码有问题，必须修复代码。

> 各模块测试命令和分层策略参见对应子项目 CLAUDE.md

### SDK-First 原则

> 详细 SDK 使用规范请参见 `backend/CLAUDE.md`

## 术语标准

详细术语规范参见 `specs/001-ai-training-platform/spec.md`

**核心实体命名**:

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |

**训练任务状态**:
`submitted` → `running` → `completed` / `failed` / `paused` / `preempted`

## 文档导航

| 文档 | 位置 | 用途 |
|------|------|------|
| **功能规范** | `specs/001-ai-training-platform/spec.md` | 完整功能需求和术语标准 |
| **实施计划** | `specs/001-ai-training-platform/plan.md` | 开发里程碑和任务分解 |
| **数据模型** | `specs/001-ai-training-platform/data-model.md` | 数据库设计和实体关系 |

> 子项目开发指南: `backend/CLAUDE.md` | `frontend/CLAUDE.md` | `infrastructure/cdk/CLAUDE.md`
> 通用规则: `.claude/rules/common.md` (Git 提交规范、代码审查、文档命名)

## Spec-Kit 规范驱动开发

本项目使用 Spec-Kit 进行规范驱动开发。详细文件体系和命令参见 `.claude/rules/common.md`。

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
