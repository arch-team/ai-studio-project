# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language

**所有对话和文档必须使用中文。**

## Project Overview

AI Training Platform - 基于 AWS SageMaker HyperPod 构建的企业级 AI 训练平台。

**核心功能**: 分布式训练管理 | 资源调度 | 数据集管理 | 检查点管理 | 多租户支持

## Architecture

**架构模式**: DDD + Modular Monolith + Clean Architecture

**依赖方向**: `API → Application → Domain ← Infrastructure`

> 详细架构规范: `backend/docs/ARCHITECTURE.md`

## Key Principles

| 原则 | 规则文件 |
|------|---------|
| TDD 工作流 | `.claude/rules/global/tdd-workflow.md` |
| SDK 优先 | `.claude/rules/backend/sdk-first.md` |
| Clean Architecture | `.claude/rules/backend/clean-arch.md` |
| Cloudscape-First | `.claude/rules/frontend/cloudscape.md` |

## Terminology Standards

详细术语规范参见 `specs/001-ai-training-platform/spec.md`

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |

**训练任务状态**: `submitted` → `running` → `completed` / `failed` / `paused` / `preempted`

## Key Documentation

| 文档 | 位置 |
|------|------|
| 功能规范 | `specs/001-ai-training-platform/spec.md` |
| 实施计划 | `specs/001-ai-training-platform/plan.md` |
| 数据模型 | `specs/001-ai-training-platform/data-model.md` |
| 后端开发 | `backend/CLAUDE.md` |
| 前端开发 | `frontend/CLAUDE.md` |
| CDK 部署 | `infrastructure/cdk/CLAUDE.md` |

## Spec-Kit 工作流

```
constitution → specify → [clarify] → plan → [checklist] → tasks → implement
```

**目录结构**:
```
.specify/memory/constitution.md    # 项目宪法
specs/{feature}/
├── spec.md          # 功能规范 (WHAT/WHY)
├── plan.md          # 实施计划 (HOW)
├── tasks.md         # 任务清单 (DO)
└── data-model.md    # 数据模型
```

运行 `/speckit.analyze` 检查一致性。
