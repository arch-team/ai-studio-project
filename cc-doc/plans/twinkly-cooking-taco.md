# 代码规范整合方案

## 目标

将项目中分散的代码规范内容按项目类型整合为**三个独立的 Claude Code Rules 文件**。

**设计决策**:
- ✅ 后端、前端、CDK 作为独立项目，各自维护独立的编码规范
- ✅ 行长度保持现状：后端 120 字符，CDK 88 字符
- ✅ 使用 Claude Code 官方 `.claude/rules/` 目录结构

---

## 现状分析

### 当前文件分布（16+ 个文件）

```
📁 代码规范相关文件
├── /CLAUDE.md                              # 全局入口 (语言规范、TDD、项目概述)
├── /backend/
│   ├── CLAUDE.md                           # 后端技术栈、行长度(120)、异常处理
│   ├── docs/ARCHITECTURE.md                # DDD 架构、黄金法则 R1-R4 (800+行)
│   ├── tests/CLAUDE.md                     # 测试命名、分层比例、Mock 策略
│   └── pyproject.toml                      # Black/Ruff/MyPy 配置
├── /frontend/
│   ├── CLAUDE.md                           # Feature-Sliced Design
│   └── DESIGN.md                           # Cloudscape-First、组件规范
├── /infrastructure/cdk/
│   ├── CLAUDE.md                           # Stack 分层、安全底线
│   ├── pyproject.toml                      # CDK 特有配置 (88字符)
│   └── .claude/rules/                      # 8 个按需加载规则
│       ├── 00-index.md
│       ├── 01-architecture.md
│       ├── 02-stack-design.md
│       ├── 03-construct-design.md
│       ├── 04-configuration.md
│       ├── 05-code-style.md
│       ├── 06-testing.md
│       ├── 07-security.md
│       └── 08-hyperpod.md
└── /specs/001-ai-training-platform/
    └── spec.md                             # 术语标准
```

### 问题分析

| 问题类型 | 具体问题 |
|---------|---------|
| **重复定义** | 行长度、TDD 流程在多处定义 |
| **分散管理** | 后端规范分布在 4 个文件中 |
| **格式不一致** | CDK 使用 rules/ 目录，后端/前端使用 CLAUDE.md |
| **维护困难** | 修改规范需要更新多个文件 |

---

## 推荐方案：三项目独立规范

### 整合后的文件结构

```
📁 项目根目录
├── CLAUDE.md                           # 简化为：语言规范 + 项目概述 + 索引
├── backend/
│   ├── .claude/
│   │   └── rules/
│   │       └── code-standards.md       # 🆕 后端统一规范
│   ├── CLAUDE.md                       # 简化为：指向 rules + 模块职责
│   └── docs/ARCHITECTURE.md            # 保留：详细架构参考
├── frontend/
│   ├── .claude/
│   │   └── rules/
│   │       └── code-standards.md       # 🆕 前端统一规范
│   └── CLAUDE.md                       # 简化为：指向 rules
└── infrastructure/cdk/
    └── .claude/
        └── rules/
            └── code-standards.md       # 🆕 CDK 统一规范 (整合 8 个文件)
```

### 统一规范文件内容结构

```markdown
# AI Training Platform - 代码规范

## 1. 语言规范 (Language Standards)
- 中文对话要求
- 代码注释语言
- 例外情况

## 2. 代码风格 (Code Style)
### 2.1 Python (后端 + CDK)
- 行长度: 后端 120 / CDK 88
- 命名规范
- 类型注解要求
- Docstring 规范

### 2.2 TypeScript (前端)
- 组件命名
- 类型定义要求

## 3. 架构规范 (Architecture)
### 3.1 后端 DDD 架构
- 四层分离
- 黄金法则 R1-R4
- 依赖注入

### 3.2 前端 Feature-Sliced Design
- 模块隔离
- 状态分层

### 3.3 CDK Stack 分层
- 依赖方向
- 资源传递

## 4. 测试规范 (Testing)
### 4.1 TDD 工作流
- 红绿重构循环

### 4.2 测试分层比例
- 后端: Unit 70% / Integration 20% / E2E 10%

### 4.3 命名规范
- test_entity_*, test_svc_*, test_api_*

## 5. 异常处理 (Exception Handling)
- @problem 装饰器
- 域异常层次

## 6. AWS 异步操作 (AWS Async)
- aioboto3 强制规范
- 禁止 run_in_executor

## 7. 术语标准 (Terminology)
- 核心实体命名表
- 状态转换定义

## 8. 禁止事项 (Anti-Patterns)
- 前端禁止项 (内联样式、自定义CSS)
- 后端禁止项 (同步boto3)
- CDK 禁止项 (Fn.import_value)
```

---

## 实施步骤

### Phase 1: 创建统一规范文件

1. 创建 `/.claude/rules/code-standards.md`
2. 从各文件提取代码规范内容
3. 整合去重，保持一致性

### Phase 2: 简化现有 CLAUDE.md

1. `/CLAUDE.md` → 保留项目概述，添加指向 `/.claude/rules/code-standards.md`
2. `/backend/CLAUDE.md` → 保留后端特定内容（如模块职责矩阵）
3. `/frontend/CLAUDE.md` → 保留前端特定内容
4. `/infrastructure/cdk/CLAUDE.md` → 保留 CDK 特定内容

### Phase 3: 清理冗余

1. 移除各 CLAUDE.md 中重复的通用规范
2. 保留详细参考文档（如 ARCHITECTURE.md）但标记为"详细参考"

---

## 整合后的文件预览

### `/.claude/rules/code-standards.md` (目标文件)

```markdown
---
description: AI Training Platform 代码规范 - 适用于后端、前端、CDK
alwaysApply: true
---

# AI Training Platform - 代码规范

> 本文件整合了项目所有代码规范，作为 Claude Code 的统一参考。

## 1. 语言规范

### 1.1 强制要求
- **所有对话**: 必须使用中文
- **代码注释**: 使用中文
- **文档内容**: 使用中文
- **Git 提交信息**: 使用中文

### 1.2 保持英文的例外
- 代码变量名、函数名、类名
- 技术术语 (API, SDK, TDD, DDD)
- 第三方库/框架名称
- 错误信息和日志 (可选)

---

## 2. 代码风格

### 2.1 Python 后端

| 项目 | 规范 |
|------|------|
| **行长度** | 120 字符 (black + ruff) |
| **缩进** | 4 空格 |
| **类命名** | PascalCase (`TrainingJob`) |
| **方法/变量** | snake_case (`create_job`) |
| **私有成员** | _snake_case (`_internal_method`) |
| **常量** | UPPER_SNAKE (`MAX_RETRIES`) |
| **类型注解** | 强制 (mypy strict) |

**Docstring 规范**:
```python
# ✅ 正确: 单行中文描述
def create_job(self, request: CreateJobRequest) -> TrainingJob:
    """创建训练任务。"""

# ❌ 错误: 冗余的 Args/Returns
def create_job(self, request: CreateJobRequest) -> TrainingJob:
    """创建训练任务。

    Args:
        request: 创建请求
    Returns:
        TrainingJob: 创建的任务
    """
```

### 2.2 Python CDK

| 项目 | 规范 |
|------|------|
| **行长度** | 88 字符 (与后端不同) |
| **Construct ID** | PascalCase (`"MainVpc"`) |
| **资源名称** | kebab-case (`"ai-platform-dev-vpc"`) |
| **私有方法** | _snake_case (`_create_vpc`) |

### 2.3 TypeScript 前端

| 项目 | 规范 |
|------|------|
| **组件命名** | PascalCase (`TrainingJobList`) |
| **方法/变量** | camelCase (`createJob`) |
| **类型定义** | 强制 (strict mode) |
| **缩进** | 2 空格 |

---

## 3. 架构规范

### 3.1 后端 DDD 四层架构

```
依赖方向: API → Application → Domain ← Infrastructure
```

**黄金法则**:
| 规则 | 描述 |
|------|------|
| **R1** | Domain 层绝对不能导入其他模块代码 |
| **R2** | Application 层只依赖接口，不依赖实现 |
| **R3** | 模块间通信必须通过事件总线或共享接口 |
| **R4** | auth 模块认证依赖是唯一例外 |

**ORM 外键例外**: 允许在 `*_model.py` 导入其他模块 ORM 模型定义外键关系

### 3.2 前端 Feature-Sliced Design

**核心约束**:
- **Cloudscape-First**: 禁止自定义 CSS、内联样式、原生 HTML
- **模块隔离**: 通过 index.ts 导入，禁止导入内部文件
- **状态分层**: TanStack Query (服务器状态) + Zustand (客户端状态)

### 3.3 CDK Stack 分层

```
Layer 1: NetworkStack, IamStack (并行)
Layer 2: DatabaseStack, StorageStack (并行)
Layer 3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
Layer 4: FsxLustreStack
Layer 5: AlbStack
```

**强制规则**:
- 上层只依赖下层，禁止反向依赖
- 通过构造函数参数传递资源 (依赖注入)
- 禁止使用 `Fn.import_value()` 跨 Stack 引用

---

## 4. 测试规范

### 4.1 TDD 工作流

```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试诚信原则**: 切勿为让测试通过而伪造结果

### 4.2 测试分层比例

| 模块 | Unit | Integration | E2E |
|------|------|-------------|-----|
| 后端 | 70% | 20% | 10% |
| 前端 | 60% | 25% | 15% |
| CDK | 70% | 30% | - |

### 4.3 后端测试命名

| 前缀 | 用途 |
|------|------|
| `test_entity_` | 领域实体测试 |
| `test_vo_` | 值对象测试 |
| `test_svc_` | 应用服务测试 |
| `test_api_` | API 端点测试 |
| `test_repo_` | 仓库实现测试 |

### 4.4 Mock 策略

- **单元测试**: Mock Repository 接口
- **真实对象**: Entity, Value Object, Domain Event
- **集成测试**: 使用真实数据库 (内存 SQLite 或测试容器)

---

## 5. 异常处理

### 5.1 后端异常框架

使用 `@problem` 装饰器 + `@dataclass` 简化异常定义:

```python
from src.shared.domain.problem import problem

@problem(
    type_="training/job-not-found",
    title="训练任务不存在",
    status=404,
)
@dataclass
class TrainingJobNotFoundError(Exception):
    job_id: str

    @property
    def detail(self) -> str:
        return f"训练任务 {self.job_id} 不存在"
```

### 5.2 域异常层次

```
DomainError (基类)
├── EntityNotFoundError
├── ValidationError
├── BusinessRuleViolationError
└── 模块特定异常
```

---

## 6. AWS 异步操作

### 6.1 强制规范

**必须使用**: `aioboto3` 原生异步客户端

```python
# ✅ 正确: aioboto3 原生异步
async def list_training_jobs(self) -> list[dict]:
    async with self._session.client("sagemaker") as client:
        response = await client.list_training_jobs()
        return response["TrainingJobSummaries"]

# ❌ 禁止: 自己封装 run_in_executor
def list_training_jobs_sync(self):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, self._sync_client.list_training_jobs)
```

### 6.2 后台任务

使用 **K8s CronJob + Watch API**，而非 Celery

---

## 7. 术语标准

### 7.1 核心实体命名

| 中文术语 | Python 类 | 数据库表 | API 路径 |
|---------|----------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 模型 | `Model` | `models` | `/models` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| 开发空间 | `Space` | `development_spaces` | `/spaces` |
| 审计日志 | `AuditLog` | `audit_logs` | `/audit-logs` |
| 用户 | `User` | `users` | `/users` |

### 7.2 训练任务状态

```
submitted → running → completed
                   ↘ failed
                   ↘ paused
                   ↘ preempted
```

---

## 8. 禁止事项

### 8.1 前端禁止项

- ❌ 内联样式 (`style={{...}}`)
- ❌ 自定义 CSS 文件
- ❌ 原生 HTML 元素 (`<div>`, `<button>`)
- ❌ 硬编码颜色值
- ❌ 自定义图表库 (使用 Cloudscape Charts)

### 8.2 后端禁止项

- ❌ 同步 boto3 客户端
- ❌ 自行封装 `run_in_executor`
- ❌ Domain 层导入其他模块
- ❌ Docstring 中的 Args/Returns 冗余描述
- ❌ Celery 后台任务

### 8.3 CDK 禁止项

- ❌ `Fn.import_value()` 跨 Stack 引用
- ❌ 硬编码资源 ARN
- ❌ 裸 except 语句
- ❌ Any 类型
- ❌ 全局变量

---

## 9. 详细参考文档

以下文档提供更详细的实现指导:

| 文档 | 路径 | 内容 |
|------|------|------|
| 后端架构详解 | `backend/docs/ARCHITECTURE.md` | 依赖注入、事件系统、完整示例 |
| 前端设计规范 | `frontend/DESIGN.md` | 组件选择指南、操作反馈时效 |
| CDK 安全规范 | `infrastructure/cdk/.claude/rules/07-security.md` | IAM、KMS、网络安全 |
| 功能规范 | `specs/001-ai-training-platform/spec.md` | 完整功能需求 |
```

---

## 简化后的 CLAUDE.md 示例

### 根目录 `/CLAUDE.md` (简化版)

```markdown
# CLAUDE.md

## 代码规范

**统一规范文件**: `.claude/rules/code-standards.md`

所有代码风格、架构规范、测试规范、异常处理、术语标准等内容已整合至上述文件。

## 项目概述

AI Training Platform - 基于 AWS SageMaker HyperPod 的企业级 AI 训练平台。

## 模块指南

- **后端开发**: `backend/CLAUDE.md`
- **前端开发**: `frontend/CLAUDE.md`
- **CDK 部署**: `infrastructure/cdk/CLAUDE.md`

## Spec-Kit 文件体系

详见 `specs/001-ai-training-platform/`
```

---

## 预期收益

| 收益 | 说明 |
|------|------|
| **单一真相源** | 所有代码规范在一个文件中 |
| **减少重复** | 消除 16+ 文件间的内容重叠 |
| **易于维护** | 修改规范只需更新一处 |
| **Claude Code 原生支持** | 使用 `.claude/rules/` 官方目录 |
| **按需加载** | `alwaysApply: true` 确保全局生效 |

---

## 待确认事项

1. **是否保留 CDK 的 8 个规则文件**?
   - 选项 A: 整合到统一文件
   - 选项 B: 保留按需加载机制

2. **详细文档 (ARCHITECTURE.md) 如何处理**?
   - 选项 A: 保留作为详细参考
   - 选项 B: 精简后整合

3. **pyproject.toml 配置差异 (120 vs 88 字符)**?
   - 现状: 后端 120 字符，CDK 88 字符
   - 是否统一?
