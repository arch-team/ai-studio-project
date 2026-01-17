# Claude Code Memory 管理规范 - 实施计划

> **版本**: 1.0 | **日期**: 2026-01-18 | **状态**: 待批准

## 目标

为 ai-studio-project 建立一套完整的 Claude Code Memory 管理规范，包括：
1. CLAUDE.md 文件组织标准
2. `.claude/rules/` 模块化规则体系
3. Serena Memory 使用规范

---

## 核心原则

| 原则 | 说明 |
|------|------|
| **单一真实源** | 每个领域有且仅有一个权威文档 |
| **300行黄金法则** | CLAUDE.md 保持 100-300 行 |
| **层级继承** | 子文档只包含差异性内容 |
| **就近放置** | 规范与代码距离最小化 |
| **按需加载** | 使用 `paths` 限制规则范围 |

---

## 实施内容

### 1. 创建规范文档

**文件**: `docs/CLAUDE-CODE-MEMORY-STANDARD.md`

包含以下章节：
- 总体原则
- 文件层级规范
- 内容模板
- Rules 规范
- Serena Memory 规范
- 继承与引用模式
- 版本控制与同步
- 反模式警告
- 快速参考

### 2. 创建 Rules 目录结构

```
.claude/rules/
├── general.md                    # 全局术语、提交规范
├── testing/
│   ├── tdd-workflow.md           # TDD 工作流 (全局)
│   └── backend-tests.md          # paths: backend/tests/**/*.py
├── backend/
│   ├── ddd-patterns.md           # paths: backend/src/**/*.py
│   └── sdk-first.md              # paths: backend/**/*.py
├── frontend/
│   └── cloudscape-rules.md       # paths: frontend/**/*.{ts,tsx}
└── infrastructure/
    └── cdk-patterns.md           # paths: infrastructure/cdk/**/*.py
```

### 3. 优化现有 CLAUDE.md

| 文件 | 当前行数 | 优化目标 |
|------|---------|---------|
| 根 `CLAUDE.md` | 131 | 保持，添加继承声明 |
| `backend/CLAUDE.md` | 265 | 消除与 tests/ 重复 |
| `frontend/CLAUDE.md` | 333 | 考虑拆分设计规范 |

### 4. 规范 Serena Memory

**命名前缀**：
- `project-` 项目级约束
- `task-` 任务进度
- `decision-` 技术决策
- `validation-` 验证结果
- `session-` 会话摘要

---

## 关键文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/CLAUDE-CODE-MEMORY-STANDARD.md` | 新建 | 完整规范文档 |
| `.claude/rules/general.md` | 新建 | 全局规范 |
| `.claude/rules/testing/tdd-workflow.md` | 新建 | TDD 规则 |
| `.claude/rules/testing/backend-tests.md` | 新建 | 后端测试规则 |
| `.claude/rules/backend/ddd-patterns.md` | 新建 | DDD 架构规则 |
| `.claude/rules/backend/sdk-first.md` | 新建 | SDK-First 规则 |
| `.claude/rules/frontend/cloudscape-rules.md` | 新建 | Cloudscape 规则 |
| `.claude/rules/infrastructure/cdk-patterns.md` | 新建 | CDK 规则 |
| `backend/CLAUDE.md` | 编辑 | 优化继承声明 |
| `backend/tests/CLAUDE.md` | 编辑 | 添加继承声明 |
| `frontend/CLAUDE.md` | 编辑 | 添加继承声明 |
| `infrastructure/cdk/CLAUDE.md` | 编辑 | 添加继承声明 |
| `CLAUDE.md` | 编辑 | 添加规范索引 |

---

## 验证方式

1. **Rules 加载验证**
   ```bash
   # 启动新会话后
   /memory
   # 应显示已加载的 rules
   ```

2. **路径匹配验证**
   - 编辑 `backend/tests/` 文件时，验证 `backend-tests.md` 规则生效
   - 编辑 `frontend/` 文件时，验证 `cloudscape-rules.md` 规则生效

3. **继承链验证**
   - 检查子模块 CLAUDE.md 首行是否有继承声明
   - 验证无重复内容

---

## 参考文档

- 现有研究: `cc-doc/plans/2026-01-17-claude-code-记忆管理与-rule-机制研究.md`
- 项目宪法: `.specify/memory/constitution.md`
- Serena 记忆: `.serena/memories/`
