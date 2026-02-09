# Claude Code 上下文管理规范迁移分析

## Context

**源项目**: `ai-agents-platform/infra` (TypeScript CDK, 规范成熟度 8.3/10)
**目标项目**: `ai-studio-project/infrastructure/cdk` (Python CDK, 规范成熟度 6.4/10)

源项目拥有一套经过验证的 Claude Code 上下文管理规范体系（12 个文件），涵盖架构、设计、安全、测试、部署、成本、检查清单等。目标项目在核心领域（Stack/Construct/安全/测试/HyperPod）已有 9 个规范文件覆盖良好，但在运维侧（部署/成本优化）和工程治理侧（PR 检查清单/技术栈版本）存在明显缺口。

**核心结论**: 建议**增量补充**而非全面替换。保留目标项目的编号索引、frontmatter 触发、HyperPod 领域特色，在此基础上补充缺失规范。

---

## 1. 技术差异分析

### 语言无关（可直接复用结构）
- `checklist.md` — PR Review 检查项是流程规范
- `cost-optimization.md` — AWS 服务层面配置
- `deployment.md` — 运维层面规范
- `context-guide.md` — 元文档
- `project-config.template.md` — 模板机制

### 需要适配（代码示例改 Python）
| 源项目规范 | 适配难度 | 关键差异 |
|-----------|---------|---------|
| `architecture.md` | 低 | Stack Props: TypeScript `interface` → Python 构造函数参数 |
| `construct-design.md` | 中 | `readonly` → `@dataclass(frozen=True)`，JSDoc → docstring |
| `security.md` | 低 | `bucket.grantRead()` → `bucket.grant_read()` |
| `testing.md` | 中 | Jest → pytest，Snapshot 语法全改 |
| `tech-stack.md` | 中 | TypeScript/Node/pnpm/Jest → Python/pip/pytest/ruff/mypy |
| `project-structure.md` | 中 | `bin/app.ts` + `lib/` → `app.py` + `stacks/` + `cdk_constructs/` |

### 不适用
TypeScript 类型系统细节、pnpm 命令体系、ESLint/Prettier/tsconfig 配置

---

## 2. 可迁移规范清单

### Phase 1: 高优先级（立即）

| # | 规范 | 目标文件 | 难度 | 适配要点 |
|---|------|---------|------|---------|
| A | PR Review 检查清单 | `09-checklist.md` | 容易 | 六维度检查直接复用；代码示例改 Python；路径改 `stacks/`/`cdk_constructs/`；新增 ruff/mypy 检查项 |
| B | 部署规范 | `10-deployment.md` | 中等 | RemovalPolicy 策略可复用（需与 `02-stack-design.md` 去重）；CI/CD 改 Python 工具链；部署顺序改 5 层分层；新增 HyperPod 部署流程 |
| C | 成本优化规范 | `11-cost-optimization.md` | 容易 | 环境资源矩阵/NAT/S3 可复用；必须新增 GPU 实例(p4d ~$32/h, p5 ~$98/h)、FSx Lustre、EFA 网络成本项 |

### Phase 2: 中优先级（后续）

| # | 规范 | 目标文件 | 难度 | 适配要点 |
|---|------|---------|------|---------|
| D | 项目配置 | `.claude/project-config.md` | 中等 | 新建内容：8 个 Stack 列表/Construct 列表/环境配置，作为 `config/*.py` 的人类可读索引 |
| E | 技术栈规范 | `12-tech-stack.md` | 容易 | 版本矩阵全替换：Python/CDK/pytest/ruff/mypy/cdk-nag |
| F | 元文档 | `docs/context-guide.md` | 容易 | 结构复用，内容填入目标项目的 00-12 编号体系和引用关系 |

### Phase 3: 低优先级（按需）

| # | 规范 | 目标文件 | 说明 |
|---|------|---------|------|
| G | 项目目录结构 | 评估合并到 `01-architecture.md` | 现有规范已有"目录职责"表 |
| H | 配置模板 | `docs/project-config.template.md` | 仅在需要初始化新项目时 |

---

## 3. 目标项目独有优势（不应替换）

| 设计 | 所在文件 | 优于源项目的原因 |
|------|---------|----------------|
| 编号索引 + frontmatter 触发 | `00-index.md` + 各文件 | 精确按需加载，避免不必要的上下文消耗 |
| 始终加载/按需加载区分 | `00-index.md` | 高效的上下文管理策略 |
| HyperPod 专题深度 | `08-hyperpod.md` | 领域特色，不可替代 |
| Python 代码风格独立规范 | `05-code-style.md` | 语言特色需求 |
| `constants.py` + `environments.py` 双文件架构 | `04-configuration.md` | 比源项目更类型安全 |
| Aspect 模式规范化 | `03-construct-design.md` | Python CDK 特色 |
| Stack 5 层分层 (L1-L5) | `01-architecture.md` | 适配 HyperPod 复杂部署链 |

---

## 4. 迁移注意事项

### 编号体系一致性
新文件沿用 `09-`/`10-`/`11-`/`12-` 编号，更新 `00-index.md` 索引。Frontmatter 建议：
- `09-checklist.md` — 无 paths（手动引用）
- `10-deployment.md` — `paths: ["app.py", "cdk.json"]`
- `11-cost-optimization.md` — `paths: ["stacks/**/*.py", "config/environments.py"]`
- `12-tech-stack.md` — 无 paths（手动引用）

### 去重处理
| 迁移项 | 冲突点 | 解决方案 |
|--------|--------|---------|
| `10-deployment.md` 删除策略 | `02-stack-design.md` 已有 | 保留在 deployment 作为 SSOT，stack-design 改为引用 |
| `11-cost-optimization.md` 环境配置 | `04-configuration.md` 环境差异 | cost 聚焦资源规格/成本，config 聚焦代码层配置 |
| `09-checklist.md` 安全检查 | `07-security.md` 环境要求 | checklist 作为检查 SSOT，引用 security 详细说明 |

### 引入的设计理念
从源项目引入以下理念以提升可维护性：
- **单一真实源 (SSOT)**: checklist.md 是 PR Review 唯一来源，tech-stack.md 是版本唯一来源
- **职责边界声明**: 相关规范文件之间明确分工说明
- **速查卡片 (Section 0)**: 新增文件统一提供开头速查区

---

## 5. 子目录覆盖建议

| 子目录 | 当前状态 | 建议 |
|--------|---------|------|
| `infrastructure/k8s/` | 无 CLAUDE.md | 建议新增：namespace/label 约定、NetworkPolicy、Kueue 配置规范 |
| `infrastructure/grafana/` | 无 CLAUDE.md | 可选：仪表盘 JSON 规范 |
| `infrastructure/tests/` | 无 CLAUDE.md | 建议新增：验证测试使用说明、集成测试标记约定 |

---

## 6. 关键文件清单

### 需要新建的文件
- `infrastructure/cdk/.claude/rules/09-checklist.md`
- `infrastructure/cdk/.claude/rules/10-deployment.md`
- `infrastructure/cdk/.claude/rules/11-cost-optimization.md`
- `infrastructure/cdk/.claude/rules/12-tech-stack.md`
- `infrastructure/cdk/.claude/project-config.md`
- `infrastructure/cdk/docs/context-guide.md`

### 需要修改的文件
- `infrastructure/cdk/.claude/rules/00-index.md` — 添加 09-12 的索引条目
- `infrastructure/cdk/.claude/rules/02-stack-design.md` — 删除策略改为引用 `10-deployment.md`
- `infrastructure/cdk/CLAUDE.md` — 添加新规范导航链接

### 参考的源文件
- `ai-agents-platform/infra/.claude/rules/checklist.md`
- `ai-agents-platform/infra/.claude/rules/deployment.md`
- `ai-agents-platform/infra/.claude/rules/cost-optimization.md`
- `ai-agents-platform/infra/.claude/rules/tech-stack.md`
- `ai-agents-platform/infra/.claude/project-config.md`
- `ai-agents-platform/infra/doc/context-guide.md`

---

## 7. 验证方式

1. **结构验证**: 确认 `00-index.md` 索引完整，所有新文件有正确的 frontmatter
2. **去重验证**: 搜索 `02-stack-design.md` 中删除策略是否改为引用链接
3. **内容验证**: 确认所有代码示例为 Python CDK 语法，无 TypeScript 残留
4. **加载测试**: 在 Claude Code 中编辑 `stacks/*.py` 文件，确认相关规范按需加载
5. **PR Review 测试**: 使用 `09-checklist.md` 对一个真实 PR 进行 Review，验证实用性

---

## 8. 预期收益

| 维度 | 迁移前 | 迁移后 |
|------|--------|--------|
| PR Review | 无标准化检查清单 | 六维度标准化检查 |
| 部署规范 | 仅简单命令 | 完整的多环境部署流程 |
| 成本控制 | 无成本意识规范 | 标签追踪 + 预算告警 + 资源矩阵 |
| 版本管理 | 无明确版本要求 | SSOT 版本矩阵 |
| 规范可维护性 | 无元文档 | context-guide.md + SSOT 设计 |
| **综合成熟度** | **6.4/10** | **预期 8.0/10** |

---

## 9. 执行方式

**逐项确认流程**: 按优先级逐个处理，每个规范文件先说明优化依据，获得确认后再执行。

### 执行顺序

| 序号 | 操作 | 类型 | 确认后执行 |
|------|------|------|-----------|
| 1 | 新建 `09-checklist.md` | 新文件 | 参考源项目 checklist.md 适配 Python CDK |
| 2 | 新建 `10-deployment.md` | 新文件 | 参考源项目 deployment.md 适配 Python CDK |
| 3 | 新建 `11-cost-optimization.md` | 新文件 | 参考源项目 cost-optimization.md + HyperPod 成本项 |
| 4 | 新建 `12-tech-stack.md` | 新文件 | 参考源项目 tech-stack.md 替换为 Python 工具链 |
| 5 | 新建 `.claude/project-config.md` | 新文件 | 集中业务配置信息 |
| 6 | 新建 `docs/context-guide.md` | 新文件 | 规范体系元文档 |
| 7 | 更新 `00-index.md` | 修改 | 添加新增规范的索引条目 |
| 8 | 更新 `02-stack-design.md` | 修改 | 删除策略改为引用 deployment |
| 9 | 更新 `CLAUDE.md` | 修改 | 添加新规范导航链接 |

每一步我会先展示:
1. **优化依据**: 为什么需要这个规范
2. **内容预览**: 规范的核心结构和要点
3. **与现有规范的关系**: 是否有冲突需要处理

获得你的确认后再创建/修改文件。
