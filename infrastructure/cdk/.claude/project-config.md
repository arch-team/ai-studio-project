# 项目配置 - AI Training Platform Infrastructure

> **职责**: 项目特定的业务配置信息。通用规范放 `rules/`，项目特定信息放此处。

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-training-platform-cdk |
| **项目描述** | 基于 SageMaker HyperPod 的企业级训练平台基础设施 |
| **架构模式** | CDK Stack 6 层分层 (L1 → L6) |
| **命名前缀** | `ai-platform` |
| **Stack 命名** | `AiPlatform{Resource}Stack-{env}` |
| **资源命名** | `ai-platform-{env}-{resource}` (kebab-case) |

---

## Construct 列表

> **位置约定**: 自定义 Construct 放在 `cdk_constructs/` 下。

| Construct | 职责 | 组合资源 |
|-----------|------|---------|
| `GpuNodeGroupConstruct` | GPU 节点组 | EKS Nodegroup, Launch Template |
| `PlatformKmsKey` | 平台级 KMS 加密密钥 | KMS Key, Alias |
| `StandardTaggingAspect` | 标准化标签 | Tags Aspect |

---

## 相关规范

| 需求 | 参见 |
|------|------|
| Stack 分层和依赖 | [architecture.md](rules/architecture.md) |
| 环境配置代码架构 | [configuration.md](rules/configuration.md) |
| 命名和代码风格 | [code-style.md](rules/code-style.md) |
| 成本标签 | [cost-optimization.md](rules/cost-optimization.md) |
| 技术栈版本 | [tech-stack.md](rules/tech-stack.md) |
| PR Review 检查清单 | [checklist.md](rules/checklist.md) |
