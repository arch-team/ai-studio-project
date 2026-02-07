# Claude Code 上下文管理规范迁移分析

> **目标**: 评估 ai-agents-platform/backend 的 `.claude/rules/` 规范体系是否可应用于 ai-studio-project/backend，并给出实施方案。

---

## Context

ai-agents-platform/backend（项目 A）是一个处于规划阶段的项目，已建立完整的 Claude Code 上下文管理规范体系（12 个文件，按 `.claude/rules/` 组织）。ai-studio-project/backend（项目 B）是一个成熟项目（366 个源码文件、161 个测试文件、9 个业务模块），规范集中在单文件 `CLAUDE.md`（354 行）+ `docs/ARCHITECTURE.md`（28KB）。

两个项目**架构模式完全相同**（DDD + Modular Monolith + Clean Architecture），技术栈高度重叠（Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + MySQL 8.0），因此规范迁移具有可行性。但项目 B 有多处独有实现（`@problem` 异常体系、类型前缀测试命名、HyperPod 集成），必须保留。

**核心结论**: 采用项目 A 的**组织形式**（多文件 + 速查卡片 + SSOT 分工），保留项目 B 的**实质内容**。

---

## 一、CLAUDE.md 质量评估报告

### 项目 A: ai-agents-platform/backend/.claude/

**Score: 92/100 (Grade: A)**

| 指标 | 分数 | 说明 |
|------|------|------|
| 命令/工作流 | 18/20 | 完整的 uv 命令集，预提交一键验证 |
| 架构清晰度 | 20/20 | 依赖矩阵、速查卡片、数据模型决策流程图 |
| 非显而易见模式 | 14/15 | R1-R5 黄金法则、事件可靠性要求、Outbox Pattern |
| 简洁性 | 13/15 | 每个文件职责明确，无重复。占位符稍增理解成本 |
| 时效性 | 13/15 | 规划阶段项目，规范超前于实现，无法验证一致性 |
| 可操作性 | 14/15 | section 0 速查卡片设计出色，命令可直接复制执行 |

**优势**: 多文件 SSOT 组织、section 0 速查卡片、依赖合法性矩阵、数据模型选择流程图、事件可靠性要求

**不足**: 占位符 `{PROJECT}` 在实际项目中需替换；无源码验证规范的可行性

### 项目 B: ai-studio-project/backend/

**Score: 68/100 (Grade: C+)**

| 指标 | 分数 | 说明 |
|------|------|------|
| 命令/工作流 | 16/20 | 命令齐全，但分散在 CLAUDE.md 多个章节 |
| 架构清晰度 | 16/20 | ARCHITECTURE.md 详尽，但 CLAUDE.md 与其重复且不同步 |
| 非显而易见模式 | 12/15 | @problem 装饰器、aioboto3 强制规则、HyperPod 踩坑记录 |
| 简洁性 | 8/15 | 354 行单文件信息密度过高，缺少导航结构 |
| 时效性 | 7/15 | ARCHITECTURE.md section 6 异常体系与实际代码不同步 |
| 可操作性 | 9/15 | 缺少安全、日志、可观测性、PR 检查清单独立规范 |

**优势**: `@problem` 异常体系、类型前缀测试命名、aioboto3 详细正反例、HyperPod 踩坑知识

**问题**:
1. CLAUDE.md 354 行包含 12 个功能区块，信息查找效率低
2. ARCHITECTURE.md section 6 异常体系仍为旧版继承式，与实际 `@problem` 代码不一致
3. 黄金法则只记录了 R1-R4，但代码中已使用 R5（跨模块事件订阅）
4. 缺少安全规范、日志规范、可观测性规范、PR 检查清单

---

## 二、规范分类分析

### 2.1 可直接复用（改动 <10%）

| 文件 | 复用度 | 修改内容 |
|------|--------|---------|
| `rules/security.md` | 95% | 无需修改，技术栈完全匹配 |
| `rules/api-design.md` | 95% | ErrorResponse 示例改为 Problem 体系格式 |
| `rules/checklist.md` | 90% | 预提交命令改为 `black --check`；测试路径改为 `tests/unit/{module}/` |

### 2.2 小幅修改后可复用（改动 10-30%）

| 文件 | 复用度 | 修改内容 |
|------|--------|---------|
| `rules/code-style.md` | 80% | "Ruff format" 改为 "black"；补充行内注释规范和 `@problem` 命名约定 |
| `rules/sdk-first.md` | 75% | 合并项目 B 的 aioboto3 强制规则+后台任务指南；移除 Bedrock AgentCore |
| `rules/logging.md` | 75% | 更新路径和环境配置，验证 structlog 依赖存在 |
| `rules/observability.md` | 70% | 替换指标名称为训练平台指标（gpu_hours 等）；添加 HyperPod Span |
| `rules/project-structure.md` | 65% | 更新为项目 B 的实际目录布局 |

### 2.3 需要重大适配

| 文件 | 说明 |
|------|------|
| `rules/architecture.md` | 从 ARCHITECTURE.md 提取精华 + 项目 A 速查卡片格式；补充 R5 规则；异常示例统一为 `@problem` |
| `rules/testing.md` | 以项目 B `tests/CLAUDE.md` 为内容基础 + 项目 A 格式框架；保留类型前缀命名 |
| `rules/tech-stack.md` | 全新编写，反映项目 B 实际版本（从 pyproject.toml 提取） |
| `project-config.md` | 全新编写，9 个模块表 + 域事件 + 导入路径 + 外部服务 + 待解决问题 |

### 2.4 不应迁移的内容

| 内容 | 原因 |
|------|------|
| uv 包管理强制 | 项目 B 使用 requirements.txt，切换影响 CI/CD 和 Docker 构建 |
| Ruff format 替代 black | pyproject.toml 有完整 black 配置，ruff lint 已委托 black 处理行长度 |
| asyncmy 替代 aiomysql | 功能等价，切换无收益有风险 |
| MyPy strict 模式 | pyproject.toml 有 18 处 overrides，强制 strict 会引入大量错误 |
| `{PROJECT}` 占位符 | 成熟项目应使用具体路径 `from src.shared.domain import ...` |
| `tests/modules/{m}/unit/domain/` 5 层目录 | 161 个文件已验证 3 层扁平结构有效 |
| factory_boy 强制 | pytest fixture 模式在项目 B 中已稳定运作 |
| Bedrock AgentCore 配置 | 项目 B 使用 SageMaker HyperPod |

### 2.5 项目 B 独有优势（必须保留）

| 内容 | 说明 |
|------|------|
| `@problem` 装饰器异常体系 | 每个异常 5 行 vs 传统 12+ 行，自动生成 message/status/details |
| 类型前缀测试命名 | `test_entity_`/`test_svc_`/`test_api_` 等，支持 `-k` 精确筛选 |
| HyperPod 踩坑记录 | TAS 配置、抢占、PriorityClass 等实际调试知识 |
| aioboto3 详细正反例 | 含 `run_in_executor` 反模式和原因说明 |
| K8s 后台任务策略 | CronJob + Watch API 架构决策 |
| docs/ARCHITECTURE.md | 28KB 含完整 PydanticEntity/PydanticRepository 代码示例 |

---

## 三、实施方案

### Phase 1: 准备（创建目录结构，不修改现有文件）

创建 `backend/.claude/rules/` 目录及以下文件：

```
backend/.claude/
├── CLAUDE.md               # 新入口（精简版，~80 行）
├── project-config.md       # 项目特定配置
└── rules/
    ├── architecture.md     # 架构速查
    ├── testing.md          # 测试规范
    ├── code-style.md       # 代码风格
    ├── security.md         # 安全规范
    ├── sdk-first.md        # SDK 原则
    ├── api-design.md       # API 设计
    ├── logging.md          # 日志规范
    ├── observability.md    # 可观测性
    ├── checklist.md        # PR Review 清单
    ├── project-structure.md # 目录结构
    └── tech-stack.md       # 技术栈版本
```

### Phase 2: 分步迁移

**P0 -- 直接复制（零风险）**:
1. `rules/security.md` -- 直接复制项目 A
2. `rules/api-design.md` -- 复制 + 更新 ErrorResponse 为 Problem 格式
3. `rules/checklist.md` -- 复制 + 更新命令和路径

**P1 -- 合并内容（低风险）**:
4. `rules/code-style.md` -- 项目 A 基础 + 项目 B 行内注释规范
5. `rules/sdk-first.md` -- 项目 A 框架 + 项目 B aioboto3 规则和后台任务指南
6. `rules/tech-stack.md` -- 项目 A 格式 + 项目 B 实际版本
7. `project-config.md` -- 项目 A 结构 + 全新内容（9 模块、域事件、导入路径）

**P2 -- 需要审查（中风险）**:
8. `rules/testing.md` -- 项目 B tests/CLAUDE.md 内容 + 项目 A 速查卡片格式
9. `rules/architecture.md` -- 从 ARCHITECTURE.md 提取精华 + 速查卡片 + R5 + @problem
10. `rules/logging.md` -- 项目 A 基础 + 更新路径
11. `rules/observability.md` -- 项目 A 基础 + 替换训练平台指标

**P3 -- 收尾**:
12. 重构 `backend/CLAUDE.md` 为精简入口（~80 行），链接到 `.claude/rules/`
13. `rules/project-structure.md` -- 反映实际目录布局
14. 精简 `tests/CLAUDE.md` 为指向 `rules/testing.md` 的简短引用

### Phase 3: 验证

1. 全局搜索 `uv run`、`ruff format`、`asyncmy` 等残留的项目 A 关键词
2. 验证所有 rules/ 文件间的交叉引用链接可达
3. 确认规范中的异常示例统一为 `@problem` 装饰器模式
4. 标记 `docs/ARCHITECTURE.md` section 6 待更新（异常体系文档滞后）
5. 在 backend/ 目录下测试 Claude Code 是否正确加载新规范

---

## 四、风险评估

### 高风险

| 风险 | 缓解措施 |
|------|---------|
| Claude Code 可能不自动加载 `.claude/CLAUDE.md` | Phase 1 先验证加载行为；备选方案是保持 `backend/CLAUDE.md` 为入口，在其中链接 `.claude/rules/` |
| ARCHITECTURE.md 和 rules/architecture.md 长期分裂 | 明确职责分工（详细参考 vs 速查索引）；rules/ 每个 section 标注"详见 docs/ARCHITECTURE.md section X"；checklist.md 添加同步检查项 |

### 中风险

| 风险 | 缓解措施 |
|------|---------|
| 复制的规范残留 `uv run` 等项目 A 命令 | Phase 3 全局搜索验证 |
| ARCHITECTURE.md section 6 异常文档与代码不一致（已存在问题） | rules/architecture.md 使用 @problem 模式；标记 ARCHITECTURE.md 待更新 |

### 低风险

| 风险 | 缓解措施 |
|------|---------|
| 迁移期间规范碎片化 | Phase 2 期间保持 CLAUDE.md 不变，rules/ 完成后再重构入口 |

---

## 五、关键文件清单

### 需要修改的文件

| 文件 | 操作 |
|------|------|
| `backend/CLAUDE.md` | Phase 3 重构为精简入口（~80 行） |
| `backend/tests/CLAUDE.md` | Phase 3 精简为指向 rules/testing.md 的引用 |

### 需要新建的文件

| 文件 | 来源 |
|------|------|
| `backend/.claude/CLAUDE.md` | 新建精简入口 |
| `backend/.claude/project-config.md` | 项目 A 结构 + 项目 B 内容 |
| `backend/.claude/rules/architecture.md` | ARCHITECTURE.md 精华 + 项目 A 速查格式 |
| `backend/.claude/rules/testing.md` | tests/CLAUDE.md 内容 + 项目 A 格式 |
| `backend/.claude/rules/code-style.md` | 项目 A 基础 + 项目 B 补充 |
| `backend/.claude/rules/security.md` | 直接复制项目 A |
| `backend/.claude/rules/sdk-first.md` | 项目 A 框架 + 项目 B 内容 |
| `backend/.claude/rules/api-design.md` | 项目 A + 小幅修改 |
| `backend/.claude/rules/logging.md` | 项目 A + 路径更新 |
| `backend/.claude/rules/observability.md` | 项目 A + 指标替换 |
| `backend/.claude/rules/checklist.md` | 项目 A + 命令/路径更新 |
| `backend/.claude/rules/project-structure.md` | 项目 A 格式 + 项目 B 布局 |
| `backend/.claude/rules/tech-stack.md` | 项目 A 格式 + 项目 B 版本 |

### 参考（只读）

| 文件 | 用途 |
|------|------|
| `backend/docs/ARCHITECTURE.md` | rules/architecture.md 和 project-config.md 的内容来源 |
| `backend/src/shared/domain/problem.py` | 确保异常示例与实际代码一致 |
| `backend/pyproject.toml` | tech-stack.md 的版本来源 |
| ai-agents-platform 全部 `.claude/rules/` 文件 | 模板来源 |

---

## 六、迁移效果预估

| 指标 | 迁移前 | 迁移后 |
|------|--------|--------|
| 规范文件数 | 3 个 | 14 个 |
| CLAUDE.md 入口行数 | 354 行 | ~80 行 |
| 单文件最大行数 | 354 行 | ~180 行 |
| 覆盖领域 | 5 个 | 11 个（+安全、日志、可观测性、API 设计、PR 清单、目录结构） |
| SSOT 违规 | 至少 3 处 | 0 处 |
