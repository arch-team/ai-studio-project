# AI Training Platform — Agent Teams 使用指导

> 基于 Phase 1-3 实战经验提炼，覆盖后端 DDD + 前端 Cloudscape + CDK 基础设施三条主线的全栈 Agent Teams 操作手册。

**定位区分**:
- **本文档**: 聚焦"团队组织和执行"——何时组建团队、团队模式、任务拆解、波次执行、Prompt 模板
- **[工具生态指导手册](claude-code-工具生态指导手册.md)**: 聚焦"工具选择"——MCP Server 用法、Plugin 启用、场景工具矩阵

两者互补: 本文 §2 的 6 个完整模式是工具生态手册 §5 的 4 个简要配方的详尽版。模式中的"工具配置"段落引用手册 §2 场景矩阵。

---

## 一、何时使用 Agent Teams

### 使用 Agent Teams 的场景

| 子项目 | 条件 | 阈值 | 说明 |
|--------|------|------|------|
| **后端** | 任务数量 + 层级 | ≥5 任务 且 ≥2 层 | 单模块按 DDD 四层拆解通常产生 9-12 个任务 |
| **前端** | 新文件数 + 层级 | ≥3 新文件 且 ≥2 层 | Feature 模块含 types/api/hooks/components/pages 五层 |
| **CDK** | Stack 层级跨度 | ≥2 个 Stack 层级 | 如同时涉及 L1 Network + L3 EKS |
| **全栈** | 前后端同时 + API 契约 | 前后端同时开发 | 需要 OpenAPI 契约先行协调 |
| **通用** | 依赖 DAG 有并行窗口 | ≥2 个独立路径 | 可并行的任务越多，Teams 收益越大 |
| **通用** | 跨模块协作 | 存在 shared/interfaces | 如 IQuotaChecker 需要 training 和 quotas 协同 |

### 单 Agent 足够的场景

- 单文件修改 (Bug 修复、小功能增强)
- 代码审查和优化 (scope 明确、无新文件创建)
- 文档更新、配置调整
- 单层级实现 (如仅 Domain 层设计、仅 types 层定义)
- 3 步以内的简单任务

**原则**: Agent Team 有协调开销，简单任务直接做比组建团队更高效。

---

## 二、经验证的团队组合模式

### 模式 A: 后端 DDD 模块开发

**适用**: 9 个后端模块 (training, datasets, checkpoints, models, quotas, billing, spaces, audit, auth) 新建或大改

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | 协调任务、管理波次、汇总验收 |
| dev-domain | `general-purpose` | Domain 层: 实体 + 值对象 + 状态机 + 事件 + 异常 + 仓库接口 |
| dev-app | `general-purpose` | Application 层: DTO + Service + 模块内接口 |
| dev-infra | `general-purpose` | Infrastructure 层: ORM Model + RepositoryImpl + Migration |
| dev-api | `general-purpose` | API 层: Schema + Endpoints + Dependencies |
| reviewer | `everything-claude-code:python-reviewer` | 代码审查 + 质量验收 |

**可选扩展**: 跨模块场景增加 `dev-shared` (`general-purpose`) 负责 `shared/interfaces` 定义 + 桥接实现。

**工作流** (4 波次):
```
波次 1: dev-domain (Domain 层)
波次 2: dev-app + dev-infra (并行)
波次 3: dev-api + 单元测试 (并行)
波次 4: reviewer (集成测试 + 质量验收)
```

**关键经验**:
- `general-purpose` 类型最灵活，适合实现类任务 (能读、写、编辑、运行命令)
- 每个 Agent 的 prompt 中必须明确: 工作范围、参考规范路径、质量验证命令
- 使用 `mode: bypassPermissions` 让 Agent 自主运行测试和 lint
- 工具配置: serena (符号导航) + context7 (FastAPI/SQLAlchemy 文档)，参见工具生态手册 §2 场景 1

---

### 模式 B: 代码优化团队

**适用**: 对已有代码进行简化、重构、优化

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | 协调、验证 |
| simplifier-domain | `code-simplifier:code-simplifier` | Domain 层优化 |
| simplifier-app | `code-simplifier:code-simplifier` | Application 层优化 |
| simplifier-infra-api | `code-simplifier:code-simplifier` | Infrastructure + API 层优化 |

**关键经验**:
- 按 DDD 层级分派，各层之间无写冲突，可完全并行
- 优化后必须全量运行验证: `black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85`

---

### 模式 C: 安全/质量审查团队

**适用**: Phase 验收、PR 批量审计、安全合规检查

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | 协调、汇总报告 |
| security-reviewer | `security-engineer` | OWASP Top 10、敏感数据、注入攻击 |
| code-reviewer | `everything-claude-code:python-reviewer` | PEP 8、类型提示、Pythonic 惯用法 |
| arch-reviewer | `everything-claude-code:architect` | 分层合规、模块隔离、依赖方向 |
| test-reviewer | `quality-engineer` | 覆盖率、边界用例、测试质量 |

**审查标准**: 引用各子项目 checklist
- 后端: `backend/.claude/rules/checklist.md` (架构、代码风格、安全、测试、API 设计等 9 类)
- 前端: `frontend/.claude/rules/checklist.md` (架构、Cloudscape 合规、安全、测试等 10 类)
- CDK: `infrastructure/cdk/.claude/rules/checklist.md` (架构、安全、测试、部署、成本等 7 类)

---

### 模式 D: 前端 Cloudscape 页面开发 (新增)

**适用**: 12 个前端 feature 模块 (training, datasets, checkpoints, models, quotas, billing, spaces, reports, monitoring, audit, auth, templates) 新建或大改

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | 协调任务、管理波次、汇总验收 |
| dev-types-api | `general-purpose` | Types 层 (类型定义) + API 层 (fetch + TanStack Query hooks) |
| dev-hooks | `general-purpose` | Hooks 层: 业务逻辑 hooks + Zustand store (如需) |
| dev-components | `general-purpose` | Components 层: Table/Form/Detail 等 Cloudscape 组件 |
| dev-pages | `general-purpose` | Pages 层: 页面组件 + 路由注册 |
| reviewer | `everything-claude-code:code-reviewer` | 代码审查 + Cloudscape 合规 + 测试 |

**可选扩展**: 大型 feature 增加 `dev-tests` (`everything-claude-code:tdd-guide`) 专门编写测试。

**工作流** (4 波次):
```
波次 1: dev-types-api (Types + API)
波次 2: dev-hooks + dev-components (并行)
波次 3: dev-pages (Pages + 路由注册)
波次 4: reviewer (测试 + Cloudscape 合规审查)
```

**关键经验**:
- **Cloudscape 强制约束**: 所有 UI 必须使用 `@cloudscape-design/components`，禁止 Magic MCP、MUI、Ant Design
- **TanStack Query + Zustand**: 服务端数据用 React Query，客户端状态用 Zustand
- **Query Keys 工厂**: 统一使用 `@lib/query` 的 `queryKeys` 工厂，禁止裸字符串 key
- **MSW mock**: 集成测试使用 MSW handler，禁止直接 mock fetch
- **ESLint 守护**: `no-restricted-imports` 规则自动检测模块边界违规
- 工具配置: context7 (Cloudscape/React/TanStack Query 文档) + serena (组件模式查找)，参见工具生态手册 §2 场景 2

---

### 模式 E: CDK Stack 开发 (新增)

**适用**: 11 个 CDK Stack (Network, IAM, Database, Storage, EKS, HyperPod, HyperPodAddons, Observability, FsxLustre, ALB, Application) 新建或修改

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | 协调、Stack 依赖验证 |
| dev-config | `general-purpose` | Config 数据类 + Props dataclass |
| dev-stack | `general-purpose` | Stack 实现 + Construct 编写 |
| dev-test | `everything-claude-code:tdd-guide` | Stack 单元测试 (Template assertions) |
| security-reviewer | `everything-claude-code:security-reviewer` | CDK Nag 审查、IAM 最小权限 |

**工作流** (3 波次):
```
波次 1: dev-config + dev-stack (Config → Stack，可部分并行)
波次 2: dev-test + app.py 注册
波次 3: security-reviewer (CDK Nag + 安全审查)
```

**关键经验**:
- **6 层 Stack 架构**: L1 Network/IAM → L2 DB/Storage → L3 EKS/HyperPod → L4 Observability/FSx → L5 ALB → L6 Application
- **依赖注入**: 通过构造函数参数传递资源，**禁止** `Fn.import_value()` 跨 Stack 引用
- **mypy --strict**: CDK 项目要求 mypy 严格模式
- **共用 Fixture**: 需要 EKS 依赖的 Stack 复用 `conftest.py` 的 `network_stack` → `eks_stack` fixture 链
- 工具配置: aws-cdk MCP + aws-knowledge MCP + sequential-thinking，参见工具生态手册 §2 场景 3

---

### 模式 F: 全栈功能开发 (新增)

**适用**: 前后端同时开发 (如 billing、spaces、datasets 等涉及 API 契约协调的模块)

**团队构成**:

| 角色 | subagent_type | 职责 |
|------|--------------|------|
| team-lead | 当前会话 | API 契约定义、前后端协调、集成验证 |
| dev-backend | `general-purpose` | 后端 Domain + Application + Infrastructure + API |
| dev-frontend | `general-purpose` | 前端 Types + API + Hooks + Components + Pages |
| dev-test | `quality-engineer` | 前后端集成测试 + API 契约一致性 |
| reviewer | `everything-claude-code:code-reviewer` | 全栈代码审查 |

**工作流** (5 波次):
```
波次 1: team-lead 定义 API 契约 (OpenAPI spec in specs/contracts/)
波次 2: dev-backend (Domain + Application) + dev-frontend (Types + API stub)  (并行)
波次 3: dev-backend (Infrastructure + API) + dev-frontend (Hooks + Components)  (并行)
波次 4: dev-frontend (Pages + 路由) + dev-test (单元测试)  (并行)
波次 5: dev-test (集成测试 + 契约验证) + reviewer (全栈审查)
```

**关键经验**:
- **API 契约先行**: OpenAPI 规范是前后端的共同前置依赖，必须最先定义
- **前端 MSW mock**: API 未就绪时，前端使用 MSW mock 基于 OpenAPI 规范开发
- **类型对齐**: 前端 `types/index.ts` 必须与后端 Entity/DTO 字段名一致
- **共享文件冲突管理**: `backend/src/main.py`、`frontend/src/app/router/routes.ts` 由 team-lead 统一修改

---

## 三、任务拆解策略

### 3.1 后端 DDD 标准 9 步模板

每个新模块按以下模板拆解:

| # | 任务 | DDD 层级 | 典型产出 |
|---|------|---------|---------|
| 1 | Domain 实体 + 值对象 + 状态机 | Domain | `modules/{m}/domain/entities/*.py`, `value_objects/*.py` |
| 2 | 领域事件 + 模块异常 + 仓库接口 | Domain | `events.py`, `exceptions.py`, `repositories/*.py` |
| 3 | DTO + Application Service | Application | `application/dto/*.py`, `application/services/*.py` |
| 4 | ORM Model + RepositoryImpl + Migration | Infrastructure | `infrastructure/models/*.py`, `repositories/*_impl.py` |
| 5 | Request/Response Schema + Endpoints + Dependencies | API | `api/schemas/*.py`, `api/endpoints/*.py`, `api/dependencies.py` |
| 6 | 模块注册 (main.py 路由 + 异常映射) | Presentation | `src/main.py` 修改 |
| 7 | 单元测试 (Domain + Application) | Tests | `tests/unit/{module}/` |
| 8 | 集成测试 (Repository + API + 架构合规) | Tests | `tests/integration/{module}/` |
| 9 | 质量验收 (lint + type check + test) | 验证 | 无文件产出 |

**跨模块变体**: 在 #2 和 #3 之间插入 `shared/interfaces` 定义任务，在 #4-#5 之间插入桥接实现任务。

### 3.2 前端 Feature-Sliced 标准 7 步模板 (新增)

每个新 feature 模块按以下模板拆解:

| # | 任务 | FSD 层级 | 典型产出 |
|---|------|---------|---------|
| 1 | 类型定义 + UI Helper Constants | Types | `features/{f}/types/index.ts` |
| 2 | API fetch 函数 + TanStack Query hooks | API | `features/{f}/api/{f}Api.ts`, `queries.ts` |
| 3 | 业务逻辑 hooks + Zustand store (如需) | Hooks | `features/{f}/hooks/index.ts` |
| 4 | 展示组件 (Table/Form/Detail) | Components | `features/{f}/components/*.tsx` |
| 5 | 页面组件 + 路由注册 | Pages | `features/{f}/pages/*.tsx`, `app/router/routes.ts` |
| 6 | 模块公共 API 导出 | 导出 | `features/{f}/index.ts` |
| 7 | 测试 (组件 + Hook + 集成) | Tests | `tests/unit/features/{f}/`, `tests/integration/` |

### 3.3 CDK Stack 标准 5 步模板 (新增)

每个新 Stack 按以下模板拆解:

| # | 任务 | 层级 | 典型产出 |
|---|------|------|---------|
| 1 | Config 数据类 + Props | Config | `config/{name}_config.py` |
| 2 | Stack 实现 (+ 可复用 Construct) | Stack | `stacks/{category}/{name}_stack.py`, `cdk_constructs/` |
| 3 | app.py 注册 + 依赖声明 | 注册 | `app.py` 修改 |
| 4 | 单元测试 (Template assertions) | Tests | `tests/stacks/test_{name}_stack.py` |
| 5 | CDK Nag 安全审查 | 安全 | Nag 规则通过验证 |

### 3.4 依赖 DAG 构建规则

**后端 DDD DAG**:
```
#1 ──► #2 ──► #3 (Application)
              └──► #4 (Infrastructure) ──► #5 (API) ──► #6 (注册)
#1-#3 ──► #7 (单元测试)
#4-#7 ──► #8 (集成测试)
#1-#8 ──► #9 (质量验收)
```

**前端 FSD DAG**:
```
#1 (Types) ──► #2 (API) ──► #3 (Hooks)
                             └──► #4 (Components) ──► #5 (Pages) ──► #6 (导出)
#1-#5 ──► #7 (测试)
```

**CDK DAG**:
```
#1 (Config) ──► #2 (Stack) ──► #3 (注册)
                               └──► #4 (测试) ──► #5 (安全审查)
```

**全栈规则**: API 契约 (OpenAPI spec) 是前后端的共同前置依赖，必须在并行开发前完成。

---

## 四、波次执行模型

### 4.1 波次划分原则

1. **同一波次内的任务必须无依赖关系** (可完全并行)
2. **波次之间严格串行** (前一波全部完成才启动下一波)
3. **每波次结束运行验证** (对应子项目的 lint + type check + test)
4. **最后一波始终是审查/验收**

### 4.2 后端标准波次

```
波次 1: Domain 层
        ├── #1 实体 + 值对象 + 状态机
        └── #2 事件 + 异常 + 仓库接口
        验证: black --check src/modules/{m}/ && ruff check src/modules/{m}/ && mypy src/modules/{m}/

波次 2: Application + Infrastructure (2 Agent 并行)
        ├── #3 DTO + Service
        └── #4 ORM + Repo + Migration
        验证: 同上 + pytest tests/unit/{m}/ -q (如有)

波次 3: API + 注册 + 单元测试 (2 Agent 并行)
        ├── #5 Schema + Endpoints + Dependencies
        ├── #6 模块注册
        └── #7 单元测试
        验证: pytest tests/unit/{m}/ -v

波次 4: 集成测试 + 质量验收
        ├── #8 集成测试
        └── #9 质量验收
        验证: black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
```

### 4.3 前端标准波次 (新增)

```
波次 1: Types + API
        ├── #1 类型定义
        └── #2 API fetch + Query hooks
        验证: npx tsc --noEmit && npm run lint

波次 2: Hooks + Components (2 Agent 并行)
        ├── #3 业务逻辑 hooks
        └── #4 展示组件
        验证: npx tsc --noEmit && npm run lint

波次 3: Pages + 路由 + 导出
        ├── #5 页面组件 + 路由注册
        └── #6 模块导出
        验证: npm run lint && npm run build

波次 4: 测试 + Cloudscape 合规审查
        └── #7 测试
        验证: npm test -- --run && npm run test:coverage
```

### 4.4 CDK 标准波次 (新增)

```
波次 1: Config + Stack
        ├── #1 Config 数据类
        └── #2 Stack 实现
        验证: ruff check . && mypy .

波次 2: 注册 + 测试
        ├── #3 app.py 注册
        └── #4 单元测试
        验证: ruff check . && ruff format --check . && mypy . && pytest -m unit

波次 3: 安全审查
        └── #5 CDK Nag 检查
        验证: pytest -m unit --cov=stacks --cov=cdk_constructs
```

### 4.5 全栈模块波次 (新增)

```
波次 1: API 契约
        └── team-lead 定义 OpenAPI spec (specs/contracts/{module}-api.yaml)

波次 2: Domain + Types (2 Agent 并行)
        ├── 后端: Domain 实体 + 值对象 + 事件 + 异常 + 仓库接口
        └── 前端: Types 定义 + API fetch (基于 MSW mock)

波次 3: Application/Infrastructure + Hooks/Components (2 Agent 并行)
        ├── 后端: DTO + Service + ORM + RepositoryImpl
        └── 前端: Hooks + Components

波次 4: API Endpoints + Pages (2 Agent 并行)
        ├── 后端: Schema + Endpoints + Dependencies + 模块注册
        └── 前端: Pages + 路由注册 + 模块导出

波次 5: 集成测试 + 全栈审查
        ├── 前后端集成测试 (MSW handler 替换为真实 API)
        ├── API 契约一致性验证
        └── 全栈代码审查
        验证:
          后端: black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
          前端: npm run lint && npm test -- --run && npm run build
```

---

## 五、Agent 类型速查表

### 按任务类型选择 subagent_type

| 任务类型 | 推荐 subagent_type | 备选 |
|---------|-------------------|------|
| **后端模块实现** (Domain/App/Infra/API) | `general-purpose` | `python-development:fastapi-pro` |
| **前端 Feature 实现** (Types/API/Hooks/Components/Pages) | `general-purpose` | `frontend-architect` |
| **CDK Stack 实现** | `general-purpose` | `devops-architect` |
| **代码优化/简化** | `code-simplifier:code-simplifier` | `refactoring-expert` |
| **Python 代码审查** | `everything-claude-code:python-reviewer` | `everything-claude-code:code-reviewer` |
| **前端代码审查** | `everything-claude-code:code-reviewer` | `superpowers:code-reviewer` |
| **安全审查** | `everything-claude-code:security-reviewer` | `security-engineer` |
| **架构设计/规划** | `everything-claude-code:planner` | `everything-claude-code:architect` |
| **调试排错** | `error-debugging:debugger` | `error-debugging:error-detective` |
| **测试编写** | `everything-claude-code:tdd-guide` | `quality-engineer` |
| **代码探索/研究** | `Explore` | `Plan` |
| **构建错误修复** | `everything-claude-code:build-error-resolver` | - |
| **需求分析** | `requirements-analyst` | `Plan` |
| **技术文档编写** | `technical-writer` | `general-purpose` |

### 按子项目层级推荐

**后端 DDD 层级**:

| DDD 层级 | 实现 Agent | 审查 Agent |
|---------|-----------|-----------|
| Domain | `general-purpose` | `everything-claude-code:python-reviewer` |
| Application | `general-purpose` | `everything-claude-code:code-reviewer` |
| Infrastructure | `python-development:fastapi-pro` | `everything-claude-code:security-reviewer` |
| API | `python-development:fastapi-pro` | `everything-claude-code:security-reviewer` |
| Tests | `everything-claude-code:tdd-guide` | `quality-engineer` |

**前端 FSD 层级**:

| FSD 层级 | 实现 Agent | 审查 Agent |
|---------|-----------|-----------|
| Types | `general-purpose` | `everything-claude-code:code-reviewer` |
| API (Query hooks) | `general-purpose` | `everything-claude-code:code-reviewer` |
| Hooks / Store | `general-purpose` | `everything-claude-code:code-reviewer` |
| Components | `general-purpose` | `everything-claude-code:code-reviewer` |
| Pages | `general-purpose` | `everything-claude-code:code-reviewer` |
| Tests | `everything-claude-code:tdd-guide` | `quality-engineer` |

**CDK 层级**:

| CDK 层级 | 实现 Agent | 审查 Agent |
|---------|-----------|-----------|
| Config | `general-purpose` | `everything-claude-code:code-reviewer` |
| Stack / Construct | `general-purpose` | `everything-claude-code:security-reviewer` |
| Tests | `everything-claude-code:tdd-guide` | `quality-engineer` |
| 安全 (Nag) | - | `everything-claude-code:security-reviewer` |

---

## 六、质量保障与验证

### 每波次验证清单

每个波次完成后，team-lead 执行对应子项目验证:

**后端** (在 `backend/` 目录下):
```bash
black --check src/modules/{module}/
ruff check src/modules/{module}/
mypy src/modules/{module}/
pytest tests/ -q
pytest tests/architecture/test_architecture_compliance.py -v  # 架构合规
```

**前端** (在 `frontend/` 目录下):
```bash
npx tsc --noEmit
npm run lint
npm test -- --run
```

**CDK** (在 `infrastructure/cdk/` 目录下):
```bash
ruff check .
ruff format --check .
mypy .
pytest -m unit -q
```

### 最终汇聚验证

**后端 Milestone 验收**:
```bash
cd backend
black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
```

**前端 Milestone 验收**:
```bash
cd frontend
npm run lint && npm test -- --run && npm run build
```

**CDK Milestone 验收**:
```bash
cd infrastructure/cdk
ruff check . && ruff format --check . && mypy . && pytest -m unit --cov=stacks --cov=cdk_constructs
```

### 架构安全网

多 Agent 并行开发的关键安全网——即使各 Agent 独立工作，合规测试也能在集成时捕获架构违规:

| 子项目 | 安全网机制 | 检测内容 |
|--------|-----------|---------|
| 后端 | `tests/architecture/test_architecture_compliance.py` | Domain 导入 FastAPI/SQLAlchemy (违反 R1)、Application 依赖具体实现 (违反 R2)、模块间横向导入 (违反 R3) |
| 前端 | ESLint `no-restricted-imports` 规则 | 跨 feature 直接导入内部文件、Types 层导入外部模块 |
| CDK | CDK Nag (staging/prod 自动扫描) | IAM 过宽权限、S3 公开访问、缺少加密、`Fn.import_value` 使用 |

---

## 七、Agent Prompt 模板

### 后端实现类 Prompt

```
你是后端开发专家。请实现 {module} 模块的 {layer} 层。

**工作范围**:
- [具体文件列表]

**参考规范** (在 backend/ 目录下):
- `backend/.claude/rules/architecture.md` — DDD 分层规则 (依赖矩阵见 §0.1)
- `backend/.claude/rules/testing.md` — 测试规范 (前缀命名见 §0)
- `backend/.claude/rules/checklist.md` — PR 检查清单

**项目约束**:
- DDD + Clean Architecture, 依赖方向: API → Application → Domain ← Infrastructure
- 代码注释使用中文，变量名/函数名/类名保持英文
- 异常使用 @problem 装饰器定义 (参见 architecture.md §5)
- 仓库实现继承 PydanticRepository (参见 architecture.md §4)
- 遵循 TDD: 先写测试再写实现

**前置依赖** (已完成，可直接导入):
- [列出已完成的模块/文件]

**验证命令** (在 backend/ 目录下执行):
1. black --check src/modules/{module}/
2. ruff check src/modules/{module}/
3. mypy src/modules/{module}/
4. pytest tests/unit/{module}/ -q

你所属的团队是 {team_name}，你的任务 ID 是 #{task_id}。
完成后请使用 TaskUpdate 将任务标记为 completed。
```

### 前端实现类 Prompt (新增)

```
你是前端开发专家。请实现 {module} feature 模块的 {layer} 层。

**工作范围**:
- [具体文件列表]

**参考规范** (在 frontend/ 目录下):
- `frontend/.claude/rules/architecture.md` — FSD 分层规则 (依赖矩阵见 §0.1)
- `frontend/.claude/rules/testing.md` — 测试规范
- `frontend/.claude/rules/checklist.md` — PR 检查清单 (含 Cloudscape 合规)

**项目约束**:
- Feature-Sliced Design, 依赖方向: pages → components → hooks → api → types
- 全部使用 @cloudscape-design/components，禁止自定义 CSS/内联样式
- 服务端数据: TanStack Query v5 (useQuery/useMutation)
- 客户端状态: Zustand (create + persist)
- Query Keys: 使用 @lib/query 的 queryKeys 工厂
- 类型定义与后端 Entity 字段名保持一致

**前置依赖** (已完成，可直接导入):
- [列出已完成的模块/文件]
- 可参考的现有 feature: features/training/ (结构模板)

**验证命令** (在 frontend/ 目录下执行):
1. npx tsc --noEmit
2. npm run lint
3. npm test -- --run tests/unit/features/{module}/

你所属的团队是 {team_name}，你的任务 ID 是 #{task_id}。
完成后请使用 TaskUpdate 将任务标记为 completed。
```

### CDK 实现类 Prompt (新增)

```
你是 AWS CDK 基础设施开发专家。请实现 {stack_name} Stack。

**工作范围**:
- [具体文件列表]

**参考规范** (在 infrastructure/cdk/ 目录下):
- `infrastructure/cdk/.claude/rules/architecture.md` — 6 层 Stack 架构规则
- `infrastructure/cdk/.claude/rules/testing.md` — 测试规范 (共用 Fixture 见 §核心 Fixtures)
- `infrastructure/cdk/.claude/rules/checklist.md` — PR 检查清单 (含安全、部署、成本)

**项目约束**:
- 6 层 Stack 架构: L1 Network/IAM → L2 DB/Storage → L3 EKS/HyperPod → L4 Obs/FSx → L5 ALB → L6 App
- 通过构造函数参数传递资源 (依赖注入)，禁止 Fn.import_value()
- mypy 严格模式 (mypy --strict)
- Props 使用 @dataclass(frozen=True) 定义
- CDK Nag 检查必须通过 (staging/prod)

**前置依赖** (已完成，可直接导入):
- [列出已完成的 Stack]

**验证命令** (在 infrastructure/cdk/ 目录下执行):
1. ruff check .
2. ruff format --check .
3. mypy .
4. pytest tests/stacks/test_{stack_name}_stack.py -v

你所属的团队是 {team_name}，你的任务 ID 是 #{task_id}。
完成后请使用 TaskUpdate 将任务标记为 completed。
```

### 审查类 Prompt

```
你是代码审查专家。请审查 {module} 模块的全部代码。

**审查范围**: {子项目路径}

**审查标准** (参照对应 checklist):
- 后端: backend/.claude/rules/checklist.md
- 前端: frontend/.claude/rules/checklist.md
- CDK: infrastructure/cdk/.claude/rules/checklist.md

**重点检查**:
- [ ] 分层与架构合规 (依赖方向、模块隔离)
- [ ] 代码风格 (类型提示/TypeScript 类型、命名规范)
- [ ] 安全 (无硬编码密钥、SQL 注入/XSS 防护)
- [ ] 测试覆盖率达标 (后端 ≥85%, 前端 ≥80%, CDK stacks ≥90%)

**验证命令**:
- 后端: black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
- 前端: npm run lint && npm test -- --run && npm run build
- CDK: ruff check . && mypy . && pytest -m unit --cov=stacks --cov=cdk_constructs

发现问题请直接修复并说明。
```

---

## 八、Phase 4-8 并行规划

### Phase 总览

| Phase | 范围 | 任务数 | 子项目 | 当前状态 |
|-------|------|--------|--------|---------|
| Phase 4 | US2 数据集管理 | 14 | 后端 + 前端 | 后端大部分完成，前端待实现 |
| Phase 5 | US3 资源配额与集群监控 | 21 | 后端 + 前端 | 后端大部分完成，前端待实现 |
| Phase 6 | US4 资源使用报表与成本分析 | 13 | 后端 (billing) + 前端 (reports) | 未开始 |
| Phase 7 | US5 在线开发环境 | 15 | 后端 (spaces) + 前端 (spaces) + CDK | 数据模型已完成，API/前端待实现 |
| Phase 8 | 质量保障、GitOps、横向功能 | 24 | 全栈 | 未开始 |

### 并行可行性分析

| 组合 | 可并行? | 理由 |
|------|:------:|------|
| Phase 4 前端 + Phase 5 前端 | ✅ | 互不依赖，对应后端已完成 |
| Phase 6 + Phase 7 | ✅ | billing 和 spaces 模块互不依赖 |
| Phase 6 + Phase 4/5 前端 | ✅ | 不同模块，无交叉 |
| Phase 7 + Phase 4/5 前端 | ✅ | 不同模块，无交叉 |
| Phase 8 + Phase 6/7 | ⚠️ 部分 | Phase 8 的测试/文档可并行，但 GitOps 依赖全部功能完成 |

### 推荐执行方案

```
当前 (可立即启动):
  ├── Phase 4 前端 (datasets feature 页面)  — 模式 D
  └── Phase 5 前端 (quotas/monitoring feature 页面)  — 模式 D

第一批并行:
  ├── Phase 6 后端 (billing 模块)  — 模式 A
  ├── Phase 6 前端 (reports feature)  — 模式 D (在 billing API 就绪后启动)
  └── Phase 7 后端 (spaces API + SageMaker 集成)  — 模式 A

第二批并行:
  ├── Phase 7 前端 (spaces feature)  — 模式 D
  └── Phase 8 前半 (单元测试 T091/T092 + 错误处理 T097-T099 + 日志 T100-T102)

第三批 (串行为主):
  └── Phase 8 后半 (GitOps T105a-T105e + 无障碍 T104 + 文档 T105)
```

### 共享文件冲突管理

多个 Team 同时运行时，以下共享文件需要由 team-lead 统一修改:

| 共享文件 | 子项目 | 冲突场景 |
|---------|--------|---------|
| `backend/src/main.py` | 后端 | 新模块路由注册 |
| `backend/src/shared/api/exception_handlers.py` | 后端 | 新异常映射 |
| `frontend/src/app/router/routes.ts` | 前端 | 新页面路由注册 |
| `frontend/src/app/navigation/config.ts` | 前端 | 导航菜单配置 |
| `infrastructure/cdk/app.py` | CDK | 新 Stack 注册 |

**管理策略**: 各 Team 完成内部开发后，由 team-lead 统一进行共享文件修改和模块注册。

---

## 九、常见问题与经验教训

### Q1: Agent 之间如何避免文件写冲突?

按 DDD 层级 (后端)、FSD 层级 (前端)、Stack 维度 (CDK) 划分工作范围，每个 Agent 只修改其负责层级的文件。共享文件 (`main.py`, `routes.ts`, `app.py`) 由 team-lead 统一修改。

### Q2: 波次之间如何传递上下文?

每个波次的 Agent prompt 中明确列出"前置依赖已完成"的文件和接口。Agent 可以读取这些文件来理解上下文，但不应修改它们。

### Q3: 某个 Agent 失败了怎么办?

1. 检查失败原因 (通常是测试失败或类型错误)
2. 可以 resume 该 Agent 继续修复 (使用 `resume` 参数传入 agent ID)
3. 或者启动新 Agent 专门修复问题 (使用 `error-debugging:debugger` 类型)

### Q4: 团队规模如何控制?

- 单模块开发: 4-6 个 Agent (含 reviewer)
- 代码优化: 2-4 个 Agent (按层级分派)
- 安全审查: 3-4 个 Agent (按审查维度分派)
- 避免超过 6 个 Agent 同时运行，防止资源竞争

### Q5: 何时用 `run_in_background` vs 同步等待?

- **background**: 任务耗时较长 (如完整模块实现)，team-lead 可同时处理其他事务
- **同步**: 任务较短 (如代码优化) 或 team-lead 需要等待结果再决策下一步

### Q6: 前后端 API 契约一致性如何保障? (新增)

- **OpenAPI 契约先行**: 在 `specs/001-ai-training-platform/contracts/` 定义 OpenAPI 规范
- **前端 MSW mock**: 基于 OpenAPI 规范创建 MSW handler，前端可独立开发
- **契约测试**: Phase 8 的 T093-T095 (API Contract 集成测试) 自动验证一致性
- **类型对齐**: 前端 `types/index.ts` 的字段名必须与后端 Entity/DTO 一致

### Q7: CDK 测试依赖链如何处理? (新增)

- **共用 Fixture**: `infrastructure/cdk/tests/conftest.py` 定义了 Stack 依赖链 fixture (`network_stack` → `iam_stack` → `eks_stack`)
- **轻量级 Fixture**: 不需要完整依赖链时使用 `lightweight_eks_cluster` 等简化 fixture
- **独立测试**: 每个 Stack 测试文件独立，通过 fixture 自动获得依赖 Stack 实例

### Q8: 如何与 Spec-Kit 工作流配合? (新增)

- **规范到任务**: `/speckit.tasks` 生成 `tasks.md` → 人工审核 → TaskCreate 创建团队任务
- **波次分派**: 根据 `tasks.md` 中的依赖关系和并行执行策略，将任务分配到波次
- **一致性检查**: `/speckit.analyze` 检查 spec.md、plan.md、tasks.md 之间的一致性
- **实现闭环**: 完成后运行 `/speckit.checklist` 生成质量检查清单进行验收
