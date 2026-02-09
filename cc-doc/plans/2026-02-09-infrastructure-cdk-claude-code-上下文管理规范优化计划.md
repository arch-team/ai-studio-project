# Infrastructure CDK - Claude Code 上下文管理规范优化计划

## Context

审计发现 `infrastructure/cdk/.claude/` 下的 16 个规范文件中存在 **6 处文档与代码不一致** 和 **4 处结构性遗漏**。以下所有改进方案已逐一获得用户确认。

---

## 已确认的改进项

### S1: 统一 Stack 层级编号为 6 层 (已确认: 同意 6 层方案)

以 `app.py` 为 SSOT，统一层级为:
```
L1: NetworkStack, IamStack (并行)
L2: DatabaseStack, StorageStack (并行)
L3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack (串行)
L4: ObservabilityStack, FsxLustreStack (并行)
L5: AlbStack
L6: ApplicationStack
```

**修改文件**:
- `infrastructure/cdk/.claude/rules/architecture.md` — 层级重写 + 目录表补全 (aspects/, stacks/application/, stacks/observability/)
- `infrastructure/cdk/stacks/__init__.py` — docstring 层级统一
- `infrastructure/cdk/.claude/rules/deployment.md:69-74` — 部署顺序更新
- `infrastructure/cdk/.claude/project-config.md:13` — "5 层" → "6 层"

### S4: 修复 configuration.md 环境差异速查表 (已确认: 同意修复)

**修改文件**: `infrastructure/cdk/.claude/rules/configuration.md:68-74`

- "多 AZ: Dev ❌" → "部署模式: Dev MULTI_AZ"
- "CDK Nag: Dev 跳过" → "CDK Nag: Dev 启用"

### S5: 简化 deployment.md RemovalPolicy 矩阵 (已确认: 同意简化)

**修改文件**: `infrastructure/cdk/.claude/rules/deployment.md:42-61`

按 `ProtectionConfig` 实际代码改为统一策略:
| 配置 | Dev | Staging | Prod |
|------|-----|---------|------|
| RemovalPolicy | DESTROY | DESTROY | RETAIN |
| Deletion Protection | 否 | 是 | 是 |

### S6: 修正 cost-optimization.md FSx/Aurora 数据 (已确认: 同意修正)

**修改文件**: `infrastructure/cdk/.claude/rules/cost-optimization.md:19-25`

- FSx: 1.2/2.4/4.8 TiB → 10/20/100 TiB (按 environments.py 实际值)
- Aurora: 固定实例 → Serverless v2 ACU (0.5-8/1-16/2-16)

### security.md CDK Nag 修正 (已确认: 同意修正)

**修改文件**: `infrastructure/cdk/.claude/rules/security.md:69-81`

移除虚假的 `skip_cdk_nag` 条件判断示例，改为实际的无条件启用写法。

### CLAUDE.md 入口优化 (已确认: 全部同意)

**修改文件**: `infrastructure/cdk/CLAUDE.md`

- 触发条件表: security/hyperpod 行改为精确 glob 路径
- 手动引用表新增 project-config.md
- 常用命令区新增 Makefile 复合命令

### project-config.md + testing.md 补全 (已确认: 全部同意)

**修改文件**:
- `infrastructure/cdk/.claude/project-config.md` — Construct 列表新增 PlatformKmsKey + 层级改 6 层
- `infrastructure/cdk/.claude/rules/testing.md` — 更新 Fixture 示例，补充共用 fixture 和 snapshot 测试说明

---

## 涉及文件汇总 (10 个)

| # | 文件 | 改动类型 |
|---|------|---------|
| 1 | `infrastructure/cdk/.claude/rules/architecture.md` | 层级重写 + 目录表补全 |
| 2 | `infrastructure/cdk/.claude/rules/configuration.md` | 环境差异表修正 |
| 3 | `infrastructure/cdk/.claude/rules/deployment.md` | RemovalPolicy 简化 + 部署顺序更新 |
| 4 | `infrastructure/cdk/.claude/rules/cost-optimization.md` | FSx/Aurora 数据修正 |
| 5 | `infrastructure/cdk/.claude/rules/security.md` | CDK Nag 描述修正 |
| 6 | `infrastructure/cdk/.claude/rules/testing.md` | Fixture 示例更新 |
| 7 | `infrastructure/cdk/.claude/project-config.md` | Construct 列表 + 层级修正 |
| 8 | `infrastructure/cdk/CLAUDE.md` | 触发条件精确化 + 引用补充 |
| 9 | `infrastructure/cdk/stacks/__init__.py` | Docstring 层级统一 |
| 10 | `infrastructure/cdk/app.py` | 无改动 (SSOT) |

## 验证方法

1. 逐一检查层级编号是否与 app.py 一致
2. 对比配置值与 environments.py 代码
3. 确认 rules 文件 frontmatter 与 CLAUDE.md 触发条件一致
4. `ruff check . && pytest -m unit` 确保代码不破坏
