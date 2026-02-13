# Claude Code 工具生态指导手册

> **定位**: 场景驱动的工具选择与组合指南，聚焦"什么场景用什么工具"。
>
> **适用**: AI Training Platform 项目日常开发。

---

## §0 速查卡片

### 工具选择决策树

```
你要做什么？
│
├─ 写代码 / 改代码
│   ├─ 后端 Python (DDD 模块)?
│   │   └─ serena (符号导航) + context7 (FastAPI/SQLAlchemy 文档) + python-development plugin
│   ├─ 前端 React (Cloudscape)?
│   │   └─ context7 (Cloudscape 文档) + serena (组件模式查找)
│   ├─ CDK 基础设施?
│   │   └─ aws-cdk MCP + aws-knowledge MCP + sequential-thinking
│   └─ HyperPod 集成?
│       └─ sagemaker-hyperpod-cli + aws-knowledge + hyperpod-scheduling skill
│
├─ 调试 / 排查问题
│   ├─ 简单 Bug → error-debugging plugin
│   ├─ 复杂多层问题 → sequential-thinking + serena (记忆) + error-debugging plugin
│   └─ 性能问题 → sequential-thinking + --think-hard flag
│
├─ 技术调研 / 选型
│   ├─ 开源库文档 → context7 (resolve-library-id + query-docs)
│   ├─ AWS 服务文档 → aws-knowledge (search_documentation)
│   ├─ HyperPod 专属 → sagemaker-hyperpod-cli (fetch_sagemaker_docs)
│   └─ 广泛调研 → tavily + sequential-thinking + /sc:research
│
├─ 架构决策 / 系统设计
│   └─ sequential-thinking + --think-hard / --ultrathink
│
└─ 项目管理 / 规范
    └─ Spec-Kit 命令 (/speckit.specify → /speckit.plan → /speckit.tasks)
```

### 开发场景 → 推荐工具映射表

| 场景 | 主力工具 | 辅助工具 | 触发示例 |
|------|---------|---------|---------|
| 后端 DDD 模块开发 | serena + context7 | python-development plugin | 新增 training module endpoint |
| 前端 Cloudscape 页面 | context7 | serena | 新增数据集管理页面 |
| CDK Stack 开发 | aws-cdk MCP + aws-knowledge | sequential-thinking | 新增 Stack 或修改资源 |
| HyperPod 集成 | sagemaker-hyperpod-cli + aws-knowledge | hyperpod-scheduling skill | 训练任务提交/调度 |
| 调试与根因分析 | error-debugging plugin + sequential-thinking | serena (记忆) | 生产问题排查 |
| 深度研究 | tavily + sequential-thinking | /sc:research | 技术选型、SDK 调研 |
| 跨模块重构 | serena (符号重命名) | code-simplifier plugin | 大规模代码重构 |
| 规范驱动开发 | Spec-Kit 命令 | sequential-thinking | 新功能从规范到实现 |

---

## §1 工具生态现状盘点

### MCP Servers (8 个)

| MCP Server | 用途 | 核心工具 |
|------------|------|---------|
| **aws-cdk** | CDK 开发辅助 | `CDKGeneralGuidance`, `ExplainCDKNagRule`, `GetAwsSolutionsConstructPattern` |
| **aws-knowledge** | AWS 官方文档查询 | `search_documentation`, `recommend`, `read_documentation` |
| **sagemaker-hyperpod-cli** | HyperPod/SageMaker 文档 | `fetch_sagemaker_docs`, `search_sagemaker_docs`, `search_sagemaker_code` |
| **serena** | 语义代码导航与记忆 | `find_symbol`, `get_symbols_overview`, `write_memory`, `read_memory` |
| **context7** | 开源库官方文档 | `resolve-library-id`, `query-docs` |
| **sequential-thinking** | 复杂推理引擎 | `sequentialthinking` |
| **tavily** | Web 搜索与研究 | `tavily_search`, `tavily_extract`, `tavily_research` |
| **pencil** | .pen 文件设计编辑 | `batch_design`, `batch_get`, `get_screenshot` |

### 已启用 Plugins (9 个)

**全局启用** (`~/.claude/settings.json`):

| Plugin | 用途 |
|--------|------|
| **python-development** | Python 开发模式 (FastAPI, async, 测试) |
| **error-debugging** | 错误调试与根因分析 |
| **code-simplifier** | 代码简化与重构 |
| **aws-cdk** | AWS CDK 开发辅助 |
| **claude-md-management** | CLAUDE.md 文件管理与优化 |

**项目级启用** (`.claude/settings.local.json`):

| Plugin | 用途 |
|--------|------|
| **everything-claude-code** | 通用增强 (TDD、代码审查、安全审查、持续学习等技能集) |
| **superpowers** | 工作流增强 (计划、调试、代码审查、并行代理等技能集) |
| **ralph-loop** | 迭代执行循环 (自动重复改进) |
| **frontend-design** | 前端设计辅助 (⚠️ 本项目禁止生成非 Cloudscape UI) |

### 全局框架: SuperClaude

| 类别 | 数量 | 示例 |
|------|------|------|
| 行为模式 | 7 | Brainstorming, DeepResearch, Introspection, Orchestration, Task Management, Token Efficiency, Business Panel |
| Skills/命令 | 26+ | /sc:implement, /sc:analyze, /sc:test, /sc:research, /sc:task 等 |
| Agent | 17 | backend-architect, frontend-architect, system-architect, security-engineer 等 |

### 项目级资产

| 类别 | 数量 | 内容 |
|------|------|------|
| Skills | 2 | `hyperpod-scheduling` (Kueue 调度踩坑), `decorator-exception` (@problem 装饰器) |
| Spec-Kit 命令 | 9 | /speckit.specify, /speckit.plan, /speckit.tasks, /speckit.implement 等 |
| Evals | 7 | HyperPod 训练提交/抢占, 前端页面组件, API 端点, S3/FSx 集成 |

---

## §2 场景化工具推荐矩阵

### 场景 1: 后端 DDD 模块开发

**典型任务**: 新增业务模块 endpoint、实现 domain entity、编写 application service

**推荐工具链** (按执行顺序):

1. **serena** `get_symbols_overview` → 了解目标模块现有结构
2. **serena** `find_symbol` → 定位需要修改或参考的符号
3. **context7** `resolve-library-id` + `query-docs` → 查 FastAPI/SQLAlchemy/Pydantic 官方用法
4. **python-development plugin** → 自动激活 Python 开发最佳实践

**命令/flag 示例**:
```bash
# 查 FastAPI 路由装饰器用法
# → context7: resolve-library-id "fastapi" → query-docs "router decorator async endpoint"

# 在 9 个后端模块中快速定位符号
# → serena: find_symbol name_path="TrainingJob" include_body=False

# 复杂业务逻辑设计时启用深度思考
# → 使用 --think-hard flag 触发 sequential-thinking
```

**反模式提醒**:
- ❌ 用 aws-knowledge 查 FastAPI 文档 → ✅ 用 context7
- ❌ 用 Grep 遍历 9 个模块找符号 → ✅ 用 serena `find_symbol`
- ❌ 跳过 serena 直接读整个文件 → ✅ 先用 `get_symbols_overview` 了解结构

---

### 场景 2: 前端 Cloudscape 页面开发

**典型任务**: 新增功能页面、实现 Cloudscape 组件、配置 TanStack Query

**推荐工具链**:

1. **context7** → 查 Cloudscape/React/TanStack Query 官方文档
2. **serena** `find_symbol` → 参考现有 feature 模块的组件模式
3. 编辑器内置工具 → 直接编写 TypeScript 代码

**命令/flag 示例**:
```bash
# 查 Cloudscape Table 组件 Props
# → context7: resolve-library-id "@cloudscape-design/components"
# → query-docs "Table component props columnDefinitions"

# 查看现有 feature 模块结构作为模板
# → serena: get_symbols_overview relative_path="frontend/src/features/training"
```

**反模式提醒**:
- ❌ 使用 Magic MCP 生成 UI → ✅ 项目强制使用 Cloudscape，禁止 Magic MCP
- ❌ 用 tavily 搜索 Cloudscape 用法 → ✅ 用 context7 查官方文档
- ❌ 自定义 CSS/内联样式 → ✅ 使用 Cloudscape 组件系统

---

### 场景 3: CDK Stack 开发

**典型任务**: 新增 Stack、修改资源配置、处理 CDK Nag 检查

**推荐工具链**:

1. **aws-cdk MCP** `CDKGeneralGuidance` → Stack 设计前咨询最佳实践
2. **aws-knowledge** `search_documentation` → 查 AWS 服务配置参数
3. **aws-cdk MCP** `GetAwsSolutionsConstructPattern` → 查找 Solutions Construct
4. **sequential-thinking** → 复杂 Stack 依赖关系分析
5. **aws-cdk MCP** `ExplainCDKNagRule` → Nag 检查失败时查规则

**命令/flag 示例**:
```bash
# Stack 设计前获取 CDK 最佳实践
# → aws-cdk: CDKGeneralGuidance

# 查 EKS 相关 CDK Construct 配置
# → aws-knowledge: search_documentation "EKS cluster CDK construct"

# Nag 检查失败时解释规则
# → aws-cdk: ExplainCDKNagRule rule_id="AwsSolutions-IAM4"

# 查找 Solutions Construct
# → aws-cdk: GetAwsSolutionsConstructPattern pattern="EKS cluster"
```

**反模式提醒**:
- ❌ 用 context7 查 AWS CDK → ✅ 用 aws-cdk MCP + aws-knowledge
- ❌ 手动猜测 CDK Nag 规则含义 → ✅ 用 `ExplainCDKNagRule`
- ❌ 跳过 `CDKGeneralGuidance` 直接写 Stack → ✅ 先咨询最佳实践

---

### 场景 4: HyperPod 集成

**典型任务**: 训练任务提交、Kueue 调度配置、抢占处理

**推荐工具链**:

1. **sagemaker-hyperpod-cli** `fetch_sagemaker_docs` → HyperPod 专属文档
2. **aws-knowledge** `search_documentation` → SageMaker API 参数
3. **hyperpod-scheduling skill** → Kueue 调度与抢占的踩坑记录和诊断清单
4. **sequential-thinking** → 复杂调度逻辑分析

**命令/flag 示例**:
```bash
# 查 HyperPod 训练任务提交 API
# → sagemaker-hyperpod-cli: fetch_sagemaker_docs "HyperPod training job submit"

# 查 Kueue 调度配置
# → sagemaker-hyperpod-cli: search_sagemaker_docs "Kueue workload priority"

# 使用项目级 Skill 获取踩坑记录
# → 调用 hyperpod-scheduling skill
```

**反模式提醒**:
- ❌ 用 context7 查 SageMaker → ✅ 用 sagemaker-hyperpod-cli + aws-knowledge
- ❌ 忽略 hyperpod-scheduling skill 的踩坑记录 → ✅ 先查阅已知陷阱

---

### 场景 5: 调试与根因分析

**典型任务**: 定位 Bug、排查生产问题、分析错误堆栈

**推荐工具链**:

1. **error-debugging plugin** → 自动激活调试模式
2. **sequential-thinking** → 结构化推理，假设验证
3. **serena** `write_memory` / `read_memory` → 持久化调试上下文，跨会话续查

**命令/flag 示例**:
```bash
# 复杂问题启用结构化推理
# → 使用 --think-hard flag
# → sequential-thinking: 分解问题 → 假设 → 验证 → 结论

# 跨会话保存调试进度
# → serena: write_memory("debug_auth_issue", "排查到 JWT decode 异常，疑似 secret 不一致")
# → 下次会话: read_memory("debug_auth_issue") 恢复上下文
```

**反模式提醒**:
- ❌ 直接猜测原因修改代码 → ✅ 先用 sequential-thinking 系统分析
- ❌ 每次新会话从头排查 → ✅ 用 serena memory 持久化调查进度

---

### 场景 6: 深度技术研究

**典型任务**: 技术选型、SDK 可行性调研、竞品分析

**推荐工具链**:

1. **tavily** `tavily_search` → 广泛搜索最新信息
2. **sequential-thinking** → 分析搜索结果，形成结论
3. **context7** → 补充查询官方文档细节
4. **/sc:research** → 激活 SuperClaude 深度研究模式

**命令/flag 示例**:
```bash
# 启动深度研究模式
# → /sc:research "比较 Kueue 和 Volcano 在 GPU 调度场景的优劣"

# 使用 --ultrathink 进行最深度分析
# → 适用于关键技术决策
```

**反模式提醒**:
- ❌ 只用 context7 做调研 → ✅ context7 适合查已知库文档，广泛调研用 tavily
- ❌ 手动逐个搜索 → ✅ 用 /sc:research 激活系统化研究流程

---

## §3 MCP Server 实战指南

### 3.1 aws-cdk — CDK 开发必备

**核心工具**:

| 工具 | 用途 | 适用时机 |
|------|------|---------|
| `CDKGeneralGuidance` | CDK 设计最佳实践 | 新 Stack 设计前、架构决策时 |
| `ExplainCDKNagRule` | 解释 Nag 检查规则 | `cdk synth` 后 Nag 检查失败 |
| `CheckCDKNagSuppressions` | 检查 Nag 抑制是否合理 | PR Review 安全审查 |
| `GetAwsSolutionsConstructPattern` | 查找 AWS Solutions Construct | 需要复合 Construct 模式时 |
| `SearchGenAICDKConstructs` | 搜索 GenAI CDK Constructs | AI/ML 相关基础设施 |

**适用场景**:
- ✅ Stack 分层设计 (L1-L6 架构)
- ✅ CDK Nag 规则解读与修复
- ✅ 查找 AWS Solutions Construct 最佳实践
- ✅ GenAI 相关 CDK Construct 搜索

**不适用场景**:
- ❌ 查具体 AWS 服务 API 参数 → 用 aws-knowledge
- ❌ 查开源库文档 → 用 context7
- ❌ 通用 Python 开发问题 → 用 python-development plugin

---

### 3.2 aws-knowledge + sagemaker-hyperpod-cli — AWS 文档查询

**aws-knowledge 核心工具**:

| 工具 | 用途 | 示例查询 |
|------|------|---------|
| `search_documentation` | 搜索 AWS 文档 | "EKS node group autoscaling" |
| `recommend` | 获取 AWS 服务选型建议 | "best storage for ML training data" |
| `read_documentation` | 读取特定文档 | 指定文档 URL |
| `get_regional_availability` | 查询服务区域可用性 | "p5.48xlarge us-east-1" |

**sagemaker-hyperpod-cli 核心工具**:

| 工具 | 用途 | 示例查询 |
|------|------|---------|
| `fetch_sagemaker_docs` | HyperPod 专属文档 | "HyperPod cluster lifecycle" |
| `search_sagemaker_docs` | 搜索 SageMaker 文档 | "training job configuration" |
| `search_sagemaker_code` | 搜索 SageMaker 代码示例 | "distributed training PyTorch" |

**aws-knowledge vs context7 区分规则**:

| 查什么 | 用什么 |
|--------|--------|
| AWS 服务 (S3, EKS, SageMaker, IAM...) | aws-knowledge |
| HyperPod 专属功能 | sagemaker-hyperpod-cli |
| 开源库 (FastAPI, React, SQLAlchemy...) | context7 |
| AWS CDK Construct 模式 | aws-cdk MCP |

---

### 3.3 serena — 代码导航与记忆

**核心工具分两类**:

**代码导航**:

| 工具 | 用途 | 使用模式 |
|------|------|---------|
| `get_symbols_overview` | 文件/目录符号概览 | 初次了解模块结构 |
| `find_symbol` | 按名称搜索符号 | 定位特定类/函数/方法 |
| `find_referencing_symbols` | 查找引用关系 | 重构前影响分析 |
| `replace_symbol_body` | 替换符号定义 | 精确修改方法体 |
| `insert_after_symbol` / `insert_before_symbol` | 在符号前后插入 | 添加新方法/导入 |

**记忆管理**:

| 工具 | 用途 | 使用模式 |
|------|------|---------|
| `write_memory` | 写入持久记忆 | 保存调试进度、架构决策 |
| `read_memory` | 读取记忆 | 恢复上下文 |
| `list_memories` | 列出所有记忆 | 会话开始时检查 |
| `delete_memory` | 删除记忆 | 清理已完成的临时记忆 |

**后端 DDD 架构中的高效导航模式**:

```
# 目标: 了解 training 模块的 domain 层
1. get_symbols_overview relative_path="backend/src/modules/training/domain"
   → 获取 entities, value_objects, repositories 概览

# 目标: 找到 TrainingJob 实体的状态转换方法
2. find_symbol name_path="TrainingJob" depth=1 include_body=False
   → 列出所有方法名

3. find_symbol name_path="TrainingJob/start" include_body=True
   → 读取具体实现

# 目标: 重构前检查哪些地方引用了这个方法
4. find_referencing_symbols symbol_name="TrainingJob.start"
   → 获取所有调用点
```

---

### 3.4 context7 — 开源库文档查询

**使用流程** (两步):

```
Step 1: resolve-library-id "fastapi"
  → 获取 library_id (如 "/tiangolo/fastapi")

Step 2: query-docs library_id="/tiangolo/fastapi" topic="dependency injection Depends"
  → 获取版本特定的官方文档
```

**本项目常用查询**:

| 库 | 典型查询主题 |
|----|-------------|
| FastAPI | 依赖注入、路由装饰器、中间件、WebSocket |
| SQLAlchemy | async session、relationship、query builder |
| Pydantic | model_validator、field_validator、ConfigDict |
| React | hooks、context、suspense、error boundary |
| TanStack Query | useQuery、useMutation、queryClient |
| Cloudscape | Table、Form、Modal、Flashbar、SplitPanel |
| Zustand | create、persist、selector |

**优于 WebSearch 的场景**:
- ✅ 需要版本特定 API 签名 (如 Pydantic v2 vs v1)
- ✅ 需要官方推荐模式 (非社区经验)
- ✅ 需要准确参数类型定义

---

### 3.5 sequential-thinking — 复杂推理引擎

**适用场景**:

| 场景 | 思考深度 | flag |
|------|---------|------|
| 多组件调试 | 标准分析 (~4K tokens) | `--think` |
| 架构决策 | 深度分析 (~10K tokens) | `--think-hard` |
| 系统重设计 | 最大深度 (~32K tokens) | `--ultrathink` |

**使用模式**:
- 架构决策: 分解选项 → 评估利弊 → 推荐方案
- 多步调试: 收集证据 → 假设 → 验证 → 排除 → 结论
- 系统设计: 需求分析 → 约束识别 → 方案设计 → 风险评估

**配合其他工具**:
- sequential-thinking + serena → 带上下文的深度代码分析
- sequential-thinking + aws-knowledge → 架构选型决策
- sequential-thinking + tavily → 技术调研综合分析

---

## §4 Plugin 启用建议

基于项目当前需求和发展阶段的插件优先级评估:

### 当前已启用 (9 个)

**全局** (`settings.json`):

| Plugin | 理由 |
|--------|------|
| python-development | 后端核心开发工具，FastAPI/async/pytest 模式 |
| error-debugging | 调试必备，自动激活错误分析模式 |
| code-simplifier | 重构助手，代码简化与清理 |
| aws-cdk | CDK 基础设施开发辅助 |
| claude-md-management | CLAUDE.md 文件审计与优化 |

**项目级** (`settings.local.json`):

| Plugin | 理由 |
|--------|------|
| everything-claude-code | 通用技能集 (TDD、代码审查、安全审查、持续学习) |
| superpowers | 工作流技能集 (计划编写、调试、并行代理、代码审查) |
| ralph-loop | 迭代改进循环 (自动重复执行直到满意) |
| frontend-design | 前端设计辅助 (⚠️ 本项目 Cloudscape-first，谨慎使用) |

### 推荐启用

| 优先级 | Plugin | 理由 |
|--------|--------|------|
| 🔴 高 | `tdd-workflows` | 项目 TDD 强制要求，可编排 Red→Green→Refactor 流程 |
| 🔴 高 | `kubernetes-operations` | HyperPod 基于 EKS，K8s manifest/Helm 管理频繁 |
| 🟡 中 | `backend-development` | 后端 DDD 架构编排，与 python-development 互补 |
| 🟡 中 | `cicd-automation` | GitHub Actions 工作流管理（部署阶段需要） |

### 按需启用

| 优先级 | Plugin | 理由 |
|--------|--------|------|
| 🟢 低 | `machine-learning-ops` | ML 实验管理（MLflow 集成阶段启用） |
| 🟢 低 | `cloud-infrastructure` | 多云场景（当前仅 AWS，暂不需要） |

### 不推荐启用

| Plugin | 理由 |
|--------|------|
| `api-scaffolding` | 与 Spec-Kit 工作流 (/speckit.specify → /speckit.plan) 重叠 |
| `business-analytics` | 与 AI 训练平台业务领域不匹配 |
| `full-stack-orchestration` | SuperClaude /sc:task 已覆盖任务编排 |
| `unit-testing` | tdd-workflows 已包含更完整的测试工作流 |
| `data-engineering` | 非数据管道项目 |

---

## §5 Agent Team 协作配方

### 配方 1: 新功能全栈开发

**场景**: 新增"模型注册"模块，涉及后端 DDD + 前端 Cloudscape + API 契约

| 角色 | Agent | 职责 |
|------|-------|------|
| Leader | system-architect | 整体架构设计与协调 |
| 成员 | backend-architect | DDD 建模 (domain/application/infrastructure/api 四层) |
| 成员 | frontend-architect | Cloudscape 页面 (Feature-Sliced Design) |
| 成员 | quality-engineer | 测试策略与覆盖率保障 |

**工作流**:
```
1. system-architect: 读取 spec.md → 设计模块架构
2. parallel:
   - backend-architect: 实现 domain → application → infrastructure → api
   - frontend-architect: 实现 types → api → hooks → components → pages
3. quality-engineer: 编写单元测试 + 集成测试
4. system-architect: 集成验证
```

**工具配置**: serena (符号导航) + context7 (文档) + python-development plugin

---

### 配方 2: CDK 基础设施变更

**场景**: 新增 Stack 或修改资源配置

| 角色 | Agent | 职责 |
|------|-------|------|
| Leader | devops-architect | Stack 设计与部署策略 |
| 成员 | security-engineer | CDK Nag 审查、IAM 最小权限 |
| 成员 | quality-engineer | Stack 单元测试 (≥90% 覆盖率) |

**工具配置**: aws-cdk MCP + aws-knowledge MCP + sequential-thinking

---

### 配方 3: 生产问题根因分析

**场景**: 复杂多层问题排查

| 角色 | Agent | 职责 |
|------|-------|------|
| Leader | root-cause-analyst | 系统化问题分解与假设验证 |
| 成员 | performance-engineer | 性能瓶颈分析 (如适用) |

**工具配置**: sequential-thinking (--think-hard) + serena (memory 持久化调查进度) + error-debugging plugin

---

### 配方 4: 跨模块重构

**场景**: 重命名核心实体、调整模块边界

| 角色 | Agent | 职责 |
|------|-------|------|
| Leader | refactoring-expert | 重构策略制定与执行 |
| 成员 | backend-architect | 架构守护，确保 DDD 规范合规 |
| 成员 | quality-engineer | 回归测试，确保无破坏性变更 |

**工具配置**: serena (find_referencing_symbols + replace_symbol_body) + code-simplifier plugin

---

### 何时不需要 Team

- 单文件 Bug 修复 → 直接执行
- 3 步以内的简单任务 → 直接执行
- 文档更新 → 直接执行
- 单个测试编写 → 直接执行

**原则**: Agent Team 有协调开销，简单任务直接做比组建团队更高效。

---

## §6 Skill 提取机会

从现有代码模式中可提取的 5 个高价值 Skill:

| Skill 名称 | 来源 | 价值 | 提取难度 |
|------------|------|------|---------|
| `cdk-stack-scaffold` | `infrastructure/cdk/stacks/` | 新 Stack 快速生成，自动遵从 6 层架构规范 | 中 |
| `ddd-module-scaffold` | 后端 DDD 模块模板 | 新业务模块脚手架 (domain/app/infra/api 四层 + 测试) | 中 |
| `cloudscape-page-scaffold` | `frontend/src/features/` | Feature-Sliced 页面快速生成 (types/api/hooks/components/pages) | 中 |
| `training-job-lifecycle` | 训练任务状态机 | 状态转换 (submitted→running→completed/failed/paused/preempted) 与事件处理模板 | 低 |
| `async-aws-integration` | aioboto3 集成模式 | 异步 AWS SDK 调用最佳实践 (session 管理 + 错误转换) | 低 |

**已有 Skill**:
- `hyperpod-scheduling` — Kueue 任务调度与抢占实现，含 5 个踩坑记录
- `decorator-exception` — @problem 装饰器异常定义，减少 60% 代码量

---

## §7 反模式与注意事项

### 反模式 1: Magic MCP 冲突

- ❌ **禁止**: 使用 Magic MCP 生成 UI 组件
- ✅ **正确**: 项目强制 Cloudscape Design System，所有 UI 必须使用 Cloudscape 组件
- **原因**: Magic MCP 生成的组件基于 21st.dev 模式，与 Cloudscape 体系不兼容

### 反模式 2: 工具过载

- ❌ **禁止**: 同时启用所有 Plugin
- ✅ **正确**: 按当前任务阶段选择性启用
- **原因**: 过多 Plugin 增加上下文消耗，降低响应质量

**推荐启用策略**:
```
日常后端开发: python-development + error-debugging + code-simplifier
CDK 开发: aws-cdk + (临时启用 kubernetes-operations)
全栈开发: 上述全部 + tdd-workflows
```

### 反模式 3: Agent Team 滥用

- ❌ **禁止**: 3 步以内的任务组建 Team
- ✅ **正确**: 仅复杂多步骤 (>3 步) 且涉及多领域时使用 Team
- **原因**: Agent 协调有开销，简单任务直接执行更快

### 反模式 4: MCP 误用

| 查什么 | 正确工具 | 错误工具 |
|--------|---------|---------|
| AWS 服务文档 | aws-knowledge | context7 |
| 开源库文档 | context7 | aws-knowledge |
| HyperPod 专属 | sagemaker-hyperpod-cli | context7 |
| CDK Construct 模式 | aws-cdk MCP | aws-knowledge |
| Web 搜索/时事 | tavily | context7 |
| 代码符号导航 | serena | Grep/Glob |

### 反模式 5: 忽略项目级 Skill

- ❌ **禁止**: 遇到 HyperPod 调度问题从头研究
- ✅ **正确**: 先调用 `hyperpod-scheduling` skill 查看踩坑记录
- ❌ **禁止**: 手写 Problem 异常定义模板
- ✅ **正确**: 先查阅 `decorator-exception` skill 的 @problem 装饰器模式

### 反模式 6: Spec-Kit 工作流断裂

- ❌ **禁止**: 直接写代码，跳过规范
- ✅ **正确**: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
- **原因**: 规范驱动确保设计一致性，减少返工

### 注意事项: 深度思考 flag 选择

| flag | 适用场景 | token 预算 |
|------|---------|-----------|
| `--think` | 一般复杂问题 | ~4K |
| `--think-hard` | 架构决策、系统级调试 | ~10K |
| `--ultrathink` | 关键系统重设计、遗留系统改造 | ~32K |

**原则**: 从 `--think` 开始，不够再升级。避免所有问题都用 `--ultrathink`。
