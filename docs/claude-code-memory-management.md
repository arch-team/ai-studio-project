# Claude Code Memory 管理规范

本规范基于 Claude Code 官方文档和社区最佳实践，为 CDK 项目定义 Memory 管理标准。

---

## 一、Memory 层级架构

### 1.1 加载优先级 (从高到低)

```
优先级 1 (最高): ./CLAUDE.local.md        # 个人项目配置 (不入库)
优先级 2:        ./CLAUDE.md               # 项目配置 (入库共享)
优先级 3:        ./.claude/rules/*.md      # 模块化规则 (入库共享)
优先级 4:        ~/.claude/CLAUDE.md       # 用户全局配置
优先级 5:        ~/.claude/rules/*.md      # 用户全局规则
优先级 6 (最低): /etc/claude-code/CLAUDE.md # 组织策略
```

### 1.2 加载机制

```
用户打开 /project/infrastructure/cdk/ 目录:

自动加载:
├── /project/infrastructure/cdk/CLAUDE.md          ✅ 当前目录
├── /project/infrastructure/cdk/.claude/rules/*.md ✅ 当前目录规则
├── /project/infrastructure/CLAUDE.md              ✅ 父目录递归
├── /project/CLAUDE.md                             ✅ 根项目
├── ~/.claude/CLAUDE.md                            ✅ 用户全局
└── ~/.claude/rules/*.md                           ✅ 用户规则

条件加载 (处理特定文件时):
├── /project/infrastructure/cdk/stacks/CLAUDE.md   仅处理 stacks/* 时
└── /project/backend/CLAUDE.md                     仅处理 backend/* 时
```

---

## 二、文件职责划分

### 2.1 CLAUDE.md vs Rules 目录

| 文件类型 | 职责 | 特点 |
|----------|------|------|
| `CLAUDE.md` | 核心规则 + 快速参考 | 始终加载，应保持精简 |
| `.claude/rules/*.md` | 详细规范 + 主题文档 | 自动加载，可按需组织 |
| `CLAUDE.local.md` | 个人配置 + 敏感信息 | 不入库，仅本地使用 |

### 2.2 本项目文件结构

```
infrastructure/cdk/
├── CLAUDE.md                     # 项目入口 (≤200行)
│   ├── 核心规则 (5条)
│   ├── 命名规范 (表格)
│   ├── 常用命令
│   └── 详细规范引用表
├── CLAUDE.local.md               # 个人配置 (不入库)
│   ├── 本地 AWS 账户 ID
│   ├── 个人测试环境
│   └── 调试偏好
└── .claude/
    ├── settings.json             # Claude Code 配置
    └── rules/
        ├── 00-memory-management.md  # 本文件
        ├── 01-architecture.md       # 架构规范
        ├── 02-stack-design.md       # Stack 设计
        ├── 03-construct-design.md   # Construct 设计
        ├── 04-configuration.md      # 配置管理
        ├── 05-code-style.md         # 代码风格
        ├── 06-testing.md            # 测试规范
        ├── 07-security.md           # 安全规范
        └── 08-hyperpod.md           # HyperPod 部署
```

---

## 三、CLAUDE.md 编写原则

### 3.1 必须包含

```markdown
✅ Claude 无法从代码推断的命令
   - 特殊的构建/测试命令
   - 环境激活步骤

✅ 项目特定的规则
   - 与语言默认不同的代码风格
   - 架构决策和约束

✅ 常见陷阱
   - 非显而易见的行为
   - 历史遗留问题

✅ 工作流规范
   - Git 分支策略
   - PR 提交规范
```

### 3.2 不应包含

```markdown
❌ Claude 能从代码推断的内容
   - 文件结构描述 (Claude 会自己探索)
   - 标准语言约定

❌ 详细的 API 文档
   - 改用 @引用 外部文档
   - 或提供文档链接

❌ 经常变化的信息
   - 版本号 (放在 package.json)
   - 配置值 (放在配置文件)

❌ 自明的实践
   - "写干净的代码"
   - "遵循最佳实践"
```

### 3.3 长度控制

| 级别 | 行数 | 适用场景 |
|------|------|----------|
| 精简 | ≤100 行 | 简单项目 |
| **标准** | **≤200 行** | **本项目推荐** |
| 详细 | ≤500 行 | 复杂项目 (需拆分) |

**黄金法则**: 对每一行问 "删除这个会导致 Claude 出错吗？"

---

## 四、Rules 目录规范

### 4.1 文件命名

```
.claude/rules/
├── 00-*.md      # 元规范 (memory 管理、索引)
├── 01-*.md      # 架构规范
├── 02-*.md      # 设计规范
├── 03-09-*.md   # 主题规范
└── 99-*.md      # 附录、参考
```

### 4.2 路径特定规则 (Frontmatter)

```markdown
---
paths:
  - "stacks/**/*.py"
  - "cdk_constructs/**/*.py"
---

# Stack 开发规则

这些规则仅在处理 stacks/ 和 cdk_constructs/ 目录时生效。
```

### 4.3 规则粒度

| 粒度 | 行数 | 示例 |
|------|------|------|
| 单一主题 | ≤300 行 | `05-code-style.md` |
| 复合主题 | ≤500 行 | `07-security.md` |
| 参考文档 | ≤1000 行 | `08-hyperpod.md` |

---

## 五、@ 引用机制

### 5.1 支持的引用方式

```markdown
# 相对路径
@docs/architecture.md
@../shared/common-rules.md

# 绝对路径
@/Users/xxx/shared-rules.md

# Home 目录
@~/.claude/my-preferences.md
```

### 5.2 引用限制

- ✅ 最大深度: 5 层递归
- ❌ 代码块内不解析 `@`
- ❌ 不支持 glob 模式

### 5.3 推荐用法

```markdown
# CLAUDE.md 中引用外部文档

## 架构设计
详见 @docs/architecture.md

## 个人配置
我的偏好 @~/.claude/cdk-preferences.md
```

---

## 六、上下文管理

### 6.1 上下文预算

| 模型 | 上下文窗口 | 推荐 Memory 占用 |
|------|-----------|-----------------|
| Claude Opus 4 | 200K tokens | ≤10K tokens (5%) |
| Claude Sonnet 4 | 200K tokens | ≤8K tokens (4%) |
| Claude Haiku | 200K tokens | ≤5K tokens (2.5%) |

### 6.2 上下文优化策略

```markdown
1. 主动压缩
   /compact 保留架构决策，压缩文件读取历史

2. 任务隔离
   /clear  # 完成任务 A 后清空
   # 开始任务 B

3. 使用 Subagent
   复杂调查交给 subagent，避免污染主上下文

4. 按需加载
   使用 @引用 而非全部写入 CLAUDE.md
```

### 6.3 监控命令

```bash
/memory   # 查看已加载的 memory 文件
/cost     # 查看 token 使用情况
```

---

## 七、本项目配置示例

### 7.1 CLAUDE.md (精简版)

```markdown
# CLAUDE.md - CDK 项目

## 核心规则
- Stack 分层: L1→L2→L3→L4→L5 单向依赖
- 依赖注入: 通过构造函数传递资源
- 禁止: Fn.import_value() 跨 Stack 引用

## 命名规范
| 类型 | 格式 | 示例 |
|------|------|------|
| Stack ID | PascalCase | NetworkStack |
| 资源名称 | kebab-case | ai-platform-dev-vpc |

## 常用命令
- pytest -m unit
- cdk deploy --context env=dev

## 详细规范
| 任务 | 规范 |
|------|------|
| 新建 Stack | @.claude/rules/02-stack-design.md |
| 安全审查 | @.claude/rules/07-security.md |
```

### 7.2 CLAUDE.local.md (个人配置)

```markdown
# CLAUDE.local.md - 个人配置 (不入库)

## 我的测试环境
- AWS Account: 123456789012
- Region: us-west-2
- Profile: dev-personal

## 调试偏好
- 启用详细日志
- 跳过某些测试

## 本地快捷命令
- make my-deploy → 部署到个人环境
```

### 7.3 settings.json

```json
{
  "permissions": {
    "allow": [
      "Bash(cdk *)",
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Bash(mypy *)"
    ]
  }
}
```

---

## 八、维护规范

### 8.1 定期审查

| 频率 | 检查项 |
|------|--------|
| 每周 | CLAUDE.md 是否过长 (>200行) |
| 每月 | Rules 文件是否过时 |
| 每季度 | Memory 结构是否需要重组 |

### 8.2 审查清单

```markdown
□ CLAUDE.md 每行都是必要的吗？
□ 有重复信息吗？
□ 有过时信息吗？
□ 有 Claude 能自己推断的内容吗？
□ 详细规范是否应该移到 rules/ ?
```

### 8.3 版本控制

```gitignore
# .gitignore
CLAUDE.local.md    # 个人配置不入库
.claude/local/     # 本地规则不入库
```

---

## 九、常见问题

### Q1: Rules 目录的文件会自动加载吗？

**是的**。`.claude/rules/` 下的所有 `.md` 文件都会自动加载，优先级与 `.claude/CLAUDE.md` 相同。

### Q2: 如何让某些规则只在特定目录生效？

使用 YAML frontmatter:

```markdown
---
paths:
  - "stacks/**/*.py"
---
```

### Q3: 上下文满了怎么办？

1. `/compact` 手动压缩
2. `/clear` 清空后重新开始
3. 检查 CLAUDE.md 是否过长

### Q4: 如何查看加载了哪些 Memory？

```bash
/memory
```

### Q5: @ 引用的文件会占用多少上下文？

引用的文件内容会完整展开，需要控制引用文件的大小。

---

## 十、检查清单

### 新建 Memory 文件时

```markdown
□ 文件放在正确的位置
□ 文件名符合命名规范
□ 内容精简，无冗余
□ 敏感信息放在 .local.md
□ 已添加到 .gitignore (如需要)
```

### 修改 CLAUDE.md 时

```markdown
□ 行数仍在 200 行以内
□ 删除的内容 Claude 能自己推断
□ 新增的内容确实必要
□ 详细内容考虑移到 rules/
```

### 项目交接时

```markdown
□ 确保 CLAUDE.md 是最新的
□ 更新 rules/ 中的过时信息
□ 记录项目特有的约定
□ 清理不再需要的规则
```
